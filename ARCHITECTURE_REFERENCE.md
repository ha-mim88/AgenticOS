# Architecture Reference: Mermaid Flowchart to Implementation

This document maps the provided Mermaid flowchart to the implemented AgenticOS codebase.

## Flowchart Architecture

```
flowchart TD

    %% === External Interaction Layer ===
    U[User / Client Apps] --> GW[API Gateway / Frontend]
    GW --> AUTH[Authentication & Rate Limiter]
    AUTH --> ROUTE[Protocol Handlers: REST / gRPC / WebSocket]

    %% === Agent Orchestration Layer ===
    ROUTE --> AM[Agent Manager]
    AM --> POOL[Agent Pool]
    AM --> SCHED[Agent Scheduler]

    %% === Workflow & Processing Layer ===
    SCHED --> WF[Workflow Engine]
    WF --> TM[Task Manager]
    TM --> PROC[Process Manager]

    %% === Intelligence Layer ===
    PROC --> LLM[LLM Services]
    PROC --> MEM[Memory Store]
    PROC --> KG[Knowledge Graph / Vector DB]
    PROC --> GR[Guardrails & Policy Engine]

    %% === Infrastructure Layer ===
    LLM --> OBS[Observability / Telemetry]
    MEM --> OBS
    KG --> OBS
    GR --> OBS

    %% === Data Layer ===
    OBS --> DB[(Databases: SQL/NoSQL)]
    OBS --> DW[(Data Warehouse)]
    OBS --> LOG[(Logs & Metrics Store)]

    %% === External Services ===
    LLM --> EXT[External AI APIs]
    KG --> EXT
    DB --> CLOUD[Cloud Storage]
```

---

## Implementation Mapping

### Layer 1: External Interaction
**Status:** Phase 2 (Scaffolded) 🔲

| Component | File | Status |
|-----------|------|--------|
| API Gateway | `api/gateway.py` | 🔲 TODO |
| Protocol Handlers | `api/handlers/*.py` | 🔲 TODO |
| - REST Handler | `api/handlers/rest_handler.py` | 🔲 TODO |
| - gRPC Handler | `api/handlers/grpc_handler.py` | 🔲 TODO |
| - WebSocket Handler | `api/handlers/websocket_handler.py` | 🔲 TODO |

```python
# Next Phase Implementation Pattern
from api.gateway import APIGateway
from api.handlers.rest_handler import handle_rest_request

gateway = APIGateway()
await gateway.handle_request(request)
```

### Layer 2: Authentication & Rate Limiting
**Status:** Phase 2 (Scaffolded) 🔲

| Component | File | Status |
|-----------|------|--------|
| Authentication | `api/auth.py` | 🔲 TODO |
| Rate Limiter | `api/auth.py` | 🔲 TODO |

```python
# Next Phase Implementation Pattern
from api.auth import AuthManager

auth = AuthManager()
user = await auth.validate_token(token)
within_limit = await auth.check_rate_limit(client_id)
```

### Layer 3: Agent Orchestration
**Status:** Phase 2-3 (Scaffolded) 🔲

| Component | File | Status |
|-----------|------|--------|
| Agent Manager | `agents/manager.py` | 🔲 TODO |
| Agent Pool | `agents/pool.py` | 🔲 TODO |
| Agent Scheduler | `agents/scheduler.py` | 🔲 TODO |

```python
# Next Phase Implementation Pattern
from agents.manager import AgentManager

manager = AgentManager()
agent_id = await manager.create_agent("worker", config)
await manager.route_task_to_agent(task, capabilities)
```

### Layer 4: Workflow & Processing
**Status:** Phase 4 (Scaffolded) 🔲

| Component | File | Status |
|-----------|------|--------|
| Workflow Engine | `workflow/__init__.py` | 🔲 TODO |
| Task Manager | `workflow/task_manager.py` | 🔲 TODO |
| Process Manager | `workflow/process_manager.py` | 🔲 TODO |

