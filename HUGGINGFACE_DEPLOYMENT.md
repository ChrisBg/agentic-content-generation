# Deploying to Hugging Face Spaces

This guide shows you how to deploy the Scientific Content Generation Agent to Hugging Face Spaces for free hosting and a public demo.

## Prerequisites

1. **Hugging Face Account**: Sign up at https://huggingface.co/join
2. **Google API Key**: Get one from https://aistudio.google.com/app/api_keys
3. **Git**: Installed on your machine

## Step-by-Step Deployment

### 1. Create a New Space on Hugging Face

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in the details:
   - **Owner**: Your username
   - **Space name**: `scientific-content-agent` (or your preferred name)
   - **License**: MIT
   - **Select the SDK**: Choose **Gradio**
   - **Space hardware**: CPU basic (free tier is sufficient)
   - **Visibility**: Public (or Private if you prefer)
4. Click **"Create Space"**

### 2. Clone the Space Repository

```bash
# Clone your newly created Space
git clone https://huggingface.co/spaces/YOUR_USERNAME/scientific-content-agent
cd scientific-content-agent
```

### 3. Copy Files from Your Project

Copy the necessary files from your local project:

```bash
# From the agentic-content-generation directory, copy these files:
cp -r src/ ../scientific-content-agent/
cp main.py ../scientific-content-agent/
cp app.py ../scientific-content-agent/
cp ui_app.py ../scientific-content-agent/
cp requirements.txt ../scientific-content-agent/
cp README_HF_SPACES.md ../scientific-content-agent/README.md
cp .env.example ../scientific-content-agent/

# Optional: Copy profile example
cp profile.example.yaml ../scientific-content-agent/
```

Or manually copy these files:
- `src/` (entire directory)
- `main.py`
- `app.py`
- `ui_app.py`
- `requirements.txt`
- `README_HF_SPACES.md` → rename to `README.md`
- `.env.example`

### 4. Configure API Key as a Secret

**Option A: Via Web Interface (Recommended)**

1. Go to your Space settings: `https://huggingface.co/spaces/YOUR_USERNAME/scientific-content-agent/settings`
2. Click on **"Variables and secrets"** section
3. Click **"New secret"**
4. Add:
   - **Name**: `GOOGLE_API_KEY`
   - **Value**: Your Google API key from AI Studio
5. Click **"Save"**

**Option B: Via Environment Variable in Code**

Add this to `app.py` if you prefer users to enter their own API key:

```python
import os
from ui_app import create_ui

# For Hugging Face Spaces deployment
if __name__ == "__main__":
    # Check for API key in environment (from HF Spaces secrets)
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️ Warning: GOOGLE_API_KEY not set. Users will need to configure it in Settings.")

    app = create_ui()
    app.queue()
    app.launch()
```

### 5. Push to Hugging Face

```bash
cd scientific-content-agent

# Add all files
git add .

# Commit
git commit -m "Initial deployment of Scientific Content Generation Agent"

# Push to Hugging Face
git push origin main
```

### 6. Wait for Build

1. Go to your Space URL: `https://huggingface.co/spaces/YOUR_USERNAME/scientific-content-agent`
2. You'll see the build logs in real-time
3. The build typically takes 2-5 minutes
4. Once complete, your app will be live!

## Verifying Deployment

### Test the Space

1. **Generate Content Tab**:
   - Enter a topic like "AI Agents and Multi-Agent Systems"
   - Select platforms (Blog, LinkedIn, Twitter)
   - Click "Generate Content"
   - Wait 2-5 minutes for results

2. **Profile Editor Tab**:
   - Click "Load Profile"
   - Edit fields as needed
   - Click "Validate Profile"
   - Click "Save Profile"

3. **Session History Tab**:
   - Click "Refresh Sessions"
   - View past generations

4. **Settings Tab**:
   - If you didn't set a secret, users can enter their API key here
   - Configure model and content preferences

## Troubleshooting

### Build Fails

**Error**: `ModuleNotFoundError`
- **Solution**: Check that `requirements.txt` includes all dependencies
- Verify file paths in `app.py` match your structure

**Error**: `No space left on device`
- **Solution**: Your Space may need more storage
- Upgrade to a larger hardware tier in Settings

### App Runs But Can't Generate Content

**Error**: `GOOGLE_API_KEY not found`
- **Solution**: Add the API key as a secret in Space settings
- Or configure it in the Settings tab

**Error**: `404 NOT_FOUND` for model
- **Solution**: Check `src/config.py` uses a valid model name
- Should be `gemini-2.0-flash-exp` or another valid Gemini model

### Slow Response Time

- This is normal! The agent pipeline takes 2-5 minutes
- Progress bar shows which agent is running
- Consider using Vertex AI deployment for production speed

## Updating Your Space

To update your deployed Space:

```bash
cd scientific-content-agent

# Make changes to files
# ...

# Commit and push
git add .
git commit -m "Update: describe your changes"
git push origin main
```

Hugging Face will automatically rebuild and redeploy.

## Configuration Options

### Custom Domain (Pro Feature)

Upgrade to HF Pro to use a custom domain:
1. Go to Space settings
2. Click "Custom domain"
3. Follow instructions

### Hardware Upgrades

For better performance:
1. Go to Space settings
2. Under "Hardware", choose:
   - **CPU basic** (free): Works fine for demos
   - **CPU upgrade** (paid): Faster response
   - **GPU** (paid): Not needed for this app

### Making Space Private

1. Go to Space settings
2. Under "Visibility", select "Private"
3. Share access with specific users

## Tips for Portfolio Demo

### Showcase in Kaggle Submission

1. **Take Screenshots**:
   - Main interface with all 4 tabs
   - Generate Content tab with results
   - Profile Editor with your data
   - Session History showing past generations

2. **Write Description**:
   - "Live demo available at: https://huggingface.co/spaces/YOUR_USERNAME/scientific-content-agent"
   - "Try it with your own research topics!"
   - "Fully deployed AI agent system with web interface"

3. **Add to README**:
   - Link to HF Space in your project README
   - Badge: `[![Hugging Face Space](https://img.shields.io/badge/🤗-Hugging%20Face-yellow)](https://huggingface.co/spaces/YOUR_USERNAME/scientific-content-agent)`

### Embed in Website

You can embed your Space in any website:

```html
<iframe
  src="https://YOUR_USERNAME-scientific-content-agent.hf.space"
  frameborder="0"
  width="850"
  height="450"
></iframe>
```

## Cost

- **Basic CPU Space**: **FREE** ✅
- **Secrets (API keys)**: **FREE** ✅
- **Public hosting**: **FREE** ✅

Your Google API key usage is billed separately by Google (generous free tier).

## Next Steps

After deployment:

1. ✅ Test all features thoroughly
2. ✅ Share the link with colleagues for feedback
3. ✅ Add to your Kaggle capstone submission (+5 bonus points!)
4. ✅ Include in your portfolio/resume
5. ✅ Share on LinkedIn/Twitter to showcase your work

## Support

- **HF Spaces Docs**: https://huggingface.co/docs/hub/spaces
- **Gradio Docs**: https://gradio.app/docs
- **Issues**: Report at your GitHub repo

---

**Congratulations!** 🎉 Your AI agent is now publicly accessible and ready to showcase!
