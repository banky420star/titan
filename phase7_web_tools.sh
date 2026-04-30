#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p agent_core downloads docs backups logs

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase7_$STAMP"

cp titan_terminal.py "backups/phase7_$STAMP/titan_terminal.py" 2>/dev/null || true
cp agent_core/tools.py "backups/phase7_$STAMP/tools.py" 2>/dev/null || true
cp agent_core/agent.py "backups/phase7_$STAMP/agent.py" 2>/dev/null || true
cp config.json "backups/phase7_$STAMP/config.json" 2>/dev/null || true

echo "[1/5] Enabling web access in config..."

python3 - <<'PY'
import json
from pathlib import Path

path = Path("config.json")
config = json.loads(path.read_text()) if path.exists() else {}

config["web_enabled"] = True
config["allow_private_network_fetch"] = False
config["max_fetch_bytes"] = 2_500_000
config["max_download_bytes"] = 250_000_000

# "*" means Titan can fetch normal public web URLs.
# Private/local network fetches are still blocked unless allow_private_network_fetch is true.
config["approved_web_domains"] = ["*"]

# Downloads are allowed from public web too, but still saved only into downloads/.
config["approved_download_domains"] = ["*"]

path.write_text(json.dumps(config, indent=2))
print("Web access enabled.")
PY

echo "[2/5] Writing agent_core/web_tools.py..."

cat > agent_core/web_tools.py <<'PY'
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse, parse_qs, unquote
import ipaddress
import json
import re
import socket
import urllib.request

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG_PATH = BASE / "config.json"
DOWNLOADS = BASE / "downloads"
DOWNLOADS.mkdir(parents=True, exist_ok=True)


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def compact(text, limit=9000):
    text = str(text or "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) > limit:
        return text[:limit] + "\n\n[TRUNCATED]"
    return text


def domain_allowed(host, allowed):
    host = (host or "").lower().strip()

    if not host:
        return False

    if "*" in allowed:
        return True

    for domain in allowed:
        domain = domain.lower().strip()
        if host == domain or host.endswith("." + domain):
            return True

    return False


def is_private_host(host):
    host = (host or "").lower().strip()

    if host in ["localhost", "0.0.0.0"]:
        return True

    if host.endswith(".local"):
        return True

    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except Exception:
        pass

    try:
        infos = socket.getaddrinfo(host, None)
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return True
    except Exception:
        return False

    return False


def validate_url(url, mode="fetch"):
    cfg = load_config()

    if not cfg.get("web_enabled", False):
        raise ValueError("Web access is disabled in config.json.")

    url = str(url or "").strip()

    if not url.startswith(("http://", "https://")):
        raise ValueError("Only http:// and https:// URLs are allowed.")

    parsed = urlparse(url)
    host = parsed.hostname or ""

    if not cfg.get("allow_private_network_fetch", False) and is_private_host(host):
        raise ValueError("Blocked private/local network fetch: " + host)

    key = "approved_download_domains" if mode == "download" else "approved_web_domains"
    allowed = cfg.get(key, ["*"])

    if not domain_allowed(host, allowed):
        raise ValueError("Domain not approved: " + host)

    return url, parsed


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.skip = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
        if tag in ["script", "style", "noscript", "svg"]:
            self.skip = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        if tag in ["script", "style", "noscript", "svg"]:
            self.skip = False

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        if self.in_title:
            self.title += data + " "
            return
        if not self.skip:
            self.parts.append(data)


class DuckResultParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.in_result = False
        self.current_href = ""
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls = attrs.get("class", "")
        href = attrs.get("href", "")

        if tag == "a" and ("result__a" in cls or "result-link" in cls or href.startswith("/l/?")):
            self.in_result = True
            self.current_href = href
            self.current_text = []

    def handle_endtag(self, tag):
        if tag == "a" and self.in_result:
            title = " ".join(self.current_text).strip()
            href = normalize_duck_url(self.current_href)

            if title and href:
                self.results.append({
                    "title": title,
                    "url": href
                })

            self.in_result = False
            self.current_href = ""
            self.current_text = []

    def handle_data(self, data):
        if self.in_result:
            data = data.strip()
            if data:
                self.current_text.append(data)


def normalize_duck_url(href):
    if not href:
        return ""

    if href.startswith("//"):
        return "https:" + href

    if href.startswith("http://") or href.startswith("https://"):
        return href

    if "uddg=" in href:
        qs = parse_qs(urlparse(href).query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])

    if href.startswith("/"):
        return "https://duckduckgo.com" + href

    return href


