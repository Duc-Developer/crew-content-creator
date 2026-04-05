import os
import warnings

from tech_new_writer.env_loader import load_local_env
from tech_new_writer.service import (
    DEFAULT_SOURCES,
    DEFAULT_TOPIC,
    run_topic_flow,
)

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
load_local_env()

def run():
    """Run the default topic flow."""
    try:
        return run_topic_flow(
            topic=os.getenv("TECH_TOPIC", DEFAULT_TOPIC),
            sources=os.getenv("TECH_SOURCES", DEFAULT_SOURCES),
        )
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
