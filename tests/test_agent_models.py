"""API tests for configured agent models."""

from typing import Any, Dict

from fastapi.testclient import TestClient

from main import app
import main


def test_hi_hello_with_all_available_models(monkeypatch):
    """Send 'hi hello' to every available model and print success messages."""

    async def fake_chat_completions(payload: Dict[str, Any]) -> Dict[str, Any]:
        model_name = payload["model"]
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Hello from {model_name}",
                    },
                    "finish_reason": "stop",
                }
            ],
        }

    monkeypatch.setattr(main.lmstudio, "chat_completions", fake_chat_completions)

    client = TestClient(app)

    models_resp = client.get("/v1/models")
    assert models_resp.status_code == 200
    models_data = models_resp.json().get("data", [])
    assert models_data, "No models are configured"

    for item in models_data:
        model_id = item["id"]
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": "hi hello"}],
            "temperature": 0.2,
            "max_tokens": 32,
        }

        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200

        body = response.json()
        assert body["choices"][0]["message"]["content"].startswith("Hello from")

        print(f"SUCCESS: model '{model_id}' handled 'hi hello'")

    print("SUCCESS: all available agent models responded correctly")

