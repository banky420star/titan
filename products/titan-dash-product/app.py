import os
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
MESSAGES = []

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Titan Dash Product</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { margin:0; min-height:100vh; background:#111214; color:white; font-family:system-ui; }
    main { width:min(980px, calc(100vw - 36px)); margin:42px auto; }
    h1 { font-size:64px; letter-spacing:-.07em; margin:0 0 14px; }
    .panel { border:1px solid rgba(255,255,255,.1); background:rgba(255,255,255,.055); border-radius:28px; overflow:hidden; }
    .messages { min-height:420px; max-height:520px; overflow-y:auto; padding:18px; display:grid; gap:12px; }
    .bubble { border:1px solid rgba(255,255,255,.1); background:rgba(255,255,255,.06); border-radius:18px; padding:12px 14px; }
    form { display:flex; gap:10px; padding:14px; border-top:1px solid rgba(255,255,255,.1); }
    input { flex:1; border:0; outline:0; border-radius:999px; padding:0 16px; background:rgba(255,255,255,.08); color:white; font-size:16px; }
    button { border:0; border-radius:999px; padding:13px 18px; background:#e8ab43; color:#111214; font-weight:850; cursor:pointer; }
  </style>
</head>
<body>
  <main>
    <h1>Titan Dash Product</h1>
    <p>Created from Titan template: flask_dashboard</p>
    <section class="panel">
      <div class="messages" id="messages"></div>
      <form onsubmit="send(event)">
        <input id="input" placeholder="Send a message...">
        <button>Send</button>
      </form>
    </section>
  </main>
<script>
async function refresh() {
  const res = await fetch("/api/messages");
  const data = await res.json();
  const box = document.getElementById("messages");
  box.innerHTML = "";
  data.messages.forEach(m => {
    const d = document.createElement("div");
    d.className = "bubble";
    d.textContent = m;
    box.appendChild(d);
  });
  box.scrollTop = box.scrollHeight;
}
async function send(e) {
  e.preventDefault();
  const input = document.getElementById("input");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  await fetch("/api/messages", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({message})});
  refresh();
}
refresh();
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/api/messages", methods=["GET", "POST"])
def messages():
    if request.method == "POST":
        MESSAGES.append((request.json or {}).get("message", ""))
    return jsonify({"messages": MESSAGES})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5055)), debug=True)
