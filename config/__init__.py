"""
Configuration management for AgenticOS.
Loads from (in priority order):
  1. Environment variables set before startup
  2. .env file at project root
  3. config/settings.yaml
  4. Built-in defaults
"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Load .env from project root (safe even when already set)
_ROOT = Path(__file__).resolve().parent.parent
_env_file = _ROOT / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=_env_file, override=False)
        logger.debug("Loaded .env from %s", _env_file)
    except ImportError:
        logger.warning("python-dotenv not installed; .env file not loaded")


class ConfigManager:
    """Load and manage system configuration."""

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
        self._apply_env_overrides()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}
            logger.info("Configuration loaded from %s", self.config_path)
        else:
            logger.warning("Config file not found: %s. Using defaults.", self.config_path)
            self._config = self._get_defaults()

    def _apply_env_overrides(self) -> None:
        """
        Override YAML values with flat env vars.
        Reads well-known env keys and maps them into the nested config tree.
        Also supports legacy AGENTICSOS_* prefix.
        """
        # ── LM Studio ────────────────────────────────────────────────
        _set(self._config, "agenticOS.intelligence.lmstudio.base_url",
             os.getenv("LMSTUDIO_BASE_URL"))
        _set(self._config, "agenticOS.intelligence.lmstudio.api_key",
             os.getenv("LMSTUDIO_API_KEY"))
        _set(self._config, "agenticOS.intelligence.lmstudio.timeout_seconds",
             _int(os.getenv("LMSTUDIO_TIMEOUT")))
        _set(self._config, "agenticOS.intelligence.lmstudio.default_model",
             os.getenv("LLM_DEFAULT_MODEL"))

        # ── Model aliases ────────────────────────────────────────────
        nemotron = os.getenv("LLM_MODEL_NEMOTRON")
        gemma    = os.getenv("LLM_MODEL_GEMMA")
        if nemotron:
            _set(self._config, "agenticOS.intelligence.lmstudio.model_aliases.nemotron", nemotron)
        if gemma:
            _set(self._config, "agenticOS.intelligence.lmstudio.model_aliases.gemma", gemma)

        # ── API server ───────────────────────────────────────────────
        _set(self._config, "agenticOS.api.host", os.getenv("AGENT_API_HOST"))
        _set(self._config, "agenticOS.api.port", _int(os.getenv("AGENT_API_PORT")))

        # ── MySQL ────────────────────────────────────────────────────
        _set(self._config, "agenticOS.database.mysql.host",     os.getenv("DB_HOST"))
        _set(self._config, "agenticOS.database.mysql.port",     _int(os.getenv("DB_PORT")))
        _set(self._config, "agenticOS.database.mysql.user",     os.getenv("DB_USER"))
        _set(self._config, "agenticOS.database.mysql.password", os.getenv("DB_PASSWORD"))
        _set(self._config, "agenticOS.database.mysql.database", os.getenv("DB_NAME"))

        # ── Observability ────────────────────────────────────────────
        _set(self._config, "agenticOS.observability.enable_traces",
             _bool(os.getenv("ENABLE_TRACES")))
        _set(self._config, "agenticOS.observability.trace_sampling_rate",
             _float(os.getenv("TRACE_SAMPLING_RATE")))
        _set(self._config, "agenticOS.observability.metrics_interval",
             _int(os.getenv("METRICS_INTERVAL")))

        # ── Security ─────────────────────────────────────────────────
        _set(self._config, "agenticOS.security.rate_limit",
             _int(os.getenv("RATE_LIMIT")))
        _set(self._config, "agenticOS.debug", _bool(os.getenv("DEBUG")))

        # ── Legacy AGENTICSOS_* prefix ───────────────────────────────
        for key, value in os.environ.items():
            if key.startswith("AGENTICSOS_"):
                config_key = key[11:].lower()
                if value.lower() in ("true", "false"):
                    self._config[config_key] = value.lower() == "true"
                elif value.isdigit():
                    self._config[config_key] = int(value)
                else:
                    self._config[config_key] = value

    def _get_defaults(self) -> Dict[str, Any]:
        return {
            "agenticOS": {
                "version": "0.1.0",
                "debug": False,
                "api": {"host": "0.0.0.0", "port": 8000, "protocols": ["rest"]},
                "agents": {"pool_size": 50, "max_agents": 200, "default_timeout": 30},
                "workflow": {"max_parallel_steps": 10, "step_timeout": 300},
                "security": {"rate_limit": 1000, "auth_token_expiry": 3600},
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def get_all(self) -> Dict[str, Any]:
        return self._config.copy()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _set(d: dict, dotted_key: str, value: Any) -> None:
    """Set a nested dict value from a dot-notation key; skip if value is None."""
    if value is None:
        return
    keys = dotted_key.split(".")
    node = d
    for k in keys[:-1]:
        node = node.setdefault(k, {})
    node[keys[-1]] = value


def _int(v: str | None) -> int | None:
    try:
        return int(v) if v is not None else None
    except ValueError:
        return None


def _float(v: str | None) -> float | None:
    try:
        return float(v) if v is not None else None
    except ValueError:
        return None


def _bool(v: str | None) -> bool | None:
    if v is None:
        return None
    return v.lower() in ("1", "true", "yes")


__all__ = ["ConfigManager"]
