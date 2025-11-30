"""Main entry point for the Scientific Content Generation Agent."""

import argparse
import asyncio
import contextlib
import logging
import os
import uuid

from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from src.agents import create_content_generation_pipeline
from src.config import GOOGLE_API_KEY, LOG_FILE, LOG_LEVEL
from src.profile import (
    DEFAULT_PROFILE,
    PROFILE_DIR,
    PROFILE_PATH,
    load_user_profile,
    save_profile_to_yaml,
)
from src.profile_editor import edit_profile_interactive, validate_after_edit
from src.session_manager import delete_session, format_session_list, list_sessions


async def run_content_generation(topic: str, preferences: dict = None, session_id: str = None):
    """Run the content generation pipeline for a given topic.

    Args:
        topic: The research topic to generate content about
        preferences: Optional dict with user preferences:
            - platforms: List of platforms (default: ["blog", "linkedin", "twitter"])
            - tone: Preferred tone (default: "professional")
            - target_audience: Target audience description
            - max_papers: Maximum papers to search (default: 5)
        session_id: Optional session ID to resume a conversation

    Returns:
        Final content for all platforms
    """
    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY not found. Please set it in .env file.\n"
            "Get your key from: https://aistudio.google.com/app/api_keys"
        )

    # Set environment variable
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

    # Load user profile
    profile = load_user_profile()
    print(f"👤 Generating content for: {profile.name} ({profile.target_role})")

    # Create the agent pipeline
    print("\n🤖 Initializing Scientific Content Generation Agent...\n")
    agent = create_content_generation_pipeline()

    # Configure logging
    # Ensure log directory exists
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            # logging.StreamHandler()  # Uncomment to see logs in console
        ],
    )

    # Initialize persistent session service
    # Ensure the directory exists (important for cloud environments like HF Spaces)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    db_path = PROFILE_DIR / "sessions.db"
    db_url = f"sqlite:///{db_path}"
    session_service = DatabaseSessionService(db_url=db_url)

    # Create runner
    app_name = "scientific-content-agent"
    runner = Runner(
        agent=agent, app_name=app_name, session_service=session_service, plugins=[LoggingPlugin()]
    )

    # Generate or use provided session ID
    if not session_id:
        session_id = str(uuid.uuid4())
        print(f"🆕 Starting new session: {session_id}")
    else:
        print(f"🔄 Resuming session: {session_id}")

    # Build the user message
    preferences = preferences or {}
    platforms = preferences.get("platforms", ["blog", "linkedin", "twitter"])
    tone = preferences.get("tone", profile.content_tone)
    audience = preferences.get("target_audience", "researchers and professionals")

    # Inject profile summary into the prompt
    profile_summary = profile.get_profile_summary()

    user_message = f"""Generate scientific content on the following topic: {topic}

Preferences:
- Target platforms: {", ".join(platforms)}
- Tone: {tone}
- Target audience: {audience}

User Profile Context:
{profile_summary}

Please create engaging, credible content that:
1. Incorporates recent research and academic sources
2. Builds professional credibility on LinkedIn
3. Demonstrates expertise in the field
4. Is suitable for scientific research monitoring
5. Aligns with the user's profile and expertise

Generate content for all three platforms: blog article, LinkedIn post, and Twitter thread.
"""

    print(f"📝 Topic: {topic}")
    print(f"🎯 Target platforms: {', '.join(platforms)}")
    print(f"👥 Target audience: {audience}\n")
    print("=" * 80)
    print("\n🔄 Running content generation pipeline...\n")
    print("Step 1: ResearchAgent - Searching for papers and current trends...")

    final_content = ""
    try:
        # Ensure session exists
        with contextlib.suppress(Exception):
            await session_service.create_session(
                app_name=app_name, user_id=profile.name, session_id=session_id
            )

        # Run the agent
        query = types.Content(role="user", parts=[types.Part(text=user_message)])

        async for event in runner.run_async(
            user_id=profile.name, session_id=session_id, new_message=query
        ):
            # Check for final content in state delta
            if (
                event.actions
                and event.actions.state_delta
                and "final_content" in event.actions.state_delta
            ):
                final_content = event.actions.state_delta["final_content"]

            # Also check if the model returned a text response (fallback)
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        # This might be intermediate thought or final answer depending on agent structure
                        # For now we rely on state_delta as per original design, but keep this as backup
                        pass

        if not final_content:
            final_content = "No content generated. Please check the logs."

        print("\n✅ Content generation complete!\n")
        print("=" * 80)
        print("\n📄 GENERATED CONTENT:\n")
        print(final_content)
        print("\n" + "=" * 80)

        return final_content

    except Exception as e:
        print(f"\n❌ Error during content generation: {str(e)}")
        raise


