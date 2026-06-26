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
        "summary": "My main backend language — web APIs, data models, auth, and wiring up AI features.",
        "usage": [
            {
                "label": "Lumo — AI To-Do App",
                "href": "/projects/#p-lumo",
                "detail": "Powers the entire backend: a Flask REST API, SQLAlchemy data "
                "models, JWT auth, and the server-side logic that calls Claude for "
                "AI quick-add, task breakdown, and “plan my day”.",
            },
            {
                "label": "This portfolio",
                "href": "https://github.com/ot-404/portfolio",
                "detail": "Built as a small Flask app with server-rendered Jinja templates "
                "and a static-site build step.",
            },
        ],
    },
    {
        "name": "Flask",
        "slug": "flask",
        "summary": "My go-to Python web framework for building APIs and server-rendered sites.",
        "usage": [
            {
                "label": "Lumo — AI To-Do App",
                "href": "/projects/#p-lumo",
                "detail": "Serves the REST API for tasks, lists, and auth, issues JWTs, and "
                "serves the compiled React/Vite frontend from a single container.",
            },
            {
                "label": "This portfolio",
                "href": "https://github.com/ot-404/portfolio",
                "detail": "Server-renders the pages with Jinja; a build script then freezes "
                "it to static HTML for GitHub Pages.",
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
                "detail": "The whole app is vanilla JavaScript: real-time audio synthesis via "
                "the Web Audio API, a 16-step sequencer, a piano roll, and a synth/mixer "
                "UI — no framework.",
            },
            {
                "label": "Lumo — AI To-Do App",
                "href": "/projects/#p-lumo",
                "detail": "Drives the React front-end and its AI-powered interactions.",
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
                "detail": "React 19 + Vite power the app shell — task views "
                "(Today/Upcoming/All), nested subtasks, the AI assistant chat drawer, and "
                "the marketing landing page — styled with Tailwind CSS.",
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
                "detail": "Hand-written HTML5 and CSS3 for the DAW layout, the grid "
                "sequencer, and all the controls.",
            },
            {
                "label": "This portfolio",
                "href": "https://github.com/ot-404/portfolio",
                "detail": "A custom dark theme built with CSS variables and a responsive "
                "layout — no UI framework.",
            },
            {
                "label": "Lumo — AI To-Do App",
                "href": "/projects/#p-lumo",
                "detail": "Styled with Tailwind CSS on top of semantic markup.",
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
                "detail": "Models users, tasks, lists, and nested subtasks via SQLAlchemy "
                "over a SQL database, with the relationships and queries that power "
                "every view.",
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
                "detail": "Every project lives in a Git repo on GitHub. I branch and commit "
                "day to day and rely on Git-based deploys — this portfolio auto-publishes "
                "to GitHub Pages on each push.",
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
                "detail": "A turn-based roguelike card battler built in Godot 4 — scenes, "
                "GDScript gameplay logic, a save system, and exports for both desktop "
                "and mobile.",
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
