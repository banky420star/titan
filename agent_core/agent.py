import json
import re
from agent_core.models import safe_chat
from agent_core.tools import dispatch_tool, compact


SYSTEM = """You are Titan, a local-first terminal coding and workspace agent.

You MUST respond with JSON only. No prose. No markdown. No explanations outside JSON.

Preferred format:
Return exactly one JSON object at a time whenever possible. Use the fewest tool calls possible.

Tool call format:
{"tool":"tool_name","input":{...}}

Final answer format:
{"final":"short useful answer"}

Available tools:
- web_search {"query":"search terms","max_results":6}
- fetch_url {"url":"https://example.com/page"}
- download_url {"url":"https://example.com/file","filename":"optional-name.ext"}
- memory_save {"text":"memory text","kind":"project_fact|preference|decision|bug_fix","scope":"project|user","tags":[]}
- memory_search {"query":"search terms","scope":"all|project|user","limit":8}
- memory_list {"scope":"all|project|user","limit":40}
- memory_delete {"id":"mem-id"}
- rag_status {}
- rag_index {}
- rag_search {"query":"search terms","top_k":5}
- workspace_tree {"max_items":180}
- list_files {}
- read_file {"filename":"path"}
- write_file {"filename":"path","content":"text"}
- append_file {"filename":"path","content":"text"}
- run_command {"command":"python3 file.py"}
- create_product {"name":"demo","kind":"python_cli|flask_app|static_website","description":"text"}
- list_products {}
- list_skills {}
- create_skill_pack {"name":"skill-name","description":"text","dependencies":[]}
- run_skill {"name":"skill-name","task":"task","context":"optional context"}
- install_dependency {"package":"package-name"}

Rules:
- Use web_search/fetch_url when current online information is needed.
- Inspect before editing.
- Use workspace-relative paths for file tools.
- Do not claim you used a tool unless tool output was provided.
- Keep output extremely concise.
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


def run_agent(task, max_steps=5):
    # TITAN_MEMORY_CONTEXT_PATCH
    memory_context = ""
    try:
        from agent_core.memory import memory_search
        memory_context = memory_search(str(task), scope="all", limit=5)
        if "No matching memories found" in memory_context:
            memory_context = ""
    except Exception:
        memory_context = ""

    user_content = str(task)
    if memory_context:
        user_content = "Relevant Titan memory:\n" + memory_context + "\n\nTask:\n" + str(task)

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_content}
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
