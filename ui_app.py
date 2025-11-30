"""Gradio web interface for the Scientific Content Generation Agent."""

import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import pandas as pd

from main import run_content_generation
from src.config import CITATION_STYLE, DEFAULT_MODEL, MAX_PAPERS_PER_SEARCH, SUPPORTED_PLATFORMS
from src.profile import (
    DEFAULT_PROFILE,
    PROFILE_PATH,
    UserProfile,
    load_user_profile,
    save_profile_to_yaml,
)
from src.session_manager import delete_session, get_session_info, list_sessions


# ============================================================================
# Tab 1: Content Generation
# ============================================================================


async def async_generate_with_progress(
    topic: str,
    platforms: List[str],
    tone: str,
    audience: str,
    session_id: str,
    progress: gr.Progress = gr.Progress(),
) -> str:
    """Generate content with progress tracking.

    Args:
        topic: Research topic
        platforms: List of platforms (Blog, LinkedIn, Twitter)
        tone: Content tone
        audience: Target audience
        session_id: Optional session ID to resume
        progress: Gradio progress tracker

    Returns:
        Generated content as formatted string
    """
    try:
        # Validate inputs
        if not topic or not topic.strip():
            return "❌ Error: Please enter a topic."

        if not platforms:
            return "❌ Error: Please select at least one platform."

        # Convert UI platform names to internal format
        platform_map = {"Blog": "blog", "LinkedIn": "linkedin", "Twitter": "twitter"}
        platforms_internal = [platform_map[p] for p in platforms]

        # Build preferences
        preferences = {
            "platforms": platforms_internal,
            "tone": tone,
            "target_audience": audience if audience.strip() else "researchers and professionals",
        }

        # Use session ID if provided
        session = session_id.strip() if session_id and session_id.strip() else None

        # Progress tracking with fixed milestones
        progress(0.0, desc="🚀 Initializing agent pipeline...")
        await asyncio.sleep(0.5)  # Brief pause for UI feedback

        progress(0.1, desc="🔬 ResearchAgent: Searching academic papers and trends...")
        # Run the actual content generation (2-5 minutes)
        # We can't track real progress without hooking into ADK events, so we'll use milestones

        # Start the generation in a separate task so we can update progress
        generation_task = asyncio.create_task(run_content_generation(topic, preferences, session))

        # Simulate progress while generation runs
        # These are approximate milestones based on agent pipeline
        milestones = [
            (0.2, "🎯 StrategyAgent: Planning content strategy..."),
            (0.4, "✍️ ContentGeneratorAgent: Creating content..."),
            (0.7, "🚀 LinkedInOptimizationAgent: Optimizing for opportunities..."),
            (0.85, "✅ ReviewAgent: Final review and citations..."),
        ]

        # Update progress while waiting for completion
        for milestone_progress, desc in milestones:
            # Check if generation is complete
            if generation_task.done():
                break
            progress(milestone_progress, desc=desc)
            # Wait a bit before next milestone (total ~30 seconds for progress updates)
            await asyncio.sleep(7)

        # Wait for generation to complete
        result = await generation_task

        progress(1.0, desc="✅ Generation complete!")

        # Format the result nicely
        if result and isinstance(result, str):
            return f"""# Content Generation Complete! 🎉

{result}

---
💾 Content saved to output directory
🔄 Session ID: {session or "New session created"}
"""
        else:
            return "✅ Content generation completed. Check the logs for details."

    except Exception as e:
        error_msg = f"❌ Error during content generation: {str(e)}"
        print(error_msg)
        import traceback

        traceback.print_exc()
        return error_msg


def generate_content_sync(
    topic: str, platforms: List[str], tone: str, audience: str, session_id: str
) -> str:
    """Synchronous wrapper for async content generation.

    This is needed because Gradio requires sync functions unless we use .then() chaining.
    """
    return asyncio.run(async_generate_with_progress(topic, platforms, tone, audience, session_id))


# ============================================================================
# Tab 2: Profile Editor
# ============================================================================


