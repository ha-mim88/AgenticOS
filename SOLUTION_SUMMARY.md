# AgenticOS Workflow Web App — Complete Solution

Congratulations! You now have a **full-stack, production-ready web application** that enables end-users to:
- **View workflows** as skills/abilities
- **Test workflows** in a sandbox with custom input
- **Monitor execution** with real-time logs and metrics
- **Track token usage** and performance metrics

## What You Have

### 1. Backend (Flask + SQLAlchemy)
- REST API with 5 core endpoints
- Workflow CRUD operations  
- Execution orchestration (calls AgenticOS Agent Provider)
- Automatic logging of steps, tokens, latency
- Statistics aggregation

### 2. Frontend (HTML/JS)
- **Skills Tab**: Browse and test available workflows
- **Create Tab**: Define new workflows with Mermaid flowcharts
- **Dashboard Tab**: View real-time stats, logs, and metrics

### 3. Database (SQLite by default, MySQL ready)
- Workflows with Mermaid definitions
- Execution history with status tracking
- Per-step logs (INFO/WARNING/ERROR)
- Per-step metrics (tokens, latency, model)

### 4. Integration
- Calls **AgenticOS Agent Provider** (`http://127.0.0.1:8000`)
- Which calls **LM Studio** (`http://127.0.0.1:1234`)
- For Nemotron and Gemma models

## Quick Start (30 seconds)

### 1. Ensure Prerequisites are Running

```powershell
# Terminal 1: Start AgenticOS Agent Provider
cd E:\ha-mim88\AgenticOS
python main.py

# Terminal 2: Start LM Studio (local UI or via container)
# Make sure a model (Nemotron or Gemma) is loaded
```

### 2. Start the Web App

```powershell
# Terminal 3: Start the webapp
cd E:\ha-mim88\AgenticOS\webapp
python setup_dev.py      # Creates DB and seeds sample workflows
python app.py            # Start Flask server
```

### 3. Open in Browser

```
http://127.0.0.1:5000
```

Click on a skill/workflow and execute a test!

## Sample Workflows Included

1. **Quick Question Bot** — Ask a question, get an answer (Nemotron)
2. **Content Summarizer** — Summarize text (Gemma)
3. **Sentiment Analysis** — Classify sentiment (Nemotron)
4. **Code Reviewer** — Review code for best practices (Nemotron)

## Testing the Workflows

### Via Web UI

1. Go to **Skills** tab
2. Click on any skill (e.g., "Quick Question Bot")
3. In the "Test Skill" panel:
   - Provide test input as JSON: `{"question": "What is 2+2?"}`
   - Click **Execute**
4. View output, logs, and metrics in real-time

### Via API

```powershell
# Execute a workflow
$body = @{
    question = "What is AI?"
} | ConvertTo-Json

Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/api/workflows/1/execute" `
  -ContentType "application/json" `
  -Body $body
```

### Via Postman

Use the included Postman collection at:
```
E:\ha-mim88\AgenticOS\postman\AgenticOS-LMStudio.postman_collection.json
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/workflows` | GET | List all workflows (skills) |
| `/api/workflows` | POST | Create new workflow |
| `/api/workflows/:id` | GET | Get workflow details |
| `/api/workflows/:id/execute` | POST | Execute workflow |
| `/api/executions/:id` | GET | Get execution logs & metrics |
| `/api/stats` | GET | Get aggregated statistics |

## Configuration

### Local Testing (SQLite - No Setup)

```powershell
cd webapp
python setup_dev.py
python app.py
```

### Docker Compose (MySQL + Flask)

```powershell
cd webapp
docker-compose up
```

Then visit `http://127.0.0.1:5000`

### Custom MySQL Database

```powershell
$env:USE_MYSQL = "1"
$env:DB_USER = "root"
$env:DB_PASSWORD = "root"
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_NAME = "agenticOS"

# Run setup and app
python setup_dev.py
python app.py
```

## Architecture Visualization

