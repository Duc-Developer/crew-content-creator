from __future__ import annotations

import json
import xml.etree.ElementTree as ET
import subprocess

from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


RSS_CANDIDATES = {
    "techcrunch.com": [
        "https://techcrunch.com/feed/",
    ],
    "www.theverge.com": [
        "https://www.theverge.com/rss/index.xml",
    ],
    "huggingface.co": [
        "https://huggingface.co/blog/feed.xml",
    ],
    "towardsdatascience.com": [
        "https://towardsdatascience.com/feed",
    ],
    "dev.to": [
        "https://dev.to/feed",
    ],
}


def candidate_feeds(source_url: str) -> list[str]:
    hostname = urlparse(source_url).netloc.lower()
    if hostname in RSS_CANDIDATES:
        return RSS_CANDIDATES[hostname]
    normalized = hostname.removeprefix("www.")
    return RSS_CANDIDATES.get(normalized, [source_url.rstrip("/") + "/feed"])


def fetch_url(url: str, timeout: int = 20) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; tech_new_writer/0.1; +https://example.local)"
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception:
        completed = subprocess.run(
            [
                "curl",
                "--silent",
                "--show-error",
                "--location",
                "--max-time",
                str(timeout),
                url,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout


def parse_feed(xml_text: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    items: list[dict[str, str]] = []

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()
        if title and link:
            items.append(
                {
                    "title": title,
                    "link": link,
                    "published": pub_date,
                    "summary": description,
                }
            )

    if items:
        return items

    namespace = {
        "atom": "http://www.w3.org/2005/Atom",
    }
    for entry in root.findall(".//atom:entry", namespace):
        title = (entry.findtext("atom:title", default="", namespaces=namespace) or "").strip()
        published = (
            entry.findtext("atom:published", default="", namespaces=namespace)
            or entry.findtext("atom:updated", default="", namespaces=namespace)
            or ""
        ).strip()
        summary = (
            entry.findtext("atom:summary", default="", namespaces=namespace)
            or entry.findtext("atom:content", default="", namespaces=namespace)
            or ""
        ).strip()
        link = ""
        for link_node in entry.findall("atom:link", namespace):
            href = link_node.attrib.get("href", "").strip()
            rel = link_node.attrib.get("rel", "alternate").strip()
            if href and rel == "alternate":
                link = href
                break
        if title and link:
            items.append(
                {
                    "title": title,
                    "link": link,
                    "published": published,
                    "summary": summary,
                }
            )
    return items


def build_source_digest(source_urls: str, limit_per_source: int = 5) -> str:
    digests: list[str] = []
    for raw_url in source_urls.split(","):
        source_url = raw_url.strip()
        if not source_url:
            continue
        host = urlparse(source_url).netloc or source_url
        feed_candidates = candidate_feeds(source_url)
        items: list[dict[str, str]] = []
        error_message = ""

        for feed_url in feed_candidates:
            try:
                xml_text = fetch_url(feed_url)
                items = parse_feed(xml_text)[:limit_per_source]
                if items:
                    break
            except (HTTPError, URLError, ET.ParseError, TimeoutError, ValueError) as exc:
                error_message = str(exc)

        if items:
            lines = [f"Source: {host}"]
            for index, item in enumerate(items, start=1):
                lines.append(
                    f"{index}. {item['title']} | {item['published']} | {item['link']}"
                )
                if item["summary"]:
                    lines.append(f"   Summary: {item['summary'][:400]}")
            digests.append("\n".join(lines))
        else:
            digests.append(
                f"Source: {host}\nNo feed entries fetched successfully from {', '.join(feed_candidates)}"
                + (f" | error: {error_message}" if error_message else "")
            )

    return "\n\n".join(digests)


BAD_IMAGE_KEYWORDS = (
    "logo",
    "icon",
    "avatar",
    "favicon",
    "emoji",
    "sprite",
    "badge",
    "thumbnail-icon",
    "profile",
)


def score_image_url(image_url: str) -> int:
    lowered = image_url.lower()
    score = 0
    if "og-image" in lowered or "ogimage" in lowered:
        score += 50
    if "twitter" in lowered:
        score += 15
    if "hero" in lowered or "cover" in lowered or "featured" in lowered:
        score += 40
    if "1200" in lowered or "1600" in lowered or "800" in lowered:
        score += 20
    if lowered.endswith(".svg"):
        score -= 100
    if any(keyword in lowered for keyword in BAD_IMAGE_KEYWORDS):
        score -= 80
    if lowered.endswith(".jpg") or lowered.endswith(".jpeg") or lowered.endswith(".png") or ".jpg?" in lowered or ".png?" in lowered:
        score += 10
    return score


def filter_image_candidates(image_urls: list[str]) -> list[str]:
    unique_urls: list[str] = []
    for image_url in image_urls:
        if image_url not in unique_urls:
            unique_urls.append(image_url)

    filtered = [url for url in unique_urls if score_image_url(url) > -20]
    filtered.sort(key=score_image_url, reverse=True)
    return filtered[:2]


def extract_image_candidates(page_url: str) -> list[str]:
    html = fetch_url(page_url, timeout=20)
    extract_script = """
import json, re, sys
html = sys.stdin.read()
patterns = [
    r'<meta[^>]+property=["\\']og:image["\\'][^>]+content=["\\']([^"\\']+)["\\']',
    r'<meta[^>]+name=["\\']twitter:image["\\'][^>]+content=["\\']([^"\\']+)["\\']',
    r'<img[^>]+src=["\\']([^"\\']+)["\\']',
]
results = []
for pattern in patterns:
    for match in re.findall(pattern, html, flags=re.IGNORECASE):
        if match.startswith("http"):
            results.append(match)
deduped = []
for item in results:
    if item not in deduped:
        deduped.append(item)
print(json.dumps(deduped[:3], ensure_ascii=False))
"""
    completed = subprocess.run(
        ["python3", "-c", extract_script],
        input=html,
        text=True,
        capture_output=True,
        check=True,
    )
    image_urls = json.loads(completed.stdout)
    return filter_image_candidates(image_urls)


def build_image_digest(source_urls: str, limit_per_source: int = 3) -> str:
    digests: list[str] = []
    for raw_url in source_urls.split(","):
        source_url = raw_url.strip()
        if not source_url:
            continue
        host = urlparse(source_url).netloc or source_url
        feed_candidates = candidate_feeds(source_url)
        items: list[dict[str, str]] = []
        error_message = ""

        for feed_url in feed_candidates:
            try:
                xml_text = fetch_url(feed_url)
                items = parse_feed(xml_text)[:limit_per_source]
                if items:
                    break
            except (HTTPError, URLError, ET.ParseError, TimeoutError, ValueError) as exc:
                error_message = str(exc)

        lines = [f"Source: {host}"]
        if not items:
            lines.append(
                f"No image candidates fetched from {', '.join(feed_candidates)}"
                + (f" | error: {error_message}" if error_message else "")
            )
            digests.append("\n".join(lines))
            continue

        for index, item in enumerate(items, start=1):
            try:
                image_urls = extract_image_candidates(item["link"])
            except Exception as exc:
                image_urls = []
                lines.append(f"{index}. {item['title']} | {item['link']}")
                lines.append(f"   Image fetch failed: {exc}")
                continue

            lines.append(f"{index}. {item['title']} | {item['link']}")
            if image_urls:
                for image_url in image_urls:
                    lines.append(f"   Image: {image_url}")
            else:
                lines.append("   Image: none found")

        digests.append("\n".join(lines))

    return "\n\n".join(digests)
