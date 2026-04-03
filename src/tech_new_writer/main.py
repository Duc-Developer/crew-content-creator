#!/usr/bin/env python
import json
import os
import sys
import warnings

from tech_new_writer.crew import TechNewWriter
from tech_new_writer.env_loader import load_local_env
from tech_new_writer.service import (
    DEFAULT_SOURCES,
    DEFAULT_TOPIC,
    build_inputs,
    run_daily_top_flow,
    run_topic_flow,
)

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
load_local_env()

def run():
    """Run the crew."""
    try:
        return run_topic_flow(
            topic=os.getenv("TECH_TOPIC", DEFAULT_TOPIC),
            sources=os.getenv("TECH_SOURCES", DEFAULT_SOURCES),
        )
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def run_with_prompted_topic():
    """Prompt for a topic from terminal input and run the crew."""
    topic = input("Nhập topic: ").strip()
    if not topic:
        topic = DEFAULT_TOPIC
    try:
        return run_topic_flow(
            topic=topic,
            sources=os.getenv("TECH_SOURCES", DEFAULT_SOURCES),
        )
    except Exception as e:
        raise Exception(f"An error occurred while running prompted topic flow: {e}")


def run_daily_top_source_articles():
    """Run once for cron: pick one popular article per source and create separate drafts."""
    return run_daily_top_flow(sources=os.getenv("TECH_SOURCES", DEFAULT_SOURCES))


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
    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = build_inputs()
    inputs["crewai_trigger_payload"] = trigger_payload

    return run_topic_flow(
        topic=inputs["topic"],
        sources=inputs["sources"],
    )
