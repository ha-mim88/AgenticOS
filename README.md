# AgenticOS - Distributed Agent Operating System

A Python-based framework for building and managing autonomous agents with system-level capabilities. AgenticOS follows an event-driven, multi-agent design where agents execute tasks concurrently, communicate via message passing, and access shared resources and capabilities.

## 🏗️ Architecture

AgenticOS is structured in **9 layers**:

```
┌─────────────────────────────────────────────────────────────┐
│  1. External Interaction: REST / gRPC / WebSocket API       │
├─────────────────────────────────────────────────────────────┤
│  2. Auth & Rate Limiting: Token validation, rate control    │
├─────────────────────────────────────────────────────────────┤
│  3. Agent Orchestration: Manager, Pool, Scheduler           │
├─────────────────────────────────────────────────────────────┤
│  4. Workflow & Processing: Engine, Task Mgr, Process Mgr    │
├─────────────────────────────────────────────────────────────┤
│  5. Intelligence: LLM Services, Memory, Knowledge Graph     │
├─────────────────────────────────────────────────────────────┤
│  6. Infrastructure: Observability, Telemetry, Health        │
├─────────────────────────────────────────────────────────────┤
│  7. Data Layer: SQL/NoSQL, Data Warehouse, Logs             │
├─────────────────────────────────────────────────────────────┤
│  8. External Services: External AI APIs, Cloud Storage      │
├─────────────────────────────────────────────────────────────┤
│  9. Core Foundation: Messaging, Registry, Base Agent        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the system
python main.py

# 3. Run tests
python -m pytest tests/ -v
```

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Get started in 5 minutes
- **[AGENTS.md](AGENTS.md)** - AI guidance for developers
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Detailed roadmap (8 phases)
- **[TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)** - API specifications and components

## 🧩 Key Components

### Phase 1: Foundation (Complete ✅)

| Component | File | Status | Purpose |
|---|---|---|---|
| **MessageBroker** | `core/messaging.py` | ✅ | Event routing & pub-sub |
| **AgentRegistry** | `core/registry.py` | ✅ | Agent discovery & state tracking |
| **Agent Base Class** | `agents/base.py` | ✅ | Agent lifecycle & interface |
| **Exceptions** | `core/exceptions.py` | ✅ | Error handling |
| **Configuration** | `config/__init__.py` | ✅ | System settings management |

### Phase 2-8: Planned

| Phase | Components | Status | ETA |
|---|---|---|---|
| Phase 2 | API Gateway, Auth, Protocol Handlers | 🔄 | Week 2-3 |
| Phase 3 | Agent Manager, Pool, Scheduler | 🔲 | Week 3-4 |
| Phase 4 | Workflow Engine, Task Mgr, Process Mgr | 🔲 | Week 4-5 |
| Phase 5 | LLM Services, Memory, KG, Guardrails | 🔲 | Week 5-7 |
| Phase 6 | Observability, Telemetry, Health | 🔲 | Week 6-7 |
| Phase 7 | Database, Warehouse, Logs | 🔲 | Week 7-8 |
| Phase 8 | External AI APIs, Cloud Storage | 🔲 | Week 8-9 |

## ⚡ Core Features

### Event-Driven Architecture
- Asynchronous message passing between agents
- Priority-based event queuing
- Publish-subscribe pattern

### Agent Lifecycle Management
- Registration in central registry
- State tracking (INIT, RUNNING, PAUSED, WORKING, SHUTDOWN, ERROR)
- Graceful startup/shutdown

### Task Execution
- Asynchronous task execution with timeouts
- Error handling and recovery
- Execution tracking

### Multi-Protocol Support
- **REST** - HTTP API endpoints
- **gRPC** - High-performance RPC
- **WebSocket** - Real-time bidirectional communication

### Intelligence Integration
- LLM service abstraction (OpenAI, Anthropic, etc.)
- Memory store for agent state
- Knowledge graph with vector embeddings
- Safety guardrails and policy engine

### Observability
- Structured logging
- Distributed tracing
- Metrics collection
- Health checks

## 🔧 Development

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_messaging.py -v

# With coverage
pytest tests/ --cov=core --cov=agents --cov-report=html
```

### Adding New Agents

```python
from agents import Agent
from core.messaging import Event

class CustomAgent(Agent):
    agent_type = "custom"
    capabilities = ["capability1", "capability2"]
    
    async def initialize(self):
        """Called on startup"""
        pass
    
    async def on_message(self, event: Event):
        """Handle incoming messages"""
        pass
    
    async def shutdown(self):
        """Called on shutdown"""
        pass
```

### Configuration

Edit `config/settings.yaml` or use environment variables (prefix `AGENTICSOS_`):

```yaml
agenticOS:
  api:
    host: "0.0.0.0"
    port: 8000
  agents:
    pool_size: 50
    max_agents: 200
  security:
    rate_limit: 1000
```

## 📊 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Agent Spawn Latency | <100ms | Create + initialize |
| Message Routing | <5ms p99 | 100k msgs/sec throughput |
| Memory per Agent | ~1-5MB | Depends on state |
| Concurrent Agents | 100+ | On modest hardware |

## 🛡️ Security

- Token-based authentication (JWT)
- Rate limiting (token bucket)
- Policy engine for action validation
- Audit logging for compliance
- Guardrails for AI safety

## 📦 Dependencies

Core dependencies include:
- `asyncio` - Asynchronous execution
- `fastapi` - REST API framework
- `pydantic` - Data validation
- `sqlalchemy` - Database abstraction
- `neo4j` - Knowledge graph
- `openai` / `anthropic` - LLM providers
- `prometheus-client` - Metrics
- `structlog` - Structured logging

See `requirements.txt` for full list.

## 🎯 Use Cases

1. **Multi-Agent Task Coordination** - Orchestrate many agents to accomplish complex tasks
2. **Distributed Workflow Execution** - Run workflows across multiple agents/machines
3. **AI Integration** - Seamlessly integrate LLMs into agent workflows
4. **System Monitoring** - Deploy agents to monitor and report on system state
5. **Knowledge Management** - Build intelligent systems with knowledge graphs
6. **Scalable Processing** - Process data at scale with distributed agents

## 🚦 Project Status

**Version**: 0.1.0 (Phase 1 Foundation Complete)

Current implementation includes Phase 1 foundation with:
- ✅ Message broker and event routing
- ✅ Agent registry and discovery
- ✅ Agent base class with lifecycle
- ✅ Error handling framework
- ✅ Configuration management

Upcoming phases will add:
- 🔄 API layer and protocol handlers
- 🔲 Advanced agent orchestration
- 🔲 Workflow execution engine
- 🔲 Intelligence integration
- 🔲 Observability and monitoring

## 📖 Learning Resources

1. **Start here**: [QUICK_START.md](QUICK_START.md)
2. **For AI agents**: [AGENTS.md](AGENTS.md)
3. **Full roadmap**: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
4. **API details**: [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)
5. **Code examples**: Check `tests/` directory

## 🤝 Contributing

When contributing to AgenticOS:

1. Follow the architecture patterns in `AGENTS.md`
2. Implement comprehensive tests in `tests/`
3. Update documentation when adding features
4. Use structured logging throughout
5. Follow async/await patterns for I/O operations

## 📄 License

[Add your license here]

## 📞 Support

For questions or issues:
1. Check the documentation in this repository
2. Review test files for usage examples
3. Check error logs for diagnostics
4. Refer to component-specific docstrings

---

**Last Updated**: June 2026 | **Python**: 3.13+ | **Status**: Active Development

