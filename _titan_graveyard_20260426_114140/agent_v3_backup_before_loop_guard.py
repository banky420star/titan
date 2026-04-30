import json
import os
import re
import shlex
import subprocess
import textwrap
import uuid
from pathlib import Path
from datetime import datetime

import requests
import chromadb
from bs4 import BeautifulSoup
from pypdf import PdfReader
from ddgs import DDGS

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG_PATH = BASE / "config.json"

CONFIG = json.loads(CONFIG_PATH.read_text())
WORKSPACE = Path(CONFIG["workspace"])
RAG_DOCS = Path(CONFIG["rag_docs"])
RAG_DB = Path(CONFIG["rag_db"])
SKILLS_DIR = Path(CONFIG["skills_dir"])
SUBAGENTS_DIR = Path(CONFIG["subagents_dir"])
LOGS_DIR = Path(CONFIG["logs_dir"])

MODEL = CONFIG["model"]
EMBED_MODEL = CONFIG["embedding_model"]
CHAT_URL = CONFIG["ollama_chat_url"]
EMBED_URL = CONFIG["ollama_embed_url"]

for p in [WORKSPACE, RAG_DOCS, RAG_DB, SKILLS_DIR, SUBAGENTS_DIR, LOGS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS_DIR / "agent_v3.log"

MAX_READ = 20000
CMD_TIMEOUT = 35

BLOCKED = [
    "sudo",
    "rm -rf /",
    "mkfs",
    "diskutil erase",
    "shutdown",
    "reboot",
    "curl ",
    "wget ",
    "ssh ",
    "scp ",
    "chmod -r 777 /",
    "chown -r",
]

SYSTEM = f"""
You are Titan v3, a private local coding and research agent on the user's Mac.

You have these qualities:
- Claude Code-style coding workflow.
- Workspace-first file control.
- RAG over local documents.
- Web search when needed.
- Local skills.
- Sub-agent role delegation.
- Safe command execution.
- Privilege commands only with explicit terminal approval.

Approved workspace:
{WORKSPACE}

Use exactly one JSON object at a time.

MANDATORY tool call format:
{{"tool":"tool_name","input":{{...}}}}

Never use this wrong format:
{{"workspace_tree":{{}}}}

Correct examples:
{{"tool":"workspace_tree","input":{{}}}}
{{"tool":"list_files","input":{{}}}}
{{"tool":"read_file","input":{{"filename":"test.txt"}}}}

Final:
{{"final":"short useful answer"}}

Important rules:
- Use workspace-relative paths only.
- Do not use absolute file paths in tool input.
- Inspect before editing.
- Use skills when relevant.
- Use subagents for planning, coding, testing, or reviewing.
- Do not claim success until a tool result confirms it.
- For web facts, use web_search or fetch_url.
- For local docs, use index_rag then rag_search.
- When editing files, call write_file or replace_in_file. Do not merely show code.
- Never put triple quotes inside JSON.
- Escape newlines in JSON strings, or use one compact string.
- Return tool calls only in this exact shape: {{"tool":"write_file","input":{{"filename":"path","content":"text"}}}}
"""

def log(label, text):
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {label}: {text}\n")

def safe_rel(value):
    value = str(value or "").strip()
    if value.startswith(str(WORKSPACE)):
        value = str(Path(value).resolve().relative_to(WORKSPACE.resolve()))
    if value.startswith("/"):
        raise ValueError("absolute paths are blocked")
    return value

def safe_path(value):
    rel = safe_rel(value)
    p = (WORKSPACE / rel).resolve()
    root = WORKSPACE.resolve()
    if not str(p).startswith(str(root)):
        raise ValueError("path outside workspace blocked")
    return p

def tree(root=WORKSPACE, depth=4):
    lines = [root.name + "/"]

    def walk(path, prefix="", d=0):
        if d >= depth:
            return
        entries = sorted(
            [x for x in path.iterdir() if x.name not in [".DS_Store", "__pycache__", ".git"]],
            key=lambda x: (x.is_file(), x.name.lower())
        )
        for i, e in enumerate(entries):
            mark = "└── " if i == len(entries) - 1 else "├── "
            lines.append(prefix + mark + e.name + ("/" if e.is_dir() else ""))
            if e.is_dir():
                walk(e, prefix + ("    " if i == len(entries) - 1 else "│   "), d + 1)
    walk(root)
    return "\n".join(lines)

def list_files():
    return [
        str(p.relative_to(WORKSPACE))
        for p in WORKSPACE.rglob("*")
        if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts
    ]

def read_file(filename):
    p = safe_path(filename)
    if not p.exists():
        return f"File not found: {filename}"
    if p.is_dir():
        return f"Folder, not file: {filename}"
    txt = p.read_text(encoding="utf-8", errors="ignore")
    return txt[:MAX_READ] + ("\n[TRUNCATED]" if len(txt) > MAX_READ else "")

def write_file(filename, content):
    p = safe_path(filename)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(str(content), encoding="utf-8")
    return f"Wrote {filename}"

def append_file(filename, content):
    p = safe_path(filename)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(str(content))
    return f"Appended {filename}"

def replace_in_file(filename, old, new):
    p = safe_path(filename)
    if not p.exists():
        return f"File not found: {filename}"
    txt = p.read_text(encoding="utf-8", errors="ignore")
    if old not in txt:
        return "Old text not found"
    p.write_text(txt.replace(old, new), encoding="utf-8")
    return f"Updated {filename}"

def make_dir(dirname):
    p = safe_path(dirname)
    p.mkdir(parents=True, exist_ok=True)
    return f"Created folder {dirname}"

def search_files(query):
    query = str(query or "").lower()
    out = []
    for p in WORKSPACE.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for n, line in enumerate(txt.splitlines(), 1):
            if query in line.lower():
                out.append(f"{p.relative_to(WORKSPACE)}:{n}: {line.strip()}")
                if len(out) >= 50:
                    return "\n".join(out)
    return "\n".join(out) if out else "No matches"

def safe_command(command):
    command = str(command or "").strip()
    low = command.lower()
    for b in BLOCKED:
        if b in low:
            return False, f"blocked command part: {b}"
    try:
        parts = shlex.split(command)
    except Exception as e:
        return False, f"parse error: {e}"
    if not parts:
        return False, "empty command"
    allowed = CONFIG.get("allowed_command_prefixes", [])
    if parts[0] not in allowed:
        return False, f"command not in allowed list: {parts[0]}"
    return True, "ok"

def run_command(command):
    ok, reason = safe_command(command)
    if not ok:
        return "Command blocked: " + reason

    try:
        r = subprocess.run(
            command,
            shell=True,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=CMD_TIMEOUT
        )
        return f"exit_code: {r.returncode}\nstdout:\n{r.stdout[-8000:]}\nstderr:\n{r.stderr[-8000:]}"

    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or "")
        stderr = (e.stderr or "")

        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="ignore")
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="ignore")

        combined = stdout + "\n" + stderr

        if "Running on" in combined or "Debugger is active" in combined or "Press CTRL+C to quit" in combined:
            return (
                "Server appears to have started successfully and kept running. "
                "The command timed out because web servers do not exit on their own.\n\n"
                "captured_output:\n" + combined[-8000:]
            )

        return (
            f"Command timed out after {CMD_TIMEOUT} seconds.\n"
            f"stdout:\n{stdout[-4000:]}\n"
            f"stderr:\n{stderr[-4000:]}"
        )

