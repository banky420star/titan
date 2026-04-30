from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse, parse_qs, unquote
import ipaddress
import json
import re
import socket
import ssl
import urllib.request

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG_PATH = BASE / "config.json"
DOWNLOADS = BASE / "downloads"
DOWNLOADS.mkdir(parents=True, exist_ok=True)


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}




def ssl_context():
    cfg = load_config()

    if cfg.get("verify_ssl", True):
        try:
            import certifi
            return ssl.create_default_context(cafile=certifi.where())
        except Exception:
            return ssl.create_default_context()

    # User-enabled fallback for Mac/Python cert-chain issues.
    # URL/domain/private-network validation still happens before requests.
    return ssl._create_unverified_context()


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

    with urllib.request.urlopen(req, timeout=30, context=ssl_context()) as response:
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
        with urllib.request.urlopen(req, timeout=30, context=ssl_context()) as response:
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
        with urllib.request.urlopen(req, timeout=60, context=ssl_context()) as response:
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
