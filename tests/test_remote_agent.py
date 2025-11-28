import argparse

import vertexai.preview.reasoning_engines


def test_remote_agent(project_id, location, resource_name, topic):
    print(f"🚀 Connecting to remote agent: {resource_name}")
    print(f"📍 Project: {project_id}, Location: {location}")

    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)

    try:
        # Get the remote agent
        remote_agent = vertexai.preview.reasoning_engines.ReasoningEngine(resource_name)

        print(f"\n📝 Sending query: '{topic}'")
        print("⏳ Waiting for response (this may take a minute)...")

        # Query the agent
        # Note: The query method signature depends on how the agent was defined.
        # Our ScientificContentAgent.query takes 'topic' and optional 'session_id'
        response = remote_agent.query(topic=topic)

        print("\n✅ Response received!")
        print("=" * 80)
        print(response)
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error querying remote agent: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Remote Vertex AI Agent")
    parser.add_argument("--project", default="ai-agents", help="GCP Project ID")
    parser.add_argument("--location", default="us-central1", help="GCP Region")
    parser.add_argument("--resource-name", required=True, help="Reasoning Engine Resource Name (projects/.../reasoningEngines/...)")
    parser.add_argument("--topic", default="The future of AI agents", help="Topic to generate content about")

    args = parser.parse_args()

    test_remote_agent(args.project, args.location, args.resource_name, args.topic)
