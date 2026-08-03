import json
import os
from typing import Iterator

import requests

# Ollama runs on the HOST, not in a container (Section 4.7 — Docker on Mac
# can't pass Metal through). `host.docker.internal` is how the backend
# container reaches it; OLLAMA_HOST overrides this for local (non-Docker) runs.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b")

# Still no native Ollama tool-calling (Epic F's `tools/` package is backend-
# orchestrated by design — see Section 8 Week 2 notes). `chat_json` below is
# just Ollama's structured-output mode (`format: "json"`), used for identity-
# field extraction (Epic B2) — the model never decides what unlocks data.


def chat(messages: list[dict]) -> str:
    """messages: list of {"role": "system"|"user"|"assistant", "content": str}"""
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def chat_stream(messages: list[dict]) -> Iterator[str]:
    """Same call as chat(), but with `stream: true` — yields each token/word
    chunk as Ollama produces it instead of blocking for the full reply.
    This is what actually shortens the *perceived* wait (Section 8's Week 2
    follow-up on latency) — the model still takes as long to finish, but the
    user sees text appearing immediately instead of a blank pause.
    """
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={"model": OLLAMA_MODEL, "messages": messages, "stream": True},
        stream=True,
        timeout=120,
    )
    response.raise_for_status()
    for line in response.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        content = chunk.get("message", {}).get("content", "")
        if content:
            yield content
        if chunk.get("done"):
            break


def chat_json(messages: list[dict]) -> dict:
    """Same as chat(), but constrains Ollama to emit valid JSON (`format:
    "json"`) and parses it. Returns {} if the model emits something that
    doesn't parse — callers must treat that as "extracted nothing new", not
    an error, since this only ever feeds a conversational nicety (Epic B2),
    never the actual match in verify_identity().
    """
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=120,
    )
    response.raise_for_status()
    content = response.json()["message"]["content"]
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}
