from pathlib import Path

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

# ------------------------------------------------------------
# 1. Toast HTML
# ------------------------------------------------------------
toast_html = r'''
  <!-- TITAN_TOASTS_HTML_START -->
  <div id="toastHost" class="toast-host" aria-live="polite"></div>
  <!-- TITAN_TOASTS_HTML_END -->
'''

if "TITAN_TOASTS_HTML_START" not in text:
    text = text.replace("</body>", toast_html + "\n</body>", 1)

# ------------------------------------------------------------
# 2. Toast CSS
# ------------------------------------------------------------
toast_css = r'''
    /* TITAN_TOASTS_START */
    .toast-host {
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 10000;
      display: grid;
      gap: 10px;
      width: min(390px, calc(100vw - 36px));
      pointer-events: none;
    }

    .toast {
      pointer-events: auto;
      border: 1px solid rgba(255,255,255,.12);
      background:
        radial-gradient(circle at 18% 0%, rgba(232,171,67,.18), transparent 36%),
        rgba(18,19,22,.96);
      box-shadow: 0 18px 50px rgba(0,0,0,.36);
      backdrop-filter: blur(12px);
      color: #f4f4f5;
      border-radius: 18px;
      padding: 13px 14px;
      display: grid;
      grid-template-columns: 28px 1fr auto;
      gap: 10px;
      align-items: start;
      animation: toastIn .18s ease both;
    }

    .toast.leaving {
      animation: toastOut .16s ease both;
    }

    @keyframes toastIn {
      from { opacity: 0; transform: translateY(8px) scale(.98); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    @keyframes toastOut {
      from { opacity: 1; transform: translateY(0) scale(1); }
      to { opacity: 0; transform: translateY(8px) scale(.98); }
    }

    .toast-icon {
      width: 28px;
      height: 28px;
      border-radius: 10px;
      display: grid;
      place-items: center;
      background: rgba(255,255,255,.075);
      font-size: 15px;
    }

    .toast.success .toast-icon {
      background: rgba(34,197,94,.14);
      color: #22c55e;
    }

    .toast.error .toast-icon {
      background: rgba(251,113,133,.16);
      color: #fb7185;
    }

    .toast.warn .toast-icon {
      background: rgba(251,191,36,.14);
      color: #fbbf24;
    }

    .toast.info .toast-icon {
      background: rgba(96,165,250,.14);
      color: #60a5fa;
    }

    .toast-title {
      font-weight: 850;
      font-size: 14px;
      margin-bottom: 3px;
    }

    .toast-body {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .toast-close {
      border: 0;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      font-size: 18px;
      line-height: 1;
      padding: 0 2px;
    }

    .toast-close:hover {
      color: white;
    }
    /* TITAN_TOASTS_END */
'''

if "TITAN_TOASTS_START" not in text:
    text = text.replace("</style>", toast_css + "\n  </style>", 1)

