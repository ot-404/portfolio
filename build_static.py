"""Build a static version of the site into ./build for GitHub Pages.

Renders each page through the Flask app, rewrites internal links for static
hosting, swaps the server contact form for a FormSubmit.co endpoint (so it
still emails submissions with no backend), and writes SEO files.

Usage:  .venv\\Scripts\\python.exe build_static.py
"""

from __future__ import annotations

import os
import shutil
from datetime import date
from pathlib import Path

# Configure the canonical site URL and contact email BEFORE importing the app
# so the template context (canonical/OG tags) uses them.
SITE_URL = os.environ.get("SITE_URL", "https://ot-404.github.io").rstrip("/")
FORMSUBMIT_EMAIL = os.environ.get("CONTACT_TO", "opshokare@gmail.com")
os.environ["SITE_URL"] = SITE_URL

import app as site  # noqa: E402

BUILD = Path("build")
PAGES = {
    "/": "index.html",
    "/projects": "projects/index.html",
    "/contact": "contact/index.html",
}


def rewrite_links(html: str) -> str:
    """Point nav links at static-friendly folder URLs."""
    return (
        html.replace('href="/projects"', 'href="/projects/"')
        .replace('href="/contact"', 'href="/contact/"')
    )


def rewrite_contact_form(html: str) -> str:
    """Swap the Flask POST form for a FormSubmit.co form (no backend needed)."""
    old = '<form class="contact-form" method="post" action="/contact">'
    new = (
        f'<form class="contact-form" method="POST" '
        f'action="https://formsubmit.co/{FORMSUBMIT_EMAIL}">\n'
        '      <input type="hidden" name="_subject" value="New portfolio contact message" />\n'
        '      <input type="hidden" name="_captcha" value="false" />\n'
        '      <input type="hidden" name="_template" value="table" />\n'
        f'      <input type="hidden" name="_next" value="{SITE_URL}/contact/" />'
    )
    return html.replace(old, new)


def main() -> None:
    # Overwrite output in place rather than deleting the tree first. This keeps
    # the deploy repo's .git intact across rebuilds and avoids Windows/OneDrive
    # "access denied" errors from removing locked directories.
    BUILD.mkdir(exist_ok=True)

    client = site.app.test_client()
    for route, out in PAGES.items():
        resp = client.get(route)
        assert resp.status_code == 200, f"{route} returned {resp.status_code}"
        html = rewrite_links(resp.get_data(as_text=True))
        if route == "/contact":
            html = rewrite_contact_form(html)
        dest = BUILD / out
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        print(f"  wrote {out}")

    # Static assets (css/js) — overwrite in place, no deletion needed.
    shutil.copytree("static", BUILD / "static", dirs_exist_ok=True)
    print("  copied static/")

    # Skip Jekyll processing on GitHub Pages.
    (BUILD / ".nojekyll").write_text("", encoding="utf-8")

    # robots.txt
    (BUILD / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n" f"Sitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )
    print("  wrote robots.txt")

    # sitemap.xml
    today = date.today().isoformat()
    locs = [f"{SITE_URL}/", f"{SITE_URL}/projects/", f"{SITE_URL}/contact/"]
    urls = "\n".join(
        f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod></url>" for loc in locs
    )
    (BUILD / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    print("  wrote sitemap.xml")

    print(f"\nStatic site built in ./{BUILD}/  (SITE_URL={SITE_URL})")


if __name__ == "__main__":
    main()
