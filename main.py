"""Main CLI and async runner for the Research-to-Brand Multi-LLM Agent System v2."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import shutil
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.genai import types

from src.agents import create_content_generation_pipeline
from src.channels import get_channel_plugin
from src.config import (
    DEFAULT_CHANNELS,
    DEFAULT_OUTPUT_DIR,
    EDITORIAL_CRITIC_AGENT_NAME,
    FACT_CHECKER_AGENT_NAME,
    GOOGLE_API_KEY,
    LINKEDIN_AGENT_NAME,
    LOG_FILE,
    LOG_LEVEL,
    NEWSLETTER_AGENT_NAME,
    OUTLINE_AGENT_NAME,
    PERSONAL_CONTEXT_AGENT_NAME,
    REFINER_AGENT_NAME,
    RESEARCH_AGENT_NAME,
    VISUAL_AGENT_NAME,
    X_AGENT_NAME,
    YOUTUBE_AGENT_NAME,
)
from src.exporter import export_content_bundle
from src.ingestion import ingest_materials
from src.knowledge_base import init_knowledge_base
from src.llm_router import ModelRouter
from src.profile import (
    DEFAULT_PROFILE,
    PROFILE_DIR,
    PROFILE_PATH,
    load_user_profile,
    save_profile_to_yaml,
)
from src.profile_editor import edit_profile_interactive, validate_after_edit
from src.session_manager import delete_session, format_session_list, list_sessions

STAGE_PROGRESS_MAP: dict[str, tuple[float, str]] = {
    OUTLINE_AGENT_NAME: (0.12, "Stage 1/4: Planning angle, biblio queries & visual blueprint..."),
    RESEARCH_AGENT_NAME: (
        0.28,
        "Stage 2/4: Searching & verifying papers (Semantic Scholar + arXiv)...",
    ),
    PERSONAL_CONTEXT_AGENT_NAME: (
        0.34,
        "Stage 2/4: Retrieving personal case studies & Voice DNA...",
    ),
    VISUAL_AGENT_NAME: (
        0.42,
        "Stage 2/4: Rendering charts, architecture diagrams & demo overlays...",
    ),
    LINKEDIN_AGENT_NAME: (0.58, "Stage 3/4: Drafting native LinkedIn post & carousel slides..."),
    X_AGENT_NAME: (0.64, "Stage 3/4: Drafting X thread, standalone posts & video storyboard..."),
    YOUTUBE_AGENT_NAME: (
        0.70,
        "Stage 3/4: Drafting YouTube long script, 60s Short & demo shotlist...",
    ),
    NEWSLETTER_AGENT_NAME: (0.74, "Stage 3/4: Drafting deep-dive newsletter edition..."),
    FACT_CHECKER_AGENT_NAME: (0.82, "Stage 4/4: Running scientific fact-checker audit..."),
    EDITORIAL_CRITIC_AGENT_NAME: (
        0.88,
        "Stage 4/4: Running anti-AI-slop & deterministic format linter...",
    ),
    REFINER_AGENT_NAME: (
        0.94,
        "Stage 4/4: Refining content & rendering PDF carousel / MP4 videos...",
    ),
}


async def run_content_generation(
    topic: str,
    preferences: dict[str, Any] | None = None,
    session_id: str | None = None,
    human_seed: str = "",
    input_paths: list[Path] | None = None,
    model_overrides: dict[str, str] | None = None,
    on_progress: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """Run the v2 hybrid multi-LLM pipeline and export a ready-to-post bundle.

    Args:
        topic: Research or industry topic.
        preferences: Optional dict with ``channels`` (or ``platforms``), ``language``,
            ``tone``, ``target_audience``.
        session_id: Optional session ID to resume.
        human_seed: Author's personal angle, bullet points, or contrarian opinion.
        input_paths: Optional PaperOrchestra raw material paths (.tex, .bib, .ipynb, .pdf, .json, .csv).
        model_overrides: Optional per-role LLM overrides passed to ``ModelRouter``.
        on_progress: Optional callback ``(fraction: float, message: str)`` invoked on ADK events.

    Returns:
        Dictionary with ``final_content``, ``bundle_dir``, ``zip_path``, ``files``,
        ``sections``, ``routing_table``, and ``session_id``.
    """
    api_key = os.getenv("GOOGLE_API_KEY") or GOOGLE_API_KEY
    if not api_key or api_key.startswith("your_"):
        raise ValueError(
            "GOOGLE_API_KEY not found. Set it in .env (required for research, ingestion & fallback).\n"
            "Get your key at: https://aistudio.google.com/app/api_keys"
        )
    os.environ["GOOGLE_API_KEY"] = api_key

    prefs = preferences or {}
    raw_channels = prefs.get("channels") or prefs.get("platforms") or DEFAULT_CHANNELS
    channels = list(dict.fromkeys(get_channel_plugin(c).key for c in raw_channels))
    language = str(prefs.get("language", "fr")).lower()

    if on_progress:
        on_progress(0.03, "Loading profile & ingesting raw materials...")

    profile = load_user_profile(validate=False)
    material_bundle = ingest_materials(
        input_paths=input_paths,
        topic=topic,
        human_seed=human_seed,
    )
    resolved_topic = material_bundle.topic

    # Clean transient asset workspace before run
    tmp_assets_dir = DEFAULT_OUTPUT_DIR / "tmp_assets"
    if tmp_assets_dir.exists():
        shutil.rmtree(tmp_assets_dir, ignore_errors=True)
    tmp_assets_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging (LOG_FILE is a Path)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(LOG_FILE)],
    )

    router = ModelRouter(overrides=model_overrides)
    routing_table = router.get_active_routing_table()
    agent = create_content_generation_pipeline(
        channels=channels,
        model_overrides=model_overrides,
    )

    # Persistent async SQLite session store (graceful fallback if sqlalchemy[asyncio]/greenlet missing)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite+aiosqlite:///{PROFILE_DIR / 'sessions.db'}"
    try:
        session_service: Any = DatabaseSessionService(db_url=db_url)
    except Exception as exc:
        logging.warning(
            "DatabaseSessionService unavailable (%s); falling back to InMemorySessionService.", exc
        )
        session_service = InMemorySessionService()

    app_name = "scientific-content-agent"
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service,
        plugins=[LoggingPlugin()],
    )

    active_session_id = session_id or str(uuid.uuid4())
    with contextlib.suppress(Exception):
        await session_service.create_session(
            app_name=app_name,
            user_id=profile.name,
            session_id=active_session_id,
        )

    lang_label = {
        "fr": "French (FR)",
        "en": "English (EN)",
        "both": "French (LinkedIn/YouTube) and English (X)",
    }.get(language, language)

    user_message = f"""Generate a publication-ready multi-channel research-to-brand bundle.

