"""
Personal portfolio site.

A small server-rendered Flask app: Jinja templates + static CSS/JS.
Run with `python app.py` (dev) or via a WSGI server in production.
"""

from __future__ import annotations

import json
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

# Load a local .env file if present (dev convenience). On a host like Render,
# set these variables in the dashboard instead of committing a .env file.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
MESSAGES_FILE = BASE_DIR / "data" / "messages.jsonl"

app = Flask(__name__)
# Used to sign the session cookie so flash() messages work.
# Override in production with a real secret via the SECRET_KEY env var.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me")

# Google Search Console "HTML tag" verification code (the value from the
# <meta name="google-site-verification" content="..."> snippet). Leave blank
# until you start verification; setting it renders the tag site-wide.
GOOGLE_SITE_VERIFICATION = os.environ.get(
    "GOOGLE_SITE_VERIFICATION", "H2X8mvsEIEKze7F5I0UBDht_xj-IicRN6LZCgrOTJ8Y"
)


# --- Site content -----------------------------------------------------------
# Edit these to make the site yours. Keeping content in one place means the
# templates stay simple and you don't have to touch HTML to update copy.

PROFILE = {
    "name": "Praise Tony-Shokare",
    "tagline": "Software developer building web apps and games.",
    "bio": (
        "I build web apps and games — from an AI-assisted help desk system "
        "to a turn-based roguelike card battler. I like clean interfaces, "
        "practical AI features, and shipping things that work."
    ),
    "email": "opshokare@gmail.com",
    "location": "Remote",
    "socials": [
        {"label": "GitHub", "url": "https://github.com/ot-404"},
        {
            "label": "LinkedIn",
            "url": "https://www.linkedin.com/in/oruaroghene-tony-shokare-0069aa391",
        },
    ],
}

