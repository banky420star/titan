from pathlib import Path

path = Path("control_panel_titan_ui.py")
if not path.exists():
    path = Path("control_panel.py")

if not path.exists():
    raise SystemExit("Could not find control_panel_titan_ui.py or control_panel.py")

text = path.read_text()

# Give app shell an ID.
text = text.replace(
    '<div class="app">',
    '<div class="app" id="appShell">',
    1
)

# Make sidebar collapse button functional.
text = text.replace(
    '<button class="collapse-btn">≪</button>',
    '<button class="collapse-btn" id="sidebarToggle" onclick="toggleSidebar()" title="Collapse navigation">≪</button>'
)

# Insert chat panel after prompt form, before feature cards.
insert_after = '</form>\n\n        <section class="card-grid">'
chat_panel = r'''</form>

        <section class="chat-panel" id="chatPanel">
          <div class="chat-topbar">
            <div>
              <div class="chat-title">Titan Chat</div>
              <div class="chat-subtitle">Ask, build, inspect, launch background jobs.</div>
            </div>
            <div class="chat-actions">
              <button class="tiny-btn" onclick="runQuick('Inspect the workspace and summarize what Titan can currently do. Do not edit files.')">Inspect</button>
              <button class="tiny-btn" onclick="clearChat()">Clear</button>
            </div>
          </div>

          <div class="chat-messages" id="chatMessages">
            <div class="message-row assistant">
              <div class="message-avatar">T</div>
              <div class="message-bubble">
                <div class="message-name">Titan</div>
                <div>Ready. Tell me what to build, inspect, fix, or launch in the background.</div>
              </div>
            </div>
          </div>
        </section>

        <section class="card-grid">'''

if insert_after in text and 'id="chatPanel"' not in text:
    text = text.replace(insert_after, chat_panel, 1)

# Inject CSS before </style>.
css_marker = "</style>"
if css_marker not in text:
    raise SystemExit("Could not find </style>")