```python
# Next Phase Implementation Pattern
from workflow import WorkflowEngine

engine = WorkflowEngine()
result = await engine.execute_workflow(workflow_def)
```

### Layer 5: Intelligence Layer
**Status:** Phase 5 (Scaffolded) 🔲

| Component | File | Status |
|-----------|------|--------|
| LLM Services | `intelligence/llm_service.py` | 🔲 TODO |
| Memory Store | `intelligence/memory.py` | 🔲 TODO |
| Knowledge Graph | `intelligence/knowledge_graph.py` | 🔲 TODO |
| Guardrails | `intelligence/guardrails.py` | 🔲 TODO |

```python
# Next Phase Implementation Pattern
from intelligence.llm_service import LLMService
from intelligence.memory import MemoryStore
from intelligence.knowledge_graph import KnowledgeGraph

llm = LLMService()
response = await llm.call_llm("prompt", model="gpt-4")

memory = MemoryStore()
await memory.store_memory(agent_id, key, value)

kg = KnowledgeGraph()
await kg.add_entity(entity_id, entity_type, properties)
```

### Layer 6: Infrastructure & Observability
**Status:** Phase 6 (Scaffolded) 🔲

| Component | File | Status |
|-----------|------|--------|
| Observability | `infrastructure/__init__.py` | 🔲 TODO |

```python
# Next Phase Implementation Pattern
from infrastructure import Observability

obs = Observability()
await obs.record_metric("latency", 125.5)
await obs.start_trace(trace_id, "operation")
health = await obs.health_check()
```

### Layer 7: Data Layer
**Status:** Phase 7 (Scaffolded) 🔲

| Component | File | Status |
|-----------|------|--------|
| Database | `data/__init__.py` | 🔲 TODO |
| Data Warehouse | `data/warehouse.py` | 🔲 TODO |
| Logs & Metrics | `data/logs_store.py` | 🔲 TODO |

```python
# Next Phase Implementation Pattern
from data import Database

db = Database()
rows = await db.query("SELECT * FROM agents")
await db.execute("INSERT INTO agents ...")
```

### Layer 8: External Services
**Status:** Phase 8 (Scaffolded) 🔲

| Component | File | Status |
|-----------|------|--------|
| External AI APIs | `external/ai_providers.py` | 🔲 TODO |
| Cloud Storage | `external/cloud_storage.py` | 🔲 TODO |

```python
# Next Phase Implementation Pattern
from external.ai_providers import ExternalAIProvider
from external.cloud_storage import CloudStorage

ai = ExternalAIProvider()
response = await ai.call_llm(prompt, model="claude-2")

storage = CloudStorage()
await storage.upload_file(filename, destination)
```

### Layer 9: Core Foundation (IMPLEMENTED ✅)
**Status:** Phase 1 (Complete) ✅

#### Message & Event System
| Component | File | Status |
|-----------|------|--------|
| MessageBroker | `core/messaging.py` | ✅ COMPLETE |
| Event System | `core/messaging.py` | ✅ COMPLETE |

**Current Usage:**
```python
from core.messaging import MessageBroker, Event, EventType

broker = MessageBroker()
await broker.initialize()

event = Event(
    sender="agent_1",
    recipient="agent_2",
    event_type=EventType.COMMAND,
    action="do_work",
    data={"param": "value"}
)

await broker.publish(event)
```

#### Agent Registry
| Component | File | Status |
|-----------|------|--------|
| AgentRegistry | `core/registry.py` | ✅ COMPLETE |
| AgentMetadata | `core/registry.py` | ✅ COMPLETE |
| AgentState | `core/registry.py` | ✅ COMPLETE |

**Current Usage:**
```python
from core.registry import AgentRegistry

registry = AgentRegistry()

await registry.register_agent(
    agent_id="agent_1",
    agent_type="worker",
    capabilities=["compute", "storage"]
)

agents = await registry.list_agents_by_capability("compute")
```

