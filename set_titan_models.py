import json
from pathlib import Path

path = Path("config.json")
config = json.loads(path.read_text()) if path.exists() else {}

config["local_only"] = True

config["embedding_model"] = "nomic-embed-text:latest"

config["model_profiles"] = {
    "tiny": {
        "model": "qwen3:1.7b",
        "fallback_model": "qwen2.5-coder:7b",
        "num_ctx": 2048,
        "num_predict": 250,
        "max_agent_steps": 3
    },
    "fast": {
        "model": "qwen2.5-coder:7b",
        "fallback_model": "qwen3:8b",
        "num_ctx": 4096,
        "num_predict": 450,
        "max_agent_steps": 5
    },
    "coder": {
        "model": "qwen2.5-coder:14b",
        "fallback_model": "qwen2.5-coder:7b",
        "num_ctx": 8192,
        "num_predict": 800,
        "max_agent_steps": 7
    },
    "smart": {
        "model": "qwen3:8b",
        "fallback_model": "qwen2.5-coder:14b",
        "num_ctx": 8192,
        "num_predict": 900,
        "max_agent_steps": 8
    },
    "heavy": {
        "model": "batiai/qwen3.6-35b:iq3",
        "fallback_model": "qwen3:8b",
        "num_ctx": 16384,
        "num_predict": 1200,
        "max_agent_steps": 10
    },
    "max": {
        "model": "qwen3.6:35b",
        "fallback_model": "batiai/qwen3.6-35b:iq3",
        "num_ctx": 16384,
        "num_predict": 1600,
        "max_agent_steps": 12
    }
}

# Default mode: smart enough but not painfully slow.
config["active_profile"] = "smart"
config.update(config["model_profiles"]["smart"])

config["role_models"] = {
    "planner": "qwen3:8b",
    "coder": "qwen2.5-coder:14b",
    "tester": "qwen2.5-coder:7b",
    "reviewer": "batiai/qwen3.6-35b:iq3"
}

path.write_text(json.dumps(config, indent=2))
print("Titan model profiles configured.")
print(json.dumps({
    "active_profile": config["active_profile"],
    "model": config["model"],
    "fallback_model": config["fallback_model"],
    "role_models": config["role_models"]
}, indent=2))
