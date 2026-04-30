from pathlib import Path

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

# -------------------------------------------------------------------
# Add palette button to sidebar footer / nav area
# -------------------------------------------------------------------
if "openCommandPalette()" not in text:
    text = text.replace(
        '<div class="side-footer">',
        '<button class="palette-button" onclick="openCommandPalette()">⌘K Command Palette</button>\n\n      <div class="side-footer">',
        1
    )

# -------------------------------------------------------------------
# Add palette HTML before closing body
# -------------------------------------------------------------------
palette_html = r'''
  <!-- TITAN_COMMAND_PALETTE_HTML_START -->
  <div class="palette-backdrop" id="paletteBackdrop" onclick="closeCommandPalette(event)">
    <div class="palette" onclick="event.stopPropagation()">
      <div class="palette-top">
        <span class="palette-icon">⌘K</span>
        <input id="paletteInput" placeholder="Search commands..." autocomplete="off">
      </div>
      <div class="palette-results" id="paletteResults"></div>
      <div class="palette-help">
        Enter to run · Esc to close · ↑↓ to move
      </div>
    </div>
  </div>
  <!-- TITAN_COMMAND_PALETTE_HTML_END -->
'''

if "TITAN_COMMAND_PALETTE_HTML_START" not in text:
    text = text.replace("</body>", palette_html + "\n</body>", 1)

# -------------------------------------------------------------------
# Add CSS
# -------------------------------------------------------------------
css = r'''
    /* TITAN_COMMAND_PALETTE_START */
    .palette-button {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.055);
      color: white;
      border-radius: 16px;
      padding: 12px 13px;
      cursor: pointer;
      text-align: left;
      font-size: 14px;
      transition: background .14s ease, transform .14s ease;
    }

    .palette-button:hover {
      background: rgba(255,255,255,.085);
      transform: translateY(-1px);
    }

    .palette-backdrop {
      position: fixed;
      inset: 0;
      z-index: 9999;
      display: none;
      align-items: flex-start;
      justify-content: center;
      padding-top: 12vh;
      background: rgba(0,0,0,.42);
      backdrop-filter: blur(10px);
    }

    .palette-backdrop.active {
      display: flex;
    }

    .palette {
      width: min(720px, calc(100vw - 28px));
      border: 1px solid rgba(255,255,255,.12);
      background:
        radial-gradient(circle at 20% -20%, rgba(232,171,67,.16), transparent 35%),
        rgba(18,19,22,.96);
      border-radius: 24px;
      box-shadow: 0 28px 80px rgba(0,0,0,.42);
      overflow: hidden;
      animation: paletteIn .14s ease both;
    }

    @keyframes paletteIn {
      from { opacity: 0; transform: translateY(8px) scale(.98); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    .palette-top {
      height: 64px;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 14px;
      border-bottom: 1px solid var(--line);
    }

    .palette-icon {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.07);
      color: #f8fafc;
      border-radius: 12px;
      padding: 8px 10px;
      font-size: 13px;
      font-weight: 800;
    }

    #paletteInput {
      flex: 1;
      border: 0;
      outline: 0;
      background: transparent;
      color: white;
      font-size: 18px;
    }

    .palette-results {
      max-height: 420px;
      overflow-y: auto;
      padding: 10px;
      display: grid;
      gap: 6px;
    }

    .palette-item {
      border: 1px solid transparent;
      background: transparent;
      color: #e5e7eb;
      border-radius: 16px;
      padding: 12px;
      display: grid;
      gap: 4px;
      cursor: pointer;
      transition: background .12s ease, border-color .12s ease;
    }

    .palette-item:hover,
    .palette-item.active {
      background: rgba(255,255,255,.075);
      border-color: rgba(232,171,67,.26);
    }

    .palette-item-title {
      font-weight: 850;
      font-size: 14px;
    }

    .palette-item-desc {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }

    .palette-help {
      padding: 10px 14px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
    }
    /* TITAN_COMMAND_PALETTE_END */
'''

