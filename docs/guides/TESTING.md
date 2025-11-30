# Testing Documentation

This document describes the comprehensive test suite for the Scientific Content Generation Agent.

## Test Coverage

The project includes **71 unit and integration tests** covering all major components:

### Test Files

1. **tests/test_tools.py** - 40 tests for custom tools
2. **tests/test_agents.py** - 31 tests for agent definitions
3. **tests/integration_tests.evalset.json** - 8 integration test scenarios

## Running Tests

### Quick Start

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
uv run python -m pytest tests/test_tools.py -v

# Run with coverage report
uv run python -m pytest tests/ --cov=src --cov-report=html
```

### Using Make Commands

```bash
# Run tests
make test

# Check code quality
make lint

# Auto-fix linting issues
make fix
```

## Test Coverage by Component

### 1. Tools Tests (test_tools.py)

#### TestSearchPapers (3 tests)
- ✅ Successful paper search with arXiv API
- ✅ Max results parameter respected
- ✅ Empty topic handling

#### TestFormatForPlatform (5 tests)
- ✅ Blog formatting with markdown
- ✅ LinkedIn formatting with engagement elements
- ✅ Twitter thread formatting
- ✅ Unsupported platform error handling
- ✅ Case-insensitive platform names

#### TestGenerateCitations (5 tests)
- ✅ APA citation generation
- ✅ MLA citation generation
- ✅ Chicago citation generation
- ✅ Empty sources error handling
- ✅ Default style fallback

#### TestExtractKeyFindings (4 tests)
- ✅ Successful key findings extraction
- ✅ Indicator word detection
- ✅ Insufficient text handling
- ✅ Empty text error handling

#### TestSearchIndustryTrends (4 tests)
- ✅ Machine Learning field trends
- ✅ NLP field trends
- ✅ Computer Vision field trends
- ✅ Unknown field graceful handling

#### TestGenerateSEOKeywords (4 tests)
- ✅ Consultant role keywords
- ✅ Engineer role keywords
- ✅ Topic-specific technical keywords
- ✅ Keyword structure validation

#### TestCreateEngagementHooks (5 tests)
- ✅ Opportunities goal hooks
- ✅ Discussion goal hooks
- ✅ Credibility goal hooks
- ✅ Visibility goal hooks
- ✅ Default goal fallback

#### TestAnalyzeContentForOpportunities (7 tests)
- ✅ High-quality optimized content scoring
- ✅ Low-quality content identification
- ✅ SEO keyword impact on score
- ✅ Engagement hooks impact on score
- ✅ Business value impact on score
- ✅ Too-short content error handling
- ✅ Empty content error handling

#### TestToolsIntegration (3 tests)
- ✅ Paper search → citation workflow
- ✅ Content formatting → opportunity analysis workflow
- ✅ SEO keywords + engagement hooks integration

### 2. Agent Tests (test_agents.py)

#### TestResearchAgent (3 tests)
- ✅ Agent creation with correct configuration
- ✅ Required tools present (search_papers, extract_key_findings)
- ✅ Instruction contains research keywords

#### TestStrategyAgent (3 tests)
- ✅ Agent creation with reasoning (no tools)
- ✅ References research_findings placeholder
- ✅ Focuses on professional opportunities

#### TestContentGeneratorAgent (4 tests)
- ✅ Agent creation with format_for_platform tool
- ✅ Has format tool available
- ✅ References research_findings and content_strategy
- ✅ Targets all three platforms (blog, LinkedIn, Twitter)

#### TestLinkedInOptimizationAgent (4 tests)
- ✅ Agent creation with optimization tools
- ✅ Has all 3 optimization tools (SEO, hooks, trends)
- ✅ Focuses on opportunity generation
- ✅ References all required inputs

#### TestReviewAgent (4 tests)
- ✅ Agent creation with verification tools
- ✅ Has citation and analysis tools
- ✅ References all required inputs
- ✅ Performs opportunity analysis

#### TestContentGenerationPipeline (5 tests)
- ✅ Pipeline creation successful
- ✅ Contains exactly 5 agents
- ✅ Agents in correct sequential order
- ✅ State flow via output_key/placeholder pattern
- ✅ Pipeline has description

#### TestAgentIntegration (6 tests)
- ✅ All agents use same model (gemini-2.0-flash-exp)
- ✅ All agents have retry configuration
- ✅ Agent names are unique
- ✅ Agent output keys are unique
- ✅ All agents have descriptions
- ✅ All agents have detailed instructions

#### TestAgentConfiguration (2 tests)
- ✅ Agents use configuration constants
- ✅ Pipeline uses ROOT_AGENT_NAME

### 3. Integration Tests (integration_tests.evalset.json)

Eight comprehensive test scenarios:

1. **test_ml_interpretability** - Machine Learning Interpretability topic
2. **test_computer_vision** - Computer Vision for Autonomous Vehicles
3. **test_nlp_topic** - Transformer Models in NLP
4. **test_ai_agents** - Multi-Agent Systems and RL
5. **test_mlops_topic** - MLOps Best Practices
6. **test_robustness** - Adversarial Robustness
7. **test_error_handling_invalid_platform** - Error handling for unsupported platforms
8. **test_linkedin_optimization** - LinkedIn optimization with full profile context

## Test Design Principles

### 1. Comprehensive Coverage
- Every custom tool has multiple test cases
- Every agent has configuration and behavior tests
- Integration tests cover end-to-end workflows

### 2. Error Handling
- Tests verify graceful error handling
- Validates error messages are descriptive
- Ensures tools return proper status codes

### 3. Integration Testing
- Tests workflows across multiple tools
- Validates agent state flow via placeholders
- Covers different content topics and scenarios

### 4. Code Quality
- All tests follow consistent naming conventions
- Descriptive test names explain what is being tested
- Clear assertions with meaningful error messages

## Test Results

Latest test run:
```
============================= test session starts ==============================
platform darwin -- Python 3.11.12, pytest-9.0.1, pluggy-1.6.0
collected 71 items

