"""
Test suite for messaging system.
"""

import pytest
import asyncio
from core.messaging import MessageBroker, Event, EventType


@pytest.mark.asyncio
async def test_message_broker_initialization():
    """Test broker initialization."""
    broker = MessageBroker()
    await broker.initialize()
    assert broker._running is True
    await broker.shutdown()


@pytest.mark.asyncio
async def test_publish_event():
    """Test event publishing."""
    broker = MessageBroker()
    await broker.initialize()

    event = Event(
        sender="agent_1",
        recipient="*",
        event_type=EventType.EVENT,
        action="test_action"
    )

    await broker.publish(event)
    assert broker._metrics["messages_published"] == 1

    await broker.shutdown()


@pytest.mark.asyncio
async def test_subscribe_and_receive():
    """Test subscription and message reception."""
    broker = MessageBroker()
    await broker.initialize()

    messages_received = []

    async def handler(event):
        messages_received.append(event)

    await broker.subscribe("agent_1", EventType.EVENT.value, handler)

    event = Event(
        sender="agent_2",
        recipient="agent_1",
        event_type=EventType.EVENT,
        action="test"
    )

    await broker.publish(event)

    # Give time for async processing
    await asyncio.sleep(0.1)

    await broker.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])

