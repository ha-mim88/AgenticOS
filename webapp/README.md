# AgenticOS Workflow Web App

Full-stack web application for defining, testing, and monitoring **agentic workflows** using the AgenticOS Agent Provider API as the backend.

## Features

✅ **Workflow Management**
- Define workflows as Mermaid flowcharts
- Configure steps with LLM calls, branching, and agent orchestration
- Save and manage multiple workflows

✅ **Testing Sandbox**
- Execute workflows with custom JSON input
- Real-time execution tracking
- View step-by-step outputs and errors

✅ **Statistics & Monitoring**
- Track total executions, success/failure rates
- Monitor token usage per model
- View execution latency and performance
- Model-specific token accounting

✅ **Debugging & Logs**
- Detailed execution logs (INFO, WARNING, ERROR)
- Per-step logs for troubleshooting
- Metric collection (tokens, latency, model)

## Architecture

```
┌─────────────────────────────────────┐
│   Frontend (HTML/JS/Mermaid)        │
│   Skills • Testing • Dashboard      │
└──────────────┬──────────────────────┘
               │ REST API
┌──────────────▼──────────────────────┐
│   Flask Backend (Python)            │
│   • Workflow CRUD                   │
│   • Execution orchestration         │
│   • Stats aggregation               │
└──────────────┬──────────────────────┘
               │ HTTP (calls)
┌──────────────▼──────────────────────┐
│   AgenticOS Agent Provider (8000)   │
│   /v1/chat/completions              │
└──────────────────────────────────────┘
               │ calls
┌──────────────▼──────────────────────┐
│   LM Studio (Nemotron / Gemma)      │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│   MySQL Database                     │
│   • workflows                        │
│   • executions                       │
│   • execution_logs                   │
│   • execution_metrics                │
└──────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.13+
- MySQL 8.0+ (or via Docker)
- AgenticOS Agent Provider running on `http://127.0.0.1:8000`
- LM Studio server running on `http://127.0.0.1:1234` (for LLM calls)

### Option 1: Local Setup

```bash
# 1. Install dependencies
cd webapp
pip install -r requirements.txt

# 2. Create database and seed sample workflows
python seed.py

# 3. Start the app
python app.py
```

Visit: `http://127.0.0.1:5000`

### Option 2: Docker Compose

```bash
cd webapp
docker-compose up
```

MySQL and Flask will start automatically. Seeds run on startup.

## API Endpoints

### Workflows

```http
GET /api/workflows
POST /api/workflows
GET /api/workflows/:id
POST /api/workflows/:id/execute
```

### Executions & Logs

```http
GET /api/executions/:id
```

Returns:
```json
{
  "id": 1,
  "workflow_id": 1,
  "status": "success",
  "output": { ... },
  "logs": [
    { "timestamp": "...", "level": "INFO", "step_id": "step1", "message": "..." }
  ],
  "metrics": [
    { "step_id": "step1", "model": "nemotron", "tokens_used": 150, "latency_ms": 890.5 }
  ]
}
```

### Statistics

```http
GET /api/stats
```

Returns:
```json
{
  "total_executions": 42,
  "successful": 40,
  "failed": 2,
  "total_tokens_used": 12500,
  "avg_latency_ms": 750.3,
  "model_usage": [
    { "model": "nemotron", "executions": 25, "total_tokens": 8000 },
    { "model": "gemma", "executions": 17, "total_tokens": 4500 }
  ]
}
```

## Web UI

### Skills Tab
- View all available workflows (displayed as "Skills" or "Abilities")
- Click to preview and test
- Select test model and input
- Execute and view results

### Create Tab
- Define new workflow name and description
- Write Mermaid flowchart
- Configure execution steps (JSON):
  ```json
  [
    {
      "id": "analysis",
      "action": "call_llm",
      "model": "nemotron",
      "prompt": "Analyze: {input}",
      "temperature": 0.7,
      "max_tokens": 256
    }
  ]
  ```

### Dashboard Tab
- Total executions, success/failure rates
- Token usage aggregates per model
- Average latency
- Recent logs viewer

## Configuration

### Environment Variables

```bash
DB_USER=root
DB_PASSWORD=Qaz123#
DB_HOST=localhost
DB_PORT=3306
DB_NAME=agenticOS
AGENT_PROVIDER_URL=http://127.0.0.1:8000
```

### sample workflows

The `seed.py` script creates three demo workflows:

1. **Quick Question Bot** - Ask a question, get an answer
2. **Content Summarizer** - Summarize text using Gemma
3. **Sentiment Analysis** - Classify text sentiment

## Database Schema

### workflows
```sql
id INT PRIMARY KEY
name VARCHAR(255) UNIQUE
description TEXT
mermaid_definition TEXT   -- Mermaid flowchart
steps JSON               -- Execution steps config
is_active BOOLEAN
created_at DATETIME
updated_at DATETIME
```

### executions
```sql
id INT PRIMARY KEY
workflow_id INT FOREIGN KEY
input_data JSON
output_data JSON
status VARCHAR(50)        -- running, success, failed
started_at DATETIME
completed_at DATETIME
```

### execution_logs
```sql
id INT PRIMARY KEY
execution_id INT FOREIGN KEY
level VARCHAR(20)         -- INFO, WARNING, ERROR
message TEXT
step_id VARCHAR(255)
timestamp DATETIME
```

### execution_metrics
```sql
id INT PRIMARY KEY
execution_id INT FOREIGN KEY
step_id VARCHAR(255)
model VARCHAR(255)
tokens_used INT
latency_ms FLOAT
timestamp DATETIME
```

## Troubleshooting

### "LM Studio request failed"
- Ensure LM Studio is running on `http://127.0.0.1:1234`
- Check that a model is loaded (Nemotron or Gemma)
- Verify model names match config in `config/settings.yaml`

### "Agent provider connection failed"
- Ensure AgenticOS app is running on `http://127.0.0.1:8000`
- Check firewall rules
- Verify `/health` endpoint responds

### Database errors
- Ensure MySQL is running and accessible
- Check DB credentials in environment or `docker-compose.yml`
- Run `python seed.py` to initialize schema

## Next Steps

- Add workflow versioning and rollback
- Support parallel step execution
- Add workflow templates and marketplace
- Implement workflow scheduling
- Add user authentication and RBAC
- Export workflow execution reports

---

**Version**: 0.1.0 | **Status**: Production ready