if "TITAN_COMMAND_PALETTE_START" not in text:
    text = text.replace("</style>", css + "\n  </style>", 1)

# -------------------------------------------------------------------
# Add JS
# -------------------------------------------------------------------
js = r'''
// TITAN_COMMAND_PALETTE_JS_START
let paletteIndex = 0;
let paletteFiltered = [];

const paletteCommands = [
  {
    title: "Open Chat",
    desc: "Go to Titan chat.",
    keywords: "chat home",
    run: () => clickNavByView("chat")
  },
  {
    title: "Open Jobs",
    desc: "Go to jobs and live trace viewer.",
    keywords: "jobs trace logs result",
    run: () => { clickNavByView("jobs"); loadJobs(); }
  },
  {
    title: "Open Files",
    desc: "Browse and edit project files.",
    keywords: "files browser editor workspace",
    run: () => { clickNavByView("files"); loadFiles(); }
  },
  {
    title: "Open Products",
    desc: "Create, start, stop, and open products.",
    keywords: "products launcher apps",
    run: () => { clickNavByView("products"); loadProducts(); }
  },
  {
    title: "Open Search / Diff",
    desc: "Search files and inspect diffs.",
    keywords: "search diff changed snapshot",
    run: () => clickNavByView("search")
  },
  {
    title: "Open Skills",
    desc: "List and create Titan skills.",
    keywords: "skills workflows",
    run: () => { clickNavByView("skills"); loadSkills(); }
  },
  {
    title: "Open Memory",
    desc: "View and search saved memories.",
    keywords: "memory remember recall",
    run: () => { clickNavByView("memory"); loadMemory(); }
  },
  {
    title: "Open RAG",
    desc: "Index and search local docs.",
    keywords: "rag docs knowledge index",
    run: () => { clickNavByView("rag"); loadRag(); }
  },
  {
    title: "Open Models",
    desc: "View or switch model profiles.",
    keywords: "models ollama fast smart heavy max",
    run: () => { clickNavByView("models"); loadModels(); }
  },
  {
    title: "Open Permissions",
    desc: "View mode and run approved shell commands.",
    keywords: "permissions mode safe power agentic run",
    run: () => { clickNavByView("permissions"); loadMode(); }
  },
  {
    title: "Refresh Jobs",
    desc: "Reload jobs and current trace.",
    keywords: "refresh jobs trace",
    run: () => loadJobs()
  },
  {
    title: "Refresh Skills",
    desc: "Reload skills list.",
    keywords: "refresh skills",
    run: () => loadSkills()
  },
  {
    title: "Refresh Memory",
    desc: "Reload memory list.",
    keywords: "refresh memory",
    run: () => loadMemory()
  },
  {
    title: "Refresh RAG",
    desc: "Reload RAG status.",
    keywords: "refresh rag",
    run: () => loadRag()
  },
  {
    title: "Refresh Models",
    desc: "Reload model config.",
    keywords: "refresh models",
    run: () => loadModels()
  },
  {
    title: "Set Fast Model",
    desc: "Switch Titan to fast profile.",
    keywords: "model fast speed",
    run: () => setProfile("fast")
  },
  {
    title: "Set Coder Model",
    desc: "Switch Titan to coder profile.",
    keywords: "model coder code",
    run: () => setProfile("coder")
  },
  {
    title: "Set Smart Model",
    desc: "Switch Titan to smart profile.",
    keywords: "model smart",
    run: () => setProfile("smart")
  },
  {
    title: "Set Heavy Model",
    desc: "Switch Titan to heavy profile.",
    keywords: "model heavy planning",
    run: () => setProfile("heavy")
  },
  {
    title: "Set Agentic Mode",
    desc: "Switch permissions to agentic mode.",
    keywords: "agentic permission mode",
    run: () => setMode("agentic")
  },
  {
    title: "Set Power Mode",
    desc: "Switch permissions to power mode.",
    keywords: "power permission mode",
    run: () => setMode("power")
  },
  {
    title: "Set Safe Mode",
    desc: "Switch permissions to safe mode.",
    keywords: "safe permission mode",
    run: () => setMode("safe")
  }
];

function clickNavByView(view) {
  const button = Array.from(document.querySelectorAll("nav button")).find(btn => {
    return btn.getAttribute("onclick") && btn.getAttribute("onclick").includes(`showView('${view}'`);
  });

  if (button) {
    button.click();
  } else {
    showView(view, null);
  }
}

function openCommandPalette() {
  const backdrop = document.getElementById("paletteBackdrop");
  const input = document.getElementById("paletteInput");

  if (!backdrop || !input) return;

  backdrop.classList.add("active");
  input.value = "";
  paletteIndex = 0;
  renderPalette("");
  setTimeout(() => input.focus(), 20);
}

function closeCommandPalette(event = null) {
  if (event && event.target && event.target.id !== "paletteBackdrop") return;
  const backdrop = document.getElementById("paletteBackdrop");
  if (backdrop) backdrop.classList.remove("active");
}

function scoreCommand(command, query) {
  if (!query) return 1;

  const haystack = `${command.title} ${command.desc} ${command.keywords}`.toLowerCase();
  const parts = query.toLowerCase().split(/\s+/).filter(Boolean);

  let score = 0;
  for (const part of parts) {
    if (command.title.toLowerCase().includes(part)) score += 5;
    if (haystack.includes(part)) score += 2;
  }
  return score;
}

function renderPalette(query) {
  const results = document.getElementById("paletteResults");
  if (!results) return;

  paletteFiltered = paletteCommands
    .map(cmd => ({cmd, score: scoreCommand(cmd, query)}))
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .map(item => item.cmd);

  results.innerHTML = "";

  if (!paletteFiltered.length) {
    results.textContent = "No matching commands.";
    return;
  }

  paletteFiltered.slice(0, 12).forEach((cmd, index) => {
    const item = document.createElement("div");
    item.className = "palette-item" + (index === paletteIndex ? " active" : "");
    item.onclick = () => runPaletteCommand(index);

    const title = document.createElement("div");
    title.className = "palette-item-title";
    title.textContent = cmd.title;

    const desc = document.createElement("div");
    desc.className = "palette-item-desc";
    desc.textContent = cmd.desc;

    item.appendChild(title);
    item.appendChild(desc);
    results.appendChild(item);
  });
}

function runPaletteCommand(index = paletteIndex) {
  const cmd = paletteFiltered[index];
  if (!cmd) return;

  closeCommandPalette();
  try {
    cmd.run();
  } catch (err) {
    console.error(err);
  }
}

window.addEventListener("keydown", event => {
  const isPaletteShortcut = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";

  if (isPaletteShortcut) {
    event.preventDefault();
    openCommandPalette();
    return;
  }

  const backdrop = document.getElementById("paletteBackdrop");
  const open = backdrop && backdrop.classList.contains("active");

  if (!open) return;

  if (event.key === "Escape") {
    event.preventDefault();
    closeCommandPalette();
    return;
  }

  if (event.key === "ArrowDown") {
    event.preventDefault();
    paletteIndex = Math.min(paletteIndex + 1, Math.min(paletteFiltered.length - 1, 11));
    renderPalette(document.getElementById("paletteInput").value);
    return;
  }

  if (event.key === "ArrowUp") {
    event.preventDefault();
    paletteIndex = Math.max(paletteIndex - 1, 0);
    renderPalette(document.getElementById("paletteInput").value);
    return;
  }

  if (event.key === "Enter") {
    event.preventDefault();
    runPaletteCommand();
  }
});

window.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("paletteInput");
  if (!input) return;

  input.addEventListener("input", () => {
    paletteIndex = 0;
    renderPalette(input.value);
  });
});
// TITAN_COMMAND_PALETTE_JS_END
'''

if "TITAN_COMMAND_PALETTE_JS_START" not in text:
    text = text.replace("</script>", js + "\n</script>", 1)

path.write_text(text, encoding="utf-8")
print("Patched dashboard command palette.")