# Each skill has its own page (/skills/<slug>/) explaining how it's used across
# the projects below. "usage" entries link to the relevant project or repo.
SKILLS = [
    {
        "name": "Python",
        "slug": "python",
        "summary": "My main backend language — REST APIs, data models, authentication, and the glue around AI features.",
        "usage": [
            {
                "label": "Lumo — AI To-Do App",
                "href": "/projects/#p-lumo",
                "detail": "Python (3.11) powers the whole backend. It's a Flask REST API built "
                "with an app-factory pattern and blueprinted routes for auth, tasks, lists, "
                "and AI. Python handles JWT-based auth (identity = user id, no roles), Werkzeug "
                "password hashing, and all the task logic: view filters "
                "(today/upcoming/all/inbox/completed), completion toggling that cascades to "
                "subtasks, and drag-to-reorder persistence. An ai_service module tries Claude "
                "first, falls back to an OpenAI-compatible endpoint, then to a local heuristic "
                "parser, so the app works even with no API keys. It runs under gunicorn in a "
                "single Docker container.",
            },
            {
                "label": "This portfolio",
                "href": "https://github.com/ot-404/portfolio",
                "detail": "A small Flask app in Python: the routes, the content model behind "
                "these project and skill pages, an SMTP contact-form mailer, and a build "
                "script (build_static.py) that renders the whole site to static HTML for "
                "GitHub Pages.",
            },
        ],
    },
    {
        "name": "Flask",
        "slug": "flask",
        "summary": "My go-to Python web framework — both JSON APIs and server-rendered sites.",
        "usage": [
            {
                "label": "Lumo — AI To-Do App",
                "href": "/projects/#p-lumo",
                "detail": "Flask is the backbone of the backend. It exposes a JSON REST API "
                "under /api (auth, tasks, lists, and four AI endpoints), issues and verifies "
                "tokens with Flask-JWT-Extended, and applies CORS. The same app factory also "
                "serves the compiled React/Vite SPA in production, so one container runs both "
                "the API and the frontend. Endpoints cover task view filters, sidebar count "
                "badges, subtask creation via parent_id, reordering, and AI quick-add, "
                "breakdown, plan, and chat.",
            },
            {
                "label": "This portfolio",
                "href": "https://github.com/ot-404/portfolio",
                "detail": "Server-renders every page from Jinja templates that extend a shared "
                "base layout — home, projects, these per-skill pages, and a contact form that "
                "emails submissions. A freeze step then turns the rendered output into the "
                "static site you're reading.",
            },
        ],
    },
    {
        "name": "JavaScript",
        "slug": "javascript",
        "summary": "The language behind my interactive front-ends — from raw browser APIs to React.",
        "usage": [
            {
                "label": "BeatLab Pro",
                "href": "/projects/#p-beatlab",
                "detail": "The entire instrument is hand-written vanilla JavaScript on top of "
                "the Web Audio API — no framework or audio library. It builds a single "
                "AudioContext graph of oscillators, gain nodes, biquad filters, a convolver "
                "for reverb, and a delay line. ADSR envelopes are shaped by scheduling "
                "setValueAtTime and exponential/linear ramps on gain nodes; a step sequencer "
                "triggers voices in time, the piano roll plays polyphonically, and your "
                "patterns are saved to localStorage.",
            },
            {
                "label": "Lumo — AI To-Do App",
                "href": "/projects/#p-lumo",
                "detail": "Drives the React 19 front-end — async fetch calls to the REST API, "
                "UI state, and the AI assistant interactions.",
            },
        ],
    },
    {
        "name": "React",
        "slug": "react",
        "summary": "My framework of choice for building component-based, stateful UIs.",
        "usage": [
            {
                "label": "Lumo — AI To-Do App",
                "href": "/projects/#p-lumo",
                "detail": "React 19 + Vite power the app shell. React Router drives the task "
                "views (Today, Upcoming, All, Inbox, Completed) and custom lists, and a "
                "sidebar shows live per-view counts. It's built from focused components — "
                "TaskRow, TaskModal, QuickAdd, ListModal, and an AIAssistant chat drawer — "
                "with auth state held in an AuthContext. The whole thing is styled with "
                "Tailwind CSS and ships as an installable PWA via a service worker.",
            },
        ],
    },
    {
        "name": "HTML & CSS",
        "slug": "html-css",
        "summary": "The foundation of every interface I build — semantic markup and clean, responsive styling.",
        "usage": [
            {
                "label": "BeatLab Pro",
                "href": "/projects/#p-beatlab",
                "detail": "Hand-written HTML5 and CSS3 for the full DAW interface — the 16-step "
                "grid sequencer, piano roll, per-track mixer, and synth/effects panels — laid "
                "out with CSS grid and flexbox in a dark theme, with no UI framework.",
            },
            {
                "label": "This portfolio",
                "href": "https://github.com/ot-404/portfolio",
                "detail": "A custom dark theme written from scratch: CSS custom properties for "
                "the colour and spacing tokens, responsive grid/flex layouts, a sticky blurred "
                "header, hover and :target highlight states, and a mobile nav — all without a "
                "CSS framework.",
            },
            {
                "label": "Lumo — AI To-Do App",
                "href": "/projects/#p-lumo",
                "detail": "Semantic markup styled with Tailwind CSS utility classes and shared "
                "design tokens for the dark SaaS look.",
            },
        ],
    },
    {
        "name": "SQL",
        "slug": "sql",
        "summary": "Relational data modeling and queries for app persistence.",
        "usage": [
            {
                "label": "Lumo — AI To-Do App",
                "href": "/projects/#p-lumo",
                "detail": "The data layer is modeled with SQLAlchemy: a User table, TaskList "
                "(name, colour, icon), and Task (priority, due date, notes, and a "
                "self-referential parent_id for nested subtasks), plus a log of AI calls. "
                "Queries back every screen — date filters for today and upcoming, inbox "
                "(tasks with no list), per-list views, and aggregate counts for the sidebar "
                "badges. It runs on SQLite locally and PostgreSQL (Neon) in production.",
            },
        ],
    },
    {
        "name": "Git",
        "slug": "git",
        "summary": "Version control for everything I build, with GitHub for hosting and deploys.",
        "usage": [
            {
                "label": "All my projects",
                "href": "https://github.com/ot-404",
                "detail": "Every project lives in a Git repo under github.com/ot-404, and I "
                "work in feature branches and commits day to day. I also use Git as the deploy "
                "mechanism: Lumo pushes to two remotes — GitHub for source and a Hugging Face "
                "Space for hosting — and this portfolio's deploy script commits the generated "
                "site and pushes it, so GitHub Pages republishes on every push.",
            },
        ],
    },
    {
        "name": "Godot",
        "slug": "godot",
        "summary": "The engine I use for game development, scripting in GDScript.",
        "usage": [
            {
                "label": "MY_Game",
                "href": "/projects/#p-mygame",
                "detail": "Built in Godot 4 with GDScript. It's organised around autoload "
                "singletons for cross-scene state — a GameData store, a SaveManager for "
                "persistence, and an AudioManager — plus a level system (a LevelRegistry, "
                "per-level LevelData, and PuzzleState/PuzzleSolver logic) and separate scenes "
                "for the main menu, level select, and gameplay. It's set up to export to both "
                "desktop and mobile.",
            },
        ],
    },
]
SKILLS_BY_SLUG = {s["slug"]: s for s in SKILLS}