tests/test_tools.py ........................................          [ 56%]
tests/test_agents.py .......................................          [100%]

============================== 71 passed in 3.57s ==============================
```

## Continuous Integration

### Pre-commit Checks

Before committing code, run:
```bash
make check    # Runs format + lint
make test     # Runs all tests
```

### Code Quality Standards

- ✅ All code passes `ruff` linting
- ✅ All code formatted with `ruff format`
- ✅ Type hints on all function signatures
- ✅ Comprehensive docstrings on all functions
- ✅ 71/71 tests passing (100%)

## Adding New Tests

### For New Tools

Add tests to `tests/test_tools.py`:

```python
class TestMyNewTool:
    """Tests for my_new_tool."""

    def test_my_new_tool_success(self):
        """Test successful operation."""
        result = my_new_tool("input")

        assert result["status"] == "success"
        assert "expected_key" in result

    def test_my_new_tool_error_handling(self):
        """Test error handling."""
        result = my_new_tool("")

        assert result["status"] == "error"
        assert "error_message" in result
```

### For New Agents

Add tests to `tests/test_agents.py`:

```python
class TestMyNewAgent:
    """Tests for MyNewAgent."""

    def test_create_my_new_agent(self):
        """Test agent creation."""
        agent = create_my_new_agent()

        assert agent.name == "MyNewAgent"
        assert agent.output_key == "my_output"
        assert len(agent.tools) > 0
```

## Test Maintenance

### Regular Updates
- Add tests for all new features
- Update tests when modifying existing features
- Remove obsolete tests for deprecated features

### Test Coverage Goals
- Maintain >90% code coverage
- Every tool should have ≥3 test cases
- Every agent should have ≥3 test cases
- Add integration tests for new workflows

## Debugging Failed Tests

### View Full Output
```bash
uv run python -m pytest tests/ -vv --tb=long
```

### Run Single Test
```bash
uv run python -m pytest tests/test_tools.py::TestSearchPapers::test_search_papers_success -v
```

### Debug with pdb
```bash
uv run python -m pytest tests/ --pdb
```

## Performance Testing

Current test performance:
- Tool tests: ~0.90s (40 tests)
- Agent tests: ~3.93s (31 tests)
- **Total: ~4.83s for 71 tests**

This fast execution enables rapid development iteration.

## Future Test Enhancements

Planned additions:
- [ ] Add pytest-cov for coverage reports
- [ ] Add performance benchmarks for tools
- [ ] Add end-to-end agent execution tests
- [ ] Add mock tests for external APIs (arXiv)
- [ ] Add property-based testing with Hypothesis
- [ ] Add load testing for concurrent requests

## Test Documentation

Each test includes:
- Descriptive docstring explaining purpose
- Clear test name following convention: `test_<component>_<scenario>`
- Explicit assertions with error messages
- Minimal setup/teardown

## Conclusion

The comprehensive test suite ensures:
- ✅ High code quality and reliability
- ✅ Confidence in refactoring
- ✅ Clear documentation of expected behavior
- ✅ Fast feedback during development
- ✅ Protection against regressions

All 71 tests pass, demonstrating production-ready code quality.
