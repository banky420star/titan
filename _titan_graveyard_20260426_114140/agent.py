import json
import requests
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Volumes/AI_DRIVE/TitanAgent")
WORKSPACE = BASE_DIR / "workspace"
MEMORY_FILE = BASE_DIR / "memory" / "facts.json"
LOG_FILE = BASE_DIR / "logs" / "agent.log"

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:7b"

WORKSPACE.mkdir(parents=True, exist_ok=True)
MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """
You are Titan, a private local AI agent running on the user's Mac.

You are direct, technical, practical, and precise.

You can use tools to work inside the approved workspace only.

Available tools:
- list_files: list files in the workspace
- read_file: read a file from the workspace
- write_file: write a file to the workspace
- remember: save a long-term memory fact
- recall_memory: show saved memory facts

Tool input rules:
- For read_file and write_file, always use "filename", not "path".
- For remember, always use "content", not "fact".
- Use workspace-relative filenames like "test.txt".
- Do not use full absolute paths.
- Do not return a final answer until after the tool result is shown to you.
- Return only one JSON object at a time.

Tool response format:
When you want to use a tool, respond only as JSON:
{
  "tool": "tool_name",
  "input": {
    "filename": "example.txt",
    "content": "example content"
  }
}

When finished, respond only as JSON:
{
  "final": "your answer"
}

Rules:
- Never access files outside the approved workspace.
- Do not invent tool results.
- Use tools when the user asks you to create, read, edit, or remember something.
- Keep answers concrete and useful.
"""

def log_event(text):
    timestamp = datetime.now().isoformat(timespec="seconds")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {text}\n")

def load_memory():
    if not MEMORY_FILE.exists():
        return []
    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

def save_memory(memory):
    MEMORY_FILE.write_text(json.dumps(memory, indent=2), encoding="utf-8")

def safe_path(filename):
    filename = str(filename or "").strip()

    if filename.startswith(str(WORKSPACE)):
        filename = str(Path(filename).resolve().relative_to(WORKSPACE.resolve()))

    if filename.startswith(str(BASE_DIR)):
        raise ValueError("Blocked: only files inside workspace are allowed.")

    path = (WORKSPACE / filename).resolve()
    workspace_root = WORKSPACE.resolve()

    if not str(path).startswith(str(workspace_root)):
        raise ValueError("Blocked: path is outside the workspace.")

    return path

def list_files():
    files = []
    for path in WORKSPACE.rglob("*"):
        if path.is_file():
            files.append(str(path.relative_to(WORKSPACE)))
    return files

def read_file(filename):
    path = safe_path(filename)
    if not path.exists():
        return f"File not found: {filename}"
    if path.is_dir():
        return f"That is a folder, not a file: {filename}"
    return path.read_text(encoding="utf-8", errors="ignore")

def write_file(filename, content):
    path = safe_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(content), encoding="utf-8")
    return f"Wrote file: {filename}"

def remember(content):
    memory = load_memory()
    memory.append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "content": str(content)
    })
    save_memory(memory)
    return "Saved to memory."

def recall_memory():
    memory = load_memory()
    if not memory:
        return "No memory saved yet."
    return json.dumps(memory, indent=2)

def run_tool(tool, tool_input):
    try:
        tool_input = tool_input or {}

        filename = (
            tool_input.get("filename")
            or tool_input.get("file")
            or tool_input.get("file_path")
            or tool_input.get("path")
            or ""
        )

        content = (
            tool_input.get("content")
            or tool_input.get("text")
            or tool_input.get("fact")
            or tool_input.get("memory")
            or ""
        )

        if tool == "list_files":
            return json.dumps(list_files(), indent=2)

        if tool == "read_file":
            return read_file(filename)

        if tool == "write_file":
            return write_file(filename, content)

        if tool == "remember":
            return remember(content)

        if tool == "recall_memory":
            return recall_memory()

        return f"Unknown tool: {tool}"

    except Exception as e:
        return f"Tool error: {e}"

def call_ollama(messages):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        },
        timeout=180
    )
    response.raise_for_status()
    return response.json()["message"]["content"]

def extract_json(text):
    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    decoder = json.JSONDecoder()
    objects = []
    index = 0

    while index < len(text):
        start = text.find("{", index)
        if start == -1:
            break

        try:
            obj, end = decoder.raw_decode(text[start:])
            objects.append(obj)
            index = start + end
        except json.JSONDecodeError:
            index = start + 1

    if not objects:
        raise ValueError("No JSON object found in model response.")

    for obj in objects:
        if isinstance(obj, dict) and "tool" in obj:
            return obj

    return objects[-1]

def run_agent(user_task, max_steps=10):
    memory = load_memory()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": f"Approved workspace: {WORKSPACE}\nSaved memory:\n{json.dumps(memory, indent=2)}"
        },
        {"role": "user", "content": user_task}
    ]

    for step in range(1, max_steps + 1):
        print(f"\n--- step {step} ---")

        reply = call_ollama(messages)
        print(reply)
        log_event(f"MODEL: {reply}")

        try:
            parsed = extract_json(reply)
        except Exception as e:
            return f"Model did not return valid JSON. Error: {e}\nRaw reply:\n{reply}"

        if "final" in parsed:
            return parsed["final"]

        tool = parsed.get("tool")
        tool_input = parsed.get("input", {})

        result = run_tool(tool, tool_input)
        print(f"\nTool result:\n{result}")
        log_event(f"TOOL {tool}: {result}")

        messages.append({"role": "assistant", "content": json.dumps(parsed)})
        messages.append({"role": "user", "content": f"Tool result:\n{result}"})

    return "Stopped: max steps reached."

def main():
    print("Titan Local Agent v1.1")
    print("Type 'exit' to quit.")
    print(f"Workspace: {WORKSPACE}")

    while True:
        try:
            task = input("\nTask > ").strip()
        except EOFError:
            print("\nInput closed. Exiting Titan.")
            break

        if task.lower() in ["exit", "quit", "/bye"]:
            break

        if not task:
            continue

        final = run_agent(task)
        print(f"\nFinal:\n{final}")

if __name__ == "__main__":
    main()
