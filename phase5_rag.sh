#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p agent_core rag/docs rag/db docs backups logs

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase5_$STAMP"

cp titan_terminal.py "backups/phase5_$STAMP/titan_terminal.py" 2>/dev/null || true
cp agent_core/tools.py "backups/phase5_$STAMP/tools.py" 2>/dev/null || true
cp agent_core/agent.py "backups/phase5_$STAMP/agent.py" 2>/dev/null || true
cp config.json "backups/phase5_$STAMP/config.json" 2>/dev/null || true

echo "[1/5] Writing agent_core/rag.py..."

cat > agent_core/rag.py <<'PY'
from pathlib import Path
import json
import math
import os
import urllib.request

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG_PATH = BASE / "config.json"
RAG_DOCS = BASE / "rag" / "docs"
RAG_DB = BASE / "rag" / "db"
INDEX_PATH = RAG_DB / "index.json"

RAG_DOCS.mkdir(parents=True, exist_ok=True)
RAG_DB.mkdir(parents=True, exist_ok=True)

TEXT_SUFFIXES = {
    ".txt", ".md", ".py", ".json", ".yaml", ".yml",
    ".html", ".css", ".js", ".ts", ".tsx", ".jsx",
    ".sh", ".zsh", ".sql", ".csv"
}


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def compact(text, limit=2200):
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[TRUNCATED]"


def chunk_text(text, size=1200, overlap=160):
    text = str(text or "").replace("\r\n", "\n")
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(0, end - overlap)

    return chunks


def embed_text(text):
    cfg = load_config()
    model = cfg.get("embedding_model", "nomic-embed-text:latest")
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

    payload = {
        "model": model,
        "input": text
    }

    req = urllib.request.Request(
        host + "/api/embed",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
        embeddings = data.get("embeddings") or []
        if embeddings:
            return embeddings[0]
    except Exception:
        pass

    # Fallback for older Ollama endpoint.
    payload = {
        "model": model,
        "prompt": text
    }

    req = urllib.request.Request(
        host + "/api/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data.get("embedding", [])


def cosine(a, b):
    if not a or not b:
        return 0.0

    n = min(len(a), len(b))
    a = a[:n]
    b = b[:n]

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))

    if na == 0 or nb == 0:
        return 0.0

    return dot / (na * nb)


def collect_files():
    files = []

    for root in [RAG_DOCS, BASE / "docs"]:
        if not root.exists():
            continue

        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            files.append(path)

    return files


def rag_status():
    if not INDEX_PATH.exists():
        return "RAG index not found. Run /rag-index."

    try:
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        return "RAG index unreadable: " + repr(e)

    sources = sorted(set(item.get("source", "") for item in data))
    return (
        f"RAG index: {INDEX_PATH}\n"
        f"Chunks: {len(data)}\n"
        f"Sources: {len(sources)}\n\n"
        + "\n".join("- " + s for s in sources[:30])
    )


def rag_index():
    files = collect_files()
    records = []

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if not text.strip():
            continue

        rel = str(path.relative_to(BASE))

        for i, chunk in enumerate(chunk_text(text)):
            try:
                embedding = embed_text(chunk)
            except Exception as e:
                return "Embedding failed for " + rel + ": " + repr(e)

            records.append({
                "source": rel,
                "chunk_id": i,
                "text": chunk,
                "embedding": embedding
            })

    INDEX_PATH.write_text(json.dumps(records), encoding="utf-8")

    return (
        f"Indexed {len(records)} chunks from {len(files)} files.\n"
        f"Index path: {INDEX_PATH}"
    )


def rag_search(query, top_k=5):
    query = str(query or "").strip()

    if not query:
        return "No query provided."

    if not INDEX_PATH.exists():
        return "RAG index not found. Run /rag-index first."

    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))

    if not data:
        return "RAG index is empty."

    try:
        qemb = embed_text(query)
    except Exception as e:
        return "Query embedding failed: " + repr(e)

    scored = []

    for item in data:
        score = cosine(qemb, item.get("embedding", []))
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)

    lines = [f"Top RAG matches for: {query}", ""]

    for score, item in scored[:int(top_k)]:
        lines.append(
            f"Score: {score:.4f}\n"
            f"Source: {item.get('source')}#chunk-{item.get('chunk_id')}\n"
            f"{compact(item.get('text', ''), 900)}\n"
        )

    return "\n".join(lines)
PY

echo "[2/5] Patching agent_core/tools.py..."

python3 - <<'PY'
from pathlib import Path

path = Path("agent_core/tools.py")
text = path.read_text()