def privileged_command(command):
    if not CONFIG.get("privilege_mode", False):
        return "Privilege mode is disabled in config.json. Set privilege_mode true only when needed."
    print("\nPRIVILEGED COMMAND REQUEST:")
    print(command)
    answer = input("Type YES to run this command: ").strip()
    if answer != "YES":
        return "User denied privileged command."
    r = subprocess.run(command, shell=True, cwd=str(BASE), capture_output=True, text=True, timeout=CMD_TIMEOUT)
    return f"exit_code: {r.returncode}\nstdout:\n{r.stdout[-8000:]}\nstderr:\n{r.stderr[-8000:]}"

def scaffold_project(name, kind):
    name = safe_rel(name)
    root = safe_path(name)
    root.mkdir(parents=True, exist_ok=True)

    if kind == "flask_app":
        (root / "templates").mkdir(exist_ok=True)
        (root / "static").mkdir(exist_ok=True)
        files = {
            "app.py": "from flask import Flask, render_template\n\napp = Flask(__name__)\n\n@app.route('/')\ndef home():\n    return render_template('index.html')\n\nif __name__ == '__main__':\n    app.run(debug=True, port=5000)\n",
            "templates/index.html": "<!doctype html><html><head><title>Titan App</title><link rel='stylesheet' href='/static/style.css'></head><body><main><h1>Titan App</h1><p>Local app online.</p></main></body></html>\n",
            "static/style.css": "body{font-family:system-ui;background:#111827;color:#f9fafb;margin:0}main{max-width:800px;margin:80px auto;padding:32px;background:#1f2937;border-radius:24px}\n",
            "requirements.txt": "flask\n",
            "README.md": "# Flask App\n\nRun:\n```bash\npip install -r requirements.txt\npython3 app.py\n```\n"
        }
    elif kind == "static_website":
        files = {
            "index.html": "<!doctype html><html><head><title>Titan Site</title><link rel='stylesheet' href='style.css'></head><body><section><h1>Titan Site</h1><p>Built locally.</p></section></body></html>\n",
            "style.css": "body{font-family:system-ui;background:#171321;color:white}section{min-height:100vh;display:grid;place-content:center;text-align:center}\n",
            "README.md": "# Static Website\n\nOpen index.html.\n"
        }
    else:
        files = {
            "main.py": "def main():\n    print('Hello from Titan.')\n\nif __name__ == '__main__':\n    main()\n",
            "requirements.txt": "",
            "README.md": "# Python CLI\n\nRun:\n```bash\npython3 main.py\n```\n"
        }

    for k, v in files.items():
        p = root / k
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(v, encoding="utf-8")

    return f"Scaffolded {kind} project: {name}"