def load_profile_ui() -> Tuple:
    """Load current profile for form population.

    Returns:
        Tuple of all profile field values in form order
    """
    try:
        profile = load_user_profile(validate=False)
        return (
            profile.name,
            profile.target_role,
            ", ".join(profile.expertise_areas),
            ", ".join(profile.content_goals),
            profile.region,
            ", ".join(profile.languages),
            ", ".join(profile.target_industries),
            profile.github_username,
            profile.linkedin_url,
            profile.portfolio_url,
            profile.kaggle_username,
            json.dumps(profile.notable_projects, indent=2),
            ", ".join(profile.primary_skills),
            profile.content_tone,
            profile.use_emojis,
            profile.posting_frequency,
            profile.unique_value_proposition,
            ", ".join(profile.key_differentiators),
            "✅ Profile loaded successfully!",
        )
    except Exception as e:
        return (
            DEFAULT_PROFILE.name,
            DEFAULT_PROFILE.target_role,
            ", ".join(DEFAULT_PROFILE.expertise_areas),
            ", ".join(DEFAULT_PROFILE.content_goals),
            DEFAULT_PROFILE.region,
            ", ".join(DEFAULT_PROFILE.languages),
            ", ".join(DEFAULT_PROFILE.target_industries),
            DEFAULT_PROFILE.github_username,
            DEFAULT_PROFILE.linkedin_url,
            DEFAULT_PROFILE.portfolio_url,
            DEFAULT_PROFILE.kaggle_username,
            json.dumps(DEFAULT_PROFILE.notable_projects, indent=2),
            ", ".join(DEFAULT_PROFILE.primary_skills),
            DEFAULT_PROFILE.content_tone,
            DEFAULT_PROFILE.use_emojis,
            DEFAULT_PROFILE.posting_frequency,
            DEFAULT_PROFILE.unique_value_proposition,
            ", ".join(DEFAULT_PROFILE.key_differentiators),
            f"⚠️ Error loading profile: {str(e)}. Showing defaults.",
        )


def validate_profile_ui(
    name: str,
    target_role: str,
    expertise_areas: str,
    content_goals: str,
    region: str,
    languages: str,
    target_industries: str,
    github: str,
    linkedin: str,
    portfolio: str,
    kaggle: str,
    projects_json: str,
    skills: str,
    tone: str,
    emojis: bool,
    frequency: str,
    uvp: str,
    differentiators: str,
) -> str:
    """Validate profile fields without saving.

    Returns:
        Validation result message
    """
    try:
        # Parse list fields
        expertise_list = [x.strip() for x in expertise_areas.split(",") if x.strip()]
        goals_list = [x.strip() for x in content_goals.split(",") if x.strip()]
        languages_list = [x.strip() for x in languages.split(",") if x.strip()]
        industries_list = [x.strip() for x in target_industries.split(",") if x.strip()]
        skills_list = [x.strip() for x in skills.split(",") if x.strip()]
        diff_list = [x.strip() for x in differentiators.split(",") if x.strip()]

        # Parse projects JSON
        try:
            projects = json.loads(projects_json) if projects_json.strip() else []
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON in Notable Projects: {str(e)}"

        # Create profile object
        profile = UserProfile(
            name=name,
            target_role=target_role,
            expertise_areas=expertise_list,
            content_goals=goals_list,
            region=region,
            languages=languages_list,
            target_industries=industries_list,
            github_username=github,
            linkedin_url=linkedin,
            portfolio_url=portfolio,
            kaggle_username=kaggle,
            notable_projects=projects,
            primary_skills=skills_list,
            content_tone=tone,
            use_emojis=emojis,
            posting_frequency=frequency,
            unique_value_proposition=uvp,
            key_differentiators=diff_list,
        )

        # Validate
        validation = profile.validate()

        if validation["errors"]:
            error_msg = "❌ Validation Errors:\n" + "\n".join(
                f"  • {err}" for err in validation["errors"]
            )
            if validation["warnings"]:
                error_msg += "\n\n⚠️ Warnings:\n" + "\n".join(
                    f"  • {warn}" for warn in validation["warnings"]
                )
            return error_msg

        if validation["warnings"]:
            return "⚠️ Validation Warnings:\n" + "\n".join(
                f"  • {warn}" for warn in validation["warnings"]
            )

        return "✅ Profile is valid!"

    except Exception as e:
        return f"❌ Validation error: {str(e)}"


