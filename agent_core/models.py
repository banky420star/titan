from pathlib import Path
import json
import os
import urllib.request

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG_PATH = BASE / "config.json"


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def ollama_chat(messages, model=None, timeout=180):
    cfg = load_config()
    model = model or cfg.get("model", "qwen3:8b")
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": int(cfg.get("num_ctx", 4096)),
            "num_predict": int(cfg.get("num_predict", 450)),
            "top_p": 0.9
        },
        "keep_alive": "10m"
    }

    req = urllib.request.Request(
        host + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data.get("message", {}).get("content", "")


def safe_chat(messages, model=None, timeout=180):
    cfg = load_config()
    primary = model or cfg.get("model", "qwen3:8b")
    fallback = cfg.get("fallback_model", "qwen2.5-coder:7b")

    try:
        return ollama_chat(messages, model=primary, timeout=timeout)
    except Exception as primary_error:
        if fallback and fallback != primary:
            try:
                return ollama_chat(messages, model=fallback, timeout=min(timeout, 120))
            except Exception as fallback_error:
                return json.dumps({
                    "final": "Titan model call failed safely. Primary error: "
                    + repr(primary_error)
                    + " Fallback error: "
                    + repr(fallback_error)
                })

        return json.dumps({
            "final": "Titan model call failed safely. Error: " + repr(primary_error)
        })
