import requests
import json

OLLAMA_HOST = "http://localhost:11434"


def get_available_models() -> list:
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"] for m in models]
    except Exception:
        pass
    return ["gemma3:4b", "llama3.2:1b"]


def query_ollama_stream(messages: list, model: str):
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {"model": model, "messages": messages, "stream": True}
    try:
        response = requests.post(url, json=payload, stream=True, timeout=None)
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if "message" in chunk:
                    yield chunk["message"].get("content", "")
    except Exception as e:
        yield f"Connection Error: {e}"
