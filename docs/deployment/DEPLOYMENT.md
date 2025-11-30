# Deployment Guide

This guide explains how to deploy the **Scientific Content Generation Agent** to **Google Cloud Vertex AI Agent Engine** (Reasoning Engine) using the ADK CLI.

## Prerequisites

1.  **Google Cloud Project**: You need an active GCP project.
2.  **APIs Enabled**:
    *   Vertex AI API (`aiplatform.googleapis.com`)
    *   Cloud Build API (`cloudbuild.googleapis.com`)
    *   Container Registry API or Artifact Registry API
3.  **Authentication**:
    *   Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
    *   Login: `gcloud auth login`
    *   Set project: `gcloud config set project YOUR_PROJECT_ID`
    *   Application Default Credentials: `gcloud auth application-default login`

## Deployment Options

There are two primary ways to deploy this agent on Google Cloud. The "best" option depends on your specific needs:

### Option 1: Vertex AI Agent Engine (Recommended for ADK)
This is the method described in this guide.
*   **Best for**: Teams fully invested in the Google Cloud GenAI ecosystem.
*   **Pros**: Managed infrastructure, built-in reasoning traces, native integration with Vertex AI, no need to manage API servers.
*   **Cons**: Specific to Google Cloud, requires using the Vertex AI SDK to call the agent.

### Option 2: Google Cloud Run
You can wrap the agent in a standard web server (e.g., FastAPI) and deploy it as a container.
*   **Best for**: Building a standard REST API backend for a web/mobile app, or if you need portability.
*   **Pros**: Standard HTTP/REST API, scales to zero, full control over the runtime.
*   **Cons**: Requires writing an API wrapper (`app.py`) and `Dockerfile`.

---

## Configuration

The agent uses environment variables for configuration. Ensure your `.env` file is not included in the deployment (the ADK handles secrets differently, or you can pass them as env vars).

For Agent Engine, you typically pass environment variables during deployment or let the agent pick them up from the runtime environment if configured.

## Deployment Steps

The `adk` CLI simplifies the deployment process by containerizing your agent and deploying it to Vertex AI.

### 1. Prepare the Environment

Ensure you are in the project root directory and your virtual environment is active.

```bash
source .venv/bin/activate
```

### 2. Deploy to Agent Engine

Run the following command to deploy. Replace the placeholders with your specific values.

```bash
adk deploy agent_engine \
  --project_id YOUR_PROJECT_ID \
  --location us-central1 \
  --staging_bucket gs://YOUR_STAGING_BUCKET_NAME \
  --display_name "scientific-content-agent"
```

*   `--project_id`: Your Google Cloud Project ID.
*   `--location`: The region to deploy to (e.g., `us-central1`).
*   `--staging_bucket`: A Cloud Storage bucket for staging artifacts (must be in the same region).
*   `--display_name`: The name for your Reasoning Engine instance.

### 3. Verify Deployment

After the command completes successfully, it will output the `resource_name` of the deployed Reasoning Engine (format: `projects/.../locations/.../reasoningEngines/...`).

You can verify it in the [Google Cloud Console](https://console.cloud.google.com/vertex-ai/reasoning-engines).

## Testing the Deployed Agent

You can test the deployed agent using the Python SDK or the `adk` CLI if supported.

```python
from google.cloud import aiplatform
import vertexai.preview.reasoning_engines

# Initialize Vertex AI
vertexai.init(project="YOUR_PROJECT_ID", location="us-central1")

# Get the remote agent
remote_agent = vertexai.preview.reasoning_engines.ReasoningEngine("YOUR_REASONING_ENGINE_RESOURCE_NAME")

# Query the agent
response = remote_agent.query(
    input="Generate a blog post about the future of AI agents."
)
print(response)
```
