"""Workflow-based web app using AgenticOS as agent provider."""

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote_plus

# Load .env from project root before reading any os.getenv
_ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
if find_spec("dotenv") is not None:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_ROOT_ENV, override=False)

from flask import Flask, abort, jsonify, render_template, request, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.utils import safe_join


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

app = Flask(__name__)
CORS(app)

# ── Database configuration (all values from .env / env vars) ───────────────
if not os.getenv("SQLALCHEMY_DATABASE_URI"):
    DB_USER     = os.getenv("DB_USER",     "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Qaz123#")
    DB_HOST     = os.getenv("DB_HOST",     "localhost")
    DB_PORT     = os.getenv("DB_PORT",     "3306")
    DB_NAME     = os.getenv("DB_NAME",     "agenticos")
    _enc_pw = quote_plus(DB_PASSWORD)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{DB_USER}:{_enc_pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ── Agent provider ────────────────────────────────────────────────────────
AGENT_PROVIDER_URL = os.getenv("AGENT_PROVIDER_URL", "http://127.0.0.1:8000")
WEBAPP_BASE_URL = os.getenv("WEBAPP_BASE_URL", f"http://127.0.0.1:{os.getenv('WEBAPP_PORT', '5000')}")

# ============ Models ============

class Workflow(db.Model):
    """Workflow definition stored as Mermaid flowchart + execution config."""
    __tablename__ = "workflows"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    mermaid_definition = db.Column(db.Text, nullable=False)  # Mermaid flowchart
    steps = db.Column(db.JSON)  # Parsed steps with LLM calls, agents, etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    executions = db.relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")


class Execution(db.Model):
    """Single workflow execution with logs and metrics."""
    __tablename__ = "executions"

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey("workflows.id"), nullable=False)
    input_data = db.Column(db.JSON)
    output_data = db.Column(db.JSON)
    status = db.Column(db.String(50), default="running")  # running, success, failed
    started_at = db.Column(db.DateTime, default=_utcnow)
    completed_at = db.Column(db.DateTime)

    workflow = db.relationship("Workflow", back_populates="executions")
    logs = db.relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")
    metrics = db.relationship("ExecutionMetric", back_populates="execution", cascade="all, delete-orphan")


class ExecutionLog(db.Model):
    """Log entry for execution troubleshooting."""
    __tablename__ = "execution_logs"

    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(db.Integer, db.ForeignKey("executions.id"), nullable=False)
    level = db.Column(db.String(20))  # INFO, WARNING, ERROR
    message = db.Column(db.Text)
    step_id = db.Column(db.String(255))  # Which step in workflow
    timestamp = db.Column(db.DateTime, default=_utcnow)

    execution = db.relationship("Execution", back_populates="logs")


class ExecutionMetric(db.Model):
    """Metrics for each step (tokens, latency, model)."""
    __tablename__ = "execution_metrics"

    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(db.Integer, db.ForeignKey("executions.id"), nullable=False)
    step_id = db.Column(db.String(255))
    model = db.Column(db.String(255))
    tokens_used = db.Column(db.Integer, default=0)
    latency_ms = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=_utcnow)

    execution = db.relationship("Execution", back_populates="metrics")


class VibeTask(db.Model):
    """User-approved automation task built from vibe sandbox thoughts."""
    __tablename__ = "vibe_tasks"

    id = db.Column(db.Integer, primary_key=True)
    task_number = db.Column(db.String(16), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    thoughts = db.Column(db.Text, nullable=False)
    output_spec = db.Column(db.Text, nullable=False)
    max_depth = db.Column(db.Integer, default=10)
    max_iterations_per_depth = db.Column(db.Integer, default=500)
    generated_mermaid = db.Column(db.Text, nullable=False)
    generated_plan = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    executions = db.relationship("VibeExecution", back_populates="task", cascade="all, delete-orphan")


class VibeExecution(db.Model):
    """A single automation execution with a persistent GUID folder."""
    __tablename__ = "vibe_executions"

    id = db.Column(db.Integer, primary_key=True)
    execution_guid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey("vibe_tasks.id"), nullable=False)
    task_number = db.Column(db.String(16), nullable=False)
    status = db.Column(db.String(32), default="running")
    token_usage = db.Column(db.Integer, default=0)
    model_used = db.Column(db.String(255))
    step_count = db.Column(db.Integer, default=0)
    folder_path = db.Column(db.Text, nullable=False)
    input_data = db.Column(db.JSON)
    output_data = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=_utcnow)
    completed_at = db.Column(db.DateTime)

    task = db.relationship("VibeTask", back_populates="executions")
    logs = db.relationship("VibeExecutionLog", back_populates="execution", cascade="all, delete-orphan")


