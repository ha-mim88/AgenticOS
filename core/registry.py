"""
Agent Registry for AgenticOS.

Manages agent registration, discovery, and lifecycle state tracking.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Enumeration of agent lifecycle states."""
    INIT = "init"           # Agent spawned, initializing
    RUNNING = "running"     # Ready to accept messages
    PAUSED = "paused"       # Temporarily suspended
    WORKING = "working"     # Processing task
    SHUTDOWN = "shutdown"   # Graceful stop in progress
    ERROR = "error"         # Unrecoverable error state


@dataclass
class AgentMetadata:
    """Metadata about a registered agent."""
    agent_id: str
    agent_type: str
    capabilities: List[str] = field(default_factory=list)
    state: AgentState = AgentState.INIT
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


class AgentRegistry:
    """
    Central registry for agent discovery and state management.
    """
    
    def __init__(self):
        """Initialize the registry."""
        self.agents: Dict[str, AgentMetadata] = {}
        self._capability_index: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
        self._metrics = {
            "total_registered": 0,
            "total_unregistered": 0,
        }

    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str],
        tags: Dict[str, str] = None,
        metadata: Dict = None
    ) -> None:
        """
        Register a new agent.
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Type/class of agent
            capabilities: List of capabilities this agent provides
            tags: Optional tags for grouping
            metadata: Optional metadata
            
        Raises:
            ValueError: If agent_id already registered
        """
        async with self._lock:
            if agent_id in self.agents:
                raise ValueError(f"Agent {agent_id} already registered")
            
            agent = AgentMetadata(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities,
                tags=tags or {},
                metadata=metadata or {},
            )
            
            self.agents[agent_id] = agent
            
            # Update capability index
            for capability in capabilities:
                if capability not in self._capability_index:
                    self._capability_index[capability] = set()
                self._capability_index[capability].add(agent_id)
            
            self._metrics["total_registered"] += 1
            logger.info(
                f"Agent {agent_id} ({agent_type}) registered "
                f"with capabilities: {capabilities}"
            )

    async def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister an agent.
        
        Args:
            agent_id: Agent to unregister
            
        Raises:
            ValueError: If agent not registered
        """
        async with self._lock:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent = self.agents[agent_id]
            
            # Remove from capability index
            for capability in agent.capabilities:
                if capability in self._capability_index:
                    self._capability_index[capability].discard(agent_id)
                    if not self._capability_index[capability]:
                        del self._capability_index[capability]
            
            del self.agents[agent_id]
            self._metrics["total_unregistered"] += 1
            logger.info(f"Agent {agent_id} unregistered")

    async def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """
        Get agent metadata.
        
        Args:
            agent_id: Agent to retrieve
            
        Returns:
            Agent metadata or None if not found
        """
        return self.agents.get(agent_id)

    async def update_agent_state(
        self,
        agent_id: str,
        state: AgentState
    ) -> None:
        """
        Update agent state.
        
        Args:
            agent_id: Agent to update
            state: New state
            
        Raises:
            ValueError: If agent not registered
        """
        async with self._lock:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            self.agents[agent_id].state = state
            self.agents[agent_id].last_heartbeat = datetime.utcnow()
            logger.debug(f"Agent {agent_id} state updated to {state.value}")

    async def update_agent_heartbeat(self, agent_id: str) -> None:
        """
        Update agent last heartbeat time.
        
        Args:
            agent_id: Agent to update
        """
        if agent_id in self.agents:
            async with self._lock:
                if agent_id in self.agents:
                    self.agents[agent_id].last_heartbeat = datetime.utcnow()

    async def list_agents_by_capability(self, capability: str) -> List[str]:
        """
        Find all agents with a specific capability.
        
        Args:
            capability: Capability name
            
        Returns:
            List of agent IDs
        """
        return list(self._capability_index.get(capability, set()))

    async def list_agents_by_state(self, state: AgentState) -> List[str]:
        """
        Find all agents in a specific state.
        
        Args:
            state: Agent state
            
        Returns:
            List of agent IDs
        """
        return [
            agent_id
            for agent_id, agent in self.agents.items()
            if agent.state == state
        ]

    async def list_all_agents(self) -> List[AgentMetadata]:
        """
        Get all registered agents.
        
        Returns:
            List of all agent metadata
        """
        return list(self.agents.values())

    async def get_registry_status(self) -> Dict:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with registry status
        """
        state_counts = {}
        for state in AgentState:
            count = len(await self.list_agents_by_state(state))
            state_counts[state.value] = count
        
        return {
            "total_agents": len(self.agents),
            "state_distribution": state_counts,
            "capabilities": len(self._capability_index),
            "metrics": self._metrics.copy(),
        }


__all__ = ["AgentRegistry", "AgentMetadata", "AgentState"]