css = r'''
    /* CHAT-FIRST MICRO INTERACTION PATCH */
    html,
    body {
      height: 100%;
      overflow: hidden;
    }

    .app {
      height: 100vh;
      overflow: hidden;
      transition: grid-template-columns 220ms ease;
    }

    .sidebar {
      height: 100vh !important;
      overflow-y: auto !important;
      overflow-x: hidden !important;
      scrollbar-width: thin;
      scrollbar-color: rgba(255,255,255,0.18) transparent;
      transition:
        width 220ms ease,
        padding 220ms ease,
        transform 220ms ease,
        opacity 220ms ease;
    }

    .sidebar::-webkit-scrollbar,
    .main::-webkit-scrollbar,
    .chat-messages::-webkit-scrollbar {
      width: 9px;
    }

    .sidebar::-webkit-scrollbar-thumb,
    .main::-webkit-scrollbar-thumb,
    .chat-messages::-webkit-scrollbar-thumb {
      background: rgba(255,255,255,0.16);
      border-radius: 999px;
    }

    .main {
      height: 100vh;
      overflow-y: auto;
      scroll-behavior: smooth;
    }

    .collapse-btn {
      cursor: pointer;
      transition:
        transform 160ms ease,
        background 160ms ease,
        border-color 160ms ease;
    }

    .collapse-btn:hover {
      transform: translateY(-1px);
      background: rgba(255,255,255,0.08);
      border-color: rgba(255,255,255,0.16);
    }

    .app.sidebar-collapsed {
      grid-template-columns: 86px 1fr !important;
    }

    .app.sidebar-collapsed .sidebar {
      padding-left: 14px !important;
      padding-right: 14px !important;
    }

    .app.sidebar-collapsed .brand-title,
    .app.sidebar-collapsed .nav-link:not(.active) span + *,
    .app.sidebar-collapsed .nav-link,
    .app.sidebar-collapsed .section-label,
    .app.sidebar-collapsed .user-meta,
    .app.sidebar-collapsed .user-card > div:last-child {
      white-space: nowrap;
    }

    .app.sidebar-collapsed .brand-title,
    .app.sidebar-collapsed .nav-link {
      font-size: 0;
    }

    .app.sidebar-collapsed .nav-icon {
      font-size: 21px;
      margin: 0 auto;
    }

    .app.sidebar-collapsed .nav-link {
      justify-content: center;
      padding-left: 10px;
      padding-right: 10px;
    }

    .app.sidebar-collapsed .section-label {
      opacity: 0;
      height: 0;
      overflow: hidden;
      margin: 0;
      padding: 0;
    }

    .app.sidebar-collapsed .user-card {
      justify-content: center;
      padding: 10px;
    }

    .app.sidebar-collapsed .user-meta,
    .app.sidebar-collapsed .user-card > div:last-child {
      display: none;
    }

    .app.sidebar-collapsed .collapse-btn {
      transform: rotate(180deg);
    }

    .nav-link {
      user-select: none;
      transform: translateZ(0);
    }

    .nav-link:active,
    .quick-card:active,
    .details:active,
    .tiny-btn:active,
    .send:active {
      transform: scale(0.985);
    }

    .chat-panel {
      border: 1px solid rgba(255,255,255,0.075);
      border-radius: 24px;
      background: rgba(255,255,255,0.04);
      margin: 0 0 22px;
      overflow: hidden;
    }

    .chat-topbar {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      padding: 18px 20px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
      background: rgba(255,255,255,0.025);
    }

    .chat-title {
      font-weight: 760;
      font-size: 18px;
      letter-spacing: -0.02em;
    }

    .chat-subtitle {
      color: #a9abb3;
      font-size: 14px;
      margin-top: 3px;
    }

    .chat-actions {
      display: flex;
      gap: 8px;
    }

    .tiny-btn {
      border: 1px solid rgba(255,255,255,0.09);
      background: rgba(255,255,255,0.055);
      color: #f4f4f5;
      border-radius: 999px;
      padding: 9px 13px;
      cursor: pointer;
      transition:
        transform 140ms ease,
        background 140ms ease,
        border-color 140ms ease;
    }

    .tiny-btn:hover {
      background: rgba(255,255,255,0.085);
      border-color: rgba(255,255,255,0.15);
    }

    .chat-messages {
      max-height: 360px;
      overflow-y: auto;
      padding: 18px;
      display: grid;
      gap: 14px;
      scroll-behavior: smooth;
    }

    .message-row {
      display: flex;
      gap: 12px;
      align-items: flex-start;
      animation: messageIn 180ms ease both;
    }

    .message-row.user {
      justify-content: flex-end;
    }

    .message-row.user .message-avatar {
      order: 2;
      background: linear-gradient(135deg, #4f46e5, #1d4ed8);
    }

    .message-avatar {
      width: 34px;
      height: 34px;
      border-radius: 12px;
      display: grid;
      place-items: center;
      flex: 0 0 auto;
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,0.46), transparent 30%),
        linear-gradient(145deg, #ffe66d, #fb923c 55%, #fb7185);
      color: white;
      font-weight: 850;
      box-shadow: 0 10px 20px rgba(0,0,0,0.22);
    }

    .message-bubble {
      max-width: min(720px, 80%);
      border-radius: 20px;
      padding: 13px 15px;
      color: #e5e7eb;
      background: rgba(255,255,255,0.055);
      border: 1px solid rgba(255,255,255,0.075);
      line-height: 1.48;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .message-row.user .message-bubble {
      background: rgba(79, 70, 229, 0.18);
      border-color: rgba(124, 140, 255, 0.24);
      color: white;
    }

    .message-name {
      color: #f8fafc;
      font-size: 12px;
      opacity: 0.68;
      margin-bottom: 4px;
      font-weight: 700;
    }

    .typing-dots {
      display: inline-flex;
      gap: 4px;
      align-items: center;
    }

    .typing-dots span {
      width: 6px;
      height: 6px;
      border-radius: 999px;
      background: #d4d4d8;
      animation: typingDot 900ms ease-in-out infinite;
      opacity: 0.4;
    }

    .typing-dots span:nth-child(2) {
      animation-delay: 120ms;
    }

    .typing-dots span:nth-child(3) {
      animation-delay: 240ms;
    }

    @keyframes typingDot {
      0%, 100% {
        transform: translateY(0);
        opacity: 0.35;
      }
      50% {
        transform: translateY(-4px);
        opacity: 1;
      }
    }

    @keyframes messageIn {
      from {
        opacity: 0;
        transform: translateY(5px) scale(0.99);
      }
      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }

    .prompt {
      position: sticky;
      top: 18px;
      z-index: 20;
      backdrop-filter: blur(18px);
      transition:
        border-color 160ms ease,
        background 160ms ease,
        transform 160ms ease;
    }

    .prompt:focus-within {
      border-color: rgba(251, 146, 60, 0.28) !important;
      background: rgba(255,255,255,0.075) !important;
      transform: translateY(-1px);
    }

    .send {
      transition:
        transform 140ms ease,
        background 140ms ease,
        box-shadow 140ms ease;
    }

    .send:hover {
      transform: translateY(-1px);
      background: rgba(255,255,255,0.16) !important;
    }

    .quick-card {
      position: relative;
      overflow: hidden;
    }

    .quick-card::before {
      content: "";
      position: absolute;
      inset: 0;
      background: radial-gradient(circle at var(--mx, 50%) var(--my, 50%), rgba(255,255,255,0.10), transparent 34%);
      opacity: 0;
      transition: opacity 180ms ease;
      pointer-events: none;
    }

    .quick-card:hover::before {
      opacity: 1;
    }

    .nav-link::after {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: linear-gradient(90deg, rgba(255,255,255,0.08), transparent);
      opacity: 0;
      transition: opacity 160ms ease;
      pointer-events: none;
    }

    .nav-link:hover::after {
      opacity: 1;
    }

    .result-drawer {
      display: none !important;
    }

    @media (max-width: 880px) {
      html,
      body {
        overflow: auto;
      }

      .app {
        display: block;
        height: auto;
      }

      .sidebar {
        height: auto !important;
        position: relative !important;
      }

      .main {
        height: auto !important;
        overflow: visible !important;
      }

      .prompt {
        position: static;
      }

      .chat-messages {
        max-height: 420px;
      }

      .message-bubble {
        max-width: 86%;
      }
    }
'''

