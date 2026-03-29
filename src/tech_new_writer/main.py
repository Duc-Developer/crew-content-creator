#!/usr/bin/env python
import os
import sys
import warnings

from datetime import datetime

from crewai import Crew, Process

from tech_new_writer.crew import TechNewWriter
from tech_new_writer.forem_publisher import publish_markdown_file
from tech_new_writer.session_workspace import (
    cleanup_section_workspace,
    create_section_workspace,
    resolve_output_path,
    section_output_paths,
)
from tech_new_writer.source_fetcher import (
    build_image_digest,
    build_source_digest,
    extract_article_title,
    extract_top_article_url,
)

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

DEFAULT_TOPIC = "Hướng dẫn tích hợp OpenCLaw bằng docker"
DEFAULT_SOURCES = ",".join(
    [
        "https://techcrunch.com/",
        "https://www.theverge.com/tech",
        "https://huggingface.co/blog",
        "https://towardsdatascience.com/",
        "https://dev.to/",
    ]
)


def build_inputs() -> dict[str, str]:
    topic = os.getenv("TECH_TOPIC", DEFAULT_TOPIC)
    sources = os.getenv("TECH_SOURCES", DEFAULT_SOURCES)
    return build_inputs_for_topic(topic, sources)


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


def single_article_crew() -> Crew:
    writer = TechNewWriter()
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


def build_section_writer(prefix: str) -> tuple[TechNewWriter, dict[str, str], object]:
    _, workspace = create_section_workspace(prefix)
    output_paths = section_output_paths(workspace)
    writer = TechNewWriter()
    writer._section_output_paths = output_paths
    return writer, output_paths, workspace

def run():
    """Run the crew."""
    inputs = build_inputs()

    writer, output_paths, workspace = build_section_writer("topic")
    try:
        result = topic_crew(writer).kickoff(inputs=inputs)
        if os.getenv("FOREM_AUTO_PUBLISH_DRAFT", "true").lower() == "true":
            publish_result = publish_markdown_file(
                markdown_file=resolve_output_path(output_paths["final_article"]),
                topic=inputs["topic"],
            )
            print(f"Forem draft created: {publish_result['title']} ({publish_result['url']})")
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
    finally:
        cleanup_section_workspace(workspace)


def run_with_prompted_topic():
    """Prompt for a topic from terminal input and run the crew."""
    topic = input("Nhập topic: ").strip()
    if not topic:
        topic = DEFAULT_TOPIC
    sources = os.getenv("TECH_SOURCES", DEFAULT_SOURCES)
    inputs = build_inputs_for_topic(topic, sources)

    writer, output_paths, workspace = build_section_writer("prompted")
    try:
        result = topic_crew(writer).kickoff(inputs=inputs)
        if os.getenv("FOREM_AUTO_PUBLISH_DRAFT", "true").lower() == "true":
            publish_result = publish_markdown_file(
                markdown_file=resolve_output_path(output_paths["final_article"]),
                topic=inputs["topic"],
            )
            print(f"Forem draft created: {publish_result['title']} ({publish_result['url']})")
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running prompted topic flow: {e}")
    finally:
        cleanup_section_workspace(workspace)


def run_daily_top_source_articles():
    """Run once for cron: pick one popular article per source and create separate drafts."""
    sources = os.getenv("TECH_SOURCES", DEFAULT_SOURCES)
    results = []

    for source in [item.strip() for item in sources.split(",") if item.strip()]:
        workspace = None
        top_article_url = extract_top_article_url(source)
        if not top_article_url:
            print(f"Skip source without top article: {source}")
            continue

        original_title = extract_article_title(top_article_url)
        topic = original_title or f"Bài viết công nghệ nổi bật từ {source}"
        inputs = build_inputs_for_topic(topic, source)
        inputs["top_article_url"] = top_article_url
        if original_title:
            inputs["original_title"] = original_title

        try:
            writer, output_paths, workspace = build_section_writer("daily")
            result = Crew(
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
            ).kickoff(inputs=inputs)
            publish_result = None
            if os.getenv("FOREM_AUTO_PUBLISH_DRAFT", "true").lower() == "true":
                publish_result = publish_markdown_file(
                    markdown_file=resolve_output_path(output_paths["final_article"]),
                    topic=inputs["topic"],
                )
                print(f"Forem draft created: {publish_result['title']} ({publish_result['url']})")
            results.append(
                {
                    "source": source,
                    "top_article_url": top_article_url,
                    "result": result,
                    "publish_result": publish_result,
                }
            )
        except Exception as e:
            print(f"Failed source {source}: {e}")
        finally:
            if workspace is not None:
                cleanup_section_workspace(workspace)

    return results


def train():
    """Train the crew for a given number of iterations."""
    inputs = build_inputs()
    try:
        TechNewWriter().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """Replay the crew execution from a specific task."""
    try:
        TechNewWriter().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """Test the crew execution and returns the results."""
    inputs = build_inputs()

    try:
        TechNewWriter().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """Run the crew with trigger payload."""
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = build_inputs()
    inputs["crewai_trigger_payload"] = trigger_payload

    try:
        result = TechNewWriter().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