# ------------------------------------------------------------
# 3. Toast JS
# ------------------------------------------------------------
toast_js = r'''
// TITAN_TOASTS_JS_START
function titanToast(title, body = "", type = "info", timeout = 4200) {
  const host = document.getElementById("toastHost");
  if (!host) return;

  const toast = document.createElement("div");
  toast.className = "toast " + type;

  const icon = document.createElement("div");
  icon.className = "toast-icon";
  icon.textContent =
    type === "success" ? "✓" :
    type === "error" ? "!" :
    type === "warn" ? "⚠" :
    "i";

  const content = document.createElement("div");

  const titleEl = document.createElement("div");
  titleEl.className = "toast-title";
  titleEl.textContent = title || "Titan";

  const bodyEl = document.createElement("div");
  bodyEl.className = "toast-body";
  bodyEl.textContent = String(body || "");

  const close = document.createElement("button");
  close.className = "toast-close";
  close.textContent = "×";
  close.onclick = () => removeToast(toast);

  content.appendChild(titleEl);
  if (body) content.appendChild(bodyEl);

  toast.appendChild(icon);
  toast.appendChild(content);
  toast.appendChild(close);

  host.appendChild(toast);

  if (timeout) {
    setTimeout(() => removeToast(toast), timeout);
  }
}

function removeToast(toast) {
  if (!toast || toast.classList.contains("leaving")) return;
  toast.classList.add("leaving");
  setTimeout(() => toast.remove(), 180);
}

function summarizeTitanResponse(url, data) {
  if (!data) return null;

  if (data.error) {
    return {
      type: "error",
      title: "Titan error",
      body: typeof data.error === "string" ? data.error.slice(0, 240) : JSON.stringify(data.error).slice(0, 240)
    };
  }

  if (url.includes("/api/task")) {
    return { type: "success", title: "Job started", body: data.job_id || "Background job queued." };
  }

  if (url.includes("/api/file/save")) {
    return { type: "success", title: "File saved", body: data.path || data.result || "Saved." };
  }

  if (url.includes("/api/folder/create")) {
    return { type: "success", title: "Folder created", body: data.path || data.result || "Created." };
  }

  if (url.includes("/api/product/create")) {
    return { type: "success", title: "Product created", body: data.result || "Created." };
  }

  if (url.includes("/api/product/start")) {
    return { type: "success", title: "Product started", body: data.url || data.name || "Started." };
  }

  if (url.includes("/api/product/stop")) {
    return { type: "warn", title: "Product stopped", body: data.name || data.result || "Stopped." };
  }

  if (url.includes("/api/skills/create")) {
    return { type: "success", title: "Skill created", body: data.result || "Created." };
  }

  if (url.includes("/api/memory/save")) {
    return { type: "success", title: "Memory saved", body: data.result || "Saved." };
  }

  if (url.includes("/api/rag/index")) {
    return { type: "success", title: "RAG indexed", body: data.result || "Index complete." };
  }

  if (url.includes("/api/models/profile")) {
    return { type: "success", title: "Model profile changed", body: data.profile || data.model || "Updated." };
  }

  if (url.includes("/api/mode")) {
    return { type: "success", title: "Permission mode updated", body: data.result || "Updated." };
  }

  if (url.includes("/api/run")) {
    return { type: "info", title: "Command finished", body: "Check output panel." };
  }

  if (url.includes("/api/snapshot")) {
    return { type: "success", title: "Snapshot saved", body: data.path || "Snapshot complete." };
  }

  return null;
}

/* Wrap jsonFetch so existing dashboard actions get toast feedback automatically. */
setTimeout(() => {
  if (typeof jsonFetch !== "function" || window.__titanToastWrapped) return;

  const originalJsonFetch = jsonFetch;
  window.__titanToastWrapped = true;

  jsonFetch = async function(url, options = {}) {
    try {
      const data = await originalJsonFetch(url, options);
      const method = String(options.method || "GET").toUpperCase();

      if (method !== "GET") {
        const summary = summarizeTitanResponse(String(url), data);
        if (summary) titanToast(summary.title, summary.body, summary.type);
      }

      if (data && data.error) {
        const summary = summarizeTitanResponse(String(url), data);
        if (summary) titanToast(summary.title, summary.body, summary.type, 6500);
      }

      return data;
    } catch (err) {
      titanToast("Network error", String(err).slice(0, 260), "error", 7000);
      throw err;
    }
  };
}, 80);

/* Toast on command palette actions */
setTimeout(() => {
  if (typeof runPaletteCommand !== "function" || window.__titanPaletteToastWrapped) return;

  const originalRunPaletteCommand = runPaletteCommand;
  window.__titanPaletteToastWrapped = true;

  runPaletteCommand = function(index = paletteIndex) {
    const cmd = paletteFiltered && paletteFiltered[index];
    originalRunPaletteCommand(index);
    if (cmd) titanToast("Command palette", cmd.title, "info", 2200);
  };
}, 120);

/* Startup hello */
window.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => titanToast("Titan dashboard ready", "Command Palette: Cmd+K / Ctrl+K", "success", 3200), 650);
});
// TITAN_TOASTS_JS_END
'''

if "TITAN_TOASTS_JS_START" not in text:
    text = text.replace("</script>", toast_js + "\n</script>", 1)

path.write_text(text, encoding="utf-8")
print("Patched dashboard toast notifications.")
