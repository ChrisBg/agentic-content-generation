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
DEFAULT_MODEL = "gemini-2.0-flash-exp"

# Retry configuration for transient failures
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
