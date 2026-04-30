from pathlib import Path
import json

# 1. Update config
config_path = Path("config.json")
config = json.loads(config_path.read_text()) if config_path.exists() else {}

config["verify_ssl"] = False
config["web_enabled"] = True
config["allow_private_network_fetch"] = False

config_path.write_text(json.dumps(config, indent=2))
print("Updated config.json: verify_ssl = false")

# 2. Patch web_tools.py
path = Path("agent_core/web_tools.py")
text = path.read_text()

if "import ssl" not in text:
    text = text.replace("import socket\n", "import socket\nimport ssl\n")

helper = r'''

def ssl_context():
    cfg = load_config()

    if cfg.get("verify_ssl", True):
        try:
            import certifi
            return ssl.create_default_context(cafile=certifi.where())
        except Exception:
            return ssl.create_default_context()

    # User-enabled fallback for Mac/Python cert-chain issues.
    # URL/domain/private-network validation still happens before requests.
    return ssl._create_unverified_context()

'''

if "def ssl_context():" not in text:
    marker = "def compact(text, limit=9000):"
    if marker not in text:
        raise SystemExit("Could not find compact() marker")
    text = text.replace(marker, helper + "\n" + marker)

# Add context=ssl_context() to urllib.urlopen calls that do not already have context.
text = text.replace(
    "urllib.request.urlopen(req, timeout=30)",
    "urllib.request.urlopen(req, timeout=30, context=ssl_context())"
)

text = text.replace(
    "urllib.request.urlopen(req, timeout=60)",
    "urllib.request.urlopen(req, timeout=60, context=ssl_context())"
)

text = text.replace(
    "urllib.request.urlopen(URL, timeout=1.2)",
    "urllib.request.urlopen(URL, timeout=1.2, context=ssl_context())"
)

path.write_text(text)
print("Patched agent_core/web_tools.py SSL handling.")
