#!/usr/bin/env python
import os
import sys
import warnings

from datetime import datetime

from tech_new_writer.crew import TechNewWriter
from tech_new_writer.source_fetcher import build_source_digest

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

DEFAULT_TOPIC = "AI"
DEFAULT_SOURCES = ",".join(
    [
        "https://techcrunch.com/",
        "https://www.theverge.com/",
        "https://huggingface.co/blog",
        "https://towardsdatascience.com/",
        "https://dev.to/",
    ]
)


def build_inputs() -> dict[str, str]:
    topic = os.getenv("TECH_TOPIC", DEFAULT_TOPIC)
    sources = os.getenv("TECH_SOURCES", DEFAULT_SOURCES)
    source_digest = build_source_digest(sources)
    return {
        "topic": topic,
        "sources": sources,
        "source_digest": source_digest,
        "current_year": str(datetime.now().year),
    }

def run():
    """Run the crew."""
    inputs = build_inputs()

    try:
        TechNewWriter().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


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
