"""Local LLM client (Ollama). No API key, nothing leaves the laptop.

    brew install ollama && ollama serve        # or the Ollama.app
    ollama pull qwen2.5:7b                      # default model (~4.7 GB)

Env: OLLAMA_URL (default http://127.0.0.1:11434), SOCH_MODEL (default qwen2.5:7b), SOCH_LLM=off to force offline rules.
"""
import json
import os
import re
import time

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.getenv("SOCH_MODEL", "qwen2.5:7b")
_PREFERRED = ["qwen2.5:7b", "qwen2.5:3b", "qwen2.5-coder:7b", "llama3.2:3b", "llama3.1:8b", "gemma2:2b", "phi3:mini"]
TIMEOUT = float(os.getenv("SOCH_LLM_TIMEOUT", "120"))
_status_cache: dict = {"t": 0, "v": None}


class LLMUnavailable(Exception):
    pass


def status(force: bool = False) -> dict:
    global MODEL
    if os.getenv("SOCH_LLM", "").lower() == "off":
        return {"online": False, "model": MODEL, "reason": "SOCH_LLM=off"}
    if not force and _status_cache["v"] and time.time() - _status_cache["t"] < 15:
        return _status_cache["v"]
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2.5)
        r.raise_for_status()
        names = [m.get("name", "") for m in r.json().get("models", [])]
        ok = any(n == MODEL or n.split(":")[0] == MODEL or n == f"{MODEL}:latest" for n in names)
        if not ok and names and not os.getenv("SOCH_MODEL"):
            # auto-pick whatever model the user has pulled (preferring known-good ones)
            MODEL = next((m for m in _PREFERRED if m in names), names[0])
            ok = True
        v = {"online": ok, "model": MODEL, "installed": names,
             "reason": None if ok else f"Ollama is running but '{MODEL}' isn't pulled. Run: ollama pull {MODEL}"}
    except Exception:
        v = {"online": False, "model": MODEL, "reason": f"Ollama not reachable at {OLLAMA_URL}. Start it with `ollama serve`."}
    _status_cache.update(t=time.time(), v=v)
    return v


def chat(messages: list[dict], want_json: bool = False, temperature: float = 0.4, max_tokens: int = 700):
    st = status()
    if not st["online"]:
        raise LLMUnavailable(st["reason"])
    body = {"model": MODEL, "messages": messages, "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens, "num_ctx": 8192}}
    if want_json:
        body["format"] = "json"
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=TIMEOUT)
        r.raise_for_status()
        text = r.json()["message"]["content"].strip()
    except Exception as e:
        _status_cache["v"] = None
        raise LLMUnavailable(f"Ollama call failed: {e}")
    if not want_json:
        return text
    return parse_json(text)


def parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    raise LLMUnavailable("Model returned invalid JSON")
