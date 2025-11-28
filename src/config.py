"""Configuration for the content generation agent system."""

import os

from dotenv import load_dotenv
from google.genai import types

# Load environment variables
load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")

# Model Configuration
DEFAULT_MODEL = "gemini-3-pro-preview"

# Retry configuration for transient failures
# Design decision: We use exponential backoff with 5 attempts to handle:
# - 429: Rate limiting (common with Gemini API free tier)
# - 500/503/504: Temporary server issues
# exp_base=7 gives: 1s, 7s, 49s... - aggressive enough for production use
# This ensures the agent completes tasks even with intermittent API issues
RETRY_CONFIG = types.HttpRetryOptions(
    attempts=5, exp_base=7, initial_delay=1, http_status_codes=[429, 500, 503, 504]
)

# Agent Configuration
RESEARCH_AGENT_NAME = "ResearchAgent"
STRATEGY_AGENT_NAME = "StrategyAgent"
CONTENT_GENERATOR_AGENT_NAME = "ContentGeneratorAgent"
REVIEW_AGENT_NAME = "ReviewAgent"
ROOT_AGENT_NAME = "ScientificContentAgent"

# Content Configuration
SUPPORTED_PLATFORMS = ["blog", "linkedin", "twitter"]
MAX_PAPERS_PER_SEARCH = 5
CITATION_STYLE = "apa"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "agent.log"
