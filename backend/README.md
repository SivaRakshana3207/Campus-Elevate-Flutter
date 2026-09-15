# AccessPathAI — Full-Stack Python Version

Same UI, same functionality as the original static site — now served by a
real Python (Flask) backend instead of raw HTML files.

## What changed vs. the original repo

- **Backend added:** Flask (`app.py`) serves all 4 pages and exposes real
  API endpoints:
  - `POST /api/translate` — server-side proxy for destination translation
    (previously called directly from the browser).
  - `POST /api/sos` — logs every Emergency SOS press (page, GPS lat/lng,
    message, timestamp) into a local SQLite database (`accesspath.db`,
    created automatically on first run).
  - `GET /api/sos/recent` — returns the last 50 SOS events as JSON, useful
    for building an admin/monitoring view later.
- **Frontend:** untouched UI/UX. Same HTML structure, same CSS, same
  navigation, same voice assistant / GPS / camera / shuttle simulation —
  all client-side browser features (Geolocation, Web Speech API,
  TensorFlow.js object detection) still run exactly as before, in the browser.
- Page files are served at the exact same paths the JS already expects
  (`/`, `/index.html`, `/shuttle.html`, `/virtual.html`, `/wheelchair.html`),
  so none of the original navigation code (`window.location.href = "..."`)
  needed to change.

## Folder structure

```
AccessPathAI_FullStack/
├── app.py               # Flask backend (routes + API + SQLite)
├── requirements.txt
├── templates/
│   ├── index.html        # AI Voice Assistant / dashboard (home page)
│   ├── shuttle.html       # Campus Shuttle Live tracking
│   ├── virtual.html       # Visual AI Guidance (camera + TensorFlow.js)
│   └── wheelchair.html    # Wheelchair Access Routes
├── static/                # reserved for any future extracted CSS/JS/images
└── accesspath.db          # created automatically on first run (SQLite)
```

## How to run

1. Make sure you have **Python 3.9+** installed.
2. Open a terminal in this folder and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   python app.py
   ```
4. Open your browser at:
   ```
   http://127.0.0.1:5000
   ```

That's it — no build step, no Node.js, no external services required
beyond an internet connection (needed for the Google Fonts/Lucide/
TensorFlow.js CDN scripts and for real-time GPS/voice/translation to work).

## Notes

- Camera-based Visual AI Guidance (`virtual.html`) and voice input require
  the browser to grant camera/microphone/location permissions — this is
  standard browser behavior and works the same as it did in the static
  version.
- `accesspath.db` is created automatically the first time you run
  `python app.py`. Delete it any time to reset the SOS log.
- This is a Flask **development server**. For real deployment, run it
  behind a production WSGI server (e.g. `gunicorn app:app`) and set
  `debug=False` in `app.py`.
