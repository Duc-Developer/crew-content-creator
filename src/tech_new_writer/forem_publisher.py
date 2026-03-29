from __future__ import annotations

import json
import os

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
    return [item.strip() for item in raw.split(",") if item.strip()]


def article_endpoint() -> str:
    base_url = os.getenv("FOREM_API_BASE_URL", "https://dev.to/api").rstrip("/")
    return f"{base_url}/articles"


def publish_markdown_file(markdown_file: Path | None = None, topic: str | None = None) -> dict[str, str]:
    article_path = markdown_file or (project_root() / "final_article.md")
    if not article_path.exists():
        raise FileNotFoundError(f"Article file not found: {article_path}")

    api_key = os.getenv("FOREM_API_KEY", "").strip()
    if not api_key:
        raise ValueError("FOREM_API_KEY is required")

    title, body_markdown, cover_image = parse_article(
        article_path.read_text(encoding="utf-8"),
        topic=topic,
    )
    payload = {
        "article": {
            "title": title,
            "body_markdown": body_markdown,
            "published": False,
            "tags": load_tags(),
        }
    }
    if cover_image:
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
    response.raise_for_status()
    data = response.json()

    return {
        "id": str(data.get("id", "")),
        "url": data.get("url", ""),
        "title": data.get("title", title),
        "status": "draft",
    }


def publish_and_print() -> None:
    result = publish_markdown_file()
    print(json.dumps(result, ensure_ascii=False, indent=2))