#### Base Agent Class
| Component | File | Status |
|-----------|------|--------|
| Agent Base Class | `agents/base.py` | ✅ COMPLETE |
| TaskResult | `agents/base.py` | ✅ COMPLETE |

**Current Usage:**
```python
from agents import Agent
from core.messaging import Event

class MyAgent(Agent):
    agent_type = "my_agent"
    capabilities = ["my_capability"]
    
    async def initialize(self):
        print("Starting up...")
    
    async def on_message(self, event: Event):
        print(f"Received: {event.action}")
    
    async def shutdown(self):
        print("Shutting down...")

agent = MyAgent(agent_id="ma1", message_broker=broker, registry=registry)
await agent.startup()
```

#### Configuration Management
| Component | File | Status |
|-----------|------|--------|
| ConfigManager | `config/__init__.py` | ✅ COMPLETE |
| Settings File | `config/settings.yaml` | ✅ COMPLETE |

**Current Usage:**
```python
from config import ConfigManager

config = ConfigManager()
port = config.get("api.port", 8000)
debug = config.get("debug", False)
```

#### Error Handling
| Component | File | Status |
|-----------|------|--------|
| Exception Hierarchy | `core/exceptions.py` | ✅ COMPLETE |

**Available Exceptions:**
- `AgenticOSException` - Base
- `AgentNotFoundError`
- `CapabilityNotFoundError`
- `MessageRoutingError`
- `TaskExecutionError`
- `ConfigurationError`
- `AuthenticationError`
- `RateLimitExceededError`
- `WorkflowExecutionError`
- `GuardrailViolationError`

---

## Data Flow Through Layers

### Request Processing Flow
```
HTTP/gRPC/WebSocket Request
    ↓ [Layer 1]
APIGateway.handle_request()
    ↓ [Layer 2]
AUTH.validate_token()
AUTH.check_rate_limit()
    ↓ [Layer 1]
ROUTE.protocol_handler()
    ↓ [Layer 3]
AgentManager.route_task_to_agent()
    ↓
AgentScheduler.schedule_task()
    ↓ [Layer 3]
Select Agent from Pool
    ↓ [Layer 4]
WorkflowEngine.execute_workflow()
    ↓ [Layer 5]
Process Task (invoke LLM, query Memory/KG, check Guardrails)
    ↓ [Layer 5]
LLMService → External APIs
Memory/KG → Vector DB
Guardrails → Policy Engine
    ↓ [Layer 6]
Observability.record_metric() / audit_log()
    ↓ [Layer 7]
Store in Database / Warehouse / Logs
    ↓
Response back through layers
```

### Agent Communication Flow
```
Agent A
    ↓
send_message()
    ↓ [Layer 9 - Core]
MessageBroker.publish(Event)
    ↓
Priority Queue
    ↓
RoutingLoop
    ↓
Find Recipients (via Registry)
    ↓
Agent B.on_message(Event)
    ↓
Process event
    ↓
Optional: send_message() back to Agent A
```

---

## Integration Points Ready for Phase 2+

### 1. How REST API Connects (Phase 2)
```python
# In api/handlers/rest_handler.py (to be implemented)
from api.gateway import APIGateway
from agents.manager import AgentManager

@app.post("/tasks")
async def create_task(request: TaskRequest):
    # Parse request
    task = Task.from_request(request)
    
    # Route through manager (connects to Layer 3)
    agent_id = await manager.route_task_to_agent(
        task,
        required_capabilities=task.capabilities
    )
    
    # Return agent_id to client
    return {"task_id": task.id, "agent_id": agent_id}
```

### 2. How Agents Execute Tasks (Current ✅)
```python
# In agents/base.py (already implemented)
async def execute_task(self, task_id, action, params, timeout=30.0):
    try:
        result = await asyncio.wait_for(
            self._execute_action(action, params),
            timeout=timeout
        )
        return TaskResult(status="success", result=result)
    except Exception as e:
        return TaskResult(status="failed", error=str(e))
```

