"""AgenticOS entrypoint with LM Studio-backed API endpoints."""

import logging
import time
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import ConfigManager
from intelligence import LMStudioClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

config = ConfigManager()

LMSTUDIO_BASE_URL = config.get(
    "agenticOS.intelligence.lmstudio.base_url", "http://127.0.0.1:1234/v1"
)
LMSTUDIO_API_KEY = config.get("agenticOS.intelligence.lmstudio.api_key", "")
LMSTUDIO_TIMEOUT = config.get("agenticOS.intelligence.lmstudio.timeout_seconds", 120)
MODEL_ALIASES = config.get("agenticOS.intelligence.lmstudio.model_aliases", {})
DEFAULT_MODEL = config.get("agenticOS.intelligence.lmstudio.default_model", "nemotron")

MYSQL_HOST = config.get("agenticOS.database.mysql.host", "localhost")
MYSQL_PORT = int(config.get("agenticOS.database.mysql.port", 3306))
MYSQL_USER = config.get("agenticOS.database.mysql.user", "root")
MYSQL_PASSWORD = config.get("agenticOS.database.mysql.password", "Qaz123#")
MYSQL_DATABASE = config.get("agenticOS.database.mysql.database", "agenticos")

_api_log_table_initialized = False

lmstudio = LMStudioClient(
    base_url=LMSTUDIO_BASE_URL,
    api_key=LMSTUDIO_API_KEY,
    timeout_seconds=LMSTUDIO_TIMEOUT,
)

app = FastAPI(title="AgenticOS", version="0.1.0")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = Field(default=DEFAULT_MODEL)
    messages: List[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=8192)


def _resolve_model(model_name: str) -> str:
    return MODEL_ALIASES.get(model_name, model_name)


def _ensure_api_log_table() -> None:
    global _api_log_table_initialized
    if _api_log_table_initialized:
        return
    try:
        import pymysql

        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            autocommit=True,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS agent_api_logs (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        endpoint VARCHAR(128) NOT NULL,
                        requested_model VARCHAR(255),
                        resolved_model VARCHAR(255),
                        status_code INT NOT NULL,
                        tokens_used INT DEFAULT 0,
                        latency_ms FLOAT DEFAULT 0,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            _api_log_table_initialized = True
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("MySQL log table init skipped: %s", exc)


def _log_api_request(
    endpoint: str,
    requested_model: str,
    resolved_model: str,
    status_code: int,
    tokens_used: int,
    latency_ms: float,
    error_message: str = "",
) -> None:
    try:
        import pymysql

        _ensure_api_log_table()
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            autocommit=True,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agent_api_logs
                    (endpoint, requested_model, resolved_model, status_code, tokens_used, latency_ms, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        endpoint,
                        requested_model,
                        resolved_model,
                        status_code,
                        tokens_used,
                        latency_ms,
                        error_message,
                    ),
                )
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("MySQL request log skipped: %s", exc)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "lmstudio_base_url": LMSTUDIO_BASE_URL,
        "default_model": DEFAULT_MODEL,
        "model_aliases": MODEL_ALIASES,
    }


@app.get("/v1/models")
async def models() -> Dict[str, Any]:
    return {
        "data": [
            {"id": key, "resolved_model": value}
            for key, value in MODEL_ALIASES.items()
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> Dict[str, Any]:
    started = time.perf_counter()
    requested_model = request.model
    resolved_model = _resolve_model(request.model)
    payload = {
        "model": resolved_model,
        "messages": [m.model_dump() for m in request.messages],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }
    try:
        result = await lmstudio.chat_completions(payload)
        elapsed_ms = (time.perf_counter() - started) * 1000
        tokens = result.get("usage", {}).get("total_tokens", 0)
        _log_api_request(
            endpoint="/v1/chat/completions",
            requested_model=requested_model,
            resolved_model=resolved_model,
            status_code=200,
            tokens_used=tokens,
            latency_ms=elapsed_ms,
        )
        return result
    except Exception as exc:  # pragma: no cover - integration path
        elapsed_ms = (time.perf_counter() - started) * 1000
        _log_api_request(
            endpoint="/v1/chat/completions",
            requested_model=requested_model,
            resolved_model=resolved_model,
            status_code=502,
            tokens_used=0,
            latency_ms=elapsed_ms,
            error_message=str(exc),
        )
        raise HTTPException(status_code=502, detail=f"LM Studio request failed: {exc}")


if __name__ == "__main__":
    host = config.get("agenticOS.api.host", "0.0.0.0")
    port = config.get("agenticOS.api.port", 8000)
    logger.info("Starting AgenticOS API on %s:%s", host, port)
    uvicorn.run("main:app", host=host, port=port, reload=False)
