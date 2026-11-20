"""Gradio UI v2 for the Research-to-Brand Multi-LLM Agent System (LinkedIn, X, YouTube)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import gradio as gr
import pandas as pd

from main import run_content_generation
from src.config import DEFAULT_OUTPUT_DIR, ROLE_MODEL_PREFERENCES
from src.exporter import zip_bundle
from src.knowledge_base import (
    init_knowledge_base,
    load_case_studies,
    load_voice_dna,
    resolve_knowledge_dir,
)
from src.llm_router import ModelRouter
from src.profile import (
    DEFAULT_PROFILE,
    PROFILE_PATH,
    UserProfile,
    load_user_profile,
    save_profile_to_yaml,
)
from src.security import get_safe_output_root, resolve_safe_path
from src.session_manager import delete_session, list_sessions

logger = logging.getLogger(__name__)


def _routing_dataframe(overrides: dict[str, str] | None = None) -> pd.DataFrame:
    router = ModelRouter(overrides=overrides)
    rows = []
    for role, info in router.get_active_routing_table().items():
        rows.append(
            {
                "Role": role,
                "Provider": info["provider"],
                "Active Model": info["model"],
                "Status": "Fallback" if info["is_fallback"] else info["reason"],
            }
        )
    return pd.DataFrame(rows)


def _provider_status_markdown() -> str:
    status = ModelRouter().get_provider_status()
    badges = [
        f"- **{k.upper()}**: {'Configured' if v else 'Not set (auto-fallback to Gemini)'}"
        for k, v in status.items()
    ]
    return "### API Providers Status\n" + "\n".join(badges)


def _list_exported_bundles() -> pd.DataFrame:
    if not DEFAULT_OUTPUT_DIR.exists():
        return pd.DataFrame(columns=["Bundle", "Topic", "Channels", "Language", "ZIP"])
    rows = []
    for meta_file in sorted(DEFAULT_OUTPUT_DIR.glob("*/bundle.json"), reverse=True)[:30]:
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            bundle_dir = meta_file.parent
            zip_file = bundle_dir.parent / f"{bundle_dir.name}.zip"
            rows.append(
                {
                    "Bundle": bundle_dir.name,
                    "Topic": meta.get("topic", ""),
                    "Channels": ", ".join(meta.get("channels", [])),
                    "Language": meta.get("language", ""),
                    "ZIP": str(zip_file) if zip_file.exists() else "",
                }
            )
        except Exception as exc:
            logger.warning("Skipping unreadable bundle metadata %s: %s", meta_file, exc)
            continue
    if not rows:
        return pd.DataFrame(columns=["Bundle", "Topic", "Channels", "Language", "ZIP"])
    return pd.DataFrame(rows)


def _format_exception(exc: BaseException) -> str:
    """Unpack Python 3.11+ ExceptionGroup / TaskGroup errors into readable root causes."""
    if isinstance(exc, BaseExceptionGroup):
        sub_msgs = [_format_exception(sub) for sub in exc.exceptions]
        return "; ".join(sub_msgs)
    return f"{type(exc).__name__}: {exc}"


async def generate_studio_bundle(
    topic: str,
    human_seed: str,
    uploaded_files: list[str] | None,
    channels_ui: list[str],
    language: str,
    session_id: str,
    override_linkedin: str,
    override_x: str,
    override_youtube: str,
    override_critic: str,
    progress: gr.Progress = gr.Progress(),  # noqa: B008
) -> tuple[Any, ...]:
    """Run the ADK v2 pipeline with real-time event progress and populate human review tabs."""
    if not topic or not topic.strip():
        return (
            "Please enter a topic (or upload PaperOrchestra materials with a topic).",
            "",
            "",
            "",
            "",
            "",
            [],
            None,
            None,
            None,
            None,
            "",
        )

    channel_map = {
        "LinkedIn": "linkedin",
        "X (Twitter)": "x",
        "YouTube": "youtube",
        "Newsletter": "newsletter",
    }
    selected_channels = [channel_map[c] for c in channels_ui if c in channel_map]
    if not selected_channels:
        selected_channels = ["linkedin", "x", "youtube"]

    overrides = {
        k: v.strip()
        for k, v in {
            "linkedin": override_linkedin or "",
            "x": override_x or "",
            "youtube": override_youtube or "",
            "editorial_critic": override_critic or "",
        }.items()
        if v and v.strip()
    }

    input_paths = [Path(f) for f in (uploaded_files or []) if f]

    def _progress_cb(frac: float, msg: str) -> None:
        progress(frac, desc=msg)

    try:
        result = await run_content_generation(
            topic=topic.strip(),
            preferences={"channels": selected_channels, "language": language},
            session_id=session_id.strip() or None,
            human_seed=human_seed or "",
            input_paths=input_paths,
            model_overrides=overrides or None,
            on_progress=_progress_cb,
        )
    except Exception as exc:
        logger.exception("Content generation failed")
        return (
            f"Generation failed: {_format_exception(exc)}",
            "",
            "",
            "",
            "",
            "",
            [],
            None,
            None,
            None,
            None,
            "",
        )

    sections = result.get("sections", {})
    files = result.get("files", {})

    linkedin_txt = sections.get("linkedin", "")
    x_txt = "\n\n---\n\n".join(
        p for p in [sections.get("x_thread", ""), sections.get("x_standalone", "")] if p
    )
    youtube_txt = sections.get("youtube", "")
    bibtex_txt = sections.get("bibtex", "")
    quality_txt = sections.get("quality_report", "") or sections.get("raw_output", "")

    figures = [p for p in files.get("figures", []) if p.endswith(".png") and Path(p).exists()]
    carousel_pdf = files.get("linkedin_carousel_pdf")
    videos = [p for p in files.get("videos", []) if p.endswith(".mp4") and Path(p).exists()]
    video_16x9 = next((v for v in videos if "16x9" in Path(v).name), videos[0] if videos else None)
    video_9x16 = next((v for v in videos if "9x16" in Path(v).name), None)

    status_msg = (
        f"Bundle ready!\n"
        f"- Directory: {result['bundle_dir']}\n"
        f"- Session ID: {result['session_id']}\n"
        f"- Figures: {len(figures)} | Videos: {len(videos)}"
    )

    return (
        status_msg,
        linkedin_txt,
        x_txt,
        youtube_txt,
        bibtex_txt,
        quality_txt,
        figures,
        carousel_pdf,
        video_16x9,
        video_9x16,
        result.get("zip_path"),
        result.get("bundle_dir", ""),
    )


def save_human_edits(
    bundle_dir_str: str,
    linkedin_text: str,
    x_text: str,
    youtube_text: str,
) -> tuple[str, str | None]:
    """Persist human edits inside the sandboxed output directory and refresh the ZIP archive."""
    if not bundle_dir_str:
        return "No active bundle directory to save.", None

    try:
        bundle_dir = resolve_safe_path(bundle_dir_str, get_safe_output_root(), must_exist=True)
    except (PermissionError, ValueError, FileNotFoundError) as exc:
        return f"Blocked invalid bundle path: {exc}", None

    if linkedin_text.strip():
        (bundle_dir / "linkedin_post.txt").write_text(
            linkedin_text.strip() + "\n", encoding="utf-8"
        )
    if x_text.strip():
        (bundle_dir / "x_thread.md").write_text(x_text.strip() + "\n", encoding="utf-8")
    if youtube_text.strip():
        (bundle_dir / "youtube_package.md").write_text(
            youtube_text.strip() + "\n", encoding="utf-8"
        )

    new_zip = zip_bundle(bundle_dir)
    return f"Human edits saved and ZIP refreshed: {new_zip.name}", str(new_zip)


def save_voice_dna_ui(voice_text: str) -> str:
    """Save edited Voice DNA markdown to local knowledge/voice_dna.md."""
    kb_dir = init_knowledge_base()
    (kb_dir / "voice_dna.md").write_text(voice_text, encoding="utf-8")
    return f"Saved Voice DNA to {kb_dir / 'voice_dna.md'}"


def load_profile_fields() -> tuple[Any, ...]:
    profile = load_user_profile(validate=False)
    return (
        profile.name,
        profile.target_role,
        ", ".join(profile.expertise_areas),
        "\n".join(profile.editorial_pillars),
        ", ".join(profile.target_personas),
        "\n".join(profile.business_offers),
        profile.unique_value_proposition,
        profile.linkedin_url,
        profile.github_username,
        profile.x_handle,
        profile.youtube_channel,
        load_voice_dna(),
        json.dumps(load_case_studies(), indent=2, ensure_ascii=False),
    )


def save_profile_fields(
    name: str,
    role: str,
    expertise: str,
    pillars: str,
    personas: str,
    offers: str,
    uvp: str,
    linkedin: str,
    github: str,
    x_handle: str,
    youtube: str,
) -> str:
    current = load_user_profile(validate=False)
    updated = UserProfile(
        name=name.strip() or DEFAULT_PROFILE.name,
        target_role=role.strip() or DEFAULT_PROFILE.target_role,
        expertise_areas=[x.strip() for x in expertise.split(",") if x.strip()],
        editorial_pillars=[x.strip() for x in pillars.splitlines() if x.strip()],
        target_personas=[x.strip() for x in personas.split(",") if x.strip()],
        business_offers=[x.strip() for x in offers.splitlines() if x.strip()],
        unique_value_proposition=uvp.strip(),
        linkedin_url=linkedin.strip(),
        github_username=github.strip(),
        x_handle=x_handle.strip(),
        youtube_channel=youtube.strip(),
        notable_projects=current.notable_projects,
        primary_skills=current.primary_skills,
        banned_phrases=current.banned_phrases,
    )
    validation = updated.validate()
    if validation["errors"]:
        return "Validation errors:\n" + "\n".join(validation["errors"])
    save_profile_to_yaml(updated, PROFILE_PATH)
    return f"Profile saved to {PROFILE_PATH}"


def list_sessions_df() -> pd.DataFrame:
    sessions = list_sessions()
    if not sessions:
        return pd.DataFrame(columns=["Session ID", "User", "Messages", "Updated"])
    return pd.DataFrame(
        [
            {
                "Session ID": s["session_id"],
                "User": s.get("user_id", ""),
                "Messages": s.get("message_count", 0),
                "Updated": s.get("updated_at", ""),
            }
            for s in sessions
        ]
    )


def delete_session_ui(session_id: str) -> tuple[pd.DataFrame, str]:
    if not session_id.strip():
        return list_sessions_df(), "Enter a Session ID to delete."
    res = delete_session(session_id.strip())
    return list_sessions_df(), res["message"]


def create_ui() -> gr.Blocks:
    """Build the Gradio v2 web studio."""
    with gr.Blocks(title="Research-to-Brand Multi-LLM Studio v2") as app:
        gr.Markdown(
            """