### 3. How Intelligence Services Connect (Phase 5)
```python
# In agents/base.py _execute_action override (subclass implementation)
class AIAgent(Agent):
    async def _execute_action(self, action, params):
        if action == "analyze_text":
            # Gets integrated in Phase 5
            from intelligence.llm_service import LLMService
            llm = LLMService()
            return await llm.call_llm(params["text"])
```

### 4. How Observability Integrates (Phase 6)
```python
# In agents/base.py (ready for Phase 6)
async def execute_task(self, task_id, action, params, timeout=30.0):
    # Already calls emit_metric() in Agent base class
    await self.emit_metric("task.started", 1, {"task_id": task_id})
    
    # Phase 6 will connect this to infrastructure.observability
```

---

## File Reference for Each Flowchart Component

| Flowchart Component | Implementation File(s) | Phase | Status |
|---|---|---|---|
| User / Client Apps | N/A (External) | - | - |
| API Gateway | `api/gateway.py` | 2 | 🔲 |
| REST Handler | `api/handlers/rest_handler.py` | 2 | 🔲 |
| gRPC Handler | `api/handlers/grpc_handler.py` | 2 | 🔲 |
| WebSocket Handler | `api/handlers/websocket_handler.py` | 2 | 🔲 |
| Authentication | `api/auth.py` | 2 | 🔲 |
| Rate Limiter | `api/auth.py` | 2 | 🔲 |
| Agent Manager | `agents/manager.py` | 3 | 🔲 |
| Agent Pool | `agents/pool.py` | 3 | 🔲 |
| Agent Scheduler | `agents/scheduler.py` | 3 | 🔲 |
| Workflow Engine | `workflow/__init__.py` | 4 | 🔲 |
| Task Manager | `workflow/task_manager.py` | 4 | 🔲 |
| Process Manager | `workflow/process_manager.py` | 4 | 🔲 |
| LLM Services | `intelligence/llm_service.py` | 5 | 🔲 |
| Memory Store | `intelligence/memory.py` | 5 | 🔲 |
| Knowledge Graph | `intelligence/knowledge_graph.py` | 5 | 🔲 |
| Guardrails | `intelligence/guardrails.py` | 5 | 🔲 |
| Observability | `infrastructure/__init__.py` | 6 | 🔲 |
| Databases | `data/__init__.py` | 7 | 🔲 |
| Data Warehouse | `data/warehouse.py` | 7 | 🔲 |
| Logs & Metrics | `data/logs_store.py` | 7 | 🔲 |
| External AI APIs | `external/ai_providers.py` | 8 | 🔲 |
| Cloud Storage | `external/cloud_storage.py` | 8 | 🔲 |
| Core Foundation | Multiple files | 1 | ✅ |

---

## Next Steps for Phase 2 Development

1. **Implement APIGateway** (`api/gateway.py`)
   - Request parsing and validation
   - Route to protocol handlers
   - Response envelope formatting

2. **Implement REST Handler** (`api/handlers/rest_handler.py`)
   - FastAPI endpoints (GET, POST, PUT, DELETE)
   - Request/response serialization
   - Connect to AgentManager

3. **Implement Authentication** (`api/auth.py`)
   - JWT token validation
   - Token bucket rate limiter
   - Error responses

4. **Implement Protocol Routing**
   - gRPC service definitions
   - WebSocket connection manager
   - Message format conversion to/from Events

---

## Architecture Validation

✅ **Core Foundation (Phase 1):** Fully implemented and tested
✅ **Message System:** Event routing ready
✅ **Agent System:** Base class and registry ready
✅ **Configuration:** Dynamic settings loaded
✅ **Error Handling:** Custom exception framework

🔲 **API Layer (Phase 2):** Ready to implement
🔲 **Intelligent Features (Phases 5+):** Ready to implement
🔲 **Data Integration (Phases 7):** Ready to implement

---

**Document Version:** 1.0 | **Created:** June 2026 | **Status:** Phase 1 Complete

