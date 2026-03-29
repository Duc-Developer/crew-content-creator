from __future__ import annotations

import json
import os

from pathlib import Path

import markdown

from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/blogger"]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def env_path(name: str, default: str) -> Path:
    return Path(os.getenv(name, str(project_root() / default))).expanduser()


def parse_article(markdown_text: str) -> tuple[str, str]:
    lines = markdown_text.splitlines()
    title = "Untitled Article"
    body_lines = lines

    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip() or title
        body_lines = lines[1:]

    body_markdown = "\n".join(body_lines).strip()
    body_html = markdown.markdown(body_markdown, extensions=["extra", "tables", "sane_lists"])
    return title, body_html


def load_labels() -> list[str]:
    raw = os.getenv("BLOGGER_LABELS", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_credentials():
    credentials_file = env_path("BLOGGER_SERVICE_ACCOUNT_FILE", "service-account.json")
    if not credentials_file.exists():
        raise FileNotFoundError(f"Service account file not found: {credentials_file}")

    creds = service_account.Credentials.from_service_account_file(
        str(credentials_file),
        scopes=SCOPES,
    )

    delegated_user = os.getenv("BLOGGER_DELEGATED_USER", "").strip()
    if delegated_user:
        creds = creds.with_subject(delegated_user)

    return creds


def publish_markdown_file(markdown_file: Path | None = None) -> dict[str, str]:
    article_path = markdown_file or (project_root() / "final_article.md")
    if not article_path.exists():
        raise FileNotFoundError(f"Article file not found: {article_path}")

    blog_id = os.getenv("BLOGGER_BLOG_ID", "").strip()
    if not blog_id:
        raise ValueError("BLOGGER_BLOG_ID is required")

    title, body_html = parse_article(article_path.read_text(encoding="utf-8"))
    creds = load_credentials()
    service = build("blogger", "v3", credentials=creds)
    request_body = {
        "kind": "blogger#post",
        "title": title,
        "content": body_html,
        "labels": load_labels(),
    }

    post = (
        service.posts()
        .insert(blogId=blog_id, body=request_body, isDraft=True)
        .execute()
    )

    return {
        "id": post.get("id", ""),
        "url": post.get("url", ""),
        "title": post.get("title", title),
        "status": "draft",
    }


def publish_and_print() -> None:
    result = publish_markdown_file()
    print(json.dumps(result, ensure_ascii=False, indent=2))