TARGET CHANNELS: {", ".join(channels)}
TARGET LANGUAGE: {lang_label}
TARGET AUDIENCE: {prefs.get("target_audience", ", ".join(profile.target_personas))}
TONE: {prefs.get("tone", profile.content_tone)}

=== AUTHOR PROFILE ===
{profile.get_profile_summary()}

=== INGESTED RAW MATERIALS & HUMAN SEED ===
{material_bundle.to_prompt_context()}
"""

    if on_progress:
        on_progress(0.08, f"Launching hybrid ADK pipeline ({', '.join(channels)})...")

    final_content = ""
    seen_agents: set[str] = set()
    query = types.Content(role="user", parts=[types.Part(text=user_message)])

    async for event in runner.run_async(
        user_id=profile.name,
        session_id=active_session_id,
        new_message=query,
    ):
        author = getattr(event, "author", None)
        if author and author in STAGE_PROGRESS_MAP and author not in seen_agents:
            seen_agents.add(author)
            frac, desc = STAGE_PROGRESS_MAP[author]
            print(f"  -> {desc}")
            if on_progress:
                on_progress(frac, desc)

        if (
            event.actions
            and event.actions.state_delta
            and "final_content" in event.actions.state_delta
        ):
            final_content = str(event.actions.state_delta["final_content"])

    if not final_content:
        final_content = "No content generated. Please check logs/agent.log for details."

    if on_progress:
        on_progress(0.97, "Exporting ready-to-post bundle & ZIP archive...")

    exported = export_content_bundle(
        topic=resolved_topic,
        final_content=final_content,
        channels=channels,
        language=language,
        routing_table=routing_table,
        tmp_assets_dir=tmp_assets_dir,
    )

    if on_progress:
        on_progress(1.0, f"Done! Bundle exported to {exported['bundle_dir']}")

    return {
        "final_content": final_content,
        "session_id": active_session_id,
        "routing_table": routing_table,
        "bundle_dir": exported["bundle_dir"],
        "zip_path": exported["zip_path"],
        "files": exported["files"],
        "sections": exported["sections"],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Research-to-Brand Multi-LLM Agent System v2 (LinkedIn, X, YouTube)"
    )
    parser.add_argument(
        "--init-profile", action="store_true", help="Initialize default profile.yaml"
    )
    parser.add_argument("--validate-profile", action="store_true", help="Validate current profile")
    parser.add_argument("--edit-profile", action="store_true", help="Edit profile in $EDITOR")
    parser.add_argument(
        "--init-knowledge", action="store_true", help="Initialize local knowledge/ folder"
    )
    parser.add_argument("--models", action="store_true", help="Show active Multi-LLM routing table")
    parser.add_argument("--list-sessions", action="store_true", help="List saved ADK sessions")
    parser.add_argument("--delete-session", type=str, metavar="SESSION_ID", help="Delete a session")
    parser.add_argument(
        "--topic",
        type=str,
        default="Agentic MFA & Ad Fraud Detection at Scale",
        help="Main topic or research angle",
    )
    parser.add_argument(
        "--seed", type=str, default="", help="Human seed / personal contrarian angle"
    )
    parser.add_argument(
        "--seed-file", type=str, default="", help="Path to text/markdown file with human seed"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="",
        help="Directory of PaperOrchestra raw materials (.tex, .bib, .ipynb, .pdf, .json, .csv)",
    )
    parser.add_argument(
        "--input-files",
        nargs="*",
        default=[],
        help="Individual raw material files to ingest",
    )
    parser.add_argument(
        "--channels",
        type=str,
        default=",".join(DEFAULT_CHANNELS),
        help="Comma-separated channels: linkedin,x,youtube[,newsletter]",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="fr",
        choices=["fr", "en", "both"],
        help="Target language (fr, en, or both)",
    )
    parser.add_argument("--session-id", type=str, help="Resume an existing session ID")
    return parser


async def main() -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.models:
        print(ModelRouter().format_routing_summary())
        return

    if args.init_knowledge:
        dest = init_knowledge_base()
        print(f"Knowledge base initialized at: {dest}")
        return

    if args.init_profile:
        if PROFILE_PATH.exists():
            print(f"Profile already exists at {PROFILE_PATH}")
        else:
            save_profile_to_yaml(DEFAULT_PROFILE, PROFILE_PATH)
            print(f"Created default profile at {PROFILE_PATH}")
        return

    if args.validate_profile:
        try:
            profile = load_user_profile(validate=True)
            print(f"Profile valid: {profile.name} ({profile.target_role})")
        except ValueError as exc:
            print(f"Profile validation failed: {exc}")
        return

    if args.edit_profile:
        if not PROFILE_PATH.exists():
            save_profile_to_yaml(DEFAULT_PROFILE, PROFILE_PATH)
        if edit_profile_interactive():
            validate_after_edit()
        return

    if args.list_sessions:
        sessions = list_sessions()
        print(format_session_list(sessions) if sessions else "No sessions found.")
        return

    if args.delete_session:
        res = delete_session(args.delete_session)
        print(res["message"])
        return

    human_seed = args.seed
    if args.seed_file and Path(args.seed_file).exists():
        human_seed = (
            human_seed + "\n\n" + Path(args.seed_file).read_text(encoding="utf-8")
        ).strip()

    input_paths: list[Path] = [Path(p) for p in args.input_files]
    if args.input_dir:
        input_paths.append(Path(args.input_dir))

    channels = [c.strip() for c in args.channels.split(",") if c.strip()]

    print("=" * 80)
    print("RESEARCH-TO-BRAND MULTI-LLM AGENT SYSTEM v2")
    print("=" * 80)
    print(ModelRouter().format_routing_summary())
    print(f"\nTopic    : {args.topic}")
    print(f"Channels : {', '.join(channels)} | Language: {args.lang}")
    if input_paths:
        print(f"Inputs   : {', '.join(str(p) for p in input_paths)}")
    print("-" * 80)

    result = await run_content_generation(
        topic=args.topic,
        preferences={"channels": channels, "language": args.lang},
        session_id=args.session_id,
        human_seed=human_seed,
        input_paths=input_paths,
    )

    print("\n" + "=" * 80)
    print(f"Bundle exported : {result['bundle_dir']}")
    print(f"Downloadable ZIP: {result['zip_path']}")
    print(f"Session ID      : {result['session_id']}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
