"""
Personal portfolio site.

A small server-rendered Flask app: Jinja templates + static CSS/JS.
Run with `python app.py` (dev) or via a WSGI server in production.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

BASE_DIR = Path(__file__).resolve().parent
MESSAGES_FILE = BASE_DIR / "data" / "messages.jsonl"

app = Flask(__name__)
# Used to sign the session cookie so flash() messages work.
# Override in production with a real secret via the SECRET_KEY env var.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me")


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

SKILLS = [
    "Python", "Flask", "JavaScript", "React",
    "HTML & CSS", "SQL", "Git", "Godot",
]

PROJECTS = [
    {
        "title": "AI Help Desk System",
        "blurb": (
            "A help desk web app with JWT auth, role-based dashboards, and "
            "AI/RAG-assisted ticket handling."
        ),
        "tags": ["Flask", "React", "AI / RAG", "JWT"],
        "url": "https://github.com/ot-404/ai-help-desk-system",
    },
    {
        "title": "MY_Game",
        "blurb": (
            "A turn-based roguelike card battler for desktop and mobile, "
            "built in Godot 4."
        ),
        "tags": ["Godot 4", "Game dev", "Mobile"],
        "url": "",
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


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        message = (request.form.get("message") or "").strip()

        if not name or not email or not message:
            flash("Please fill in every field.", "error")
            return redirect(url_for("contact"))

        _save_message(name, email, message)
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


@app.context_processor
def inject_globals():
    """Make these available to every template without passing them in."""
    return {"now": datetime.now(timezone.utc), "profile": PROFILE}


if __name__ == "__main__":
    app.run(debug=True, port=5000)
