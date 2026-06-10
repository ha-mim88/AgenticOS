# AGENTS.md: AgenticOS Developer Guide

This guide helps AI agents contribute effectively to AgenticOS, an agent-based operating system framework.

## Project Vision

AgenticOS is a Python-based framework for building and managing autonomous agents with system-level capabilities. The architecture follows an event-driven, multi-agent design where agents can:
- Execute tasks concurrently
- Communicate via message passing
- Access shared resources and capabilities
- Self-organize based on workload

## Architecture Principles

### 1. Agent-Centric Design
- Each agent is a discrete, long-lived entity with its own lifecycle
- Agents expose capabilities through a unified interface
- Minimal coupling between agents; communicate through well-defined protocols

### 2. Event-Driven Execution
- Agents react to events (messages, timers, resource availability)
- Non-blocking operations; async/concurrent where possible
- Event queue acts as coordinator and buffer

### 3. Capability-Based Access
- Resources and operations are exposed as capabilities
- Agents must declare required capabilities at initialization
- Runtime validation prevents unauthorized access

## Code Organization

**Expected module structure:**
```
AgenticOS/
├── main.py              # Entry point; initializes system
├── agents/              # Agent implementations
│   ├── __init__.py
│   ├── base.py         # Agent base class and lifecycle
│   ├── executor.py     # Execution engine for agent tasks
│   └── builtin/        # Standard agents (logger, scheduler, etc.)
├── core/               # Core system components
│   ├── __init__.py
│   ├── messaging.py    # Event/message passing system
│   ├── registry.py     # Agent registry & discovery
│   └── capabilities.py # Capability definitions
├── config/             # Configuration and schemas
└── tests/              # Test suite
```

## Key Patterns & Conventions

### Agent Implementation
All agents should extend `agents.base.Agent`:
```python
from agents.base import Agent

class MyAgent(Agent):
    agent_type = "my_agent"
    capabilities = ["read_data", "log_info"]
    
    async def initialize(self):
        """Called on agent startup"""
        pass
    
    async def on_message(self, message):
        """Handle incoming messages"""
        pass
    
    async def shutdown(self):
        """Cleanup on agent stop"""
        pass
```

### Message Format
All inter-agent communication uses this format:
```python
{
    "sender": "agent_id",
    "recipient": "agent_id" or "*",  # * for broadcast
    "type": "command|response|event",
    "action": "method_name",
    "data": { ... },
    "timestamp": ISO8601
}
```

### Async-First Approach
- Use `async/await` for all I/O-bound operations
- Define event handlers as async coroutines
- Never block the event loop; offload CPU-intensive work

### Error Handling
- All agents must implement error recovery
- Propagate errors as error messages (not exceptions across agents)
- Log errors with context; include agent state in logs

## Development Workflows

### Running the System
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run main system
python main.py

# Run with debug logging
python main.py --debug
```

### Testing Agents
Place tests in `tests/` directory:
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=agents --cov=core
```

### Adding a New Agent
1. Create `agents/my_agent.py` extending `Agent`
2. Register capabilities in class definition
3. Add integration test in `tests/test_my_agent.py`
4. Update `agents/builtin/__init__.py` if it's a built-in

## Integration Points & Dependencies

### Configuration
- Use `config/` directory for system configuration
- Support environment variable overrides: `AGENTICSOS_*`
- Validate config at startup; fail fast on misconfiguration

### Logging
- All agents log via `core.logging` module
- Use structured logging with agent_id and action fields
- Log levels: DEBUG (detailed flow), INFO (events), WARN (anomalies), ERROR (failures)

### Resource Management
- Registry tracks active agents and their state
- Implement graceful shutdown in `shutdown()` method
- Clean up resources (files, connections) explicitly

## Performance Considerations

- **Concurrency**: Use `asyncio` for task concurrency; target 100+ concurrent agents
- **Memory**: Agents should be lightweight; ~1MB baseline per agent
- **Messaging**: Keep message payloads <1MB; batch large data transfers
- **Timeouts**: Use reasonable timeouts on inter-agent calls (default 30s)

## Common Pitfalls to Avoid

1. **Blocking I/O in agents**: Wrap blocking calls in `asyncio.to_thread()`
2. **Tight coupling between agents**: Always communicate via messages
3. **Unhandled message types**: Implement catch-all handlers or reject gracefully
4. **Circular dependencies**: Registry prevents direct imports between agents
5. **Stateful agents**: Keep agent state minimal; persist to external store if needed

## Quick Reference: Essential Files

| File | Purpose |
|------|---------|
| `agents/base.py` | `Agent` base class; defines lifecycle & interface |
| `core/messaging.py` | `MessageBroker`; routes messages between agents |
| `core/registry.py` | `AgentRegistry`; tracks agents and capabilities |
| `main.py` | System initialization and orchestration |

---

**Last Updated**: June 2026 | **Python Version**: 3.13+

