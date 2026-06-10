# AgenticOS Quick Start Guide

Welcome to AgenticOS! This guide will help you get the system up and running.

## Prerequisites

- Python 3.13+
- PowerShell (Windows) or Bash (Unix/Linux)
- pip (Python package manager)

## Installation

### 1. Activate Virtual Environment

```powershell
# On Windows PowerShell
.\.venv\Scripts\Activate.ps1

# On Linux/macOS bash
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running AgenticOS

### Start the System

```bash
python main.py
```

Expected output:
```
INFO - Starting AgenticOS...
INFO - MessageBroker started
INFO - AgenticOS initialized successfully
```

### Run Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_messaging.py -v

# Run with coverage
python -m pytest tests/ --cov=core --cov=agents
```

## Project Structure

```
AgenticOS/
├── main.py                  # Entry point
├── AGENTS.md               # AI guidance (this file)
├── IMPLEMENTATION_PLAN.md  # Detailed implementation roadmap
├── TECHNICAL_SPEC.md       # Technical specifications
├── requirements.txt        # Python dependencies
│
├── config/
│   ├── __init__.py        # ConfigManager
│   └── settings.yaml      # Configuration file
│
├── core/
│   ├── __init__.py
│   ├── messaging.py       # MessageBroker, Event handling
│   ├── registry.py        # AgentRegistry for discovery
│   ├── exceptions.py      # Custom exceptions
│   └── logging.py         # Structured logging (planned)
│
├── agents/
│   ├── __init__.py
│   ├── base.py           # Agent base class
│   ├── manager.py        # AgentManager
│   ├── pool.py           # AgentPool (planned)
│   ├── scheduler.py      # AgentScheduler (planned)
│   └── builtin/          # Built-in agents (planned)
│
├── api/
│   ├── __init__.py
│   ├── gateway.py        # APIGateway
│   ├── auth.py          # Authentication & rate limiting
│   └── handlers/        # Protocol handlers
│
├── workflow/
│   ├── __init__.py
│   ├── engine.py        # WorkflowEngine (planned)
│   ├── task_manager.py  # TaskManager (planned)
│   └── process_manager.py # ProcessManager (planned)
│
├── intelligence/
│   ├── __init__.py
│   ├── llm_service.py      # LLM integration (planned)
│   ├── memory.py           # Memory store (planned)
│   ├── knowledge_graph.py  # KG/Vector DB (planned)
│   └── guardrails.py       # Safety policies (planned)
│
├── infrastructure/
│   ├── __init__.py
│   └── observability.py    # Telemetry (planned)
│
├── data/
│   ├── __init__.py
│   ├── database.py        # DB abstraction (planned)
│   ├── warehouse.py       # Data warehouse (planned)
│   └── logs_store.py      # Log storage (planned)
│
├── external/
│   ├── __init__.py
│   ├── ai_providers.py    # External LLM APIs (planned)
│   └── cloud_storage.py   # Cloud storage (planned)
│
└── tests/
    └── test_messaging.py  # Messaging tests
```

## Key Components

### MessageBroker (core/messaging.py)
- Routes events between agents asynchronously
- Supports pub-sub pattern with priority queues

**Usage:**
```python
broker = MessageBroker()
await broker.initialize()

# Subscribe to events
await broker.subscribe(agent_id, "event_type", handler)

# Publish an event
event = Event(sender="agent_1", recipient="agent_2", action="do_work")
await broker.publish(event)
```

### Agent Registry (core/registry.py)
- Tracks registered agents and their capabilities
- Enables agent discovery

**Usage:**
```python
registry = AgentRegistry()

# Register an agent
await registry.register_agent(
    agent_id="my_agent",
    agent_type="worker",
    capabilities=["compute", "storage"]
)

# Find agents with specific capability
agents = await registry.list_agents_by_capability("compute")
```

### Agent Base Class (agents/base.py)
- Abstract base for all agents
- Handles lifecycle, messaging, and task execution

**Usage:**
```python
from agents import Agent

class MyAgent(Agent):
    agent_type = "my_agent"
    capabilities = ["custom_capability"]
    
    async def initialize(self):
        print("Agent started!")
    
    async def on_message(self, event):
        print(f"Received: {event.action}")
    
    async def shutdown(self):
        print("Agent stopping!")

# Startup
agent = MyAgent(agent_id="ma1", message_broker=broker, registry=registry)
await agent.startup()

# Send messages
await agent.send_message("other_agent", "do_something", {"param": "value"})

# Execute tasks
result = await agent.execute_task(
    task_id="task_1",
    action="my_action",
    params={"key": "value"}
)
```

## Configuration

Edit `config/settings.yaml` to customize:
- API host/port
- Agent pool size
- Workflow timeouts
- LLM provider and model
- Database connections
- Security settings (rate limits, auth)

Override settings with environment variables (prefix `AGENTICSOS_`):
```bash
# On Windows PowerShell
$env:AGENTICSOS_API_PORT = "9000"

# On Linux/bash
export AGENTICSOS_API_PORT=9000
```

## Common Tasks

### Create a Custom Agent

1. Create `agents/my_agent.py`:
```python
from agents import Agent
from core.messaging import Event

class MyCustomAgent(Agent):
    agent_type = "my_custom"
    capabilities = ["data_processing", "reporting"]
    
    async def initialize(self):
        await self.emit_metric("agent.initialized", 1)
    
    async def on_message(self, event: Event):
        if event.action == "process_data":
            result = await self.execute_task(
                task_id=event.event_id,
                action="process",
                params=event.data
            )
            await self.send_message(
                event.sender,
                "process_complete",
                {"result": result.result}
            )
    
    async def shutdown(self):
        pass
```

2. Spawn the agent in `main()`:
```python
agent = MyCustomAgent("custom_1", message_broker, agent_registry)
await agent.startup()
```

### Run Specific Tests

```bash
# Test messaging
pytest tests/test_messaging.py::test_publish_event -v

# Test with coverage
pytest tests/ --cov=core --cov=agents --cov-report=html
```

## Debugging

Enable debug logging:
```bash
python main.py --debug
```

Or set environment variable:
```bash
export AGENTICSOS_DEBUG=true
python main.py
```

## Next Steps

1. **Read AGENTS.md** for AI-focused guidance
2. **Read IMPLEMENTATION_PLAN.md** for phase-by-phase roadmap
3. **Read TECHNICAL_SPEC.md** for detailed API specifications
4. **Review core/messaging.py** to understand event routing
5. **Review agents/base.py** to understand agent lifecycle
6. **Explore tests/test_messaging.py** for usage examples

## Support

For issues or questions:
1. Check logs for error messages
2. Review relevant documentation above
3. Check existing tests for usage patterns
4. Add debug logging to understand flow

---

**Current Status**: Phase 1 Foundation Complete (v0.1.0)

**Next Phase**: API & Protocol Layer (REST/gRPC/WebSocket)

Last Updated: June 2026