# Research-to-Brand Multi-LLM Studio v2
*PaperOrchestra Ingestion + Semantic Scholar Verification + Multi-LLM Channel Writers (LinkedIn, X, YouTube) + Anti-AI-Slop Loop*
"""
        )

        active_bundle_dir = gr.State("")

        with gr.Tabs():
            # ===== TAB 1: CONTENT STUDIO =====
            with gr.Tab("Content Studio"), gr.Row():
                with gr.Column(scale=1):
                    topic_in = gr.Textbox(
                        label="Topic / Research Subject",
                        placeholder="e.g. Agentic MFA & Ad Fraud Detection under 0.001 EUR/page",
                        lines=2,
                    )
                    seed_in = gr.Textbox(
                        label="Human Seed (Your contrarian take / production experience)",
                        placeholder="Write 2-3 bullet points of your real opinion so the content never reads like generic AI...",
                        lines=4,
                    )
                    files_in = gr.File(
                        label="PaperOrchestra Raw Materials (.tex, .bib, .ipynb, .pdf, .json, .csv, .md)",
                        file_count="multiple",
                        type="filepath",
                    )
                    channels_in = gr.CheckboxGroup(
                        choices=["LinkedIn", "X (Twitter)", "YouTube", "Newsletter"],
                        value=["LinkedIn", "X (Twitter)", "YouTube"],
                        label="Target Channels",
                    )
                    with gr.Row():
                        lang_in = gr.Radio(
                            choices=["fr", "en", "both"],
                            value="fr",
                            label="Language",
                        )
                        session_in = gr.Textbox(
                            label="Resume Session ID (optional)",
                            placeholder="Leave empty for new session",
                        )
                    generate_btn = gr.Button(
                        "Generate Multi-Channel Bundle", variant="primary", size="lg"
                    )
                    status_box = gr.Textbox(label="Pipeline Status", lines=4, interactive=False)
                    zip_out = gr.File(label="Download Ready-to-Post Pack (.zip)")

                with gr.Column(scale=2):
                    with gr.Tabs():
                        with gr.Tab("LinkedIn"):
                            li_text = gr.Textbox(
                                label="Native LinkedIn Post (Plain Text — Editable)",
                                lines=18,
                            )
                            li_gallery = gr.Gallery(
                                label="Generated Charts & Architecture Diagrams (PNG)",
                                columns=2,
                                height="auto",
                            )
                            li_pdf = gr.File(label="LinkedIn Carousel PDF (4:5)")

                        with gr.Tab("X (Twitter)"):
                            x_text = gr.Textbox(
                                label="X Thread & Standalone Posts (Editable)",
                                lines=18,
                            )
                            x_video = gr.Video(label="Short Explainer / Demo Video (16:9 for X)")

                        with gr.Tab("YouTube"):
                            yt_text = gr.Textbox(
                                label="YouTube Package (Titles, Thumbnails, Long Script, 60s Short, Live Demo Shotlist)",
                                lines=20,
                            )
                            yt_short_video = gr.Video(
                                label="YouTube Short / LinkedIn Vertical Video (9:16)"
                            )

                        with gr.Tab("Sources & Quality Gate"):
                            bib_text = gr.Code(
                                label="Verified BibTeX References", language="markdown", lines=10
                            )
                            qual_text = gr.Markdown(label="Fact-Check & Anti-AI-Slop Report")

                    save_edits_btn = gr.Button("Save Human Edits & Refresh ZIP")
                    edit_status = gr.Textbox(label="Save Status", lines=1, interactive=False)

            # ===== TAB 2: MULTI-LLM ROUTING =====
            with gr.Tab("Multi-LLM Routing"):
                gr.Markdown(_provider_status_markdown())
                routing_table_df = gr.Dataframe(
                    value=_routing_dataframe(),
                    label="Active Model Assignment per Pipeline Role",
                    interactive=False,
                )
                gr.Markdown(
                    "#### Optional Runtime Model Overrides (leave blank for automatic routing)"
                )
                with gr.Row():
                    ov_linkedin = gr.Textbox(
                        label="LinkedIn Writer Model",
                        placeholder=ROLE_MODEL_PREFERENCES["linkedin"][0],
                    )
                    ov_x = gr.Textbox(
                        label="X Writer Model",
                        placeholder=ROLE_MODEL_PREFERENCES["x"][0],
                    )
                with gr.Row():
                    ov_youtube = gr.Textbox(
                        label="YouTube Writer Model",
                        placeholder=ROLE_MODEL_PREFERENCES["youtube"][0],
                    )
                    ov_critic = gr.Textbox(
                        label="Editorial Critic Model",
                        placeholder=ROLE_MODEL_PREFERENCES["editorial_critic"][0],
                    )
                refresh_routing_btn = gr.Button("Preview Routing With Overrides")

                def _preview_routing(li: str, x: str, yt: str, cr: str) -> pd.DataFrame:
                    return _routing_dataframe(
                        {"linkedin": li, "x": x, "youtube": yt, "editorial_critic": cr}
                    )

                refresh_routing_btn.click(
                    fn=_preview_routing,
                    inputs=[ov_linkedin, ov_x, ov_youtube, ov_critic],
                    outputs=routing_table_df,
                )

            # ===== TAB 3: PROFILE & KNOWLEDGE BASE =====
            with gr.Tab("Profile & Knowledge Base"):
                gr.Markdown(f"Active Knowledge Base directory: `{resolve_knowledge_dir()}`")
                with gr.Row():
                    with gr.Column():
                        p_name = gr.Textbox(label="Name")
                        p_role = gr.Textbox(label="B2B / R&D Positioning")
                        p_expertise = gr.Textbox(label="Expertise Areas (comma-separated)")
                        p_pillars = gr.Textbox(label="Editorial Pillars (one per line)", lines=3)
                        p_personas = gr.Textbox(label="Target B2B Personas (comma-separated)")
                        p_offers = gr.Textbox(
                            label="Business Offers / CIR-CII Positioning (one per line)", lines=3
                        )
                        p_uvp = gr.Textbox(label="Unique Value Proposition", lines=2)
                        with gr.Row():
                            p_linkedin = gr.Textbox(label="LinkedIn URL")
                            p_github = gr.Textbox(label="GitHub Username")
                        with gr.Row():
                            p_x = gr.Textbox(label="X Handle")
                            p_youtube = gr.Textbox(label="YouTube Channel")
                        with gr.Row():
                            load_prof_btn = gr.Button("Reload Profile & KB")
                            save_prof_btn = gr.Button("Save Profile", variant="primary")
                        prof_status = gr.Textbox(label="Profile Status", lines=2, interactive=False)

                    with gr.Column():
                        voice_dna_box = gr.Textbox(
                            label="Voice DNA (knowledge/voice_dna.md)", lines=16
                        )
                        save_voice_btn = gr.Button("Save Voice DNA")
                        voice_status = gr.Textbox(
                            label="Voice DNA Status", lines=1, interactive=False
                        )
                        cases_preview = gr.Code(
                            label="Loaded Case Studies (read-only preview)",
                            language="json",
                            lines=12,
                        )

            # ===== TAB 4: SESSIONS & EXPORTS =====
            with gr.Tab("Sessions & Bundles"):
                gr.Markdown("### Exported Ready-to-Post Bundles (`output/`)")
                bundles_df = gr.Dataframe(value=_list_exported_bundles(), interactive=False)
                refresh_bundles_btn = gr.Button("Refresh Bundles")
                refresh_bundles_btn.click(fn=_list_exported_bundles, outputs=bundles_df)

                gr.Markdown("### Saved ADK Sessions")
                sessions_df = gr.Dataframe(value=list_sessions_df(), interactive=False)
                with gr.Row():
                    del_sid = gr.Textbox(label="Session ID to Delete")
                    del_btn = gr.Button("Delete Session", variant="stop")
                    ref_sess_btn = gr.Button("Refresh Sessions")
                sess_status = gr.Textbox(label="Session Status", lines=1, interactive=False)

                ref_sess_btn.click(fn=list_sessions_df, outputs=sessions_df)
                del_btn.click(
                    fn=delete_session_ui, inputs=del_sid, outputs=[sessions_df, sess_status]
                )

        # Wire Studio actions
        generate_btn.click(
            fn=generate_studio_bundle,
            inputs=[
                topic_in,
                seed_in,
                files_in,
                channels_in,
                lang_in,
                session_in,
                ov_linkedin,
                ov_x,
                ov_youtube,
                ov_critic,
            ],
            outputs=[
                status_box,
                li_text,
                x_text,
                yt_text,
                bib_text,
                qual_text,
                li_gallery,
                li_pdf,
                x_video,
                yt_short_video,
                zip_out,
                active_bundle_dir,
            ],
        )

        save_edits_btn.click(
            fn=save_human_edits,
            inputs=[active_bundle_dir, li_text, x_text, yt_text],
            outputs=[edit_status, zip_out],
        )

        load_prof_btn.click(
            fn=load_profile_fields,
            outputs=[
                p_name,
                p_role,
                p_expertise,
                p_pillars,
                p_personas,
                p_offers,
                p_uvp,
                p_linkedin,
                p_github,
                p_x,
                p_youtube,
                voice_dna_box,
                cases_preview,
            ],
        )
        save_prof_btn.click(
            fn=save_profile_fields,
            inputs=[
                p_name,
                p_role,
                p_expertise,
                p_pillars,
                p_personas,
                p_offers,
                p_uvp,
                p_linkedin,
                p_github,
                p_x,
                p_youtube,
            ],
            outputs=prof_status,
        )
        save_voice_btn.click(fn=save_voice_dna_ui, inputs=voice_dna_box, outputs=voice_status)

        app.load(
            fn=load_profile_fields,
            outputs=[
                p_name,
                p_role,
                p_expertise,
                p_pillars,
                p_personas,
                p_offers,
                p_uvp,
                p_linkedin,
                p_github,
                p_x,
                p_youtube,
                voice_dna_box,
                cases_preview,
            ],
        )

    return app


def get_launch_config() -> dict[str, Any]:
    """Build secure Gradio launch parameters (localhost by default, optional Basic Auth)."""
    host = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1").strip() or "127.0.0.1"
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    auth_user = os.getenv("GRADIO_AUTH_USER", "").strip()
    auth_pass = os.getenv("GRADIO_AUTH_PASSWORD", "").strip()
    auth = (auth_user, auth_pass) if (auth_user and auth_pass) else None

    if host not in {"127.0.0.1", "localhost", "::1"} and auth is None:
        allow_lan = os.getenv("ALLOW_UNAUTHENTICATED_LAN", "").lower() == "true"
        if not allow_lan:
            raise PermissionError(
                f"Refusing to bind Gradio on '{host}' without GRADIO_AUTH_USER/GRADIO_AUTH_PASSWORD. "
                "Keep localhost (127.0.0.1) or configure Basic Auth."
            )

    return {
        "server_name": host,
        "server_port": port,
        "share": False,
        "auth": auth,
        "theme": gr.themes.Soft(),
    }


if __name__ == "__main__":
    ui = create_ui()
    ui.queue()
    ui.launch(**get_launch_config())