def fetch_url(url):
    url, parsed = validate_url(url, mode="fetch")
    cfg = load_config()
    max_bytes = int(cfg.get("max_fetch_bytes", 2_500_000))

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "TitanAgent/1.0 (+local terminal assistant)"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "")
        raw = response.read(max_bytes + 1)

    if len(raw) > max_bytes:
        return "Fetch blocked: response exceeds max_fetch_bytes."

    text = raw.decode("utf-8", errors="ignore")

    if "html" in content_type.lower() or "<html" in text[:500].lower():
        parser = TextExtractor()
        parser.feed(text)

        title = parser.title.strip()
        body = "\n".join(parser.parts)
        body = re.sub(r"\s{2,}", " ", body)
        body = compact(body, 9000)

        return (
            f"URL: {url}\n"
            f"Title: {title or '(no title)'}\n"
            f"Content-Type: {content_type}\n\n"
            f"{body}"
        )

    return (
        f"URL: {url}\n"
        f"Content-Type: {content_type}\n\n"
        f"{compact(text, 9000)}"
    )


def web_search(query, max_results=6):
    query = str(query or "").strip()

    if not query:
        return "No search query provided."

    validate_url("https://duckduckgo.com", mode="fetch")

    params = urlencode({"q": query})
    url = "https://duckduckgo.com/html/?" + params

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 TitanAgent/1.0"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read(2_500_000).decode("utf-8", errors="ignore")
    except Exception as e:
        return "Web search failed: " + repr(e)

    parser = DuckResultParser()
    parser.feed(html)

    seen = set()
    cleaned = []

    for item in parser.results:
        url = item["url"]
        if url in seen:
            continue
        seen.add(url)
        cleaned.append(item)
        if len(cleaned) >= int(max_results):
            break

    if not cleaned:
        return "No web search results found."

    lines = [f"Web search results for: {query}", ""]

    for i, item in enumerate(cleaned, 1):
        lines.append(f"{i}. {item['title']}\n   {item['url']}")

    return "\n".join(lines)


def download_url(url, filename=""):
    url, parsed = validate_url(url, mode="download")
    cfg = load_config()
    max_bytes = int(cfg.get("max_download_bytes", 250_000_000))

    guessed = Path(parsed.path).name or "downloaded-file"
    filename = str(filename or guessed).strip()

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-") or "downloaded-file"
    target = (DOWNLOADS / safe_name).resolve()

    if not str(target).startswith(str(DOWNLOADS.resolve())):
        return "Blocked unsafe download path."

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "TitanAgent/1.0 (+local terminal assistant)"
        }
    )

    total = 0

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            with target.open("wb") as f:
                while True:
                    chunk = response.read(1024 * 512)
                    if not chunk:
                        break

                    total += len(chunk)

                    if total > max_bytes:
                        target.unlink(missing_ok=True)
                        return "Download blocked: file exceeds max_download_bytes."

                    f.write(chunk)

        return f"Downloaded {total} bytes to: {target}"

    except Exception as e:
        target.unlink(missing_ok=True)
        return "Download failed: " + repr(e)
PY

echo "[3/5] Patching agent_core/tools.py..."

python3 - <<'PY'
from pathlib import Path

path = Path("agent_core/tools.py")
text = path.read_text()

if "from agent_core.web_tools import" not in text:
    # place after other agent_core imports if possible
    anchor = "from agent_core.memory import memory_save, memory_search, memory_list, memory_delete\n"
    import_line = "from agent_core.web_tools import web_search, fetch_url, download_url\n"

    if anchor in text:
        text = text.replace(anchor, anchor + import_line)
    else:
        text = import_line + text

unknown = '    return "Unknown tool: " + str(name)\n'

dispatch = '''    if name == "web_search":
        return web_search(inp.get("query", ""), inp.get("max_results", 6))
    if name == "fetch_url":
        return fetch_url(inp.get("url", ""))
    if name == "download_url":
        return download_url(inp.get("url", ""), inp.get("filename", ""))

'''

if dispatch.strip() not in text:
    if unknown not in text:
        raise SystemExit("Could not find Unknown tool return.")
    text = text.replace(unknown, dispatch + unknown)