class VibeExecutionLog(db.Model):
    """Per-step and per-guardrail logs for vibe executions."""
    __tablename__ = "vibe_execution_logs"

    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(db.Integer, db.ForeignKey("vibe_executions.id"), nullable=False)
    step_id = db.Column(db.String(255))
    level = db.Column(db.String(20), default="INFO")
    message = db.Column(db.Text, nullable=False)
    payload = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=_utcnow)

    execution = db.relationship("VibeExecution", back_populates="logs")


# ============ API Endpoints ============

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "agent_provider": AGENT_PROVIDER_URL})


@app.route("/api/workflows", methods=["GET"])
def list_workflows():
    """List all workflow definitions available as skills."""
    workflows = Workflow.query.filter_by(is_active=True).all()
    return jsonify([
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "mermaid_definition": w.mermaid_definition,
        }
        for w in workflows
    ])


@app.route("/api/workflows", methods=["POST"])
def create_workflow():
    """Create a new workflow from Mermaid definition."""
    data = request.json
    name = data.get("name")
    description = data.get("description", "")
    mermaid_def = data.get("mermaid_definition")
    steps = data.get("steps", [])

    if not name or not mermaid_def:
        return jsonify({"error": "name and mermaid_definition required"}), 400

    workflow = Workflow(
        name=name,
        description=description,
        mermaid_definition=mermaid_def,
        steps=steps,
    )
    db.session.add(workflow)
    db.session.commit()

    return jsonify({"id": workflow.id, "name": workflow.name}), 201


@app.route("/api/workflows/<int:workflow_id>", methods=["GET"])
def get_workflow(workflow_id):
    """Get a workflow definition."""
    workflow = Workflow.query.get(workflow_id)
    if not workflow:
        return jsonify({"error": "not found"}), 404

    return jsonify({
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "mermaid_definition": workflow.mermaid_definition,
        "steps": workflow.steps,
    })


@app.route("/api/workflows/<int:workflow_id>/execute", methods=["POST"])
def execute_workflow(workflow_id):
    """Execute a workflow synchronously and return results."""
    workflow = Workflow.query.get(workflow_id)
    if not workflow:
        return jsonify({"error": "workflow not found"}), 404

    input_data = request.json or {}

    # Create execution record
    execution = Execution(
        workflow_id=workflow_id,
        input_data=input_data,
        status="running",
    )
    db.session.add(execution)
    db.session.commit()

    try:
        output = execute_workflow_steps(execution, workflow)
        execution.output_data = output
        execution.status = "success"
        execution.completed_at = _utcnow()
        db.session.commit()

        return jsonify({
            "execution_id": execution.id,
            "status": "success",
            "output": output,
        })
    except Exception as e:
        execution.status = "failed"
        execution.completed_at = _utcnow()
        log_entry(execution, "ERROR", str(e), None)
        db.session.commit()

        return jsonify({
            "execution_id": execution.id,
            "status": "failed",
            "error": str(e),
        }), 500


def execute_workflow_steps(execution: Execution, workflow: Workflow) -> Dict[str, Any]:
    """Execute workflow steps, calling agent provider API as needed."""
    steps = workflow.steps or []
    context = dict(execution.input_data or {})

    for step in steps:
        step_id = step.get("id", "unknown")
        action = step.get("action", "")

        try:
            if action == "call_llm":
                result = call_llm_step(execution, step, context)
                context[step_id] = result
                log_entry(execution, "INFO", f"Step {step_id} completed", step_id)

            elif action == "branch":
                # For now, just execute next steps
                log_entry(execution, "INFO", f"Step {step_id} branch executed", step_id)

            else:
                log_entry(execution, "WARNING", f"Unknown action: {action}", step_id)

        except Exception as e:
            log_entry(execution, "ERROR", f"Step {step_id} failed: {e}", step_id)
            raise

    return context


def call_llm_step(execution: Execution, step: Dict, context: Dict) -> str:
    """Call LM Studio via agent provider API."""
    import time

    step_id = step.get("id")
    model = step.get("model", "nemotron")
    prompt_template = step.get("prompt", "")

    # Replace template variables
    prompt = _safe_dict_format(prompt_template, context)

    # Call agent provider
    start = time.time()
    response = requests.post(
        f"{AGENT_PROVIDER_URL}/v1/chat/completions",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": step.get("temperature", 0.7),
            "max_tokens": step.get("max_tokens", 256),
        },
        timeout=120,
    )
    elapsed_ms = (time.time() - start) * 1000

    if response.status_code != 200:
        raise Exception(f"LM Studio returned {response.status_code}: {response.text}")

    body = response.json()
    result = body["choices"][0]["message"]["content"]

    # Record metrics
    metric = ExecutionMetric(
        execution_id=execution.id,
        step_id=step_id,
        model=model,
        tokens_used=body.get("usage", {}).get("total_tokens", 0),
        latency_ms=elapsed_ms,
    )
    db.session.add(metric)
    db.session.commit()

    return result


def log_entry(execution: Execution, level: str, message: str, step_id: str = None):
    """Add a log entry to execution."""
    log = ExecutionLog(
        execution_id=execution.id,
        level=level,
        message=message,
        step_id=step_id,
    )
    db.session.add(log)
    db.session.commit()


