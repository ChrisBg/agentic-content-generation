---
title: Scientific Content Generation Agent
emoji: 🔬
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.0.1
app_file: app.py
pinned: false
license: mit
---

# 🔬 Scientific Content Generation Agent

An AI-powered multi-agent system that generates research-backed content (blog articles, LinkedIn posts, Twitter threads) from scientific topics. Built with Google's Agent Development Kit (ADK).

## Features

- 🔬 **Deep Research**: Searches academic papers (arXiv) and web sources (DuckDuckGo)
- 📝 **Multi-Platform Output**: Blog, LinkedIn, and Twitter content
- 🎯 **Professional Credibility**: SEO-optimized for recruiter visibility
- 📚 **Proper Citations**: APA-formatted references
- 👤 **User Profiles**: Personalized content based on your expertise
- 💾 **Session Management**: Resume conversations and track history

## How to Use

1. **Generate Content Tab**: Enter a research topic and click Generate
2. **Profile Editor Tab**: Customize your professional profile
3. **Session History Tab**: View and resume past generations
4. **Settings Tab**: Configure API key and preferences

## Requirements

⚠️ **Important**: You need a Google API key to use this app.

Get your free API key from: [Google AI Studio](https://aistudio.google.com/app/api_keys)

Then add it in the **Settings Tab** or set it as a Space secret named `GOOGLE_API_KEY`.

## Architecture

Multi-agent pipeline with 5 specialized agents:
1. **ResearchAgent**: Searches papers and trends
2. **StrategyAgent**: Plans content approach
3. **ContentGeneratorAgent**: Creates platform-specific content
4. **LinkedInOptimizationAgent**: Optimizes for opportunities
5. **ReviewAgent**: Adds citations and validates

## Local Development

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/scientific-content-agent
cd scientific-content-agent
pip install -r requirements.txt
python app.py
```

## About

Built for the Google/Kaggle Agents Intensive Week capstone project.

- **Framework**: Google Agent Development Kit (ADK)
- **Model**: Gemini 2.0 Flash
- **UI**: Gradio 6.0

## License

MIT License - See LICENSE file for details
