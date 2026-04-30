from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

if "def run_titan_prompt(" in text:
    print("run_titan_prompt already exists.")
else:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helper = r'''
def run_titan_prompt(command):
    try:
        from agent_core.agent import run_agent
        return run_agent(command, max_steps=8)
    except Exception as e:
        return "Titan brain failed safely: " + repr(e)


'''
    text = text.replace(marker, helper + marker)

path.write_text(text)
print("Added missing run_titan_prompt().")
