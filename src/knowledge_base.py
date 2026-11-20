"""Personal Knowledge Base loader and lightweight lexical retrieval (Voice DNA & Case Studies).

Loads private personal branding knowledge from:
1. ``<repo>/knowledge/`` (gitignored)
2. ``~/.agentic-content-generation/knowledge/``
3. Fallback: ``<repo>/knowledge.example/`` (generic templates tracked in git)
"""

import logging
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from .config import PROJECT_ROOT
from .profile import DEFAULT_BANNED_PHRASES, PROFILE_DIR

logger = logging.getLogger(__name__)

LOCAL_KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
HOME_KNOWLEDGE_DIR = PROFILE_DIR / "knowledge"
EXAMPLE_KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge.example"


def resolve_knowledge_dir(custom_dir: Path | None = None) -> Path:
    """Find the active personal knowledge base directory."""
    if custom_dir and custom_dir.exists():
        return custom_dir
    if LOCAL_KNOWLEDGE_DIR.exists():
        return LOCAL_KNOWLEDGE_DIR
    if HOME_KNOWLEDGE_DIR.exists():
        return HOME_KNOWLEDGE_DIR
    return EXAMPLE_KNOWLEDGE_DIR


def init_knowledge_base(target_dir: Path | None = None) -> Path:
    """Initialize a personal knowledge base directory from knowledge.example/."""
    dest = target_dir or LOCAL_KNOWLEDGE_DIR
    dest.mkdir(parents=True, exist_ok=True)
    if EXAMPLE_KNOWLEDGE_DIR.exists():
        for src_file in EXAMPLE_KNOWLEDGE_DIR.iterdir():
            dst_file = dest / src_file.name
            if src_file.is_file() and not dst_file.exists():
                shutil.copy2(src_file, dst_file)
    return dest


def load_case_studies(knowledge_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load verified personal case studies and quantified achievements."""
    kb_dir = resolve_knowledge_dir(knowledge_dir)
    path = kb_dir / "case_studies.yaml"
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            return list(data.get("case_studies", []))
        if isinstance(data, list):
            return data
    except Exception:
        return []
    return []


def load_voice_dna(knowledge_dir: Path | None = None) -> str:
    """Load personal voice DNA & writing style rules."""
    kb_dir = resolve_knowledge_dir(knowledge_dir)
    path = kb_dir / "voice_dna.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def load_banned_phrases(knowledge_dir: Path | None = None) -> list[str]:
    """Load anti-AI-slop banned phrases list."""
    kb_dir = resolve_knowledge_dir(knowledge_dir)
    path = kb_dir / "banned_phrases.yaml"
    phrases = list(DEFAULT_BANNED_PHRASES)
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            custom = data.get("banned_phrases", []) if isinstance(data, dict) else data
            if isinstance(custom, list):
                phrases.extend(str(p).strip().lower() for p in custom if str(p).strip())
        except Exception as exc:
            logger.warning("Failed to load banned phrases from %s: %s", path, exc)
    # Deduplicate preserving order
    return list(dict.fromkeys(p.lower() for p in phrases))


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9À-ÿ]{3,}", text.lower()))


def retrieve_personal_evidence(
    topic: str,
    max_items: int = 3,
) -> dict[str, Any]:
    """Retrieve the most relevant real case studies and quantified metrics for a topic.

    Use this tool to anchor posts, threads, and YouTube scripts in verified
    first-hand production achievements instead of generic LLM commentary.

    Security: Always reads exclusively from the configured personal knowledge base
    directory (cannot be redirected by LLM tool arguments).

    Args:
        topic: Research or industry topic to match against personal case studies.
        max_items: Maximum number of matching case studies to return (default: 3).

    Returns:
        Dictionary with status, matched case_studies, and count.
    """
    max_items = max(1, min(int(max_items), 10))
    cases = load_case_studies()
    if not cases:
        return {
            "status": "success",
            "case_studies": [],
            "count": 0,
            "note": "No case studies found in personal knowledge base.",
        }

    query_tokens = _tokenize(topic)
    scored: list[tuple[int, dict[str, Any]]] = []
    for case in cases:
        blob = " ".join(
            [
                str(case.get("title", "")),
                str(case.get("domain", "")),
                " ".join(case.get("tags", [])),
                str(case.get("summary", "")),
                " ".join(case.get("metrics", [])),
            ]
        )
        overlap = len(query_tokens & _tokenize(blob))
        scored.append((overlap, case))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    selected = [case for _, case in scored[:max_items]]

    return {
        "status": "success",
        "case_studies": selected,
        "count": len(selected),
    }


def get_voice_and_style_guide(
    language: str = "fr",
) -> dict[str, Any]:
    """Return the author's Voice DNA, channel rules, and anti-AI-slop banned phrases.

    Security: Always reads exclusively from the configured personal knowledge base
    directory (cannot be redirected by LLM tool arguments).

    Args:
        language: Target content language ("fr", "en", or "both").

    Returns:
        Dictionary with voice_dna markdown, banned_phrases list, and platform formatting rules.
    """
    voice_dna = load_voice_dna()
    banned = load_banned_phrases()

    return {
        "status": "success",
        "language": language,
        "voice_dna": voice_dna,
        "banned_phrases": banned,
        "platform_rules": {
            "linkedin": [
                "Plain text ONLY: NEVER use Markdown bold (**text**), headers (###), or code fences.",
                "First 2 lines must be a concrete hook before the 'See more' fold.",
                "Short paragraphs (1-2 sentences) with blank lines for mobile readability.",
                "Zero placeholders like [mention project] or [insert metric].",
                "Maximum 3-4 relevant hashtags at the very end, never inline.",
            ],
            "x": [
                "Every single tweet MUST be strictly <= 280 characters.",
                "Lead tweet (1/N) must deliver a contrarian insight or concrete number.",
                "No fluff, no 'Thread incoming!' filler without substance.",
            ],
            "youtube": [
                "First 30 seconds: state the concrete problem, real cost/impact, and what viewer will learn.",
                "Insert explicit visual cues like [VISUAL #1: chart/diagram] tied to generated assets.",
                "Include both a 6-10 min script and a punchy 45-60s YouTube Short / X Demo script.",
            ],
        },
    }
