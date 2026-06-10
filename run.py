#!/usr/bin/env python
"""
AgenticOS Bundle Runner
=======================
Starts all services from a single command:

    python run.py

Services launched:
  • AgenticOS Agent Provider API  →  http://127.0.0.1:8000
  • Workflow Web App               →  http://127.0.0.1:5000

Config is read from .env in this directory.
Each service streams colour-coded logs to the console.
Press Ctrl+C to stop all services gracefully.
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env before anything else ───────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
load_dotenv(dotenv_path=ROOT / ".env", override=False)

AGENT_API_PORT = int(os.getenv("AGENT_API_PORT", 8000))
WEBAPP_PORT    = int(os.getenv("WEBAPP_PORT",    5000))

# ── Colour helpers ────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"

COLOURS = {
    "agent-api": "\033[36m",   # cyan
    "webapp":    "\033[35m",   # magenta
    "runner":    "\033[33m",   # yellow
}


def cprint(service: str, line: str, err: bool = False) -> None:
    colour = COLOURS.get(service, "")
    tag = f"{colour}{BOLD}[{service}]{RESET}"
    stream = sys.stderr if err else sys.stdout
    print(f"{tag} {line}", file=stream, flush=True)


def stream_output(proc: subprocess.Popen, service: str) -> None:
    """Forward process stdout/stderr lines with service prefix."""
    for raw in iter(proc.stdout.readline, b""):
        line = raw.decode("utf-8", errors="replace").rstrip()
        if line:
            cprint(service, line)


# ── Service definitions ───────────────────────────────────────────────────────

SERVICES = [
    {
        "name": "agent-api",
        "cmd":  [sys.executable, "main.py"],
        "cwd":  str(ROOT),
        "url":  f"http://127.0.0.1:{AGENT_API_PORT}/health",
        "ready_phrase": "Application startup complete",
    },
    {
        "name": "webapp",
        "cmd":  [sys.executable, "app.py"],
        "cwd":  str(ROOT / "webapp"),   # run from webapp/ so templates & DB paths resolve
        "url":  f"http://127.0.0.1:{WEBAPP_PORT}/api/health",
        "ready_phrase": "Running on",
    },
]


def start_service(svc: dict) -> subprocess.Popen:
    """Spawn a service subprocess and begin streaming its output."""
    cprint("runner", f"Starting {svc['name']}  →  {svc['url']}")
    env = {**os.environ}   # inherit current env (already has .env loaded)
    proc = subprocess.Popen(
        svc["cmd"],
        cwd=svc["cwd"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    t = threading.Thread(
        target=stream_output,
        args=(proc, svc["name"]),
        daemon=True,
    )
    t.start()
    return proc


def wait_healthy(svc: dict, timeout: int = 30) -> bool:
    """Poll a service URL until it responds or timeout expires."""
    import urllib.request
    import urllib.error

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(svc["url"], timeout=2):
                return True
        except Exception:
            time.sleep(1)
    return False


def seed_webapp_db() -> None:
    """Ensure the webapp MySQL schema and sample workflows exist."""
    cprint("runner", "Seeding webapp database …")
    env = {**os.environ}
    result = subprocess.run(
        [sys.executable, "setup_dev.py"],
        cwd=str(ROOT / "webapp"),
        env=env,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        cprint("webapp", line)
    if result.returncode != 0:
        for line in result.stderr.splitlines():
            cprint("webapp", line, err=True)
        cprint("runner", "⚠  DB seed returned non-zero exit code")


def main() -> None:
    procs: list[subprocess.Popen] = []

    def shutdown(sig=None, frame=None):
        cprint("runner", "Stopping all services …")
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        cprint("runner", "All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # ── Pre-flight: seed DB ────────────────────────────────────────────────
    seed_webapp_db()

    # ── Launch services ────────────────────────────────────────────────────
    for svc in SERVICES:
        proc = start_service(svc)
        procs.append(proc)

    # ── Wait for each service to become healthy ────────────────────────────
    all_healthy = True
    for svc in SERVICES:
        ok = wait_healthy(svc, timeout=30)
        if ok:
            cprint("runner", f"✓  {svc['name']} is ready  →  {svc['url']}")
        else:
            cprint("runner", f"✗  {svc['name']} did not become healthy in time", err=True)
            all_healthy = False

    if all_healthy:
        print()
        cprint("runner", "=" * 56)
        cprint("runner", f"  Agent API   →  http://127.0.0.1:{AGENT_API_PORT}")
        cprint("runner", f"  Web App     →  http://127.0.0.1:{WEBAPP_PORT}")
        cprint("runner", f"  API Docs    →  http://127.0.0.1:{AGENT_API_PORT}/docs")
        cprint("runner", "  Ctrl+C to stop all services")
        cprint("runner", "=" * 56)
        print()

    # ── Keep running until interrupted ────────────────────────────────────
    try:
        while True:
            for proc in procs:
                if proc.poll() is not None:
                    name = next(
                        (s["name"] for s in SERVICES
                         if SERVICES.index(s) == procs.index(proc)),
                        "unknown",
                    )
                    cprint("runner", f"⚠  {name} exited unexpectedly (code {proc.returncode})", err=True)
            time.sleep(2)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()