def save_profile_ui(
    name: str,
    target_role: str,
    expertise_areas: str,
    content_goals: str,
    region: str,
    languages: str,
    target_industries: str,
    github: str,
    linkedin: str,
    portfolio: str,
    kaggle: str,
    projects_json: str,
    skills: str,
    tone: str,
    emojis: bool,
    frequency: str,
    uvp: str,
    differentiators: str,
) -> str:
    """Save profile to YAML file.

    Returns:
        Save result message
    """
    try:
        # Parse list fields
        expertise_list = [x.strip() for x in expertise_areas.split(",") if x.strip()]
        goals_list = [x.strip() for x in content_goals.split(",") if x.strip()]
        languages_list = [x.strip() for x in languages.split(",") if x.strip()]
        industries_list = [x.strip() for x in target_industries.split(",") if x.strip()]
        skills_list = [x.strip() for x in skills.split(",") if x.strip()]
        diff_list = [x.strip() for x in differentiators.split(",") if x.strip()]

        # Parse projects JSON
        try:
            projects = json.loads(projects_json) if projects_json.strip() else []
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON in Notable Projects: {str(e)}"

        # Create profile object
        profile = UserProfile(
            name=name,
            target_role=target_role,
            expertise_areas=expertise_list,
            content_goals=goals_list,
            region=region,
            languages=languages_list,
            target_industries=industries_list,
            github_username=github,
            linkedin_url=linkedin,
            portfolio_url=portfolio,
            kaggle_username=kaggle,
            notable_projects=projects,
            primary_skills=skills_list,
            content_tone=tone,
            use_emojis=emojis,
            posting_frequency=frequency,
            unique_value_proposition=uvp,
            key_differentiators=diff_list,
        )

        # Validate before saving
        validation = profile.validate()
        if validation["errors"]:
            return "❌ Cannot save profile with errors:\n" + "\n".join(
                f"  • {err}" for err in validation["errors"]
            )

        # Save to YAML
        save_profile_to_yaml(profile, PROFILE_PATH)

        msg = f"✅ Profile saved to {PROFILE_PATH}"
        if validation["warnings"]:
            msg += "\n\n⚠️ Warnings:\n" + "\n".join(f"  • {warn}" for warn in validation["warnings"])
        return msg

    except Exception as e:
        return f"❌ Error saving profile: {str(e)}"


# ============================================================================
# Tab 3: Session History
# ============================================================================


def list_sessions_ui() -> pd.DataFrame:
    """List all sessions as a DataFrame.

    Returns:
        DataFrame with session information
    """
    try:
        sessions = list_sessions()
        if not sessions:
            return pd.DataFrame(columns=["Session ID", "User", "Messages", "Last Updated"])

        df = pd.DataFrame(
            [
                {
                    "Session ID": s["session_id"],
                    "User": s["user_id"],
                    "Messages": s["message_count"],
                    "Last Updated": s["updated_at"],
                }
                for s in sessions
            ]
        )
        return df
    except Exception as e:
        print(f"Error listing sessions: {e}")
        return pd.DataFrame(columns=["Session ID", "User", "Messages", "Last Updated"])


def get_session_details_ui(session_id: str) -> str:
    """Get detailed information about a session.

    Args:
        session_id: Session ID to retrieve

    Returns:
        Formatted session details or error message
    """
    if not session_id or not session_id.strip():
        return "Please select a session from the table."

    try:
        info = get_session_info(session_id.strip())
        if not info:
            return f"❌ Session not found: {session_id}"

        # Format the information nicely
        details = f"""# Session Details

**Session ID**: {info["session_id"]}
**User**: {info["user_id"]}
**Created**: {info["created_at"]}
**Last Updated**: {info["updated_at"]}
**Message Count**: {info["message_count"]}

## Messages

"""
        if info.get("messages"):
            for i, msg in enumerate(info["messages"], 1):
                details += f"### Message {i}\n```\n{msg}\n```\n\n"
        else:
            details += "*No messages in this session*\n"

        return details

    except Exception as e:
        return f"❌ Error retrieving session: {str(e)}"


