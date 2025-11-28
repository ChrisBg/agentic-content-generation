import os
import sys

# Add the parent directory to sys.path to allow importing src
# This is critical for Vertex AI deployment where the working directory might vary
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.agents import create_content_generation_pipeline
from src.profile import load_user_profile


class ScientificContentAgent:
    """Wrapper for the Scientific Content Generation Agent for Vertex AI Reasoning Engine."""

    def __init__(self):
        """Initialize the agent and runner."""
        self.agent = create_content_generation_pipeline()
        # Use in-memory session for the deployed instance as it's stateless per request
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=self.agent,
            app_name="scientific-content-agent",
            session_service=self.session_service
        )
        # Load profile once at startup (or could be passed in query)
        self.profile = load_user_profile()

    def query(self, topic: str, session_id: str = "default-session") -> str:
        """Run the agent for a given topic.

        Args:
            topic: The research topic.
            session_id: Optional session ID.

        Returns:
            The generated content.
        """
        print(f"Received query for topic: {topic}")

        # Construct the user message similar to main.py
        profile_summary = self.profile.get_profile_summary()

        user_message = f"""Generate scientific content on the following topic: {topic}

User Profile Context:
{profile_summary}

Please create engaging, credible content for Blog, LinkedIn, and Twitter.
"""

        # Create content object
        query_content = types.Content(role="user", parts=[types.Part(text=user_message)])

        # Run the agent synchronously (Reasoning Engine expects sync return or async handling)
        # Since ADK runner is async, we need to run it in an event loop.
        # However, Vertex AI Reasoning Engine supports async methods if defined as `async def query`.
        # But for simplicity and compatibility, we'll use a helper to run it if needed,
        # or better yet, define query as async if the runtime supports it.
        # The standard pattern for ADK on Vertex is often to use the runner's execute method if available,
        # or run the async loop.

        import asyncio

        async def run_pipeline():
            final_content = ""
            # Create session
            await self.session_service.create_session(
                app_name="scientific-content-agent", user_id="user", session_id=session_id
            )

            async for event in self.runner.run_async(
                user_id="user", session_id=session_id, new_message=query_content
            ):
                if event.actions and event.actions.state_delta and "final_content" in event.actions.state_delta:
                    final_content = event.actions.state_delta["final_content"]

            return final_content or "No content generated."

        # Run the async pipeline
        try:
            return asyncio.run(run_pipeline())
        except RuntimeError:
            # If we are already in an event loop (e.g. some notebook environments),
            # we might need nest_asyncio, but for standard deployment this is fine.
            # For Vertex AI Reasoning Engine, it handles async entry points well.
            # Let's try to return the coroutine if the caller expects it,
            # but standard Reasoning Engine expects a response.
            # Safest is asyncio.run for a top-level entry.
            return asyncio.run(run_pipeline())

# Create the agent instance for the runtime
agent = ScientificContentAgent()
