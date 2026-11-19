"""Configuration for the Scientific Content Generation Agent v2."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google.genai import types

# Load environment variables from .env if present
load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")

# Default Gemini Models (replaces deprecated gemini-2.0-flash-exp)
DEFAULT_PRO_MODEL = os.getenv("DEFAULT_PRO_MODEL", "gemini-2.5-pro")
DEFAULT_FLASH_MODEL = os.getenv("DEFAULT_FLASH_MODEL", "gemini-2.5-flash")
DEFAULT_MODEL = DEFAULT_PRO_MODEL

# Preferred Multi-LLM routing table per role (ordered by preference; auto-fallback to Gemini)
ROLE_MODEL_PREFERENCES: dict[str, list[str]] = {
    "outline": [DEFAULT_PRO_MODEL],
    "research": [DEFAULT_FLASH_MODEL, DEFAULT_PRO_MODEL],
    "personal_context": [DEFAULT_FLASH_MODEL, DEFAULT_PRO_MODEL],
    "visual": [DEFAULT_PRO_MODEL],
    "linkedin": [
        "anthropic/claude-sonnet-4-5-20250929",
        "openai/gpt-4.1",
        DEFAULT_PRO_MODEL,
    ],
    "x": [
        "xai/grok-3",
        "openai/gpt-4.1",
        "anthropic/claude-sonnet-4-5-20250929",
        DEFAULT_PRO_MODEL,
    ],
    "youtube": [
        "anthropic/claude-sonnet-4-5-20250929",
        "openai/gpt-4.1",
        DEFAULT_PRO_MODEL,
    ],
    "newsletter": [
        "anthropic/claude-sonnet-4-5-20250929",
        DEFAULT_PRO_MODEL,
    ],
    "fact_checker": [DEFAULT_PRO_MODEL],
    "editorial_critic": [
        "openai/gpt-4.1",
        DEFAULT_PRO_MODEL,
        "anthropic/claude-sonnet-4-5-20250929",
    ],
    "refiner": [
        "anthropic/claude-sonnet-4-5-20250929",
        DEFAULT_PRO_MODEL,
    ],
}

# Retry configuration for transient API failures
RETRY_CONFIG = types.HttpRetryOptions(
    attempts=5,
    exp_base=4,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Agent Names
OUTLINE_AGENT_NAME = "OutlineBlueprintAgent"
RESEARCH_AGENT_NAME = "HybridLiteratureAgent"
PERSONAL_CONTEXT_AGENT_NAME = "PersonalEvidenceAgent"
VISUAL_AGENT_NAME = "VisualAssetAgent"
LINKEDIN_AGENT_NAME = "LinkedInWriterAgent"
X_AGENT_NAME = "XThreadWriterAgent"
YOUTUBE_AGENT_NAME = "YouTubeWriterAgent"
NEWSLETTER_AGENT_NAME = "NewsletterWriterAgent"
FACT_CHECKER_AGENT_NAME = "FactCheckerCritic"
EDITORIAL_CRITIC_AGENT_NAME = "EditorialAntiSlopCritic"
REFINER_AGENT_NAME = "ContentRefinerAgent"
ROOT_AGENT_NAME = "ResearchToBrandPipeline"

# Content Configuration
SUPPORTED_PLATFORMS = ["linkedin", "x", "youtube", "newsletter"]
DEFAULT_CHANNELS = ["linkedin", "x", "youtube"]
MAX_PAPERS_PER_SEARCH = 5
CITATION_STYLE = "bibtex"
MAX_REFINEMENT_ITERATIONS = 3
QUALITY_PASS_THRESHOLD = 85

# Paths & Logging (fixed: Path instead of str)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path(os.getenv("LOG_FILE", "logs/agent.log"))
