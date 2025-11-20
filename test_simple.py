"""Simple test to debug the agent pipeline."""

import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify API key is loaded
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

from google.adk.agents import SequentialAgent  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402

from src.agents import (  # noqa: E402
    create_content_generator_agent,
    create_research_agent,
    create_strategy_agent,
)


async def test_pipeline():
    """Test pipeline with first 3 agents only."""

    # Create agents
    research_agent = create_research_agent()
    strategy_agent = create_strategy_agent()
    content_agent = create_content_generator_agent()

    # Create simple pipeline
    pipeline = SequentialAgent(
        name="TestPipeline",
        description="Test pipeline with 3 agents",
        sub_agents=[research_agent, strategy_agent, content_agent],
    )

    # Create runner
    runner = InMemoryRunner(agent=pipeline)

    # Test message
    message = """Generate content on: AI Agents and Large Language Models

Create content for blog, LinkedIn, and Twitter."""

    print("=" * 80)
    print("Testing 3-agent pipeline...")
    print("=" * 80)

    try:
        response = await runner.run_debug(message)
        print("\n" + "=" * 80)
        print("SUCCESS! Pipeline completed.")
        print("=" * 80)
        print(f"\nResponse preview: {response.text[:500]}...")
        return response
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_pipeline())
