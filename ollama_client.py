import os
import urllib.request
import urllib.error
import json

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "smollm:135m")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "15"))


def chat(messages: list[dict]) -> str:
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_BASE_URL.rstrip("/") + "/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return (data.get("message", {}).get("content") or "").strip()
