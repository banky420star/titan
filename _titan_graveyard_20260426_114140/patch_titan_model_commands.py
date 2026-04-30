from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

if "def set_model_profile(" not in text:
    marker = "def models():"
    if marker not in text:
        raise SystemExit("Could not find def models()")

    helper = r'''
def set_model_profile(profile):
    cfg = load_config()
    profiles = cfg.get("model_profiles", {})

    if profile not in profiles:
        say_panel(
            "Unknown profile: " + profile + "\n\nAvailable: " + ", ".join(profiles.keys()),
            title="Models",
            style="yellow"
        )
        return

    selected = profiles[profile]

    for key, value in selected.items():
        cfg[key] = value

    cfg["active_profile"] = profile
    CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    say_panel(
        f"Profile enabled: {profile}\n\n"
        f"Model: {cfg.get('model')}\n"
        f"Fallback: {cfg.get('fallback_model')}\n"
        f"Context: {cfg.get('num_ctx')}\n"
        f"Predict: {cfg.get('num_predict')}\n"
        f"Max steps: {cfg.get('max_agent_steps')}",
        title="Models",
        style="green"
    )


'''
    text = text.replace(marker, helper + marker)

if 'lower == "/tiny"' not in text:
    target = '''            if lower == "/models":
                models()
                continue
'''

    replacement = '''            if lower == "/models":
                models()
                continue

            if lower == "/tiny":
                set_model_profile("tiny")
                continue

            if lower == "/fast":
                set_model_profile("fast")
                continue

            if lower == "/coder":
                set_model_profile("coder")
                continue

            if lower == "/smart":
                set_model_profile("smart")
                continue

            if lower == "/heavy":
                set_model_profile("heavy")
                continue

            if lower == "/max":
                set_model_profile("max")
                continue
'''

    if target not in text:
        raise SystemExit("Could not find /models handler.")
    text = text.replace(target, replacement)

path.write_text(text)
print("Patched Titan model profile commands.")