@app.route("/api/executions/<int:execution_id>", methods=["GET"])
def get_execution(execution_id):
    """Get execution details, logs, and metrics."""
    execution = Execution.query.get(execution_id)
    if not execution:
        return jsonify({"error": "not found"}), 404

    logs = [{
        "timestamp": log.timestamp.isoformat(),
        "level": log.level,
        "step_id": log.step_id,
        "message": log.message,
    } for log in execution.logs]

    metrics = [{
        "step_id": m.step_id,
        "model": m.model,
        "tokens_used": m.tokens_used,
        "latency_ms": m.latency_ms,
    } for m in execution.metrics]

    return jsonify({
        "id": execution.id,
        "workflow_id": execution.workflow_id,
        "status": execution.status,
        "input": execution.input_data,
        "output": execution.output_data,
        "started_at": execution.started_at.isoformat(),
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "logs": logs,
        "metrics": metrics,
    })


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get aggregate statistics: total executions, tokens, latency."""
    total_execs = Execution.query.count()
    success_execs = Execution.query.filter_by(status="success").count()
    failed_execs = Execution.query.filter_by(status="failed").count()

    total_tokens = db.session.query(db.func.sum(ExecutionMetric.tokens_used)).scalar() or 0
    avg_latency = db.session.query(db.func.avg(ExecutionMetric.latency_ms)).scalar() or 0

    model_usage = db.session.query(
        ExecutionMetric.model,
        db.func.count(ExecutionMetric.id).label("count"),
        db.func.sum(ExecutionMetric.tokens_used).label("total_tokens"),
    ).group_by(ExecutionMetric.model).all()

    return jsonify({
        "total_executions": total_execs,
        "successful": success_execs,
        "failed": failed_execs,
        "total_tokens_used": total_tokens,
        "avg_latency_ms": float(avg_latency),
        "model_usage": [
            {
                "model": m[0],
                "executions": m[1],
                "total_tokens": m[2] or 0,
            }
            for m in model_usage
        ],
    })



# ============ AI Workflow Generation ============

GENERATION_PROMPT = """You are an expert AI workflow designer.
Given a workflow name and description, produce a Mermaid flowchart and a JSON steps array.

Workflow Name: {name}
Description: {description}

Respond ONLY with a JSON object in this exact format (no markdown, no explanation):
{{
  "mermaid": "flowchart TD\\n    A[Start] --> B[Step]\\n    B --> C[End]",
  "steps": [
    {{
      "id": "step_id",
      "action": "call_llm",
      "model": "nemotron",
      "prompt": "Your prompt here using {{variable_name}}",
      "temperature": 0.7,
      "max_tokens": 300
    }}
  ]
}}

CRITICAL INSTRUCTIONS FOR PROMPTS:
- Use SINGLE curly braces {{ }} for template variables in prompts
- Do NOT use double braces {{{{ }}}} - those are escape sequences
- Variable format: {{input_name}} (example: "Analyze: {{text}}" or "Translate to {{language}}")
- These variables will be replaced at runtime by the workflow engine
- Never use double braces like {{{{variable}}}} - use {{variable}} instead

