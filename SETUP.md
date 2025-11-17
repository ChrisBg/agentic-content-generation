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

## Step 7: Run Your First Content Generation

```bash
# Using make
make run

# Or directly
python main.py
```

This will generate content on the default topic: "Large Language Models and AI Agents"

## Step 8: Customize for Your Topic

Edit `main.py` and change these lines:

```python
# Around line 70
topic = "Your Research Topic Here"  # Change this

preferences = {
    "platforms": ["blog", "linkedin", "twitter"],
    "tone": "professional",  # or "accessible", "academic", etc.
    "target_audience": "Your target audience",  # customize this
}
```

Then run again:
```bash
make run
```

## Next Steps

### Use the Interactive Web UI

```bash
adk web --log_level DEBUG
```

Then open the URL shown in the terminal to interact with your agent in a chat interface.

### Generate Content for Different Topics

Edit the topic in `main.py` and run multiple times for different subjects.

### Check Your Output

Generated content is saved in the `output/` directory with filenames based on your topic.

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

- See [README.md](README.md) for detailed documentation
- See [CLAUDE.md](../CLAUDE.md) for architecture details
- Check the [notebooks/](notebooks/) for ADK framework examples
- Run `make help` to see available commands
