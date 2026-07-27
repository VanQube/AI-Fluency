import os

import requests

# Ollama runs on the HOST, not in a container (Section 4.7 — Docker on Mac
# can't pass Metal through). `host.docker.internal` is how the backend
# container reaches it; OLLAMA_HOST overrides this for local (non-Docker) runs.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b")

# No tool defs yet — plain chat, no gating, no tool-calling (Epic F).
# See docs/system-prompt.md for the persona.


def chat(messages: list[dict]) -> str:
    """messages: list of {"role": "system"|"user"|"assistant", "content": str}"""
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]
