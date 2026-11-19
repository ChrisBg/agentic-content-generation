"""Entry point for Google ADK web UI and Agent Engine deployment."""

from .agents import create_content_generation_pipeline

# Root agent discovered by `adk web` and `adk eval`
root_agent = create_content_generation_pipeline()
