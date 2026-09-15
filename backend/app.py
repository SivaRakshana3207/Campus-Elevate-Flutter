"""
AccessPathAI — Full-Stack Python Version
==========================================
Flask backend serving the exact same frontend (HTML/CSS/JS, same UI)
that used to run as static files, now with real Python backend routes:

  - /api/translate   : server-side translation proxy (Google Translate)
  - /api/sos         : logs Emergency SOS events to a local SQLite database
  - /api/sos/recent  : lists recent SOS events (simple JSON, for admin/testing)

Run:
    pip install -r requirements.txt
    python app.py

Then open: http://127.0.0.1:5000
"""

import os
import sqlite3
import datetime

import requests
from flask import Flask, render_template, request, jsonify, g

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "accesspath.db")

app = Flask(__name__, template_folder="templates", static_folder="static")


# =============================================================
# DATABASE HELPERS
# =============================================================

def get_db():
    """Open (or reuse) a SQLite connection for this request."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables if they don't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sos_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page TEXT,
            lat REAL,
            lng REAL,
            message TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# =============================================================
# PAGE ROUTES  (same filenames the frontend JS already links to,
# so none of the original navigation code has to change)
# =============================================================

@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html")


@app.route("/shuttle.html")
def shuttle():
    return render_template("shuttle.html")


@app.route("/virtual.html")
def virtual():
    return render_template("virtual.html")


@app.route("/wheelchair.html")
def wheelchair():
    return render_template("wheelchair.html")


# =============================================================
# API — TRANSLATION PROXY
# =============================================================

@app.route("/api/translate", methods=["POST"])
def api_translate():
    """
    Server-side proxy to Google's translation endpoint.
    Keeps the API call on the Python backend instead of the browser
    (more reliable, no client-side CORS dependency).

    Body: {"text": "...", "target": "en"}
    Returns: {"translated": "...", "original": "..."}
    """
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    target = str(payload.get("target", "en")).strip() or "en"

    if not text:
        return jsonify({"error": "No text provided", "translated": ""}), 400

    try:
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "auto",
                "tl": target,
                "dt": "t",
                "q": text,
            },
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()

        translated = ""
        if isinstance(data, list) and data and isinstance(data[0], list):
            translated = " ".join(
                part[0] for part in data[0] if isinstance(part, list) and part
            ).strip()

        if not translated:
            return jsonify({"error": "Empty translation", "translated": ""}), 502

        return jsonify({"translated": translated, "original": text})

    except requests.RequestException as exc:
        return jsonify({"error": str(exc), "translated": ""}), 502


# =============================================================
# API — EMERGENCY SOS LOGGING
# =============================================================

@app.route("/api/sos", methods=["POST"])
def api_sos():
    """
    Logs an Emergency SOS event triggered from any page.
    Body: {"page": "index", "lat": 12.9, "lng": 80.2, "message": "..."}
    """
    payload = request.get_json(silent=True) or {}

    page = str(payload.get("page", "unknown"))
    lat = payload.get("lat")
    lng = payload.get("lng")
    message = str(payload.get("message", ""))
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    db = get_db()
    db.execute(
        "INSERT INTO sos_events (page, lat, lng, message, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (page, lat, lng, message, created_at),
    )
    db.commit()

    print(f"[SOS] page={page} lat={lat} lng={lng} at={created_at} :: {message}")

    return jsonify({"status": "logged", "created_at": created_at})


@app.route("/api/sos/recent", methods=["GET"])
def api_sos_recent():
    """Returns the most recent SOS events (handy for an admin dashboard)."""
    db = get_db()
    rows = db.execute(
        "SELECT id, page, lat, lng, message, created_at "
        "FROM sos_events ORDER BY id DESC LIMIT 50"
    ).fetchall()

    return jsonify([dict(row) for row in rows])


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