if "from agent_core.rag import" not in text:
    anchor = "from agent_core.skills import create_skill_pack, list_skills, run_skill, install_dependency\n"
    import_line = "from agent_core.rag import rag_status, rag_index, rag_search\n"

    if anchor in text:
        text = text.replace(anchor, anchor + import_line)
    else:
        text = import_line + text

unknown = '    return "Unknown tool: " + str(name)\n'

rag_dispatch = '''    if name == "rag_status":
        return rag_status()
    if name == "rag_index":
        return rag_index()
    if name == "rag_search":
        return rag_search(inp.get("query", ""), inp.get("top_k", 5))

'''

if rag_dispatch.strip() not in text:
    if unknown not in text:
        raise SystemExit("Could not find Unknown tool return.")
    text = text.replace(unknown, rag_dispatch + unknown)

path.write_text(text)
print("Patched tools with RAG dispatch.")
PY

echo "[3/5] Patching agent_core/agent.py tool list..."

python3 - <<'PY'
from pathlib import Path

path = Path("agent_core/agent.py")
text = path.read_text()

addition = """- rag_status {}
- rag_index {}
- rag_search {"query":"search terms","top_k":5}
"""

if "rag_search" not in text:
    marker = "Available tools:\n"
    if marker in text:
        text = text.replace(marker, marker + addition)
    else:
        text = text.replace("Tools:", "Tools:\n" + addition)

path.write_text(text)
print("Patched agent tool list with RAG tools.")
PY

echo "[4/5] Patching titan_terminal.py commands..."

python3 - <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

if "def show_rag_status(" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helpers = r'''
def show_rag_status():
    try:
        from agent_core.rag import rag_status
        say_panel(rag_status(), title="RAG", style="cyan")
    except Exception as e:
        say_panel("RAG status failed: " + repr(e), title="RAG", style="red")


def run_rag_index():
    try:
        from agent_core.rag import rag_index
        say_panel("Indexing RAG docs. This can take a bit...", title="RAG", style="yellow")
        result = rag_index()
        say_panel(result, title="RAG Index", style="green")
    except Exception as e:
        say_panel("RAG indexing failed: " + repr(e), title="RAG", style="red")


def run_rag_search(query):
    try:
        from agent_core.rag import rag_search
        result = rag_search(query, top_k=5)
        say_panel(result, title="RAG Search", style="magenta")
    except Exception as e:
        say_panel("RAG search failed: " + repr(e), title="RAG", style="red")


'''
    text = text.replace(marker, helpers + marker)

if 'lower == "/rag"' not in text:
    target = '''            if lower == "/skills":
                show_skills()
                continue
'''

    replacement = '''            if lower == "/skills":
                show_skills()
                continue

            if lower == "/rag":
                show_rag_status()
                continue

            if lower == "/rag-index":
                run_rag_index()
                continue

            if lower.startswith("/rag-search "):
                run_rag_search(command.replace("/rag-search ", "", 1).strip())
                continue
'''

    if target not in text:
        target = '''            if lower == "/models":
                models()
                continue
'''
        replacement = target + '''
            if lower == "/rag":
                show_rag_status()
                continue

            if lower == "/rag-index":
                run_rag_index()
                continue

            if lower.startswith("/rag-search "):
                run_rag_search(command.replace("/rag-search ", "", 1).strip())
                continue
'''
        if target not in text:
            raise SystemExit("Could not find insertion point for RAG commands.")

    text = text.replace(target, replacement, 1)

text = text.replace(
    "/skills      Show Titan skills\n",
    "/skills      Show Titan skills\n/rag         Show RAG status\n/rag-index   Index rag/docs and docs\n/rag-search <query>\n"
)

path.write_text(text)
print("Patched terminal RAG commands.")
PY

echo "[5/5] Adding starter RAG note and verifying..."

cat > rag/docs/titan_system_note.md <<'MD'
# Titan System Note

Titan is a local-first terminal and dashboard agent.

Current priorities:
- Keep the official three-bar Titan mascot style.
- Use local Ollama models by default.
- Dashboard runs on port 5050.
- Old UI on port 5000 should stay archived.
- Terminal should support tools, subagents, skills, RAG, and background jobs.
MD

python3 -m py_compile agent_core/rag.py agent_core/tools.py agent_core/agent.py titan_terminal.py

cat > docs/PHASE5_RAG.md <<EOF
# Phase 5 RAG

Timestamp: $STAMP

Added:
- agent_core/rag.py
- /rag
- /rag-index
- /rag-search <query>

Agent tools:
- rag_status
- rag_index
- rag_search

Docs indexed from:
- rag/docs/
- docs/

Embedding model:
- nomic-embed-text:latest

Next:
- dashboard RAG page
- memory system
- agent auto-RAG when useful
EOF

echo "Phase 5 complete."