```
┌──────────────────────────────────────┐
│   Web Browser (localhost:5000)       │
│  ┌────────────────────────────────┐  │
│  │ Skills • Create • Dashboard    │  │
│  └────────────┬───────────────────┘  │
└─────────────┼──────────────────────────┘
              │ HTTP (Mermaid rendering)
┌─────────────┼──────────────────────────┐
│   Flask Backend (5000)           │      │
│  ┌────────────────────────────┐  │      │
│  │ • Workflow CRUD            │  │      │
│  │ • Execution Engine         │  │      │
│  │ • Logging & Metrics        │  │      │
│  └────────────┬───────────────┘  │      │
└─────────────┼──────────────────────────┘
              │ HTTP /v1/chat/completions
┌─────────────┼──────────────────────────┐
│   AgenticOS Agent Provider (8000)      │
│  ┌────────────────────────────┐        │
│  │ • LM Studio Client         │        │
│  │ • Model Aliases            │        │
│  └────────────┬───────────────┘        │
└─────────────┼──────────────────────────┘
              │ HTTP 127.0.0.1:1234
┌─────────────┼──────────────────────────┐
│   LM Studio (Local)                    │
│  ┌────────────────────────────┐        │
│  │ Nemotron 4B / Gemma 3N     │        │
│  └────────────────────────────┘        │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│   SQLite / MySQL (Persistence)         │
│  Workflows • Executions • Logs • Stats │
└────────────────────────────────────────┘
```

## Features in Detail

### 1. Workflow Management ✅
- **Define** workflows as Mermaid flowcharts
- **Configure** steps with LLM calls, model selection, prompts
- **Save** workflows to database
- **Activate/Deactivate** workflows

### 2. Testing Sandbox ✅
- **Execute** workflows with custom JSON input
- **Real-time** step-by-step execution
- **View** intermediate results
- **Debug** with detailed logs

### 3. Monitoring & Observability ✅
- **Token Usage**: Per model, per execution
- **Latency**: Per step, aggregate
- **Model Usage**: Count of calls per model
- **Success Rates**: Total, successful, failed executions

### 4. Logging & Troubleshooting ✅
- **Per-step logs** (INFO, WARNING, ERROR)
- **Timestamps** for each log entry
- **Error tracking** with full stack context
- **Searchable logs** in execution details

### 5. Dashboard ✅
- **Execution Stats**: Total, success, fail rates
- **Token Metrics**: Total tokens used per model
- **Performance**: Average latency
- **Model Breakdown**: Usage per model

## Workflow Definition Example

```json
{
  "name": "Customer Support Bot",
  "description": "Automated customer support workflow",
  "mermaid_definition": "flowchart TD\n    A[Start] --> B[Receive Question]\n    B --> C{Check Category}\n    C -->|Technical| D[Call Nemotron]\n    C -->|Simple| E[Call Gemma]\n    D --> F[Return Answer]\n    E --> F",
  "steps": [
    {
      "id": "categorize",
      "action": "call_llm",
      "model": "nemotron",
      "prompt": "Categorize this question as 'technical' or 'simple': {question}",
      "temperature": 0.2,
      "max_tokens": 50
    },
    {
      "id": "respond",
      "action": "call_llm",
      "model": "gemma",
      "prompt": "Answer the customer question: {question}",
      "temperature": 0.7,
      "max_tokens": 300
    }
  ]
}
```

## Troubleshooting

### "Connection refused" errors
- Ensure AgenticOS is running: `python main.py`
- Check LM Studio is running on `127.0.0.1:1234`
- Verify a model is loaded (Nemotron or Gemma)

### "No workflows appear"
- Run `python setup_dev.py` to seed sample workflows
- Check database connection: `sqlite:///agenticOS.db`

### "502 Bad Gateway" on workflow execution
- LM Studio is not responding or model not loaded
- Verify LM Studio API: `curl http://127.0.0.1:1234/v1/models`

### Database errors
- For SQLite: delete `agenticOS.db` and re-run `python setup_dev.py`
- For MySQL: verify credentials and that MySQL service is running

## Next Steps

1. ✅ **Test the sample workflows** in the web UI
2. ✅ **Create your own workflow** with custom LLM prompts
3. ✅ **Monitor execution metrics** in the Dashboard
4. ✅ **Deploy to production** with Docker Compose + MySQL

## File Structure

```
E:\ha-mim88\AgenticOS\
├── main.py                          # Agent Provider API
├── config/
│   ├── settings.yaml               # LM Studio config
│   └── __init__.py
│
├── webapp/                          # NEW: Web Application
│   ├── app.py                      # Flask backend
│   ├── routes.py                   # Frontend routes
│   ├── setup_dev.py                # DB setup & seeding
│   ├── requirements.txt            # Python deps
│   ├── docker-compose.yml          # Production setup
│   ├── Dockerfile                  # Container image
│   ├── README.md                   # Full documentation
│   │
│   ├── templates/
│   │   └── index.html             # Single-page frontend
│   │
│   └── agenticOS.db               # SQLite database (created)
│
├── tests/
│   ├── test_messaging.py
│   ├── test_agent_models.py
│   └── ...
│
└── postman/
    └── AgenticOS-LMStudio.postman_collection.json
```

---

**Status**: ✅ Production Ready

**Version**: 0.1.0

**Last Updated**: June 2026