Rules:
- flowchart TD direction only
- Node labels must describe real steps
- Use {{variable_name}} syntax for user inputs in prompts (SINGLE braces)
- 1–3 steps max
- Use "nemotron" for reasoning tasks, "gemma" for simple/short ones
"""


@app.route("/api/workflows/generate", methods=["POST"])
def generate_workflow():
    """Use the Nemotron agent to generate a Mermaid flowchart + step config."""
    import json as _json
    data = request.json or {}
    name = data.get("name", "")
    description = data.get("description", "")
    if not name or not description:
        return jsonify({"error": "name and description required"}), 400

    prompt = GENERATION_PROMPT.format(name=_escape_format(name), description=_escape_format(description))

    try:
        resp = requests.post(
            f"{AGENT_PROVIDER_URL}/v1/chat/completions",
            json={
                "model": "nemotron",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 1024,
            },
            timeout=90,
        )
    except Exception as e:
        return jsonify({"error": f"Agent provider unreachable: {e}"}), 502

    if resp.status_code != 200:
        return jsonify({"error": f"Agent returned {resp.status_code}: {resp.text[:200]}"}), 502

    content = resp.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown fences if present
    content = re.sub(r"^```[a-z]*\n?", "", content)
    content = re.sub(r"\n?```$", "", content.strip())

    # Extract first JSON object
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return jsonify({"error": "Agent response contained no JSON", "raw": content}), 500

    try:
        result = _json.loads(match.group())
    except _json.JSONDecodeError as e:
        return jsonify({"error": f"JSON parse failed: {e}", "raw": content}), 500

    # Normalize double braces in prompts to single braces
    result_normalized = _normalize_prompts(result)

    return jsonify({
        "mermaid": result_normalized.get("mermaid", ""),
        "steps":   result_normalized.get("steps",   []),
    })


def _normalize_prompts(result: Dict[str, Any]) -> Dict[str, Any]:
    """Convert any {{var}} template variables to {var} recursively."""

    def _norm(value: Any) -> Any:
        if isinstance(value, str):
            return re.sub(r"\{\{(\w+)\}\}", r"{\1}", value)
        if isinstance(value, list):
            return [_norm(v) for v in value]
        if isinstance(value, dict):
            return {k: _norm(v) for k, v in value.items()}
        return value

    return _norm(result)


@app.route("/api/workflows/<int:workflow_id>", methods=["PUT"])
def update_workflow(workflow_id):
    """Update an existing workflow (name, description, mermaid, steps)."""
    workflow = Workflow.query.get(workflow_id)
    if not workflow:
        return jsonify({"error": "not found"}), 404

    data = request.json or {}
    if "name" in data:
        workflow.name = data["name"]
    if "description" in data:
        workflow.description = data["description"]
    if "mermaid_definition" in data:
        workflow.mermaid_definition = data["mermaid_definition"]
    if "steps" in data:
        workflow.steps = data["steps"]

    db.session.commit()
    return jsonify({"id": workflow.id, "name": workflow.name})


@app.route("/api/workflows/<int:workflow_id>", methods=["DELETE"])
def delete_workflow(workflow_id):
    """Delete a workflow."""
    workflow = Workflow.query.get(workflow_id)
    if not workflow:
        return jsonify({"error": "not found"}), 404
    db.session.delete(workflow)
    db.session.commit()
    return jsonify({"deleted": workflow_id})


@app.route("/api/executions/recent", methods=["GET"])
def recent_logs():
    """Return the 50 most recent execution log entries for the dashboard."""
    logs = (ExecutionLog.query
            .order_by(ExecutionLog.timestamp.desc())
            .limit(50).all())
    return jsonify([{
        "timestamp": log.timestamp.isoformat(),
        "level":     log.level,
        "step_id":   log.step_id,
        "message":   log.message,
    } for log in logs])


# ============ Vibe Sandbox APIs ============

@app.route("/api/vibe/skills", methods=["GET"])
def vibe_skills():
    """Return available skills/workflows for the vibe planner prompt."""
    skills = Workflow.query.filter_by(is_active=True).order_by(Workflow.name.asc()).all()
    return jsonify([
        {"id": s.id, "name": s.name, "description": s.description}
        for s in skills
    ])


@app.route("/api/vibe/generate", methods=["POST"])
def vibe_generate():
    """Generate a Mermaid plan + JSON config from two user thought boxes."""
    import json as _json

    data = request.json or {}
    thoughts = (data.get("thoughts") or "").strip()
    output_spec = (data.get("output_spec") or "").strip()
    max_depth = int(data.get("max_depth", 10))
    max_iterations = int(data.get("max_iterations_per_depth", 500))

    if not thoughts or not output_spec:
        return jsonify({"error": "thoughts and output_spec are required"}), 400

    skills = Workflow.query.filter_by(is_active=True).order_by(Workflow.name.asc()).all()
    skills_text = "\n".join([f"- {s.name}: {s.description or ''}" for s in skills])

    prompt = VIBE_GENERATION_PROMPT.format(
        thoughts=_escape_format(thoughts),
        output_spec=_escape_format(output_spec),
        max_depth=max_depth,
        max_iterations=max_iterations,
        skills_text=_escape_format(skills_text),
    )

    try:
        resp = requests.post(
            f"{AGENT_PROVIDER_URL}/v1/chat/completions",
            json={
                "model": "nemotron",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 1800,
            },
            timeout=120,
        )
    except Exception as e:
        return jsonify({"error": f"Agent provider unreachable: {e}"}), 502

    if resp.status_code != 200:
        return jsonify({"error": f"Agent returned {resp.status_code}: {resp.text[:240]}"}), 502

    content = resp.json()["choices"][0]["message"]["content"].strip()
    content = re.sub(r"^```[a-z]*\n?", "", content)
    content = re.sub(r"\n?```$", "", content.strip())
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return jsonify({"error": "No JSON returned by agent", "raw": content}), 500

    try:
        result = _json.loads(match.group())
    except _json.JSONDecodeError as e:
        return jsonify({"error": f"JSON parse failed: {e}", "raw": content}), 500

    result = _normalize_prompts(result)
    return jsonify(result)


@app.route("/api/vibe/tasks", methods=["GET", "POST"])
def vibe_tasks():
    """Create approved vibe tasks or list them as a tree root."""
    if request.method == "GET":
        tasks = VibeTask.query.order_by(VibeTask.created_at.desc()).all()
        return jsonify([
            {
                "id": t.id,
                "task_number": t.task_number,
                "title": t.title,
                "thoughts": t.thoughts,
                "output_spec": t.output_spec,
                "max_depth": t.max_depth,
                "max_iterations_per_depth": t.max_iterations_per_depth,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
                "executions": [
                    {
                        "id": e.id,
                        "execution_guid": e.execution_guid,
                        "status": e.status,
                        "started_at": e.started_at.isoformat(),
                        "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                    }
                    for e in t.executions
                ],
            }
            for t in tasks
        ])

    data = request.json or {}
    title = (data.get("title") or "").strip()
    thoughts = (data.get("thoughts") or "").strip()
    output_spec = (data.get("output_spec") or "").strip()
    generated_mermaid = (data.get("generated_mermaid") or "").strip()
    generated_plan = data.get("generated_plan") or {}
    max_depth = int(data.get("max_depth", 10))
    max_iterations = int(data.get("max_iterations_per_depth", 500))

    if not title or not thoughts or not output_spec or not generated_mermaid:
        return jsonify({"error": "title, thoughts, output_spec and generated_mermaid are required"}), 400

    task = VibeTask(
        task_number=_next_vibe_task_number(),
        title=title,
        thoughts=thoughts,
        output_spec=output_spec,
        max_depth=max_depth,
        max_iterations_per_depth=max_iterations,
        generated_mermaid=generated_mermaid,
        generated_plan=generated_plan,
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({
        "id": task.id,
        "task_number": task.task_number,
        "title": task.title,
    }), 201


@app.route("/api/vibe/tasks/<int:task_id>", methods=["GET", "PUT"])
def vibe_task_detail(task_id):
    task = VibeTask.query.get(task_id)
    if not task:
        return jsonify({"error": "not found"}), 404

    if request.method == "GET":
        return jsonify(_vibe_task_json(task))

    data = request.json or {}
    if "title" in data:
        task.title = data["title"]
    if "thoughts" in data:
        task.thoughts = data["thoughts"]
    if "output_spec" in data:
        task.output_spec = data["output_spec"]
    if "generated_mermaid" in data:
        task.generated_mermaid = data["generated_mermaid"]
    if "generated_plan" in data:
        task.generated_plan = data["generated_plan"]
    if "max_depth" in data:
        task.max_depth = int(data["max_depth"])
    if "max_iterations_per_depth" in data:
        task.max_iterations_per_depth = int(data["max_iterations_per_depth"])
    db.session.commit()
    return jsonify(_vibe_task_json(task))


@app.route("/api/vibe/tasks/<int:task_id>/execute", methods=["POST"])
def vibe_task_execute(task_id):
    """Create execution row and start background execution."""
    task = VibeTask.query.get(task_id)
    if not task:
        return jsonify({"error": "not found"}), 404

    execution_guid = uuid.uuid4().hex
    folder = _task_execution_folder(task.task_number, execution_guid)
    output_dir = folder / "output"
    logs_dir = folder / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    execution = VibeExecution(
        execution_guid=execution_guid,
        task_id=task.id,
        task_number=task.task_number,
        status="running",
        folder_path=str(folder),
        input_data=request.json or {},
    )
    db.session.add(execution)
    db.session.commit()

    _write_json(folder / "task.json", _vibe_task_json(task))
    _write_json(folder / "input.json", execution.input_data or {})
    _write_json(folder / "plan.json", task.generated_plan or {})

    threading.Thread(target=_run_vibe_execution, args=(execution_guid,), daemon=True).start()

    return jsonify({
        "execution_guid": execution_guid,
        "task_number": task.task_number,
        "status": "running",
        "folder_path": str(folder),
    }), 202


@app.route("/api/vibe/executions/<string:execution_guid>", methods=["GET"])
def vibe_execution_detail(execution_guid):
    execution = VibeExecution.query.filter_by(execution_guid=execution_guid).first()
    if not execution:
        return jsonify({"error": "not found"}), 404
    return jsonify(_vibe_execution_json(execution))


@app.route("/api/vibe/executions/<string:execution_guid>/logs", methods=["GET"])
def vibe_execution_logs(execution_guid):
    execution = VibeExecution.query.filter_by(execution_guid=execution_guid).first()
    if not execution:
        return jsonify({"error": "not found"}), 404
    logs = VibeExecutionLog.query.filter_by(execution_id=execution.id).order_by(VibeExecutionLog.timestamp.asc()).all()
    return jsonify([{
        "timestamp": l.timestamp.isoformat(),
        "level": l.level,
        "step_id": l.step_id,
        "message": l.message,
        "payload": l.payload,
    } for l in logs])


@app.route("/api/vibe/executions/<string:execution_guid>/tree", methods=["GET"])
def vibe_execution_tree(execution_guid):
    execution = VibeExecution.query.filter_by(execution_guid=execution_guid).first()
    if not execution:
        return jsonify({"error": "not found"}), 404
    root = Path(execution.folder_path)
    return jsonify(_build_tree(root))


@app.route("/api/vibe/executions/<string:execution_guid>/files", methods=["GET"])
def vibe_execution_files(execution_guid):
    execution = VibeExecution.query.filter_by(execution_guid=execution_guid).first()
    if not execution:
        return jsonify({"error": "not found"}), 404
    root = Path(execution.folder_path)
    rel = request.args.get("path", "")
    target = _safe_path(root, rel)
    if target is None or not target.exists():
        return jsonify({"error": "file not found"}), 404
    if target.is_dir():
        return jsonify(_build_tree(target, base=root))

    if request.args.get("download") == "1":
        return send_file(target, as_attachment=True)
    return jsonify(_read_file_payload(target))


@app.route("/api/vibe/executions/<string:execution_guid>/files/<path:relpath>", methods=["GET"])
def vibe_execution_file_by_path(execution_guid, relpath):
    execution = VibeExecution.query.filter_by(execution_guid=execution_guid).first()
    if not execution:
        return jsonify({"error": "not found"}), 404
    root = Path(execution.folder_path)
    target = _safe_path(root, relpath)
    if target is None or not target.exists():
        return jsonify({"error": "file not found"}), 404
    if target.is_dir():
        return jsonify(_build_tree(target, base=root))
    if request.args.get("download") == "1":
        return send_file(target, as_attachment=True)
    return jsonify(_read_file_payload(target))


@app.route("/api/vibe/tree", methods=["GET"])
def vibe_tree():
    """Return task→execution tree for browsing."""
    tasks = VibeTask.query.order_by(VibeTask.created_at.desc()).all()
    return jsonify([_vibe_task_json(task) for task in tasks])


# ── Vibe Sandbox helpers ───────────────────────────────────────────────────

VIBE_GENERATION_PROMPT = """You are the default skill assist agent for Vibe Sandbox.
You convert the user's written thoughts into a safe, testable automation plan.

