from pathlib import Path

path = Path("agent_core/agent.py")
text = path.read_text()

Path("backups").mkdir(exist_ok=True)
Path("backups/agent_core_agent_before_multi_json.py").write_text(text)

new_text = r'''import json
import re
from agent_core.models import safe_chat
from agent_core.tools import dispatch_tool, compact


SYSTEM = """You are Titan, a local-first terminal coding and workspace agent.

You MUST respond with JSON.

Preferred format:
Return exactly one JSON object at a time.

Tool call format:
{"tool":"tool_name","input":{...}}

Final answer format:
{"final":"short useful answer"}

Available tools:
- workspace_tree {"max_items":180}
- list_files {}
- read_file {"filename":"path"}
- write_file {"filename":"path","content":"text"}
- append_file {"filename":"path","content":"text"}
- run_command {"command":"python3 file.py"}
- create_product {"name":"demo","kind":"python_cli|flask_app|static_website","description":"text"}
- list_products {}

Rules:
- Inspect before editing.
- Use workspace-relative paths for file tools.
- Do not claim you used a tool unless tool output was provided.
- Keep output concise.
- If you need multiple tool calls, prefer one JSON object per model turn.
"""


def extract_json_objects(text):
    """Extract one or more JSON objects from model output.

    Handles:
    {"tool":"write_file",...}
    {"tool":"read_file",...}
    {"final":"done"}

    Also handles prose wrapped around JSON.
    """
    text = str(text or "").strip()
    decoder = json.JSONDecoder()
    objects = []

    i = 0
    n = len(text)

    while i < n:
        # Find the next possible object start.
        start = text.find("{", i)
        if start == -1:
            break

        try:
            obj, end = decoder.raw_decode(text[start:])
            if isinstance(obj, dict):
                objects.append(obj)
            i = start + end
        except Exception:
            i = start + 1

    return objects


def run_agent(task, max_steps=8):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": str(task)}
    ]

    for step in range(1, int(max_steps) + 1):
        raw = safe_chat(messages)
        objects = extract_json_objects(raw)

        if not objects:
            return "The model returned prose instead of JSON:\n\n" + compact(raw, 4000)

        saw_tool = False
        final_text = None
        tool_summaries = []

        for obj in objects:
            if "tool" in obj:
                saw_tool = True
                name = obj.get("tool")
                inp = obj.get("input") or {}

                result = dispatch_tool(name, inp)
                result = compact(result)

                tool_summaries.append(f"Tool {name} result:\n{result}")

                messages.append({"role": "assistant", "content": json.dumps(obj)})
                messages.append({
                    "role": "user",
                    "content": "Tool result for " + str(name) + ":\n" + result
                })
                continue

            if "final" in obj:
                final_text = str(obj.get("final", ""))
                continue

            return "Invalid JSON object from model:\n" + json.dumps(obj, indent=2)

        # If model gave tools and final in one batch, accept the final after running tools.
        # This fixes outputs like:
        # {"tool":...}
        # {"tool":...}
        # {"final":"..."}
        if final_text is not None:
            return final_text

        # If tools ran but no final yet, ask the model for the next step/final.
        if saw_tool:
            continue

    return "Stopped after max steps without final answer."
'''

path.write_text(new_text)
print("Patched agent_core/agent.py to handle multiple JSON objects.")
