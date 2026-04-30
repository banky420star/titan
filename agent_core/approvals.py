from pathlib import Path
import json
import shlex

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG = BASE / "config.json"

SAFE_READ_PREFIXES = {
    "ls",
    "pwd",
    "cat",
    "find",
    "grep"
}

WRITE_PREFIXES = {
    "python",
    "python3",
    "pip",
    "mkdir",
    "touch",
    "pytest",
    "node",
    "npm",
    "git",
    "ollama"
}

HARD_BLOCK_FRAGMENTS = [
    "sudo ",
    " rm -rf /",
    "rm -rf /",
    "diskutil erase",
    "mkfs",
    "dd if=",
    "dd of=",
    ":(){",
    "chmod -R 777 /",
    "chown -R"
]


def load_config():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def save_config(config):
    CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")


def get_mode():
    return load_config().get("permission_mode", "power")


def set_mode(mode):
    mode = str(mode or "").strip().lower()

    if mode not in ["safe", "power", "agentic"]:
        return "Unknown mode. Use safe, power, or agentic."

    config = load_config()
    config["permission_mode"] = mode
    save_config(config)

    return "Permission mode set to: " + mode


def permission_status():
    config = load_config()
    mode = config.get("permission_mode", "power")
    allowed = config.get("allowed_command_prefixes", [])

    return (
        f"Permission mode: {mode}\n\n"
        "Modes:\n"
        "- safe: read/check commands only\n"
        "- power: normal workspace build commands\n"
        "- agentic: broader autonomous build commands, still blocks destructive commands\n\n"
        "Allowed prefixes:\n"
        + "\n".join("- " + x for x in allowed)
    )


def validate_command(command):
    config = load_config()
    mode = config.get("permission_mode", "power")
    command = str(command or "").strip()

    if not command:
        return False, "No command provided.", []

    lowered = command.lower()

    blocked = config.get("blocked_command_fragments", HARD_BLOCK_FRAGMENTS)

    for fragment in blocked:
        if fragment.lower() in lowered:
            return False, "Blocked dangerous fragment: " + fragment, []

    try:
        parts = shlex.split(command)
    except Exception as e:
        return False, "Could not parse command: " + repr(e), []

    if not parts:
        return False, "No command provided.", []

    prefix = parts[0]

    allowed = set(config.get("allowed_command_prefixes", []))

    if prefix not in allowed:
        return False, "Command prefix is not allowed: " + prefix, parts

    if mode == "safe":
        if prefix not in SAFE_READ_PREFIXES:
            return False, "Safe mode blocks non-read command: " + prefix, parts

    if mode == "power":
        if prefix not in SAFE_READ_PREFIXES and prefix not in WRITE_PREFIXES:
            return False, "Power mode blocks command: " + prefix, parts

    if mode == "agentic":
        # Agentic allows configured prefixes, but hard-blocks destructive fragments above.
        return True, "Allowed in agentic mode.", parts

    return True, "Allowed.", parts