PROJECTS = [
    {
        "title": "Lumo — AI To-Do App",
        "slug": "lumo",
        "blurb": (
            "A dark, SaaS-style to-do app where AI does the busywork — capture "
            "tasks in plain English, auto-extract due dates and priorities, break "
            "tasks into subtasks, plan your day, and chat with an assistant that "
            "knows your list."
        ),
        "tags": ["Flask", "React", "Tailwind CSS", "Claude AI"],
        "url": "https://github.com/ot-404/ai-help-desk-system",
    },
    {
        "title": "BeatLab Pro",
        "slug": "beatlab",
        "blurb": (
            "A browser-based DAW and beat sequencer — 16-step drum grid, "
            "polyphonic piano roll, per-track mixer, synth editor with ADSR "
            "and filter, reverb and delay, and live keyboard input. "
            "Entirely synthesised in-browser via the Web Audio API."
        ),
        "tags": ["JavaScript", "Web Audio API", "HTML5", "CSS3"],
        "url": "/beatlab/",
    },
    {
        "title": "MY_Game",
        "slug": "mygame",
        "blurb": (
            "A turn-based roguelike card battler for desktop and mobile, "
            "built in Godot 4."
        ),
        "tags": ["Godot 4", "Game dev", "Mobile"],
        "url": "https://github.com/ot-404/my-game",
    },
]


# --- Routes -----------------------------------------------------------------


@app.route("/")
def index():
    return render_template(
        "index.html",
        profile=PROFILE,
        skills=SKILLS,
        featured=PROJECTS[:2],
    )


@app.route("/projects")
def projects():
    return render_template("projects.html", profile=PROFILE, projects=PROJECTS)


@app.route("/skills/<slug>/")
def skill(slug):
    s = SKILLS_BY_SLUG.get(slug)
    if s is None:
        abort(404)
    return render_template("skill.html", profile=PROFILE, skill=s)


@app.route("/beatlab/")
def beatlab():
    return send_from_directory("static/beatlab", "index.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        message = (request.form.get("message") or "").strip()

        if not name or not email or not message:
            flash("Please fill in every field.", "error")
            return redirect(url_for("contact"))

        # Always keep a local copy, then try to email it.
        _save_message(name, email, message)
        try:
            _send_contact_email(name, email, message)
        except Exception as exc:  # noqa: BLE001 - never 500 on a mail hiccup
            app.logger.warning("Contact email failed: %s", exc)

        flash("Thanks — your message was received!", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html", profile=PROFILE)


def _save_message(name: str, email: str, message: str) -> None:
    """Append a contact submission to a local JSONL file."""
    MESSAGES_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "at": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "email": email,
        "message": message,
    }
    with MESSAGES_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def _send_contact_email(name: str, email: str, message: str) -> bool:
    """Email a contact submission via SMTP.

    Configured entirely through environment variables (see .env.example):
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, CONTACT_TO, SMTP_USE_TLS

    Returns False (without raising) when SMTP isn't configured, so the form
    still works locally — the submission is already saved to disk either way.
    """
    host = os.environ.get("SMTP_HOST")
    if not host:
        return False

    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    recipient = os.environ.get("CONTACT_TO", PROFILE["email"])
    # From address: with a relay (e.g. Brevo) the login often differs from the
    # verified sender, so allow setting it explicitly. Falls back to the login.
    sender = os.environ.get("SMTP_FROM") or user or recipient
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() not in ("0", "false", "no")

    msg = EmailMessage()
    msg["Subject"] = f"Portfolio contact from {name}"
    msg["From"] = f"Portfolio Contact <{sender}>"
    msg["To"] = recipient
    msg["Reply-To"] = email  # so replying goes straight to the sender
    msg.set_content(
        "New message from your portfolio contact form:\n\n"
        f"Name:  {name}\n"
        f"Email: {email}\n\n"
        f"{message}\n"
    )

    server = (
        smtplib.SMTP_SSL(host, port, timeout=15)
        if port == 465
        else smtplib.SMTP(host, port, timeout=15)
    )
    try:
        if port != 465 and use_tls:
            server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(msg)
    finally:
        server.quit()
    return True


@app.context_processor
def inject_globals():
    """Make these available to every template without passing them in."""
    return {
        "now": datetime.now(timezone.utc),
        "profile": PROFILE,
        # Absolute base URL, used for canonical/OG tags. Override via env.
        "site_url": os.environ.get("SITE_URL", "https://ot-404.github.io"),
        "google_verification": GOOGLE_SITE_VERIFICATION,
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)
