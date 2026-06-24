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
    flash,
    redirect,
    render_template,
    request,
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
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() not in ("0", "false", "no")

    msg = EmailMessage()
    msg["Subject"] = f"Portfolio contact from {name}"
    msg["From"] = f"Portfolio Contact <{user or recipient}>"
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
    return {"now": datetime.now(timezone.utc), "profile": PROFILE}


if __name__ == "__main__":
    app.run(debug=True, port=5000)
