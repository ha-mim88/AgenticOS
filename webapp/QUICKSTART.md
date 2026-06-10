# 🚀 Quick Start: AgenticOS Workflow Web App

## 60-Second Setup

### Prerequisites
- ✅ Python 3.13+ (already installed)
- ✅ AgenticOS Agent Provider running
- ✅ LM Studio running with a model loaded

### Step 1: Initialize Database & Seed Workflows

```powershell
cd E:\ha-mim88\AgenticOS\webapp
python setup_dev.py
```

Expected output:
```
✓ Using SQLite (agenticOS.db) for local testing
✓ Created workflow: Quick Question Bot
✓ Created workflow: Content Summarizer
✓ Created workflow: Sentiment Analysis
✓ Created workflow: Code Reviewer
✓ Setup complete!
```

### Step 2: Start the Web App

```powershell
python app.py
```

App is running at: **http://127.0.0.1:5000**

### Step 3: Open Browser

```
http://127.0.0.1:5000
```

## What You Can Do Now

### 📋 Skills Tab
View all available workflows as user-facing "skills" and test them:

1. Click **"Quick Question Bot"**
2. In test input box: `{"question": "What is Python?"}`
3. Click **Execute**
4. See output, logs, and metrics in real-time

### ➕ Create Tab  
Define new agentic workflows:

1. Workflow name: `"My Custom Bot"`
2. Description: `"Does X, Y, Z"`
3. Mermaid diagram: Draw flowchart
4. Steps (JSON): Configure LLM calls and logic
5. Click **Create Workflow**

### 📊 Dashboard Tab
Monitor all executions:

- Total executions count
- Success/failure rates
- Token usage per model
- Average latency
- View recent logs

## API Testing

### Get All Workflows

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/workflows"
```

### Execute a Workflow

```powershell
$body = @{
    question = "Explain quantum computing"
} | ConvertTo-Json

Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:5000/api/workflows/1/execute" `
  -ContentType "application/json" `
  -Body $body
```

### View Statistics

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/stats"
```

## Database

### SQLite (Default - No Setup)
Database file: `webapp/agenticOS.db`
- Automatically created on first run
- Great for development & testing
- No additional setup needed

### MySQL (Production Ready)

```powershell
# Set environment variables
$env:USE_MYSQL = "1"
$env:DB_USER = "root"
$env:DB_PASSWORD = "yourpassword"
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_NAME = "agenticOS"

# Run setup
python setup_dev.py
python app.py
```

### Docker Compose (MySQL + Flask)

```powershell
docker-compose up
```

## Workflow Structure

A workflow defines how an agentic system processes user requests:

```json
{
  "name": "Support Bot",
  "mermaid_definition": "flowchart TD...",
  "steps": [
    {
      "id": "step1",
      "action": "call_llm",
      "model": "nemotron",
      "prompt": "Analyze: {user_input}",
      "temperature": 0.5,
      "max_tokens": 256
    }
  ]
}
```

**Model options**: `nemotron` or `gemma`

## Monitoring & Debugging

### View Execution Logs

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/executions/1"
```

Returns:
- Input/output data
- Logs (INFO/WARNING/ERROR)
- Metrics (tokens, latency, model)
- Status (success/failed)

### Dashboard Metrics

The **Dashboard** tab shows:
- Total executions
- Success rate
- Failed executions  
- Tokens used per model
- Model performance breakdown

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | LM Studio not running or model not loaded |
| No workflows show | Run `python setup_dev.py` first |
| Database errors | Delete `agenticOS.db`, re-run `setup_dev.py` |
| Connection timeout | Ensure all 3 services running (Agent Provider, LM Studio, Webapp) |

## Architecture

```
User Browser
    ↓ (HTTP)
Flask Web App (5000)
    ├─ REST API
    ├─ SQLite / MySQL
    └─ HTML/JS Frontend (Mermaid flowcharts)
    ↓ (HTTP /v1/chat/completions)
AgenticOS Agent Provider (8000)
    ↓ (HTTP 127.0.0.1:1234)
LM Studio
    ↓
Local Nemotron / Gemma models
```

## Files & Locations

| File | Purpose |
|------|---------|
| `app.py` | Flask backend with API |
| `routes.py` | Frontend routes |
| `setup_dev.py` | Initialize & seed DB |
| `templates/index.html` | Web UI (HTML/CSS/JS) |
| `agenticOS.db` | SQLite database |
| `requirements.txt` | Python dependencies |
| `docker-compose.yml` | MySQL + Flask compose |

## Next: Production Deployment

1. Use MySQL instead of SQLite
2. Deploy with Docker Compose
3. Set up monitoring & alerts
4. Add user authentication
5. Enable workflow versioning

---

**Everything working? Great!** 🎉

Now visit `http://127.0.0.1:5000` and test a workflow.

For more info, see `SOLUTION_SUMMARY.md` and `README.md` in the webapp folder.

