import os
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)
ITEMS = []

@app.route("/")
def home():
    return jsonify({"service": "titan-api", "title": "Titan Api", "description": "Created from Titan template: api_service", "endpoints": ["/health", "/api/items"]})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat(timespec="seconds")})

@app.route("/api/items", methods=["GET", "POST"])
def items():
    if request.method == "POST":
        data = request.json or {}
        item = {"id": len(ITEMS) + 1, "name": data.get("name", "Untitled"), "created_at": datetime.now().isoformat(timespec="seconds")}
        ITEMS.append(item)
        return jsonify(item), 201
    return jsonify({"items": ITEMS})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5055)), debug=True)
