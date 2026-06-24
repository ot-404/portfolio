# Portfolio

A small personal portfolio site built with Flask + server-rendered Jinja
templates and a static CSS/JS frontend. Independent of any other project.

## Pages
- **Home** (`/`) — hero, skills, featured projects
- **Projects** (`/projects`) — full project list
- **Contact** (`/contact`) — contact form (submissions saved to `data/messages.jsonl`)

## Run locally

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell: .venv\Scripts\Activate.ps1)
# source .venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python app.py
```

Then open http://127.0.0.1:5000

## Make it yours
All site content lives in the `PROFILE`, `SKILLS`, and `PROJECTS` variables near
the top of [`app.py`](app.py) — edit those (name, bio, email, social links,
project entries). No HTML changes needed for content updates.

## Project structure
```
portfolio/
├── app.py              # Flask app + site content
├── requirements.txt
├── templates/          # Jinja templates (base, index, projects, contact)
├── static/
│   ├── css/style.css   # Theme + layout
│   └── js/main.js      # Mobile nav
└── data/               # Contact submissions (git-ignored, created at runtime)
```

## Deploy (Render)
This repo includes a [`render.yaml`](render.yaml) blueprint and uses `gunicorn`
as the production server.

1. Push this repo to GitHub (already done: https://github.com/ot-404/portfolio).
2. In the [Render dashboard](https://dashboard.render.com/): **New → Blueprint**.
3. Connect this GitHub repo. Render reads `render.yaml`, creates a free web
   service, and generates a `SECRET_KEY` automatically.
4. Click **Apply**. First build takes a couple of minutes; you'll get a public
   `https://portfolio-xxxx.onrender.com` URL.

Render auto-redeploys on every push to `main`. Note: free instances sleep after
~15 min idle, so the first request after a nap takes ~30-50s to wake.

## Notes
- Set a real `SECRET_KEY` env var in production (used to sign the session cookie
  for flash messages). On Render this is generated for you by `render.yaml`.
- Contact-form submissions are written to `data/messages.jsonl` on local disk.
  On Render's free tier the filesystem is ephemeral, so messages are lost on
  redeploy/restart — wire up email (SMTP) or a database for durable storage.
- The contact form stores messages locally. To email them instead, wire up SMTP
  in the `_save_message` / `contact` handler.
