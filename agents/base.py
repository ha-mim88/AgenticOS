"""
Base Agent class for AgenticOS.

Defines the agent lifecycle and interface.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, Any
import logging
import uuid

from core.messaging import Event, EventType, MessageBroker
from core.registry import AgentRegistry, AgentState

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    status: str  # "success", "failed", "timeout"
    result: Any = None
    error: Optional[str] = None


class Agent(ABC):
    """
    Base class for all agents in AgenticOS.

    Subclasses must implement:
    - initialize()
    - on_message()
    - shutdown()
    """

    # Subclasses should override these
    agent_type: str = "base_agent"
    capabilities: list = []

    def __init__(
        self,
        agent_id: str,
        message_broker: MessageBroker,
        registry: AgentRegistry,
        config: Dict = None
    ):
        """
        Initialize the agent.

        Args:
            agent_id: Unique identifier for this agent
            message_broker: Message broker instance
            registry: Agent registry instance
            config: Optional configuration dict
        """
        self.agent_id = agent_id
        self.message_broker = message_broker
        self.registry = registry
        self.config = config or {}
        self._state = AgentState.INIT
        self._running = False
        logger.info(f"Agent {self.agent_id} initialized")

    @property
    def state(self) -> AgentState:
        """Get current agent state."""
        return self._state

    @state.setter
    def state(self, value: AgentState) -> None:
        """Set agent state."""
        self._state = value

    async def startup(self) -> None:
        """
        Start the agent (internal method).

        Handles registration and initialization.
        """
        try:
            # Register with registry
            await self.registry.register_agent(
                self.agent_id,
                self.agent_type,
                self.capabilities,
            )

            # Subscribe to messages
            await self.message_broker.subscribe(
                self.agent_id,
                "*",  # Subscribe to all event types
                self.on_message
            )

            # Call subclass initialization
            await self.initialize()

            # Mark as running
            self._running = True
            self.state = AgentState.RUNNING
            logger.info(f"Agent {self.agent_id} started successfully")

        except Exception as e:
            logger.error(f"Agent {self.agent_id} startup failed: {e}")
            self.state = AgentState.ERROR
            raise

    async def stop(self) -> None:
        """
        Stop the agent gracefully (internal method).

        Handles cleanup and unregistration.
        """
        try:
            self.state = AgentState.SHUTDOWN
            self._running = False

            # Call subclass shutdown
            await self.shutdown()

            # Unregister from registry
            await self.registry.unregister_agent(self.agent_id)

            logger.info(f"Agent {self.agent_id} stopped successfully")

        except Exception as e:
            logger.error(f"Agent {self.agent_id} shutdown error: {e}")
            self.state = AgentState.ERROR

    @abstractmethod
    async def initialize(self) -> None:
        """
        Called once on agent startup.

        Override in subclass to perform initialization tasks.
        """
        pass

    @abstractmethod
    async def on_message(self, event: Event) -> None:
        """
        Handle incoming messages.

        Override in subclass to implement message handling logic.

        Args:
            event: Incoming event/message
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Called on agent termination.

        Override in subclass to perform cleanup tasks.
        """
        pass

    async def execute_task(
        self,
        task_id: str,
        action: str,
        params: Dict = None,
        timeout: float = 30.0
    ) -> TaskResult:
        """
        Execute a task with error handling and timeout.

        Args:
            task_id: Unique task identifier
            action: Action/method name
            params: Task parameters
            timeout: Execution timeout in seconds

        Returns:
            TaskResult with status and output
        """
        params = params or {}

        try:
            self.state = AgentState.WORKING
            await self.registry.update_agent_state(self.agent_id, AgentState.WORKING)

            logger.debug(f"Agent {self.agent_id} executing task {task_id}: {action}")

            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    self._execute_action(action, params),
                    timeout=timeout
                )

                return TaskResult(
                    task_id=task_id,
                    status="success",
                    result=result
                )

            except asyncio.TimeoutError:
                error_msg = f"Task {task_id} timed out after {timeout}s"
                logger.error(error_msg)
                return TaskResult(
                    task_id=task_id,
                    status="timeout",
                    error=error_msg
                )

        except Exception as e:
            error_msg = f"Task {task_id} execution failed: {e}"
            logger.error(error_msg)
            return TaskResult(
                task_id=task_id,
                status="failed",
                error=error_msg
            )

        finally:
            self.state = AgentState.RUNNING
            await self.registry.update_agent_state(self.agent_id, AgentState.RUNNING)

    async def _execute_action(self, action: str, params: Dict) -> Any:
        """
        Execute a specific action (subclass can override).

        Args:
            action: Action name
            params: Action parameters

        Returns:
            Action result

        Raises:
            NotImplementedError: If action not implemented
        """
        raise NotImplementedError(f"Action {action} not implemented")

    async def send_message(
        self,
        recipient: str,
        action: str,
        data: Dict = None,
        event_type: EventType = EventType.COMMAND,
        priority: int = 0
    ) -> None:
        """
        Send a message to another agent.

        Args:
            recipient: Target agent ID or "*" for broadcast
            action: Action to invoke
            data: Message payload
            event_type: Type of event
            priority: Message priority (0-100)
        """
        event = Event(
            event_id=str(uuid.uuid4()),
            sender=self.agent_id,
            recipient=recipient,
            event_type=event_type,
            action=action,
            data=data or {},
            priority=priority,
        )

        await self.message_broker.publish(event)
        logger.debug(
            f"Agent {self.agent_id} sent message to {recipient}: {action}"
        )

    async def emit_metric(
        self,
        name: str,
        value: float,
        labels: Dict = None
    ) -> None:
        """
        Emit a telemetry metric.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels

        Note: This is a placeholder; real implementation depends on observability system.
        """
        labels = labels or {}
        labels["agent_id"] = self.agent_id
        # TODO: Integrate with observability system
        logger.debug(f"Metric {name}={value} labels={labels}")


__all__ = ["Agent", "TaskResult"]


