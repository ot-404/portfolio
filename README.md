# Portfolio

A small personal portfolio site built with Flask + server-rendered Jinja
templates and a static CSS/JS frontend. Independent of any other project.

## Pages
- **Home** (`/`) — hero, skills, featured projects
- **Projects** (`/projects`) — full project list
- **Contact** (`/contact`) — contact form (submissions saved to `data/messages.jsonl`)

## Run locally

**Easiest (Windows):** double-click **`run.bat`** — it creates the virtual
environment if needed, installs dependencies, and starts the site.

**Manual:**
```bash
# 1. Create the virtual environment
python -m venv .venv

# 2. Install dependencies (use the venv's pip)
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Run with the venv's Python (avoids "No module named 'flask'")
.venv\Scripts\python.exe app.py
# macOS / Linux: .venv/bin/python app.py
```

Then open http://127.0.0.1:5000

> Tip: a plain `python app.py` uses your *system* Python, which doesn't have
> Flask installed — that's the usual "can't run" error. Use `run.bat` or the
> `.venv\Scripts\python.exe` path above.

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

## Contact form → email (SMTP)
Each submission is saved to `data/messages.jsonl` **and** emailed to your inbox
when SMTP is configured. If SMTP isn't set, the form still works and just logs
to the file. Configuration is via environment variables — see
[`.env.example`](.env.example).

It works with any SMTP provider. The default config uses **Brevo** (free tier,
300 emails/day, no Gmail 2FA needed). Mail still lands in your normal inbox.

### Get Brevo SMTP credentials (one-time)
1. Sign up at https://www.brevo.com (free, no card).
2. Verify a sender: **Senders, Domains & Dedicated IPs → Senders → Add a sender**,
   using the address you want mail to come *from* (e.g. opshokare@gmail.com), and
   click the confirmation link Brevo emails you.
3. Get SMTP creds: account menu → **SMTP & API → SMTP** tab. Note the **Login**
   and click **Generate a new SMTP key**; copy the key.

### Local
Copy `.env.example` to `.env` and set `SMTP_USER` (Brevo login),
`SMTP_PASSWORD` (SMTP key), `SMTP_FROM` (verified sender), and `CONTACT_TO`.
Run `python app.py` and submit the form — it emails `CONTACT_TO`.

### Render
On first Blueprint deploy, Render prompts for `SMTP_USER`, `SMTP_PASSWORD`,
`SMTP_FROM`, and `CONTACT_TO` (declared `sync: false`). `SMTP_HOST`/`SMTP_PORT`
are preset for Brevo. (To use Gmail instead, set `SMTP_HOST=smtp.gmail.com` and
use a Gmail App Password — requires 2-Step Verification enabled.)

## Notes
- Set a real `SECRET_KEY` env var in production (used to sign the session cookie
  for flash messages). On Render this is generated for you by `render.yaml`.
- Contact-form submissions are also written to `data/messages.jsonl` on local
  disk. On Render's free tier the filesystem is ephemeral, so that file is lost
  on redeploy/restart — which is why email delivery is the durable path.
