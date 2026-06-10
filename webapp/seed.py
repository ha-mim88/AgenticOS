"""Seed initial workflows into the database."""

import json
from app import app, db, Workflow

sample_workflows = [
    {
        "name": "Quick Question Bot",
        "description": "Ask a simple question and get an answer from LLM",
        "mermaid_definition": """flowchart TD
    A[Start] --> B[User Question]
    B --> C[Send to LLM]
    C --> D[Return Answer]
    D --> E[End]""",
        "steps": [
            {
                "id": "analyze_question",
                "action": "call_llm",
                "model": "nemotron",
                "prompt": "Answer this question clearly: {question}",
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
    B --> C[Call Gemma]
    C --> D[Return Summary]
    D --> E[End]""",
        "steps": [
            {
                "id": "summarize",
                "action": "call_llm",
                "model": "gemma",
                "prompt": "Summarize the following in 3 sentences: {content}",
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
    B --> C[Analyze]
    C --> D{Sentiment Check}
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
                "prompt": "Analyze the sentiment of this text and respond with just 'positive', 'negative', or 'neutral': {text}",
                "temperature": 0.2,
                "max_tokens": 20,
            }
        ],
    },
]


def seed_workflows():
    """Insert sample workflows."""
    with app.app_context():
        db.create_all()

        for wf_data in sample_workflows:
            existing = Workflow.query.filter_by(name=wf_data["name"]).first()
            if not existing:
                workflow = Workflow(
                    name=wf_data["name"],
                    description=wf_data["description"],
                    mermaid_definition=wf_data["mermaid_definition"],
                    steps=wf_data["steps"],
                    is_active=True,
                )
                db.session.add(workflow)

        db.session.commit()
        print("✓ Sample workflows seeded successfully")


if __name__ == "__main__":
    seed_workflows()