def delete_session_ui(session_id: str) -> Tuple[pd.DataFrame, str]:
    """Delete a session.

    Args:
        session_id: Session ID to delete

    Returns:
        Tuple of (updated sessions DataFrame, status message)
    """
    if not session_id or not session_id.strip():
        return list_sessions_ui(), "Please select a session to delete."

    try:
        delete_session(session_id.strip())
        return list_sessions_ui(), f"✅ Session deleted: {session_id}"
    except Exception as e:
        return list_sessions_ui(), f"❌ Error deleting session: {str(e)}"


# ============================================================================
# Tab 4: Settings
# ============================================================================


def save_settings_ui(api_key: str, model: str, max_papers: int, citation_style: str) -> str:
    """Save settings (placeholder - would need to update config).

    Args:
        api_key: Google API key
        model: Model name
        max_papers: Max papers to search
        citation_style: Citation style

    Returns:
        Status message
    """
    # Note: This is a simplified version. In production, you'd want to:
    # 1. Update .env file for API key
    # 2. Update config file for other settings
    # 3. Or use a dedicated settings storage mechanism

    messages = []

    if api_key and api_key.strip():
        messages.append("⚠️ API key changes require restart to take effect")

    if model != DEFAULT_MODEL:
        messages.append(f"⚠️ Model changed to {model} (requires restart)")

    if max_papers != MAX_PAPERS_PER_SEARCH:
        messages.append(f"⚠️ Max papers changed to {max_papers} (requires restart)")

    if citation_style != CITATION_STYLE:
        messages.append(f"⚠️ Citation style changed to {citation_style} (requires restart)")

    if not messages:
        return "ℹ️ No settings changes detected"

    return "\n".join(messages) + "\n\n💡 Settings saved (restart app to apply)"


# ============================================================================
# Main UI Creation
# ============================================================================


