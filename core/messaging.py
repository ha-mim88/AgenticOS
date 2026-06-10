"""
Event and Message Broker for AgenticOS.

Handles asynchronous message passing between agents.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Set, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enumeration of event types."""
    COMMAND = "command"          # Request to execute action
    RESPONSE = "response"         # Response to command
    EVENT = "event"              # General event notification
    ERROR = "error"              # Error event


@dataclass
class Event:
    """
    Represents a message/event in the system.
    
    Attributes:
        event_id: Unique identifier
        sender: Source agent ID
        recipient: Target agent ID or "*" for broadcast
        event_type: Type of event (command, response, event, error)
        action: Method/function name
        data: Payload
        timestamp: When event was created
        priority: 0-100, higher = more urgent
        trace_id: For distributed tracing
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    recipient: str = "*"
    event_type: EventType = EventType.EVENT
    action: str = ""
    data: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: int = 0
    trace_id: Optional[str] = None

    def __lt__(self, other):
        """For priority queue ordering (higher priority = lower value)."""
        return self.priority > other.priority


class MessageBroker:
    """
    Routes events between agents asynchronously.
    
    Implements publish-subscribe pattern with priority queue support.
    """
    
    def __init__(self, max_queue_size: int = 10000):
        """
        Initialize message broker.
        
        Args:
            max_queue_size: Maximum pending messages before blocking
        """
        self.event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(
            maxsize=max_queue_size
        )
        self.subscribers: Dict[str, Dict[str, Set[Callable]]] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._metrics = {
            "messages_published": 0,
            "messages_routed": 0,
            "errors": 0,
        }

    async def initialize(self) -> None:
        """Start the message broker event loop."""
        if self._running:
            logger.warning("MessageBroker already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._route_loop())
        logger.info("MessageBroker initialized")

    async def shutdown(self) -> None:
        """Gracefully shut down the broker."""
        self._running = False
        if self._task:
            await self._task
        logger.info("MessageBroker shut down")

    async def publish(self, event: Event) -> None:
        """
        Publish an event to subscribers.
        
        Args:
            event: Event to publish
            
        Raises:
            asyncio.QueueFull: If queue is full
        """
        try:
            # Use negative priority so higher priority = processed first
            await self.event_queue.put((event.priority, event))
            self._metrics["messages_published"] += 1
            logger.debug(
                f"Published event {event.event_id} from {event.sender} "
                f"to {event.recipient} (priority={event.priority})"
            )
        except asyncio.QueueFull:
            logger.error(f"MessageBroker queue full, rejecting event {event.event_id}")
            self._metrics["errors"] += 1
            raise

    async def subscribe(
        self,
        agent_id: str,
        event_type: str,
        handler: Callable
    ) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            agent_id: Agent subscribing
            event_type: Event type filter (or "*" for all)
            handler: Async callable to invoke on matching events
        """
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = {}
        
        if event_type not in self.subscribers[agent_id]:
            self.subscribers[agent_id][event_type] = set()
        
        self.subscribers[agent_id][event_type].add(handler)
        logger.debug(f"Agent {agent_id} subscribed to {event_type} events")

    async def unsubscribe(
        self,
        agent_id: str,
        event_type: str,
        handler: Callable
    ) -> None:
        """Remove a subscription."""
        if (agent_id in self.subscribers and 
            event_type in self.subscribers[agent_id]):
            self.subscribers[agent_id][event_type].discard(handler)

    async def _route_loop(self) -> None:
        """Main event routing loop (runs continuously)."""
        logger.info("MessageBroker routing loop started")
        
        while self._running:
            try:
                # Get next event (with timeout to check _running flag)
                try:
                    _, event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Route to subscribers
                await self._route_event(event)
                self._metrics["messages_routed"] += 1
                
            except Exception as e:
                logger.error(f"Error in message routing loop: {e}")
                self._metrics["errors"] += 1

        logger.info("MessageBroker routing loop stopped")

    async def _route_event(self, event: Event) -> None:
        """
        Route an event to matching subscribers.
        
        Args:
            event: Event to route
        """
        recipients = self._find_recipients(event)
        
        if not recipients:
            logger.debug(f"No subscribers for event {event.event_id}")
            return
        
        # Send to all matching subscribers concurrently
        tasks = []
        for agent_id, handlers in recipients.items():
            for handler in handlers:
                # Don't await; collect all tasks
                tasks.append(
                    asyncio.create_task(self._invoke_handler(agent_id, handler, event))
                )
        
        # Wait for all handlers with timeout
        if tasks:
            try:
                await asyncio.wait(tasks, timeout=30.0)
            except Exception as e:
                logger.error(f"Error waiting for handlers: {e}")

    def _find_recipients(self, event: Event) -> Dict[str, Set[Callable]]:
        """
        Find agents that should receive this event.
        
        Args:
            event: Event to find recipients for
            
        Returns:
            Dict mapping agent_id to set of handlers
        """
        recipients = {}
        
        # Broadcast: send to all subscribers
        if event.recipient == "*":
            for agent_id, event_types in self.subscribers.items():
                # Check for specific event type or wildcard subscription
                matching_handlers = set()
                if event.event_type.value in event_types:
                    matching_handlers.update(event_types[event.event_type.value])
                if "*" in event_types:
                    matching_handlers.update(event_types["*"])
                
                if matching_handlers:
                    recipients[agent_id] = matching_handlers
        
        # Targeted: send to specific recipient
        elif event.recipient in self.subscribers:
            agent_subs = self.subscribers[event.recipient]
            matching_handlers = set()
            
            if event.event_type.value in agent_subs:
                matching_handlers.update(agent_subs[event.event_type.value])
            if "*" in agent_subs:
                matching_handlers.update(agent_subs["*"])
            
            if matching_handlers:
                recipients[event.recipient] = matching_handlers
        
        return recipients

    async def _invoke_handler(
        self,
        agent_id: str,
        handler: Callable,
        event: Event
    ) -> None:
        """
        Invoke a single handler safely.
        
        Args:
            agent_id: ID of receiving agent
            handler: Handler function
            event: Event being handled
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(
                f"Handler error for agent {agent_id} processing event {event.event_id}: {e}"
            )
            self._metrics["errors"] += 1

    def get_metrics(self) -> Dict:
        """Get broker metrics."""
        return {
            **self._metrics,
            "queue_size": self.event_queue.qsize(),
            "active_subscriptions": sum(
                len(types) for types in self.subscribers.values()
            ),
        }


__all__ = ["Event", "EventType", "MessageBroker"]