if "/* CHAT-FIRST MICRO INTERACTION PATCH */" not in text:
    text = text.replace(css_marker, css + "\n  " + css_marker)

# Inject JS before </script>.
script_marker = "</script>"
if script_marker not in text:
    raise SystemExit("Could not find </script>")

js = r'''
    // CHAT-FIRST MICRO INTERACTION PATCH
    function toggleSidebar() {
      const shell = document.getElementById("appShell");
      const btn = document.getElementById("sidebarToggle");
      if (!shell) return;

      shell.classList.toggle("sidebar-collapsed");

      const collapsed = shell.classList.contains("sidebar-collapsed");
      localStorage.setItem("titanSidebarCollapsed", collapsed ? "1" : "0");

      if (btn) {
        btn.textContent = collapsed ? "≫" : "≪";
        btn.title = collapsed ? "Expand navigation" : "Collapse navigation";
      }
    }

    function restoreSidebarState() {
      const shell = document.getElementById("appShell");
      const btn = document.getElementById("sidebarToggle");
      if (!shell) return;

      const collapsed = localStorage.getItem("titanSidebarCollapsed") === "1";
      shell.classList.toggle("sidebar-collapsed", collapsed);

      if (btn) {
        btn.textContent = collapsed ? "≫" : "≪";
        btn.title = collapsed ? "Expand navigation" : "Collapse navigation";
      }
    }

    function getChatMessages() {
      return document.getElementById("chatMessages");
    }

    function appendMessage(role, content, name) {
      const chat = getChatMessages();
      if (!chat) return null;

      const row = document.createElement("div");
      row.className = "message-row " + (role === "user" ? "user" : "assistant");

      const avatar = document.createElement("div");
      avatar.className = "message-avatar";
      avatar.textContent = role === "user" ? "Y" : "T";

      const bubble = document.createElement("div");
      bubble.className = "message-bubble";

      const label = document.createElement("div");
      label.className = "message-name";
      label.textContent = name || (role === "user" ? "You" : "Titan");

      const body = document.createElement("div");
      body.textContent = typeof content === "string" ? content : JSON.stringify(content, null, 2);

      bubble.appendChild(label);
      bubble.appendChild(body);
      row.appendChild(avatar);
      row.appendChild(bubble);
      chat.appendChild(row);

      chat.scrollTop = chat.scrollHeight;
      return row;
    }

    function appendTyping() {
      const chat = getChatMessages();
      if (!chat) return null;

      const row = document.createElement("div");
      row.className = "message-row assistant";
      row.id = "typingRow";

      const avatar = document.createElement("div");
      avatar.className = "message-avatar";
      avatar.textContent = "T";

      const bubble = document.createElement("div");
      bubble.className = "message-bubble";
      bubble.innerHTML = '<div class="message-name">Titan</div><div class="typing-dots"><span></span><span></span><span></span></div>';

      row.appendChild(avatar);
      row.appendChild(bubble);
      chat.appendChild(row);
      chat.scrollTop = chat.scrollHeight;

      return row;
    }

    function removeTyping() {
      const row = document.getElementById("typingRow");
      if (row) row.remove();
    }

    function clearChat() {
      const chat = getChatMessages();
      if (!chat) return;
      chat.innerHTML = "";
      appendMessage("assistant", "Clean slate. What are we building?", "Titan");
      setTitanState("happy", "✓");
      resetTitanState(900);
    }

    function stringifyResult(content) {
      if (typeof content === "string") return content;
      if (content && typeof content === "object") {
        if (content.result) return String(content.result);
        if (content.error) return "Error: " + JSON.stringify(content, null, 2);
        return JSON.stringify(content, null, 2);
      }
      return String(content);
    }

    const oldShowResult = window.showResult;
    window.showResult = function(content) {
      removeTyping();
      appendMessage("assistant", stringifyResult(content), "Titan");

      const drawer = document.getElementById("resultDrawer");
      const output = document.getElementById("resultOutput");
      if (drawer && output) {
        output.textContent = stringifyResult(content);
      }
    };

    window.postJSON = async function(url, data) {
      const taskText = data && data.task ? data.task : "Working...";
      appendTyping();

      try {
        setTitanState("working", "⚙");

        const response = await fetch(url, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(data || {})
        });

        const json = await response.json();

        if (json.error) {
          setTitanState("error", "!");
          showResult(json);
          resetTitanState(2400);
          return;
        }

        setTitanState("happy", "✓");
        showResult(json);
        resetTitanState(1400);

      } catch (err) {
        setTitanState("error", "!");
        showResult(String(err));
        resetTitanState(2400);
      }
    };

    window.getJSON = async function(url) {
      appendTyping();

      try {
        setTitanState("searching", "🔎");
        const response = await fetch(url);
        const json = await response.json();

        if (json.error) {
          setTitanState("error", "!");
          showResult(json);
          resetTitanState(2200);
          return;
        }

        setTitanState("happy", "✓");
        showResult(json);
        resetTitanState(1200);

      } catch (err) {
        setTitanState("error", "!");
        showResult(String(err));
        resetTitanState(2200);
      }
    };

    window.submitPrompt = function(event) {
      event.preventDefault();
      const task = promptInput.value.trim();
      if (!task) return;

      appendMessage("user", task, "You");

      const pair = taskToState(task);
      setTitanState(pair[0], pair[1]);

      promptInput.value = "";
      postJSON("/api/task", { task });
    };

    window.runQuick = function(task) {
      promptInput.value = "";
      appendMessage("user", task, "You");

      const pair = taskToState(task);
      setTitanState(pair[0], pair[1]);

      postJSON("/api/task", { task });
    };

    document.querySelectorAll(".quick-card").forEach((card) => {
      card.addEventListener("mousemove", (event) => {
        const rect = card.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width) * 100;
        const y = ((event.clientY - rect.top) / rect.height) * 100;
        card.style.setProperty("--mx", x + "%");
        card.style.setProperty("--my", y + "%");
      });
    });

    document.querySelectorAll("button, .nav-link, .quick-card").forEach((el) => {
      el.addEventListener("click", () => {
        el.animate(
          [
            { transform: "scale(1)" },
            { transform: "scale(0.985)" },
            { transform: "scale(1)" }
          ],
          { duration: 150, easing: "ease-out" }
        );
      });
    });

    restoreSidebarState();
'''

if "// CHAT-FIRST MICRO INTERACTION PATCH" not in text:
    text = text.replace(script_marker, js + "\n  " + script_marker)

path.write_text(text)
print(f"Patched chat UI, sidebar collapse, independent scroll, and micro interactions in {path}")