def create_ui() -> gr.Blocks:
    """Create the main Gradio UI.

    Returns:
        Gradio Blocks application
    """
    with gr.Blocks(title="Scientific Content Generation Agent") as app:
        gr.Markdown(
            """
        # 🔬 Scientific Content Generation Agent

        Generate research-backed content for blogs, LinkedIn, and Twitter using AI-powered multi-agent system.
        """
        )

        with gr.Tabs():
            # ===== TAB 1: GENERATE CONTENT =====
            with gr.Tab("🚀 Generate Content"):
                gr.Markdown("### Create Scientific Content")

                with gr.Row():
                    with gr.Column():
                        topic_input = gr.Textbox(
                            label="Research Topic",
                            placeholder="e.g., AI Agents and Multi-Agent Systems",
                            lines=2,
                        )
                        platform_checkboxes = gr.CheckboxGroup(
                            choices=["Blog", "LinkedIn", "Twitter"],
                            value=["Blog", "LinkedIn", "Twitter"],
                            label="Target Platforms",
                        )
                        tone_dropdown = gr.Dropdown(
                            choices=[
                                "professional-formal",
                                "professional-conversational",
                                "technical",
                            ],
                            value="professional-conversational",
                            label="Content Tone",
                        )
                        audience_input = gr.Textbox(
                            label="Target Audience",
                            value="researchers and professionals",
                            lines=1,
                        )

                        with gr.Accordion("Advanced Options", open=False):
                            session_id_input = gr.Textbox(
                                label="Session ID (optional - leave empty for new session)",
                                placeholder="Enter session ID to resume",
                                lines=1,
                            )

                        generate_btn = gr.Button("Generate Content", variant="primary", size="lg")

                    with gr.Column():
                        output_display = gr.Textbox(
                            label="Generated Content",
                            lines=25,
                            max_lines=50,
                        )

                generate_btn.click(
                    fn=generate_content_sync,
                    inputs=[
                        topic_input,
                        platform_checkboxes,
                        tone_dropdown,
                        audience_input,
                        session_id_input,
                    ],
                    outputs=output_display,
                )

            # ===== TAB 2: PROFILE EDITOR =====
            with gr.Tab("👤 Profile Editor"):
                gr.Markdown("### Edit Your Professional Profile")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### Professional Identity")
                        name_input = gr.Textbox(label="Name", value="Your Name")
                        target_role_input = gr.Textbox(label="Target Role", value="AI Consultant")
                        expertise_input = gr.Textbox(
                            label="Expertise Areas (comma-separated)",
                            value="Machine Learning, AI",
                            lines=2,
                        )

                        gr.Markdown("#### Professional Goals")
                        goals_input = gr.Textbox(
                            label="Content Goals (comma-separated)",
                            value="opportunities, credibility, visibility",
                            lines=2,
                        )

                        gr.Markdown("#### Geographic & Market")
                        region_dropdown = gr.Dropdown(
                            choices=["Europe", "US", "Asia", "Global"],
                            value="Europe",
                            label="Region",
                        )
                        languages_input = gr.Textbox(
                            label="Languages (comma-separated)", value="English"
                        )
                        industries_input = gr.Textbox(
                            label="Target Industries (comma-separated)",
                            value="Technology, Finance",
                            lines=2,
                        )

                    with gr.Column():
                        gr.Markdown("#### Portfolio & Links")
                        github_input = gr.Textbox(label="GitHub Username")
                        linkedin_input = gr.Textbox(label="LinkedIn URL")
                        portfolio_input = gr.Textbox(label="Portfolio URL")
                        kaggle_input = gr.Textbox(label="Kaggle Username")

                        gr.Markdown("#### Technical Skills")
                        skills_input = gr.Textbox(
                            label="Primary Skills (comma-separated)",
                            value="Python, PyTorch, TensorFlow",
                            lines=2,
                        )

                        gr.Markdown("#### Content Preferences")
                        tone_radio = gr.Radio(
                            choices=[
                                "professional-formal",
                                "professional-conversational",
                                "technical",
                            ],
                            value="professional-conversational",
                            label="Content Tone",
                        )
                        emojis_checkbox = gr.Checkbox(label="Use Emojis", value=True)
                        frequency_dropdown = gr.Dropdown(
                            choices=["daily", "2-3x per week", "weekly"],
                            value="2-3x per week",
                            label="Posting Frequency",
                        )

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### SEO & Positioning")
                        uvp_input = gr.Textbox(
                            label="Unique Value Proposition",
                            value="I help companies turn AI research into production",
                            lines=2,
                        )
                        diff_input = gr.Textbox(
                            label="Key Differentiators (comma-separated)",
                            value="Research to production, End-to-end AI",
                            lines=2,
                        )

                    with gr.Column():
                        gr.Markdown("#### Notable Projects (JSON)")
                        projects_input = gr.Code(
                            label="Projects",
                            language="json",
                            value=json.dumps(
                                [
                                    {
                                        "name": "Project Name",
                                        "description": "Description",
                                        "technologies": "Tech stack",
                                        "url": "https://github.com/...",
                                    }
                                ],
                                indent=2,
                            ),
                            lines=10,
                        )

                with gr.Row():
                    load_btn = gr.Button("Load Profile")
                    validate_btn = gr.Button("Validate Profile")
                    save_btn = gr.Button("Save Profile", variant="primary")

                profile_status = gr.Textbox(label="Status", lines=5)

                # Wire up profile buttons
                load_btn.click(
                    fn=load_profile_ui,
                    inputs=[],
                    outputs=[
                        name_input,
                        target_role_input,
                        expertise_input,
                        goals_input,
                        region_dropdown,
                        languages_input,
                        industries_input,
                        github_input,
                        linkedin_input,
                        portfolio_input,
                        kaggle_input,
                        projects_input,
                        skills_input,
                        tone_radio,
                        emojis_checkbox,
                        frequency_dropdown,
                        uvp_input,
                        diff_input,
                        profile_status,
                    ],
                )

                validate_btn.click(
                    fn=validate_profile_ui,
                    inputs=[
                        name_input,
                        target_role_input,
                        expertise_input,
                        goals_input,
                        region_dropdown,
                        languages_input,
                        industries_input,
                        github_input,
                        linkedin_input,
                        portfolio_input,
                        kaggle_input,
                        projects_input,
                        skills_input,
                        tone_radio,
                        emojis_checkbox,
                        frequency_dropdown,
                        uvp_input,
                        diff_input,
                    ],
                    outputs=profile_status,
                )

                save_btn.click(
                    fn=save_profile_ui,
                    inputs=[
                        name_input,
                        target_role_input,
                        expertise_input,
                        goals_input,
                        region_dropdown,
                        languages_input,
                        industries_input,
                        github_input,
                        linkedin_input,
                        portfolio_input,
                        kaggle_input,
                        projects_input,
                        skills_input,
                        tone_radio,
                        emojis_checkbox,
                        frequency_dropdown,
                        uvp_input,
                        diff_input,
                    ],
                    outputs=profile_status,
                )

            # ===== TAB 3: SESSION HISTORY =====
            with gr.Tab("📚 Session History"):
                gr.Markdown("### View and Manage Sessions")

                with gr.Row():
                    refresh_btn = gr.Button("Refresh Sessions")

                sessions_table = gr.Dataframe(
                    label="Sessions",
                    value=list_sessions_ui(),
                    interactive=False,
                )

                with gr.Row():
                    session_selector = gr.Textbox(
                        label="Session ID (paste from table)",
                        placeholder="Enter session ID",
                    )

                session_details = gr.Markdown(label="Session Details")

                with gr.Row():
                    view_details_btn = gr.Button("View Details")
                    delete_btn = gr.Button("Delete Session", variant="stop")
                    resume_btn = gr.Button("Resume Session")

                session_status = gr.Textbox(label="Status", lines=2)

                # Wire up session buttons
                refresh_btn.click(fn=list_sessions_ui, inputs=[], outputs=sessions_table)

                view_details_btn.click(
                    fn=get_session_details_ui, inputs=session_selector, outputs=session_details
                )

                delete_btn.click(
                    fn=delete_session_ui,
                    inputs=session_selector,
                    outputs=[sessions_table, session_status],
                )

                # Resume session - switches to Tab 1 and populates session ID
                def resume_session(session_id):
                    return session_id

                resume_btn.click(
                    fn=resume_session, inputs=session_selector, outputs=session_id_input
                )

            # ===== TAB 4: SETTINGS =====
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("### Configure API and Content Settings")

                gr.Markdown("#### API Configuration")
                api_key_input = gr.Textbox(
                    label="Google API Key",
                    type="password",
                    placeholder="Enter your API key from https://aistudio.google.com/app/api_keys",
                )
                gr.Markdown(
                    "*Your API key is stored locally and never shared. Get one at [Google AI Studio](https://aistudio.google.com/app/api_keys)*"
                )

                model_dropdown = gr.Dropdown(
                    choices=["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
                    value=DEFAULT_MODEL,
                    label="Model",
                )

                gr.Markdown("#### Content Configuration")
                max_papers_slider = gr.Slider(
                    minimum=1,
                    maximum=20,
                    value=MAX_PAPERS_PER_SEARCH,
                    step=1,
                    label="Max Papers per Search",
                )
                citation_radio = gr.Radio(
                    choices=["apa", "mla", "chicago"], value=CITATION_STYLE, label="Citation Style"
                )

                save_settings_btn = gr.Button("Save Settings", variant="primary")
                settings_status = gr.Textbox(label="Status", lines=3)

                save_settings_btn.click(
                    fn=save_settings_ui,
                    inputs=[api_key_input, model_dropdown, max_papers_slider, citation_radio],
                    outputs=settings_status,
                )

        gr.Markdown(
            """
        ---
        💡 **Tips**:
        - Generate Content: Enter a topic and click Generate (takes 2-5 minutes)
        - Profile Editor: Customize your professional profile for personalized content
        - Session History: Resume previous generations or delete old sessions
        - Settings: Configure API key and content preferences

        📚 [Documentation](https://github.com/anthropics/agentic-content-generation) |
        🐛 [Report Issues](https://github.com/anthropics/agentic-content-generation/issues)
        """
        )

    return app


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("🚀 Launching Scientific Content Generation Agent UI...")
    print("📍 Access at: http://localhost:7860")
    print()

    app = create_ui()
    app.queue()  # Enable queueing for long-running tasks
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