path.write_text(text)
print("Patched tools with web tools.")
PY

echo "[4/5] Patching agent_core/agent.py tool list..."

python3 - <<'PY'
from pathlib import Path

path = Path("agent_core/agent.py")
text = path.read_text()

addition = """- web_search {"query":"search terms","max_results":6}
- fetch_url {"url":"https://example.com/page"}
- download_url {"url":"https://example.com/file","filename":"optional-name.ext"}
"""

if "web_search" not in text:
    marker = "Available tools:\n"
    if marker in text:
        text = text.replace(marker, marker + addition)
    else:
        text = addition + text

# Add a brief web rule.
rule = "- Use web_search/fetch_url when current online information is needed.\n"
if rule not in text:
    text = text.replace("Rules:\n", "Rules:\n" + rule)

path.write_text(text)
print("Patched agent tool list with web tools.")
PY

echo "[5/5] Patching titan_terminal.py commands..."

python3 - <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

if "def web_search_terminal(" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helpers = r'''
def web_search_terminal(query):
    try:
        from agent_core.web_tools import web_search
        result = web_search(query, max_results=6)
        say_panel(result, title="Web Search", style="cyan")
    except Exception as e:
        say_panel("Web search failed: " + repr(e), title="Web Search", style="red")


def fetch_url_terminal(url):
    try:
        from agent_core.web_tools import fetch_url
        result = fetch_url(url)
        say_panel(result, title="Fetch URL", style="magenta")
    except Exception as e:
        say_panel("Fetch failed: " + repr(e), title="Fetch URL", style="red")


def download_url_terminal(args):
    try:
        from agent_core.web_tools import download_url

        parts = str(args or "").strip().split(" ", 1)
        if not parts or not parts[0]:
            say_panel("Usage: /download <url> [filename]", title="Download", style="yellow")
            return

        url = parts[0]
        filename = parts[1].strip() if len(parts) > 1 else ""

        result = download_url(url, filename)
        say_panel(result, title="Download", style="green")
    except Exception as e:
        say_panel("Download failed: " + repr(e), title="Download", style="red")


'''
    text = text.replace(marker, helpers + marker)

if 'lower.startswith("/web ")' not in text:
    target = '''            if lower == "/memory":
                show_memory()
                continue
'''

    replacement = '''            if lower == "/memory":
                show_memory()
                continue

            if lower.startswith("/web "):
                web_search_terminal(command.replace("/web ", "", 1).strip())
                continue

            if lower.startswith("/fetch "):
                fetch_url_terminal(command.replace("/fetch ", "", 1).strip())
                continue

            if lower.startswith("/download "):
                download_url_terminal(command.replace("/download ", "", 1).strip())
                continue
'''

    if target not in text:
        target = '''            if lower == "/rag":
                show_rag_status()
                continue
'''
        replacement = target + '''
            if lower.startswith("/web "):
                web_search_terminal(command.replace("/web ", "", 1).strip())
                continue

            if lower.startswith("/fetch "):
                fetch_url_terminal(command.replace("/fetch ", "", 1).strip())
                continue

            if lower.startswith("/download "):
                download_url_terminal(command.replace("/download ", "", 1).strip())
                continue
'''

    if target not in text:
        raise SystemExit("Could not find insertion point for web commands.")

    text = text.replace(target, replacement, 1)

text = text.replace(
    "/memory      Show saved Titan memories\n",
    "/memory      Show saved Titan memories\n/web <query> Search the web\n/fetch <url> Fetch public URL text\n/download <url> [filename]\n"
)

path.write_text(text)
print("Patched terminal web commands.")
PY

python3 -m py_compile agent_core/web_tools.py agent_core/tools.py agent_core/agent.py titan_terminal.py

cat > docs/PHASE7_WEB_TOOLS.md <<EOF
# Phase 7 Web Tools

Timestamp: $STAMP

Added:
- agent_core/web_tools.py
- /web <query>
- /fetch <url>
- /download <url> [filename]

Agent tools:
- web_search
- fetch_url
- download_url

Config:
- web_enabled = true
- private/local network fetch blocked by default
- downloads saved only to downloads/

Next:
- approvals mode
- dashboard web/search page
- automatic source notes in agent answers
EOF

echo "Phase 7 complete."
