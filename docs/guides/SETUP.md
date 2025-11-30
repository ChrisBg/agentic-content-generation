# Quick Setup Guide

Follow these steps to get your Scientific Content Generation Agent running with **uv** and **ruff**.

## Step 1: Get Your Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/api_keys)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

## Step 2: Install UV (if not already installed)

```bash
# Install uv (universal Python package installer)
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell):
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify installation:
```bash
uv --version
```

## Step 3: Install Dependencies with UV

```bash
cd agentic-content-generation

# UV will automatically create a virtual environment and install dependencies
uv pip install -e .

# Install development tools (ruff for linting/formatting, pytest for testing)
uv pip install -e ".[dev]"
```

## Step 4: Configure API Key

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
# Replace "your_api_key_here" with the key you copied in Step 1
```

Your `.env` file should look like:
```bash
GOOGLE_API_KEY=AIzaSy...your_actual_key...
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

## Step 5: Check Code Quality

```bash
# Format code with ruff (auto-fixes style issues)
make format

# Check for linting issues
make lint

# Auto-fix linting issues
make fix

# Run all checks (format + lint)
make check
```

## Step 6: Test the Installation

```bash
# Quick test of the arXiv search tool
python -c "from src.tools import search_papers; import json; print(json.dumps(search_papers('AI agents', max_results=1), indent=2))"
```

If you see paper results, you're ready!

## Step 7: Set Up Your Profile

```bash
# Create your profile configuration
python main.py --init-profile

# This creates: ~/.agentic-content-generation/profile.yaml
# Edit this file with your information:
# - Your name and target professional role
# - Expertise areas (e.g., "Machine Learning", "NLP")
# - Portfolio links (GitHub, LinkedIn, Kaggle)
# - Notable projects you want to mention
# - Content goals (opportunities, credibility, visibility)
```

Example profile customization:
```yaml
name: Your Name
target_role: AI Consultant
expertise_areas:
  - Machine Learning
  - Natural Language Processing
github_username: your-github
linkedin_url: https://linkedin.com/in/yourprofile
```

See [profile.example.yaml](profile.example.yaml) for a complete example.

## Step 8: Validate Your Profile

```bash
# Check your profile for errors and warnings
python main.py --validate-profile
```

Fix any errors or warnings shown before proceeding.

## Step 9: Run Your First Content Generation

```bash
# Generate content with default topic
python main.py

# Or with a custom topic
python main.py --topic "Transformer Models in NLP"

# Using make (default topic)
make run
```

This generates personalized content based on your profile!

## Next Steps

### Manage Your Sessions

```bash
# List all previous conversations
python main.py --list-sessions

# Resume a conversation
python main.py --session-id <SESSION_ID>

# Delete old sessions
python main.py --delete-session <SESSION_ID>
```

### Use the Interactive Web UI

```bash
adk web --log_level DEBUG
```

Then open the URL shown in the terminal to interact with your agent in a chat interface.

### Generate Content for Different Topics

```bash
# Just change the topic in the command
python main.py --topic "AI Ethics and Bias"
python main.py --topic "Quantum Machine Learning"
python main.py --topic "Edge AI Deployment"
```

### Check Your Output

Generated content is saved in the `output/` directory with filenames based on your topic.

### Advanced Features

- **Profile Validation**: `python main.py --validate-profile`
- **Session Management**: `python main.py --list-sessions`
- **Custom Preferences**: Edit your `profile.yaml` to change tone, goals, and expertise

## Available Make Commands

Run `make help` to see all available commands:

```bash
make help
```

Commands:
- `make install` - Install dependencies with uv
- `make dev` - Install development dependencies
- `make format` - Format code with ruff
- `make lint` - Lint code with ruff
- `make check` - Run format and lint checks
- `make fix` - Auto-fix linting issues
- `make test` - Run tests with pytest
- `make run` - Run the main agent
- `make clean` - Clean up generated files

## Troubleshooting

### "GOOGLE_API_KEY not found"

Make sure:
1. You created the `.env` file (not just `.env.example`)
2. You added your actual API key (not the placeholder text)
3. You're running from the `agentic-content-generation/` directory

### "Module 'google.adk' not found"

Reinstall dependencies with uv:
```bash
uv pip install -e ".[dev]"
```

### "uv: command not found"

Install uv first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Then restart your terminal
```

### arXiv Search Takes Too Long

The first search can be slow. If it times out, increase the timeout in [src/tools.py](src/tools.py:44):
```python
response = requests.get(base_url, params=params, timeout=30)
```

### Code Quality Issues

Run ruff to auto-fix most issues:
```bash
make fix
```

For remaining issues, run:
```bash
make lint
```

## Need Help?

- See [README.md](../../README.md) for main documentation
- See [CLAUDE.md](../../CLAUDE.md) for architecture details (if available)
- Check the [notebooks/](notebooks/) for ADK framework examples
- Run `make help` to see available commands
