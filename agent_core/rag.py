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