User thoughts:
{thoughts}

Desired output file format/content:
{output_spec}

Constraints:
- Maximum depth: {max_depth}
- Maximum iteration count per depth: {max_iterations}

Available skills you may use when appropriate:
{skills_text}

Hard rules:
- Prefer existing skills by name when they fit the task.
- If no skill fits, use a direct LLM call with Nemotron.
- Add failure guardrails to every branch.
- Stop and log if max depth or iteration limits may be exceeded.
- Use single curly braces only in runtime template variables like {{thoughts}}, {{output_spec}}, {{input}}, {{context}}.
- Do not output double braces in any prompt field.

Return ONLY JSON in this exact structure:
{{
  "title": "...",
  "mermaid": "flowchart TD\\n    A[Start] --> B[Guardrails]\\n    B --> C[Skill or LLM]\\n    C --> D[Output]",
  "generated_summary": "...",
  "guardrails": {{
    "max_depth": {max_depth},
    "max_iterations_per_depth": {max_iterations},
    "failure_policy": "stop_and_log"
  }},
  "steps": [
    {{
      "id": "g1",
      "action": "guardrail",
      "message": "Validate depth and iteration limits"
    }},
    {{
      "id": "s1",
      "action": "skill",
      "skill_name": "Content Summarizer",
      "input_map": {{"content": "{{thoughts}}"}}
    }},
    {{
      "id": "llm1",
      "action": "call_llm",
      "model": "nemotron",
      "prompt": "Use the result of {{thoughts}} to continue the plan safely."
    }},
    {{
      "id": "o1",
      "action": "write_output",
      "model": "nemotron",
      "format": "markdown",
      "prompt": "Format the final output to satisfy: {{output_spec}}"
    }}
  ]
}}
"""


def _vibe_execution_root() -> Path:
    root = Path(__file__).resolve().parent / "runtime" / "vibe"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _append_jsonl(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def _next_vibe_task_number() -> str:
    highest = 0
    for t in VibeTask.query.all():
        m = re.match(r"T(\d+)$", t.task_number or "")
        if m:
            highest = max(highest, int(m.group(1)))
    return f"T{highest + 1}"


def _safe_dict_format(template: str, context: Dict[str, Any]) -> str:
    class _SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"

    try:
        return template.format_map(_SafeDict(**{k: str(v) for k, v in context.items()}))
    except Exception:
        return template


def _escape_format(value: Any) -> str:
    """Escape braces so user-provided text can be safely inserted into .format templates."""
    return str(value).replace("{", "{{").replace("}", "}}")


def _render_value(value: Any, context: Dict[str, Any]) -> Any:
    if isinstance(value, str):
        return _safe_dict_format(value, context)
    if isinstance(value, list):
        return [_render_value(v, context) for v in value]
    if isinstance(value, dict):
        return {k: _render_value(v, context) for k, v in value.items()}
    return value


def _guess_output_extension(output_spec: str) -> str:
    spec = (output_spec or "").lower()
    if "markdown" in spec or ".md" in spec:
        return "md"
    if "json" in spec:
        return "json"
    if "csv" in spec:
        return "csv"
    if "html" in spec:
        return "html"
    if "txt" in spec or "text" in spec:
        return "txt"
    return "txt"


def _read_file_payload(path: Path) -> Dict[str, Any]:
    content = path.read_text(encoding="utf-8", errors="replace")
    return {
        "name": path.name,
        "path": str(path),
        "size": path.stat().st_size,
        "content": content,
    }


def _safe_path(root: Path, relpath: str) -> Path | None:
    try:
        joined = safe_join(str(root), relpath or "")
        return Path(joined) if joined else None
    except Exception:
        return None


def _task_execution_folder(task_number: str, execution_guid: str) -> Path:
    root = _vibe_execution_root() / task_number / execution_guid
    root.mkdir(parents=True, exist_ok=True)
    return root


def _build_tree(path: Path, base: Path | None = None) -> Dict[str, Any]:
    base = base or path
    if path.is_file():
        return {
            "name": path.name,
            "type": "file",
            "path": str(path.relative_to(base)).replace("\\", "/"),
            "size": path.stat().st_size,
        }
    return {
        "name": path.name,
        "type": "folder",
        "path": str(path.relative_to(base)).replace("\\", "/") if path != base else "",
        "children": [
            _build_tree(child, base=base)
            for child in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        ],
    }

def _call_agent_completion(model: str, prompt: str, temperature: float = 0.2, max_tokens: int = 1200) -> Dict[str, Any]:
    resp = requests.post(
        f"{AGENT_PROVIDER_URL}/v1/chat/completions",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Agent provider returned {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    content = body["choices"][0]["message"]["content"]
    tokens = body.get("usage", {}).get("total_tokens", 0)
    return {"content": content, "tokens": tokens, "raw": body}


def _vibe_task_json(task: VibeTask) -> Dict[str, Any]:
    return {
        "id": task.id,
        "task_number": task.task_number,
        "title": task.title,
        "thoughts": task.thoughts,
        "output_spec": task.output_spec,
        "max_depth": task.max_depth,
        "max_iterations_per_depth": task.max_iterations_per_depth,
        "generated_mermaid": task.generated_mermaid,
        "generated_plan": task.generated_plan,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "executions": [
            _vibe_execution_json(e) for e in sorted(task.executions, key=lambda x: x.started_at, reverse=True)
        ],
    }


def _vibe_execution_json(execution: VibeExecution) -> Dict[str, Any]:
    return {
        "id": execution.id,
        "execution_guid": execution.execution_guid,
        "task_id": execution.task_id,
        "task_number": execution.task_number,
        "status": execution.status,
        "token_usage": execution.token_usage,
        "model_used": execution.model_used,
        "step_count": execution.step_count,
        "folder_path": execution.folder_path,
        "input_data": execution.input_data,
        "output_data": execution.output_data,
        "error_message": execution.error_message,
        "started_at": execution.started_at.isoformat(),
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
    }


def _vibe_log(execution: VibeExecution, level: str, step_id: str, message: str, payload: Dict[str, Any] | None = None) -> None:
    row = VibeExecutionLog(
        execution_id=execution.id,
        step_id=step_id,
        level=level,
        message=message,
        payload=payload,
    )
    db.session.add(row)
    db.session.commit()

    folder = Path(execution.folder_path)
    _append_jsonl(folder / "logs" / "events.jsonl", {
        "timestamp": _utcnow().isoformat(),
        "level": level,
        "step_id": step_id,
        "message": message,
        "payload": payload,
    })


def _run_vibe_execution(execution_guid: str) -> None:
    with app.app_context():
        execution = VibeExecution.query.filter_by(execution_guid=execution_guid).first()
        if not execution:
            return

        task = execution.task
        folder = Path(execution.folder_path)
        output_dir = folder / "output"
        logs_dir = folder / "logs"
        output_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        plan = task.generated_plan or {}
        steps = plan.get("steps", [])
        context: Dict[str, Any] = {
            "thoughts": task.thoughts,
            "output_spec": task.output_spec,
            **(execution.input_data or {}),
        }
        total_tokens = 0
        latest_model = None
        output_file = None

        _vibe_log(execution, "INFO", "start", f"Starting automation {task.task_number}", {
            "task_number": task.task_number,
            "max_depth": task.max_depth,
            "max_iterations_per_depth": task.max_iterations_per_depth,
        })

        try:
            if len(steps) > task.max_depth:
                raise RuntimeError(f"Plan exceeds max depth ({task.max_depth})")

            for idx, step in enumerate(steps, start=1):
                step_id = step.get("id", f"step_{idx}")
                action = step.get("action", "")
                _vibe_log(execution, "INFO", step_id, f"Step {idx}/{len(steps)} started: {action}", step)

                if action == "guardrail":
                    _vibe_log(execution, "INFO", step_id, "Guardrail validated", {
                        "max_depth": task.max_depth,
                        "max_iterations_per_depth": task.max_iterations_per_depth,
                    })
                    continue

                if action == "skill":
                    skill_name = step.get("skill_name")
                    skill = Workflow.query.filter_by(name=skill_name, is_active=True).first()
                    if not skill:
                        raise RuntimeError(f"Requested skill not found: {skill_name}")

                    skill_input = _render_value(step.get("input_map") or {}, context)
                    if not skill_input:
                        skill_input = context

                    skill_result = requests.post(
                        f"{WEBAPP_BASE_URL}/api/workflows/{skill.id}/execute",
                        json=skill_input,
                        timeout=180,
                    )
                    if skill_result.status_code != 200:
                        raise RuntimeError(f"Skill {skill_name} failed: {skill_result.text[:300]}")

                    skill_json = skill_result.json()
                    context[step_id] = skill_json.get("output")

                    nested_exec_id = skill_json.get("execution_id")
                    nested_tokens = 0
                    if nested_exec_id:
                        nested_detail = requests.get(
                            f"{WEBAPP_BASE_URL}/api/executions/{nested_exec_id}",
                            timeout=60,
                        ).json()
                        nested_tokens = sum(m.get("tokens_used", 0) for m in nested_detail.get("metrics", []))
                    total_tokens += nested_tokens
                    latest_model = latest_model or "workflow-skill"

                    _write_json(output_dir / f"{idx:02d}_{step_id}_skill.json", {
                        "skill_name": skill_name,
                        "input": skill_input,
                        "result": skill_json,
                    })
                    _vibe_log(execution, "INFO", step_id, f"Skill {skill_name} completed", {
                        "nested_execution": nested_exec_id,
                        "tokens_used": nested_tokens,
                    })
                    continue

                if action == "call_llm":
                    model = step.get("model", "nemotron")
                    prompt = _safe_dict_format(step.get("prompt", ""), context)
                    llm = _call_agent_completion(
                        model=model,
                        prompt=prompt,
                        temperature=float(step.get("temperature", 0.2)),
                        max_tokens=int(step.get("max_tokens", 800)),
                    )
                    context[step_id] = llm["content"]
                    total_tokens += int(llm["tokens"] or 0)
                    latest_model = model
                    _write_json(output_dir / f"{idx:02d}_{step_id}_llm.json", {
                        "prompt": prompt,
                        "result": llm["content"],
                        "tokens": llm["tokens"],
                    })
                    _vibe_log(execution, "INFO", step_id, "LLM step completed", {
                        "model": model,
                        "tokens_used": llm["tokens"],
                    })
                    continue

                if action == "write_output":
                    model = step.get("model", "nemotron")
                    fmt = (step.get("format") or task.output_spec or "txt").lower()
                    output_prompt = _safe_dict_format(step.get("prompt") or f"Format the final result to satisfy: {task.output_spec}", context)
                    llm = _call_agent_completion(
                        model=model,
                        prompt=output_prompt,
                        temperature=float(step.get("temperature", 0.2)),
                        max_tokens=int(step.get("max_tokens", 1200)),
                    )
                    total_tokens += int(llm["tokens"] or 0)
                    latest_model = model
                    ext = _guess_output_extension(fmt)
                    output_file = output_dir / f"final_output.{ext}"
                    output_file.write_text(llm["content"], encoding="utf-8")
                    context[step_id] = str(output_file)
                    _write_json(output_dir / f"{idx:02d}_{step_id}_output_meta.json", {
                        "format": fmt,
                        "path": str(output_file),
                        "tokens": llm["tokens"],
                    })
                    _vibe_log(execution, "INFO", step_id, "Output file created", {
                        "path": str(output_file),
                        "format": fmt,
                    })
                    continue

                _vibe_log(execution, "WARNING", step_id, f"Unknown step action: {action}", step)

            summary = {
                "task_number": task.task_number,
                "execution_guid": execution.execution_guid,
                "token_usage": total_tokens,
                "model_used": latest_model,
                "output_file": str(output_file) if output_file else None,
                "context": context,
            }
            _write_json(folder / "summary.json", summary)

            execution.status = "success"
            execution.token_usage = total_tokens
            execution.model_used = latest_model
            execution.step_count = len(steps)
            execution.output_data = summary
            execution.completed_at = _utcnow()
            db.session.commit()
            _vibe_log(execution, "INFO", "complete", "Automation completed successfully", summary)

        except Exception as exc:
            execution.status = "failed"
            execution.error_message = str(exc)
            execution.completed_at = _utcnow()
            execution.step_count = len(steps)
            execution.token_usage = total_tokens
            execution.model_used = latest_model
            db.session.commit()
            _vibe_log(execution, "ERROR", "failed", f"Automation failed: {exc}", {"error": str(exc)})
            _write_json(folder / "error.json", {"error": str(exc), "task_number": task.task_number})



# ============ Frontend ============

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    host = os.getenv("WEBAPP_HOST", "0.0.0.0")
    port = int(os.getenv("WEBAPP_PORT", 5000))
    app.run(host=host, port=port, debug=os.getenv("DEBUG", "false").lower() == "true")




