#!/usr/bin/env python
"""
Database initialisation and sample-workflow seeder.
Reads credentials from root .env (or environment variables).
"""

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

# ── Load .env from project root ───────────────────────────────────────────
_ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_ROOT_ENV, override=False)
except ImportError:
    pass


def setup_sqlite():
    """Setup SQLite for local testing."""
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///agenticOS.db"
    print("✓ Using SQLite (agenticOS.db) for local testing")


def setup_mysql():
    """Build MySQL URI from env vars and create database if missing."""
    db_user     = os.getenv("DB_USER",     "root")
    db_password = os.getenv("DB_PASSWORD", "Qaz123#")
    db_host     = os.getenv("DB_HOST",     "localhost")
    db_port     = os.getenv("DB_PORT",     "3306")
    db_name     = os.getenv("DB_NAME",     "agenticos")

    # Create database if it does not exist yet.
    import pymysql
    admin_conn = pymysql.connect(
        host=db_host,
        port=int(db_port),
        user=db_user,
        password=db_password,
        autocommit=True,
    )
    try:
        with admin_conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
    finally:
        admin_conn.close()

    encoded_password = quote_plus(db_password)
    os.environ["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
    )
    print(f"✓ Using MySQL at {db_host}:{db_port}")


def main():
    # Always use MySQL (credentials come from .env / env vars)
    setup_mysql()

    # Now import and seed
    from app import app, db, Workflow

    sample_workflows = [
        {
            "name": "Quick Question Bot",
            "description": "Ask a simple question and get an answer from LLM",
            "mermaid_definition": """flowchart TD
    A[Start] --> B[User Question]
    B --> C[Send to LLM]
    C --> D{Check Result}
    D -->|Success| E[Return Answer]
    D -->|Error| F[Retry]
    E --> G[End]
    F --> C""",
            "steps": [
                {
                    "id": "analyze_question",
                    "action": "call_llm",
                    "model": "nemotron",
                    "prompt": "Answer this question clearly and concisely: {question}",
                    "temperature": 0.5,
                    "max_tokens": 256,
                }
            ],
        },
        {
            "name": "Content Summarizer",
            "description": "Summarize provided content using Gemma model",
            "mermaid_definition": """flowchart TD
    A[Start] --> B[Receive Content]
    B --> C{Content Length?}
    C -->|Long| D[Call Gemma]
    C -->|Short| E[Skip Summarization]
    D --> F[Return Summary]
    E --> G[Return Original]
    F --> H[End]
    G --> H""",
            "steps": [
                {
                    "id": "summarize",
                    "action": "call_llm",
                    "model": "gemma",
                    "prompt": "Summarize the following in 2-3 sentences:\n{content}",
                    "temperature": 0.3,
                    "max_tokens": 200,
                }
            ],
        },
        {
            "name": "Sentiment Analysis",
            "description": "Analyze sentiment of provided text",
            "mermaid_definition": """flowchart TD
    A[Start] --> B[Receive Text]
    B --> C[Analyze Sentiment]
    C --> D{Sentiment Result}
    D -->|Positive| E[Return Positive]
    D -->|Negative| F[Return Negative]
    D -->|Neutral| G[Return Neutral]
    E --> H[End]
    F --> H
    G --> H""",
            "steps": [
                {
                    "id": "sentiment",
                    "action": "call_llm",
                    "model": "nemotron",
                    "prompt": "Analyze the sentiment and respond ONLY with 'positive', 'negative', or 'neutral':\n{text}",
                    "temperature": 0.2,
                    "max_tokens": 20,
                }
            ],
        },
        {
            "name": "Code Reviewer",
            "description": "Review code for best practices and improvements",
            "mermaid_definition": """flowchart TD
    A[Start] --> B[Receive Code]
    B --> C[Check Syntax]
    C --> D[Review Logic]
    D --> E[Generate Feedback]
    E --> F[End]""",
            "steps": [
                {
                    "id": "code_review",
                    "action": "call_llm",
                    "model": "nemotron",
                    "prompt": "Review this code for best practices and suggest improvements:\n{code}",
                    "temperature": 0.7,
                    "max_tokens": 512,
                }
            ],
        },
    ]

    with app.app_context():
        db.create_all()
        print("\n✓ Schema ready")

    # Run the 20-skill seeder
    from seed_skills import seed
    seed()

    print(f"\nWebapp: http://127.0.0.1:{os.getenv('WEBAPP_PORT', 5000)}")


if __name__ == "__main__":
    main()

