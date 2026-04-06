from __future__ import annotations

import os
from urllib.parse import urlparse

from pathlib import Path

import requests


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def fallback_title(topic: str | None = None) -> str:
    return (topic or "").strip() or "Untitled Article"


def parse_article(markdown_text: str, topic: str | None = None) -> tuple[str, str]:
    lines = markdown_text.splitlines()
    title = fallback_title(topic)
    body_lines = lines[:]
    cover_image = ""

    if lines and lines[0].startswith("# "):
        parsed_title = lines[0][2:].strip()
        if parsed_title and parsed_title.lower() != "untitled article":
            title = parsed_title
        body_lines = lines[1:]

    filtered_lines: list[str] = []
    for line in body_lines:
        if line.startswith("Cover Image:"):
            cover_image = line.split(":", 1)[1].strip()
            continue
        if line.startswith("Cover Image Source:"):
            continue
        filtered_lines.append(line)

    body_markdown = "\n".join(filtered_lines).strip()
    return title or fallback_title(topic), body_markdown, cover_image


def load_tags() -> list[str]:
    raw = os.getenv("FOREM_TAGS", os.getenv("BLOGGER_LABELS", ""))
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def sanitize_tags(tags: list[str]) -> list[str]:
    sanitized: list[str] = []
    for tag in tags:
        normalized = "".join(ch for ch in tag.lower() if ch.isalnum())
        if not normalized:
            continue
        sanitized.append(normalized[:20])
    return sanitized[:4]


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def article_endpoint() -> str:
    base_url = os.getenv("FOREM_API_BASE_URL", "https://dev.to/api").rstrip("/")
    return f"{base_url}/articles"


def publish_markdown(markdown_text: str, topic: str | None = None) -> dict[str, str]:
    api_key = os.getenv("FOREM_API_KEY", "").strip()
    if not api_key:
        raise ValueError("FOREM_API_KEY is required")

    title, body_markdown, cover_image = parse_article(markdown_text, topic=topic)
    payload = {
        "article": {
            "title": title,
            "body_markdown": body_markdown,
            "published": False,
            "tags": sanitize_tags(load_tags()),
        }
    }
    if cover_image and is_http_url(cover_image):
        payload["article"]["main_image"] = cover_image

    response = requests.post(
        article_endpoint(),
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise requests.HTTPError(
            f"{exc}. Response body: {response.text}",
            response=response,
            request=response.request,
        ) from exc
    data = response.json()

    return {
        "id": str(data.get("id", "")),
        "url": data.get("url", ""),
        "title": data.get("title", title),
        "status": "draft",
    }


def publish_markdown_file(markdown_file: Path | None = None, topic: str | None = None) -> dict[str, str]:
    article_path = markdown_file or (project_root() / "final_article.md")
    if not article_path.exists():
        raise FileNotFoundError(f"Article file not found: {article_path}")

    return publish_markdown(article_path.read_text(encoding="utf-8"), topic=topic)


def publish_and_print(markdown_file: Path | None = None, topic: str | None = None) -> dict[str, str]:
    return publish_markdown_file(markdown_file=markdown_file, topic=topic)