def web_search(query, max_results=5):
    results = DDGS().text(str(query), max_results=int(max_results))
    clean = []
    for r in results:
        clean.append({
            "title": r.get("title"),
            "href": r.get("href"),
            "body": r.get("body")
        })
    return json.dumps(clean, indent=2)

def fetch_url(url):
    res = requests.get(url, timeout=15, headers={"User-Agent": "TitanAgent/1.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = " ".join(soup.get_text("\n").split())
    return text[:12000]

def ollama_embed(texts):
    if isinstance(texts, str):
        texts = [texts]
    res = requests.post(
        EMBED_URL,
        json={"model": EMBED_MODEL, "input": texts},
        timeout=180
    )
    res.raise_for_status()
    data = res.json()
    return data["embeddings"]

def read_doc_text(path):
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="ignore")

def chunks(text, size=1200, overlap=150):
    text = text.strip()
    out = []
    i = 0
    while i < len(text):
        out.append(text[i:i+size])
        i += size - overlap
    return out

def index_rag():
    client = chromadb.PersistentClient(path=str(RAG_DB))
    col = client.get_or_create_collection("titan_rag")
    docs = []
    metas = []
    ids = []

    files = [p for p in RAG_DOCS.rglob("*") if p.is_file() and p.suffix.lower() in [".txt", ".md", ".py", ".pdf"]]
    if not files:
        return f"No supported docs found in {RAG_DOCS}"

    for p in files:
        try:
            text = read_doc_text(p)
        except Exception as e:
            continue
        for idx, ch in enumerate(chunks(text)):
            if not ch.strip():
                continue
            docs.append(ch)
            metas.append({"source": str(p.relative_to(RAG_DOCS)), "chunk": idx})
            ids.append(str(uuid.uuid4()))

    if not docs:
        return "No text extracted."

    embeddings = ollama_embed(docs)
    col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
    return f"Indexed {len(docs)} chunks from {len(files)} files."

def rag_search(query, n=5):
    client = chromadb.PersistentClient(path=str(RAG_DB))
    col = client.get_or_create_collection("titan_rag")
    emb = ollama_embed(str(query))[0]
    res = col.query(query_embeddings=[emb], n_results=int(n))
    out = []
    for doc, meta in zip(res.get("documents", [[]])[0], res.get("metadatas", [[]])[0]):
        out.append(f"SOURCE: {meta.get('source')} CHUNK: {meta.get('chunk')}\n{doc[:1200]}")
    return "\n\n---\n\n".join(out) if out else "No RAG matches."

def list_skills():
    return "\n".join(sorted([p.name for p in SKILLS_DIR.iterdir() if p.is_dir()]))

def load_skill(name):
    p = SKILLS_DIR / safe_name(name) / "SKILL.md"
    if not p.exists():
        return f"Skill not found: {name}"
    return p.read_text(encoding="utf-8", errors="ignore")

def safe_name(name):
    name = str(name or "").lower().strip()
    name = re.sub(r"[^a-z0-9-]+", "-", name)
    return name.strip("-") or "new-skill"

def create_skill(name, description):
    name = safe_name(name)
    root = SKILLS_DIR / name
    root.mkdir(parents=True, exist_ok=True)
    (root / "SKILL.md").write_text(f"# {name}\n\n{description}\n\nWorkflow:\n1. Understand the task.\n2. Inspect relevant files.\n3. Execute the repeatable process.\n4. Verify output.\n", encoding="utf-8")
    (root / "templates").mkdir(exist_ok=True)
    (root / "scripts").mkdir(exist_ok=True)
    return f"Created local skill: {name}"

def call_subagent(name, task):
    p = SUBAGENTS_DIR / (safe_name(name) + ".json")
    if not p.exists():
        return f"Subagent not found: {name}"
    spec = json.loads(p.read_text())
    messages = [
        {"role": "system", "content": f"You are subagent {spec['name']}. Role: {spec['role']}. Return concise useful output."},
        {"role": "user", "content": str(task)}
    ]
    return chat(messages)

def chat(messages):
    r = requests.post(
        CHAT_URL,
        json={"model": MODEL, "messages": messages, "stream": False, "options": {"temperature": 0.1, "num_ctx": 8192}},
        timeout=180
    )
    r.raise_for_status()
    return r.json()["message"]["content"]

def extract_json(text):
    original = text
    text = text.strip()

    # Remove common markdown fences.
    text = text.replace("```json", "").replace("```python", "").replace("```html", "").replace("```css", "").replace("```", "").strip()

    known_tools = {
        "workspace_tree",
        "list_files",
        "read_file",
        "write_file",
        "append_file",
        "replace_in_file",
        "make_dir",
        "search_files",
        "run_command",
        "privileged_command",
        "scaffold_project",
        "web_search",
        "fetch_url",
        "index_rag",
        "rag_search",
        "list_skills",
        "load_skill",
        "create_skill",
        "call_subagent"
    }

    def scan_json_objects(s):
        dec = json.JSONDecoder()
        objs = []
        i = 0
        while i < len(s):
            start = s.find("{", i)
            if start == -1:
                break
            try:
                obj, end = dec.raw_decode(s[start:])
                objs.append(obj)
                i = start + end
            except Exception:
                i = start + 1
        return objs

    objs = scan_json_objects(text)

    # Repair common invalid JSON caused by Python triple-quoted content:
    # {"tool":"write_file","input":{"filename":"x","content": """..."""}}
    if not objs and '"""' in text and '"tool"' in text and '"write_file"' in text:
        try:
            tool_match = re.search(r'"tool"\s*:\s*"([^"]+)"', text, re.S)
            filename_match = re.search(r'"filename"\s*:\s*"([^"]+)"', text, re.S)
            content_match = re.search(r'"content"\s*:\s*"""(.*?)"""', text, re.S)

            if tool_match and filename_match and content_match:
                return {
                    "tool": tool_match.group(1),
                    "input": {
                        "filename": filename_match.group(1),
                        "content": content_match.group(1)
                    }
                }
        except Exception:
            pass

    if not objs:
        # Last resort: if the model wrote useful prose instead of JSON, return it as final.
        return {
            "final": "The model returned prose instead of a tool call. Raw response:\n" + original[:4000]
        }

    for o in objs:
        if isinstance(o, dict) and "tool" in o:
            return o

    for o in objs:
        if isinstance(o, dict) and "final" in o:
            return o

    # Auto-fix sloppy tool shape like {"workspace_tree": {}}
    for o in objs:
        if isinstance(o, dict):
            keys = list(o.keys())
            if len(keys) == 1 and keys[0] in known_tools:
                value = o[keys[0]]
                return {
                    "tool": keys[0],
                    "input": value if isinstance(value, dict) else {}
                }

    return objs[-1]

def tool(name, inp):
    inp = inp or {}
    if name == "workspace_tree": return tree()
    if name == "list_files": return json.dumps(list_files(), indent=2)
    if name == "read_file": return read_file(inp.get("filename") or inp.get("path") or "")
    if name == "write_file": return write_file(inp.get("filename") or inp.get("path") or "", inp.get("content") or "")
    if name == "append_file": return append_file(inp.get("filename") or "", inp.get("content") or "")
    if name == "replace_in_file": return replace_in_file(inp.get("filename") or "", inp.get("old") or "", inp.get("new") or "")
    if name == "make_dir": return make_dir(inp.get("dirname") or inp.get("path") or "")
    if name == "search_files": return search_files(inp.get("query") or "")
    if name == "run_command": return run_command(inp.get("command") or "")
    if name == "privileged_command": return privileged_command(inp.get("command") or "")
    if name == "scaffold_project": return scaffold_project(inp.get("project_name") or "new_project", inp.get("kind") or "python_cli")
    if name == "web_search": return web_search(inp.get("query") or "", inp.get("max_results") or 5)
    if name == "fetch_url": return fetch_url(inp.get("url") or "")
    if name == "index_rag": return index_rag()
    if name == "rag_search": return rag_search(inp.get("query") or "", inp.get("n") or 5)
    if name == "list_skills": return list_skills()
    if name == "load_skill": return load_skill(inp.get("name") or "")
    if name == "create_skill": return create_skill(inp.get("name") or "", inp.get("description") or "")
    if name == "call_subagent": return call_subagent(inp.get("name") or "planner", inp.get("task") or "")
    return f"Unknown tool: {name}"

TOOLS = """
Tools:
workspace_tree {}
list_files {}
read_file {"filename":"..."}
write_file {"filename":"...","content":"..."}
append_file {"filename":"...","content":"..."}
replace_in_file {"filename":"...","old":"...","new":"..."}
make_dir {"dirname":"..."}
search_files {"query":"..."}
run_command {"command":"python3 main.py"}
privileged_command {"command":"..."}  # requires privilege_mode true and terminal approval
scaffold_project {"project_name":"...","kind":"python_cli|flask_app|static_website"}
web_search {"query":"...","max_results":5}
fetch_url {"url":"..."}
index_rag {}
rag_search {"query":"...","n":5}
list_skills {}
load_skill {"name":"..."}
create_skill {"name":"...","description":"..."}
call_subagent {"name":"planner|coder|tester|reviewer","task":"..."}
"""

def run_agent(task, max_steps=20):
    messages = [
        {"role": "system", "content": SYSTEM + "\n" + TOOLS},
        {"role": "user", "content": task}
    ]
    for step in range(1, max_steps + 1):
        print(f"\n--- step {step} ---")
        reply = chat(messages)
        print(reply)
        log("MODEL", reply)
        try:
            obj = extract_json(reply)
        except Exception as e:
            return f"Could not parse model JSON: {e}\nRaw:\n{reply}"
        if "final" in obj:
            return obj["final"]
        name = obj.get("tool")
        inp = obj.get("input", {})
        try:
            result = tool(name, inp)
        except Exception as e:
            result = f"Tool error: {e}"
        print("\nTool result:\n" + str(result))
        log("TOOL " + str(name), str(result))
        messages.append({"role": "assistant", "content": json.dumps(obj)})
        messages.append({"role": "user", "content": "Tool result:\n" + str(result)})
    return "Stopped: max steps reached."

def main():
    print("Titan Local Agent v3")
    print("Workspace:", WORKSPACE)
    print("Icon:", BASE / "assets" / "titan_pixel_diva.svg")
    print("Type exit to quit.")
    while True:
        try:
            task = input("\nTask > ").strip()
        except EOFError:
            print("\nInput closed.")
            break
        if task.lower() in ["exit", "quit", "/bye"]:
            break
        if not task:
            continue
        print("\nFinal:\n" + str(run_agent(task)))

if __name__ == "__main__":
    main()
