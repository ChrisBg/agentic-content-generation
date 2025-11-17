"""Main entry point for the Scientific Content Generation Agent."""

import asyncio
import os

from google.adk.runners import InMemoryRunner

from src.agents import create_content_generation_pipeline
from src.config import GOOGLE_API_KEY


async def run_content_generation(topic: str, preferences: dict = None):
    """Run the content generation pipeline for a given topic.

    Args:
        topic: The research topic to generate content about
        preferences: Optional dict with user preferences:
            - platforms: List of platforms (default: ["blog", "linkedin", "twitter"])
            - tone: Preferred tone (default: "professional")
            - target_audience: Target audience description
            - max_papers: Maximum papers to search (default: 5)

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

    # Create the agent pipeline
    print("\n🤖 Initializing Scientific Content Generation Agent...\n")
    agent = create_content_generation_pipeline()

    # Create runner
    runner = InMemoryRunner(agent=agent)

    # Build the user message
    preferences = preferences or {}
    platforms = preferences.get("platforms", ["blog", "linkedin", "twitter"])
    tone = preferences.get("tone", "professional")
    audience = preferences.get("target_audience", "researchers and professionals")

    user_message = f"""Generate scientific content on the following topic: {topic}

Preferences:
- Target platforms: {", ".join(platforms)}
- Tone: {tone}
- Target audience: {audience}

Please create engaging, credible content that:
1. Incorporates recent research and academic sources
2. Builds professional credibility on LinkedIn
3. Demonstrates expertise in the field
4. Is suitable for scientific research monitoring

Generate content for all three platforms: blog article, LinkedIn post, and Twitter thread.
"""

    print(f"📝 Topic: {topic}")
    print(f"🎯 Target platforms: {', '.join(platforms)}")
    print(f"👥 Target audience: {audience}\n")
    print("=" * 80)
    print("\n🔄 Running content generation pipeline...\n")
    print("Step 1: ResearchAgent - Searching for papers and current trends...")

    try:
        # Run the agent
        response = await runner.run_debug(user_message)

        # Extract the final content from the response
        # run_debug returns a list of events, we need the last event's content
        if isinstance(response, list) and len(response) > 0:
            # Get the final_content from the state
            final_event = response[-1]
            if hasattr(final_event, 'actions') and final_event.actions and final_event.actions.state_delta:
                final_content = final_event.actions.state_delta.get('final_content', '')
            else:
                final_content = str(response)
        else:
            final_content = str(response)

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
    print("\n" + "=" * 80)
    print("🔬 SCIENTIFIC CONTENT GENERATION AGENT")
    print("=" * 80)

    # Example usage
    topic = "Large Language Models and AI Agents"

    preferences = {
        "platforms": ["blog", "linkedin", "twitter"],
        "tone": "professional",
        "target_audience": "AI researchers and industry professionals",
    }

    result = await run_content_generation(topic, preferences)

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