async def main():
    """Main function to demonstrate the agent."""
    parser = argparse.ArgumentParser(description="Scientific Content Generation Agent")
    parser.add_argument(
        "--init-profile",
        action="store_true",
        help="Initialize a default user profile in ~/.agentic-content-generation/profile.yaml",
    )
    parser.add_argument(
        "--validate-profile",
        action="store_true",
        help="Validate the current profile and show warnings/errors",
    )
    parser.add_argument(
        "--edit-profile",
        action="store_true",
        help="Open profile in your default editor",
    )
    parser.add_argument(
        "--list-sessions",
        action="store_true",
        help="List all saved sessions",
    )
    parser.add_argument(
        "--delete-session",
        type=str,
        metavar="SESSION_ID",
        help="Delete a specific session by ID",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="Large Language Models and AI Agents",
        help="Topic to generate content about",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        help="Session ID to resume a conversation",
    )
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("🔬 SCIENTIFIC CONTENT GENERATION AGENT")
    print("=" * 80)

    if args.init_profile:
        if PROFILE_PATH.exists():
            print(f"⚠️  Profile already exists at {PROFILE_PATH}")
            print("Edit this file to customize your profile.")
        else:
            save_profile_to_yaml(DEFAULT_PROFILE, PROFILE_PATH)
            print(f"✅ Created default profile at {PROFILE_PATH}")
            print(
                "👉 Please edit this file with your personal information before running the agent."
            )
        return

    if args.validate_profile:
        print("\n🔍 Validating profile...\n")
        try:
            profile = load_user_profile(validate=True)
            print("✅ Profile validation complete!")
            if profile.name != "Your Name":
                print(f"👤 Profile: {profile.name} ({profile.target_role})")
        except ValueError as e:
            print(f"\n❌ Validation failed: {e}")
            return
        return

    if args.edit_profile:
        print("\n📝 Opening profile editor...\n")
        if not PROFILE_PATH.exists():
            print("⚠️  No profile found. Creating one first...")
            save_profile_to_yaml(DEFAULT_PROFILE, PROFILE_PATH)
            print(f"✅ Created default profile at {PROFILE_PATH}\n")

        changed = edit_profile_interactive()
        if changed:
            # Validate after editing
            validate_after_edit()
        return

    if args.list_sessions:
        print("\n📋 Listing all sessions...\n")
        sessions = list_sessions()
        if sessions:
            print(format_session_list(sessions))
            print(f"Total: {len(sessions)} session(s)")
            print("\n💡 To resume a session: python main.py --session-id <SESSION_ID>")
            print("💡 To delete a session: python main.py --delete-session <SESSION_ID>")
        else:
            print("No sessions found. Start a new conversation to create one!")
        return

    if args.delete_session:
        session_id_to_delete = args.delete_session
        print(f"\n🗑️  Deleting session: {session_id_to_delete}...")
        result = delete_session(session_id_to_delete)
        if result["status"] == "success":
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
        return

    # Example usage
    topic = args.topic
    session_id = args.session_id

    preferences = {
        "platforms": ["blog", "linkedin", "twitter"],
        # Tone is now loaded from profile by default
        "target_audience": "AI researchers and industry professionals",
    }

    result = await run_content_generation(topic, preferences, session_id)

    # Save output to file
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    output_file = f"{output_dir}/content_{topic.replace(' ', '_').lower()}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\n💾 Content saved to: {output_file}")
    print("\n✨ Done!")


if __name__ == "__main__":
    asyncio.run(main())
