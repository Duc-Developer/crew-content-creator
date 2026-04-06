from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from crewai import Crew, Process

from tech_new_writer.crew import TechNewWriter
from tech_new_writer.forem_publisher import publish_markdown
from tech_new_writer.source_fetcher import (
    build_image_digest,
    build_source_digest,
    extract_article_title,
    extract_top_article_url,
)


DEFAULT_TOPIC = "Hướng dẫn tích hợp OpenCLaw bằng docker"
DEFAULT_SOURCES = ",".join(
    [
        "https://techcrunch.com/",
        "https://www.theverge.com/tech",
        "https://huggingface.co/blog",
        "https://towardsdatascience.com/",
        # "https://dev.to/",
    ]
)


@dataclass
class FlowResult:
    status: str
    flow: str
    topic: str | None
    sources: list[str]
    result: Any
    final_article_markdown: str | None = None
    publish_result: dict[str, str] | None = None
    top_article_url: str | None = None
    original_title: str | None = None


def should_auto_publish(publish_draft: bool | None) -> bool:
    if publish_draft is not None:
        return publish_draft
    return True


def split_sources(sources: str | None) -> list[str]:
    raw = sources or DEFAULT_SOURCES
    return [item.strip() for item in raw.split(",") if item.strip()]


def build_inputs_for_topic(topic: str, sources: str) -> dict[str, str]:
    source_digest = build_source_digest(sources)
    image_digest = build_image_digest(sources)
    return {
        "topic": topic,
        "sources": sources,
        "source_digest": source_digest,
        "image_digest": image_digest,
        "current_year": str(datetime.now().year),
    }


def build_inputs(topic: str | None = None, sources: str | None = None) -> dict[str, str]:
    resolved_topic = topic or os.getenv("TECH_TOPIC", DEFAULT_TOPIC)
    resolved_sources = sources or os.getenv("TECH_SOURCES", DEFAULT_SOURCES)
    return build_inputs_for_topic(resolved_topic, resolved_sources)


def extract_final_markdown(result: Any) -> str:
    raw = getattr(result, "raw", None)
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    raise ValueError("Final article markdown is missing from crew result")


def topic_crew(writer: TechNewWriter) -> Crew:
    return Crew(
        agents=[
            writer.trend_researcher(),
            writer.sme(),
            writer.seo_specialist(),
            writer.content_writer(),
            writer.editor(),
        ],
        tasks=[
            writer.trend_research_task(),
            writer.technical_review_task(),
            writer.seo_planning_task(),
            writer.article_writing_task(),
            writer.final_edit_task(),
        ],
        process=Process.sequential,
        verbose=True,
    )


def single_article_crew(writer: TechNewWriter) -> Crew:
    return Crew(
        agents=[
            writer.trend_researcher(),
            writer.sme(),
            writer.seo_specialist(),
            writer.content_writer(),
            writer.editor(),
        ],
        tasks=[
            writer.single_article_research_task(),
            writer.single_article_technical_review_task(),
            writer.single_article_seo_task(),
            writer.single_article_writing_task(),
            writer.single_article_final_edit_task(),
        ],
        process=Process.sequential,
        verbose=True,
    )


def finalize_flow_result(
    *,
    flow: str,
    topic: str | None,
    sources: list[str],
    result: Any,
    final_article_markdown: str,
    publish_result: dict[str, str] | None = None,
    top_article_url: str | None = None,
    original_title: str | None = None,
) -> FlowResult:
    return FlowResult(
        status="completed",
        flow=flow,
        topic=topic,
        sources=sources,
        result=result,
        final_article_markdown=final_article_markdown,
        publish_result=publish_result,
        top_article_url=top_article_url,
        original_title=original_title,
    )


def run_topic_flow(
    *,
    topic: str | None = None,
    sources: str | None = None,
    publish_draft: bool | None = None,
    cleanup_workspace: bool = False,
) -> FlowResult:
    inputs = build_inputs(topic=topic, sources=sources)
    writer = TechNewWriter()
    result = topic_crew(writer).kickoff(inputs=inputs)
    final_article_markdown = extract_final_markdown(result)
    publish_result = None
    if should_auto_publish(publish_draft):
        publish_result = publish_markdown(
            final_article_markdown,
            topic=inputs["topic"],
        )
    return finalize_flow_result(
        flow="topic",
        topic=inputs["topic"],
        sources=split_sources(inputs["sources"]),
        result=result,
        final_article_markdown=final_article_markdown,
        publish_result=publish_result,
    )


def run_single_article_flow(
    *,
    source_url: str,
    publish_draft: bool | None = None,
    cleanup_workspace: bool = False,
) -> FlowResult:
    top_article_url = extract_top_article_url(source_url)
    if not top_article_url:
        raise ValueError(f"Could not determine top article from source: {source_url}")

    original_title = extract_article_title(top_article_url)
    topic = original_title or f"Bài viết công nghệ nổi bật từ {source_url}"
    inputs = build_inputs_for_topic(topic, source_url)
    inputs["top_article_url"] = top_article_url
    if original_title:
        inputs["original_title"] = original_title

    writer = TechNewWriter()
    result = single_article_crew(writer).kickoff(inputs=inputs)
    final_article_markdown = extract_final_markdown(result)
    publish_result = None
    if should_auto_publish(publish_draft):
        publish_result = publish_markdown(
            final_article_markdown,
            topic=inputs["topic"],
        )
    return finalize_flow_result(
        flow="single_article",
        topic=inputs["topic"],
        sources=[source_url],
        result=result,
        final_article_markdown=final_article_markdown,
        publish_result=publish_result,
        top_article_url=top_article_url,
        original_title=original_title,
    )


def run_daily_top_flow(
    *,
    sources: str | None = None,
    publish_draft: bool | None = None,
    cleanup_workspace: bool = False,
) -> list[FlowResult]:
    results: list[FlowResult] = []
    for source in split_sources(sources or DEFAULT_SOURCES):
        top_article_url = extract_top_article_url(source)
        if not top_article_url:
            continue

        original_title = extract_article_title(top_article_url)
        topic = original_title or f"Bài viết công nghệ nổi bật từ {source}"
        inputs = build_inputs_for_topic(topic, source)
        inputs["top_article_url"] = top_article_url
        if original_title:
            inputs["original_title"] = original_title

        writer = TechNewWriter()
        result = single_article_crew(writer).kickoff(inputs=inputs)
        final_article_markdown = extract_final_markdown(result)
        publish_result = None
        if should_auto_publish(publish_draft):
            publish_result = publish_markdown(
                final_article_markdown,
                topic=inputs["topic"],
            )
        results.append(
            finalize_flow_result(
                flow="daily_top",
                topic=inputs["topic"],
                sources=[source],
                result=result,
                final_article_markdown=final_article_markdown,
                publish_result=publish_result,
                top_article_url=top_article_url,
                original_title=original_title,
            )
        )

    return results
