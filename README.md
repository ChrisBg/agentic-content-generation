# Scientific Content Generation Agent

An AI-powered agent system that generates research-backed content (blog articles, LinkedIn posts, Twitter threads) from scientific topics. Built with Google's Agent Development Kit (ADK) for the Agents Intensive Week capstone project.

## Features

- 🔬 **Research-Backed Content**: Automatically searches academic papers and current trends
- 📝 **Multi-Platform Output**: Generates tailored content for blogs, LinkedIn, and Twitter
- 🎯 **Professional Credibility**: Creates content that builds scientific authority
- 📚 **Proper Citations**: Includes formatted references and source attribution
- 🤖 **Multi-Agent Pipeline**: Uses specialized agents for research, strategy, generation, and review

## Architecture

The system uses a **Sequential Agent Pipeline** with four specialized agents:

1. **ResearchAgent**: Searches for academic papers (arXiv) and current trends (Google Search)
2. **StrategyAgent**: Analyzes research and plans content approach for each platform
3. **ContentGeneratorAgent**: Creates platform-specific drafts (blog, LinkedIn, Twitter)
4. **ReviewAgent**: Verifies accuracy, adds citations, and polishes content

## Installation

### Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- Google AI API Key ([Get one here](https://aistudio.google.com/app/api_keys))

### Quick Setup

See [SETUP.md](SETUP.md) for detailed step-by-step instructions.

```bash
# 1. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Navigate to project directory
cd agentic-content-generation

# 3. Install dependencies with uv
uv pip install -e ".[dev]"

# 4. Configure API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 5. Check code quality (optional)
make format  # Format code with ruff
make lint    # Check for issues

# 6. Run the agent
make run
```

## Usage

### Basic Usage

```bash
python main.py
```

This runs the agent with a default example topic.

### Custom Topic

Edit [main.py](main.py) and modify the `topic` variable:

```python
topic = "Your Research Topic Here"

preferences = {
    "platforms": ["blog", "linkedin", "twitter"],
    "tone": "professional",
    "target_audience": "researchers and practitioners",
}

result = await run_content_generation(topic, preferences)
```

### Programmatic Usage

```python
from main import run_content_generation
import asyncio

async def generate():
    topic = "Transformer Models in NLP"
    result = await run_content_generation(topic)
    print(result)

asyncio.run(generate())
```

## Output

The agent generates:

1. **Blog Article** (1000-2000 words)
   - Structured with headings
   - Deep dive into research
   - Complete references section

2. **LinkedIn Post** (300-800 words)
   - Professional tone
   - Key takeaways
   - Engagement hooks

3. **Twitter Thread** (8-12 tweets)
   - Numbered tweets
   - Under 280 chars each
   - Strategic emojis and hashtags

4. **Citations**
   - Formatted references (APA style)
   - Source links

## Project Structure

```
agentic-content-generation/
├── src/
│   ├── __init__.py
│   ├── agents.py          # Agent definitions (Research, Strategy, Content, Review)
│   ├── config.py          # Configuration and constants
│   └── tools.py           # Custom tools (search_papers, format_for_platform, etc.)
├── tests/
│   ├── integration_tests.evalset.json  # Test cases
│   └── test_config.json                # Evaluation config
├── output/                # Generated content files
├── notebooks/             # Course notebooks (reference)
├── main.py               # Main entry point
├── pyproject.toml        # Project config (uv, ruff)
├── Makefile              # Development commands
├── requirements.txt      # Legacy pip dependencies
├── .env.example         # Environment variable template
├── SETUP.md             # Quick setup guide
└── README.md            # This file
```

## Development

### Code Quality with Ruff

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Format code
make format

# Check for linting issues
make lint

# Auto-fix issues
make fix

# Run all checks
make check
```

### Running Tests

```bash
# Run pytest tests
make test

# Run ADK evaluation
adk eval src.agents tests/integration_tests.evalset.json \
  --config_file_path=tests/test_config.json
```

### Web UI for Interactive Testing

```bash
# Start ADK web interface
adk web --log_level DEBUG
```

### Adding Custom Tools

Add new tools in [src/tools.py](src/tools.py):

```python
def my_custom_tool(param: str) -> Dict[str, Any]:
    """Tool description for the LLM.

    Args:
        param: Parameter description

    Returns:
        Dict with status and data
    """
    return {"status": "success", "data": result}
```

Then add to agent in [src/agents.py](src/agents.py):

```python
from .tools import my_custom_tool

agent = LlmAgent(
    tools=[my_custom_tool],
    # ... other config
)
```

## Configuration

Key settings in [src/config.py](src/config.py):

- `DEFAULT_MODEL`: Gemini model to use (default: `gemini-2.0-flash-exp`)
- `MAX_PAPERS_PER_SEARCH`: Number of papers to search (default: 5)
- `CITATION_STYLE`: Citation format (default: "apa")
- `SUPPORTED_PLATFORMS`: Available platforms

## Troubleshooting

### API Key Issues

```bash
# Verify API key is set
echo $GOOGLE_API_KEY

# Test API access
python -c "import os; from google.genai import types; print('API key loaded' if os.getenv('GOOGLE_API_KEY') else 'API key missing')"
```

### Module Import Errors

```bash
# Ensure you're in the project directory
cd agentic-content-generation

# Reinstall dependencies
pip install -r requirements.txt
```

### Paper Search Timeout

The `search_papers` tool uses arXiv API which may be slow. Increase timeout in [src/tools.py](src/tools.py:44):

```python
response = requests.get(base_url, params=params, timeout=30)  # Increase from 10 to 30
```

## Future Enhancements

- [ ] Add more research sources (Google Scholar, PubMed)
- [ ] Implement session memory for user preferences
- [ ] Add human-in-the-loop approval for content
- [ ] Support more platforms (Medium, Instagram)
- [ ] Add content scheduling and publishing
- [ ] Integrate with LangSmith for evaluation

## License

This project was created for the Agents Intensive Week capstone project (Kaggle/Google).

## Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Kaggle Capstone Project](https://www.kaggle.com/competitions/agents-intensive-capstone-project)
- [Google AI Studio](https://aistudio.google.com/)
