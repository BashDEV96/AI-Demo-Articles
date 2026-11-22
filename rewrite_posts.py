#!/usr/bin/env python3
"""Replace placeholder WordPress post bodies with AI-written articles based on each title.

Usage:
    python rewrite_posts.py --dry-run --limit 2   # preview 2 articles, nothing changes on the site
    python rewrite_posts.py                       # do all posts
    python rewrite_posts.py --redo                # ignore progress file and redo everything
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE = Path(__file__).parent
PROMPT_FILE = BASE / "Prompts" / "article.md"
BACKUP_DIR = BASE / "backups"      # original post content, saved before every change
PREVIEW_DIR = BASE / "previews"    # dry-run output
PROGRESS_FILE = BASE / "progress.json"

# All three speak the OpenAI-style chat API, so one code path covers them.
PROVIDERS = {
    "google": "https://generativelanguage.googleapis.com/v1beta/openai",
    "openrouter": "https://openrouter.ai/api/v1",
    "openai": "https://api.openai.com/v1",
}


def need(name):
    value = os.getenv(name, "").strip()
    if not value:
        sys.exit(f"Missing {name} in your .env file.")
    return value


def load_config():
    load_dotenv(BASE / ".env")
    provider = need("AI_PROVIDER").lower()
    if provider not in PROVIDERS:
        sys.exit(f"AI_PROVIDER must be one of: {', '.join(PROVIDERS)}")
    return {
        "wp_url": need("WP_URL").rstrip("/"),
        "wp_auth": (need("WP_USER"), need("WP_APP_PASSWORD")),
        "ai_url": PROVIDERS[provider],
        "ai_key": need("AI_API_KEY"),
        "ai_model": need("AI_MODEL"),
    }


def get_posts(cfg):
    """Fetch every post (published and draft), including raw content for backup."""
    posts, page = [], 1
    while True:
        r = requests.get(
            f"{cfg['wp_url']}/wp-json/wp/v2/posts",
            auth=cfg["wp_auth"],
            params={"per_page": 100, "page": page, "status": "publish,draft", "context": "edit"},
            timeout=60,
        )
        if r.status_code == 400:  # past the last page
            break
        r.raise_for_status()
        posts.extend(r.json())
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1
    return posts


def clean_html(text):
    text = text.strip()
    text = re.sub(r"^```(?:html)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = re.sub(r"<h1[^>]*>.*?</h1>", "", text, flags=re.S | re.I)
    return text.strip()


def generate(cfg, title):
    prompt = PROMPT_FILE.read_text(encoding="utf-8").replace("{title}", title)
    delay = 10
    for attempt in range(5):
        try:
            r = requests.post(
                f"{cfg['ai_url']}/chat/completions",
                headers={"Authorization": f"Bearer {cfg['ai_key']}"},
                json={"model": cfg["ai_model"], "messages": [{"role": "user", "content": prompt}]},
                timeout=180,
            )
            if r.status_code in (429, 500, 502, 503, 504):
                raise RuntimeError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return clean_html(r.json()["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"   AI call failed ({e}); retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("AI kept failing, giving up on this post")


def update_post(cfg, post_id, html):
    r = requests.post(
        f"{cfg['wp_url']}/wp-json/wp/v2/posts/{post_id}",
        auth=cfg["wp_auth"],
        json={"content": html},
        timeout=60,
    )
    r.raise_for_status()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="save previews, do not touch the site")
    ap.add_argument("--limit", type=int, default=0, help="only process this many posts")
    ap.add_argument("--delay", type=float, default=4, help="seconds to wait between posts (helps with free-tier limits)")
    ap.add_argument("--redo", action="store_true", help="ignore progress.json and redo every post")
    args = ap.parse_args()

    cfg = load_config()
    done = set()
    if PROGRESS_FILE.exists() and not args.redo and not args.dry_run:
        done = set(json.loads(PROGRESS_FILE.read_text()))

    BACKUP_DIR.mkdir(exist_ok=True)
    PREVIEW_DIR.mkdir(exist_ok=True)

    posts = get_posts(cfg)
    todo = [p for p in posts if p["id"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"Found {len(posts)} posts, {len(todo)} to process.")

    for i, post in enumerate(todo, 1):
        pid = post["id"]
        title = post["title"].get("raw") or post["title"]["rendered"]
        print(f"[{i}/{len(todo)}] #{pid}: {title}")
        try:
            html = generate(cfg, title)
            if len(html) < 200:
                raise RuntimeError("AI returned almost nothing")
            if args.dry_run:
                (PREVIEW_DIR / f"{pid}.html").write_text(f"<h2>{title}</h2>\n{html}", encoding="utf-8")
            else:
                (BACKUP_DIR / f"post-{pid}.json").write_text(
                    json.dumps({"id": pid, "title": title, "content": post["content"].get("raw", "")}, indent=2),
                    encoding="utf-8",
                )
                update_post(cfg, pid, html)
                done.add(pid)
                PROGRESS_FILE.write_text(json.dumps(sorted(done)))
        except Exception as e:
            print(f"   SKIPPED: {e}")
        time.sleep(args.delay)

    print("Done." if not args.dry_run else f"Dry run done. Open the files in {PREVIEW_DIR}.")


if __name__ == "__main__":
    main()
