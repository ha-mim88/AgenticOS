#!/usr/bin/env python
"""
Seed 20 production-ready skills/workflows into the database.
Run from the webapp/ directory:  python seed_skills.py
"""

import os
import sys
from pathlib import Path

_ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_ROOT_ENV, override=False)
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app import app, db, Workflow

SKILLS = [
    {
        "name": "Quick Q&A Bot",
        "description": "Answers any general question clearly and concisely.",
        "mermaid_definition": """flowchart TD
    A[User Question] --> B[Nemotron Answers]
    B --> C{Complete?}
    C -->|Yes| D[Return Answer]
    C -->|No| E[Clarify & Retry]
    E --> B
    D --> F[End]""",
        "steps": [{"id": "answer", "action": "call_llm", "model": "nemotron",
                   "prompt": "Answer this question clearly and helpfully: {question}",
                   "temperature": 0.6, "max_tokens": 300}],
    },
    {
        "name": "Content Summarizer",
        "description": "Summarizes long text into 3 bullet-point key takeaways.",
        "mermaid_definition": """flowchart TD
    A[Receive Content] --> B[Gemma Summarizes]
    B --> C[Format as Bullets]
    C --> D[Return Summary]""",
        "steps": [{"id": "summarize", "action": "call_llm", "model": "gemma",
                   "prompt": "Summarize the following into exactly 3 concise bullet points:\n{content}",
                   "temperature": 0.3, "max_tokens": 200}],
    },
    {
        "name": "Sentiment Analyzer",
        "description": "Classifies text sentiment as Positive, Negative, or Neutral with a brief explanation.",
        "mermaid_definition": """flowchart TD
    A[Input Text] --> B[Analyze Sentiment]
    B --> C{Result}
    C -->|Positive| D[✅ Positive]
    C -->|Negative| E[❌ Negative]
    C -->|Neutral| F[➖ Neutral]
    D --> G[End]
    E --> G
    F --> G""",
        "steps": [{"id": "sentiment", "action": "call_llm", "model": "nemotron",
                   "prompt": "Analyze the sentiment of this text. Respond with the label (Positive/Negative/Neutral) followed by a one-sentence explanation:\n{text}",
                   "temperature": 0.2, "max_tokens": 80}],
    },
    {
        "name": "Code Reviewer",
        "description": "Reviews code for bugs, best practices, and performance improvements.",
        "mermaid_definition": """flowchart TD
    A[Receive Code] --> B[Check for Bugs]
    B --> C[Review Best Practices]
    C --> D[Check Performance]
    D --> E[Generate Report]
    E --> F[Return Feedback]""",
        "steps": [{"id": "review", "action": "call_llm", "model": "nemotron",
                   "prompt": "Review the following code. Identify any bugs, suggest best practice improvements, and note performance concerns:\n\n{code}",
                   "temperature": 0.4, "max_tokens": 512}],
    },
    {
        "name": "Professional Email Writer",
        "description": "Drafts a professional email given a topic and recipient context.",
        "mermaid_definition": """flowchart TD
    A[Get Topic & Context] --> B[Draft Email]
    B --> C[Add Subject Line]
    C --> D[Polish Tone]
    D --> E[Return Email]""",
        "steps": [{"id": "draft_email", "action": "call_llm", "model": "nemotron",
                   "prompt": "Write a professional email. Topic: {topic}. Recipient: {recipient}. Tone: {tone}.\nInclude subject line.",
                   "temperature": 0.7, "max_tokens": 400}],
    },
    {
        "name": "Language Translator",
        "description": "Translates any text to the specified target language.",
        "mermaid_definition": """flowchart TD
    A[Input Text] --> B[Detect Source Language]
    B --> C[Translate to Target]
    C --> D[Return Translation]""",
        "steps": [{"id": "translate", "action": "call_llm", "model": "gemma",
                   "prompt": "Translate the following text to {target_language}. Return only the translation:\n{text}",
                   "temperature": 0.1, "max_tokens": 500}],
    },
    {
        "name": "Customer Support Handler",
        "description": "Classifies a customer complaint, empathizes, and drafts a resolution response.",
        "mermaid_definition": """flowchart TD
    A[Customer Message] --> B[Classify Issue Type]
    B --> C[Generate Empathetic Response]
    C --> D[Suggest Resolution Steps]
    D --> E[Return Response]""",
        "steps": [
            {"id": "classify", "action": "call_llm", "model": "gemma",
             "prompt": "Classify this customer message into one of: Billing, Technical, Shipping, Returns, Other. Reply with just the category:\n{message}",
             "temperature": 0.1, "max_tokens": 20},
            {"id": "respond", "action": "call_llm", "model": "nemotron",
             "prompt": "You are a helpful customer support agent. The customer says: {message}\nIssue category: {classify}\nWrite an empathetic, professional response that acknowledges their concern and offers concrete next steps.",
             "temperature": 0.6, "max_tokens": 350},
        ],
    },
    {
        "name": "Meeting Notes Summarizer",
        "description": "Extracts action items, decisions, and key points from meeting notes.",
        "mermaid_definition": """flowchart TD
    A[Raw Meeting Notes] --> B[Extract Key Points]
    B --> C[Identify Action Items]
    C --> D[List Decisions Made]
    D --> E[Structured Summary]""",
        "steps": [{"id": "summarize_meeting", "action": "call_llm", "model": "nemotron",
                   "prompt": "Analyze these meeting notes and return a structured summary with three sections:\n\n**Key Discussion Points:**\n**Decisions Made:**\n**Action Items (with owners if mentioned):**\n\nNotes:\n{notes}",
                   "temperature": 0.3, "max_tokens": 500}],
    },
    {
        "name": "SQL Query Generator",
        "description": "Generates a SQL query from a plain-English description and table schema.",
        "mermaid_definition": """flowchart TD
    A[Natural Language Request] --> B[Understand Schema]
    B --> C[Generate SQL]
    C --> D[Validate Logic]
    D --> E[Return Query]""",
        "steps": [{"id": "generate_sql", "action": "call_llm", "model": "nemotron",
                   "prompt": "Generate a SQL query for the following request.\n\nRequest: {request}\nTable schema: {schema}\n\nReturn only the SQL query, no explanation.",
                   "temperature": 0.1, "max_tokens": 300}],
    },
    {
        "name": "Product Description Writer",
        "description": "Writes compelling marketing product descriptions from feature lists.",
        "mermaid_definition": """flowchart TD
    A[Product Features] --> B[Identify Benefits]
    B --> C[Write Headline]
    C --> D[Craft Description]
    D --> E[Add CTA]
    E --> F[Return Copy]""",
        "steps": [{"id": "write_description", "action": "call_llm", "model": "nemotron",
                   "prompt": "Write a compelling product description for an e-commerce listing.\n\nProduct: {product_name}\nKey features: {features}\nTarget audience: {audience}\n\nInclude: headline, 3-4 sentence description, 3 bullet benefits, call to action.",
                   "temperature": 0.8, "max_tokens": 400}],
    },
    {
        "name": "Resume Reviewer",
        "description": "Reviews a resume and provides actionable improvement suggestions.",
        "mermaid_definition": """flowchart TD
    A[Resume Text] --> B[Analyze Structure]
    B --> C[Check Content Quality]
    C --> D[Assess Impact Language]
    D --> E[Generate Feedback Report]""",
        "steps": [{"id": "review_resume", "action": "call_llm", "model": "nemotron",
                   "prompt": "Review the following resume for a {role} position. Provide feedback on:\n1. Overall structure\n2. Impact of achievements (are metrics used?)\n3. Skills alignment\n4. Top 3 improvements to make\n\nResume:\n{resume}",
                   "temperature": 0.5, "max_tokens": 600}],
    },
    {
        "name": "Social Media Post Creator",
        "description": "Creates platform-optimized social media posts from a topic or content brief.",
        "mermaid_definition": """flowchart TD
    A[Topic & Platform] --> B[Analyze Audience]
    B --> C[Craft Hook]
    C --> D[Write Post Body]
    D --> E[Add Hashtags]
    E --> F[Return Post]""",
        "steps": [{"id": "create_post", "action": "call_llm", "model": "nemotron",
                   "prompt": "Create a {platform} post about: {topic}\nTone: {tone}\nTarget audience: {audience}\n\nInclude appropriate emojis, hashtags, and a clear call to action.",
                   "temperature": 0.9, "max_tokens": 300}],
    },
    {
        "name": "Bug Report Analyzer",
        "description": "Analyzes a bug report to identify probable cause, severity, and fix recommendations.",
        "mermaid_definition": """flowchart TD
    A[Bug Report] --> B[Parse Error Details]
    B --> C[Identify Root Cause]
    C --> D[Assess Severity]
    D --> E[Suggest Fix]
    E --> F[Return Analysis]""",
        "steps": [{"id": "analyze_bug", "action": "call_llm", "model": "nemotron",
                   "prompt": "Analyze this bug report:\n{bug_report}\n\nProvide:\n1. **Probable Root Cause**\n2. **Severity** (Critical/High/Medium/Low)\n3. **Suggested Fix**\n4. **Files/Components Likely Affected**",
                   "temperature": 0.3, "max_tokens": 500}],
    },
    {
        "name": "Interview Question Generator",
        "description": "Generates tailored interview questions for a given role and skill area.",
        "mermaid_definition": """flowchart TD
    A[Role & Skills] --> B[Determine Question Types]
    B --> C[Generate Technical Qs]
    B --> D[Generate Behavioral Qs]
    C --> E[Combine & Format]
    D --> E
    E --> F[Return Question Set]""",
        "steps": [{"id": "gen_questions", "action": "call_llm", "model": "nemotron",
                   "prompt": "Generate 10 interview questions for a {role} position focused on {skill_area}.\nInclude 5 technical questions and 5 behavioral questions (STAR format).\nFor each question, briefly note what good answer signals.",
                   "temperature": 0.7, "max_tokens": 700}],
    },
    {
        "name": "Sales Email Sequence Writer",
        "description": "Writes a 3-email cold outreach sequence for a product or service.",
        "mermaid_definition": """flowchart TD
    A[Product & Prospect Info] --> B[Email 1: Hook]
    B --> C[Email 2: Value Prop]
    C --> D[Email 3: Follow-up CTA]
    D --> E[Return Sequence]""",
        "steps": [{"id": "write_sequence", "action": "call_llm", "model": "nemotron",
                   "prompt": "Write a 3-email cold outreach sequence.\n\nProduct/Service: {product}\nProspect role: {prospect_role}\nKey pain point: {pain_point}\nValue proposition: {value_prop}\n\nEmail 1 (Day 0): Brief hook and curiosity.\nEmail 2 (Day 3): Value, proof, and relevance.\nEmail 3 (Day 7): Final follow-up with clear CTA.",
                   "temperature": 0.75, "max_tokens": 700}],
    },
    {
        "name": "Data Extractor",
        "description": "Extracts structured data fields from unstructured text.",
        "mermaid_definition": """flowchart TD
    A[Unstructured Text] --> B[Identify Data Fields]
    B --> C[Extract Values]
    C --> D[Format as JSON]
    D --> E[Return Structured Data]""",
        "steps": [{"id": "extract", "action": "call_llm", "model": "nemotron",
                   "prompt": "Extract the following fields from the text below and return as a JSON object.\n\nFields to extract: {fields}\nText:\n{text}\n\nReturn only the JSON object.",
                   "temperature": 0.1, "max_tokens": 400}],
    },
    {
        "name": "Technical Documentation Writer",
        "description": "Writes API or feature documentation from a code snippet or description.",
        "mermaid_definition": """flowchart TD
    A[Code or Feature] --> B[Understand Functionality]
    B --> C[Write Overview]
    C --> D[Document Parameters]
    D --> E[Add Usage Examples]
    E --> F[Return Docs]""",
        "steps": [{"id": "write_docs", "action": "call_llm", "model": "nemotron",
                   "prompt": "Write technical documentation for the following.\n\nFeature/Code: {code_or_feature}\nLanguage/Framework: {language}\n\nInclude: Overview, Parameters/Fields, Return values, 2 usage examples.",
                   "temperature": 0.4, "max_tokens": 700}],
    },
    {
        "name": "User Feedback Analyzer",
        "description": "Analyzes user feedback to identify themes, top issues, and improvement suggestions.",
        "mermaid_definition": """flowchart TD
    A[Feedback Collection] --> B[Identify Themes]
    B --> C[Count Frequency]
    C --> D[Rank Issues]
    D --> E[Generate Insights]
    E --> F[Return Report]""",
        "steps": [{"id": "analyze_feedback", "action": "call_llm", "model": "nemotron",
                   "prompt": "Analyze this user feedback and produce an insights report:\n\n{feedback}\n\nReport should include:\n1. **Top 3 Themes** (with frequency estimate)\n2. **Critical Issues to Fix**\n3. **Most Requested Features**\n4. **Overall Sentiment Score** (1–10)\n5. **Recommended Next Actions**",
                   "temperature": 0.4, "max_tokens": 600}],
    },
    {
        "name": "Legal Text Simplifier",
        "description": "Rewrites complex legal or contract text into plain, easy-to-understand language.",
        "mermaid_definition": """flowchart TD
    A[Legal Text] --> B[Identify Key Clauses]
    B --> C[Simplify Language]
    C --> D[Highlight Important Points]
    D --> E[Return Plain Language Version]""",
        "steps": [{"id": "simplify_legal", "action": "call_llm", "model": "nemotron",
                   "prompt": "Rewrite the following legal text in plain, easy-to-understand language for a non-lawyer.\nPreserve all important meaning but remove jargon. Use short sentences.\n\nLegal text:\n{legal_text}",
                   "temperature": 0.3, "max_tokens": 600}],
    },
    {
        "name": "Text Classifier",
        "description": "Classifies any text into one of the provided categories with a confidence note.",
        "mermaid_definition": """flowchart TD
    A[Input Text] --> B[Read Categories]
    B --> C[Analyze Text]
    C --> D[Assign Category]
    D --> E[Return Label + Reason]""",
        "steps": [{"id": "classify", "action": "call_llm", "model": "gemma",
                   "prompt": "Classify the following text into one of these categories: {categories}\n\nText: {text}\n\nRespond with: Category: <name>\\nReason: <one sentence>",
                   "temperature": 0.2, "max_tokens": 100}],
    },
]


def seed():
    with app.app_context():
        db.create_all()
        added = 0
        for s in SKILLS:
            if not Workflow.query.filter_by(name=s["name"]).first():
                db.session.add(Workflow(
                    name=s["name"],
                    description=s["description"],
                    mermaid_definition=s["mermaid_definition"],
                    steps=s["steps"],
                    is_active=True,
                ))
                added += 1
                print(f"  ✓  {s['name']}")
            else:
                print(f"  ⊘  {s['name']} (already exists)")
        db.session.commit()
        print(f"\n✅ Seeded {added} new skill(s). Total in DB: {Workflow.query.count()}")


if __name__ == "__main__":
    print("Seeding 20 skills…")
    seed()

