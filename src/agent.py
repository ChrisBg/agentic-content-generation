"""Entry point for Agent Engine deployment.

This module provides the root_agent instance required by the ADK deployment system.
"""

from .agents import create_content_generation_pipeline

# Create the root agent for deployment
root_agent = create_content_generation_pipeline()
