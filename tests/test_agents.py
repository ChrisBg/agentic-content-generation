"""Unit tests for agent definitions in src/agents.py."""

from src.agents import (
    create_content_generation_pipeline,
    create_content_generator_agent,
    create_linkedin_optimization_agent,
    create_research_agent,
    create_review_agent,
    create_strategy_agent,
)


class TestResearchAgent:
    """Tests for the ResearchAgent."""

    def test_create_research_agent(self):
        """Test that ResearchAgent is created with correct configuration."""
        agent = create_research_agent()

        assert agent.name == "ResearchAgent"
        assert agent.output_key == "research_findings"
        assert len(agent.tools) == 2  # search_papers, extract_key_findings
        assert agent.description is not None
        assert "search" in agent.description.lower()

    def test_research_agent_has_tools(self):
        """Test that ResearchAgent has required tools."""
        agent = create_research_agent()

        tool_names = [tool.__name__ for tool in agent.tools]
        assert "search_papers" in tool_names
        assert "extract_key_findings" in tool_names

    def test_research_agent_instruction(self):
        """Test that ResearchAgent has comprehensive instruction."""
        agent = create_research_agent()

        instruction = agent.instruction.lower()
        assert "research" in instruction
        assert "papers" in instruction
        assert "search" in instruction
        assert "findings" in instruction


class TestStrategyAgent:
    """Tests for the StrategyAgent."""

    def test_create_strategy_agent(self):
        """Test that StrategyAgent is created with correct configuration."""
        agent = create_strategy_agent()

        assert agent.name == "StrategyAgent"
        assert agent.output_key == "content_strategy"
        assert len(agent.tools) == 0  # Strategy agent uses reasoning, not tools
        assert agent.description is not None

    def test_strategy_agent_references_research_findings(self):
        """Test that StrategyAgent instruction references research_findings placeholder."""
        agent = create_strategy_agent()

        instruction = agent.instruction
        assert "{research_findings}" in instruction

    def test_strategy_agent_focuses_on_opportunities(self):
        """Test that StrategyAgent instruction emphasizes opportunities."""
        agent = create_strategy_agent()

        instruction = agent.instruction.lower()
        assert "opportunity" in instruction or "opportunities" in instruction
        assert "professional" in instruction
        assert "linkedin" in instruction
        assert "recruiter" in instruction


class TestContentGeneratorAgent:
    """Tests for the ContentGeneratorAgent."""

    def test_create_content_generator_agent(self):
        """Test that ContentGeneratorAgent is created correctly."""
        agent = create_content_generator_agent()

        assert agent.name == "ContentGeneratorAgent"
        assert agent.output_key == "generated_content"
        assert len(agent.tools) == 1  # format_for_platform
        assert agent.description is not None

    def test_content_generator_has_format_tool(self):
        """Test that ContentGeneratorAgent has format_for_platform tool."""
        agent = create_content_generator_agent()

        tool_names = [tool.__name__ for tool in agent.tools]
        assert "format_for_platform" in tool_names

    def test_content_generator_references_inputs(self):
        """Test that ContentGeneratorAgent references required inputs."""
        agent = create_content_generator_agent()

        instruction = agent.instruction
        assert "{research_findings}" in instruction
        assert "{content_strategy}" in instruction

    def test_content_generator_targets_three_platforms(self):
        """Test that ContentGeneratorAgent targets all three platforms."""
        agent = create_content_generator_agent()

        instruction = agent.instruction.lower()
        assert "blog" in instruction
        assert "linkedin" in instruction
        assert "twitter" in instruction


class TestLinkedInOptimizationAgent:
    """Tests for the LinkedInOptimizationAgent."""

    def test_create_linkedin_optimization_agent(self):
        """Test that LinkedInOptimizationAgent is created correctly."""
        agent = create_linkedin_optimization_agent()

        assert agent.name == "LinkedInOptimizationAgent"
        assert agent.output_key == "optimized_linkedin"
        assert (
            len(agent.tools) == 3
        )  # generate_seo_keywords, create_engagement_hooks, search_industry_trends
        assert agent.description is not None

    def test_linkedin_agent_has_optimization_tools(self):
        """Test that LinkedInOptimizationAgent has all optimization tools."""
        agent = create_linkedin_optimization_agent()

        tool_names = [tool.__name__ for tool in agent.tools]
        assert "generate_seo_keywords" in tool_names
        assert "create_engagement_hooks" in tool_names
        assert "search_industry_trends" in tool_names

    def test_linkedin_agent_focuses_on_opportunities(self):
        """Test that LinkedInOptimizationAgent focuses on opportunities."""
        agent = create_linkedin_optimization_agent()

        instruction = agent.instruction.lower()
        assert "seo" in instruction
        assert "engagement" in instruction
        assert "portfolio" in instruction
        assert "business value" in instruction or "business" in instruction
        assert "opportunities" in instruction or "opportunity" in instruction

    def test_linkedin_agent_references_inputs(self):
        """Test that LinkedInOptimizationAgent references required inputs."""
        agent = create_linkedin_optimization_agent()

        instruction = agent.instruction
        assert "{research_findings}" in instruction
        assert "{content_strategy}" in instruction
        assert "{generated_content}" in instruction


class TestReviewAgent:
    """Tests for the ReviewAgent."""

    def test_create_review_agent(self):
        """Test that ReviewAgent is created correctly."""
        agent = create_review_agent()

        assert agent.name == "ReviewAgent"
        assert agent.output_key == "final_content"
        assert len(agent.tools) == 2  # generate_citations, analyze_content_for_opportunities
        assert agent.description is not None

    def test_review_agent_has_verification_tools(self):
        """Test that ReviewAgent has citation and analysis tools."""
        agent = create_review_agent()

        tool_names = [tool.__name__ for tool in agent.tools]
        assert "generate_citations" in tool_names
        assert "analyze_content_for_opportunities" in tool_names

    def test_review_agent_references_all_inputs(self):
        """Test that ReviewAgent references all required inputs."""
        agent = create_review_agent()

        instruction = agent.instruction
        assert "{research_findings}" in instruction
        assert "{generated_content}" in instruction
        assert "{optimized_linkedin}" in instruction

    def test_review_agent_performs_analysis(self):
        """Test that ReviewAgent instruction includes opportunity analysis."""
        agent = create_review_agent()

        instruction = agent.instruction.lower()
        assert "opportunity" in instruction
        assert "score" in instruction or "scoring" in instruction
        assert "citation" in instruction
        assert "verify" in instruction or "accuracy" in instruction


class TestContentGenerationPipeline:
    """Tests for the complete content generation pipeline."""

    def test_create_pipeline(self):
        """Test that the pipeline is created successfully."""
        pipeline = create_content_generation_pipeline()

        assert pipeline is not None
        assert pipeline.name == "ScientificContentAgent"
        assert hasattr(pipeline, "sub_agents")

    def test_pipeline_has_five_agents(self):
        """Test that the pipeline contains exactly 5 agents."""
        pipeline = create_content_generation_pipeline()

        assert len(pipeline.sub_agents) == 5

    def test_pipeline_agent_order(self):
        """Test that agents are in the correct sequential order."""
        pipeline = create_content_generation_pipeline()

        agent_names = [agent.name for agent in pipeline.sub_agents]

        # Verify correct order
        assert agent_names[0] == "ResearchAgent"
        assert agent_names[1] == "StrategyAgent"
        assert agent_names[2] == "ContentGeneratorAgent"
        assert agent_names[3] == "LinkedInOptimizationAgent"
        assert agent_names[4] == "ReviewAgent"

    def test_pipeline_state_flow(self):
        """Test that output keys flow correctly between agents."""
        pipeline = create_content_generation_pipeline()

        # ResearchAgent outputs research_findings
        assert pipeline.sub_agents[0].output_key == "research_findings"

        # StrategyAgent outputs content_strategy and should reference research_findings
        assert pipeline.sub_agents[1].output_key == "content_strategy"
        assert "{research_findings}" in pipeline.sub_agents[1].instruction

        # ContentGeneratorAgent outputs generated_content
        assert pipeline.sub_agents[2].output_key == "generated_content"
        assert "{research_findings}" in pipeline.sub_agents[2].instruction
        assert "{content_strategy}" in pipeline.sub_agents[2].instruction

        # LinkedInOptimizationAgent outputs optimized_linkedin
        assert pipeline.sub_agents[3].output_key == "optimized_linkedin"
        assert "{generated_content}" in pipeline.sub_agents[3].instruction

        # ReviewAgent outputs final_content
        assert pipeline.sub_agents[4].output_key == "final_content"
        assert "{generated_content}" in pipeline.sub_agents[4].instruction
        assert "{optimized_linkedin}" in pipeline.sub_agents[4].instruction

    def test_pipeline_description(self):
        """Test that pipeline has a description."""
        pipeline = create_content_generation_pipeline()

        assert pipeline.description is not None
        assert "content generation" in pipeline.description.lower()


class TestAgentIntegration:
    """Integration tests for agent interactions."""

    def test_all_agents_use_same_model(self):
        """Test that all agents use the configured model."""
        from src.config import DEFAULT_MODEL

        agents = [
            create_research_agent(),
            create_strategy_agent(),
            create_content_generator_agent(),
            create_linkedin_optimization_agent(),
            create_review_agent(),
        ]

        for agent in agents:
            # Check that the model is configured
            assert agent.model is not None
            assert hasattr(agent.model, "model")
            assert agent.model.model == DEFAULT_MODEL

    def test_all_agents_have_retry_config(self):
        """Test that all agents have retry configuration for reliability."""
        agents = [
            create_research_agent(),
            create_strategy_agent(),
            create_content_generator_agent(),
            create_linkedin_optimization_agent(),
            create_review_agent(),
        ]

        for agent in agents:
            # Check that retry options are configured
            assert agent.model is not None
            assert hasattr(agent.model, "retry_options")
            assert agent.model.retry_options is not None

    def test_agent_names_are_unique(self):
        """Test that all agents have unique names."""
        pipeline = create_content_generation_pipeline()

        agent_names = [agent.name for agent in pipeline.sub_agents]
        assert len(agent_names) == len(set(agent_names))  # No duplicates

    def test_agent_output_keys_are_unique(self):
        """Test that all agents have unique output keys."""
        pipeline = create_content_generation_pipeline()

        output_keys = [agent.output_key for agent in pipeline.sub_agents]
        assert len(output_keys) == len(set(output_keys))  # No duplicates

    def test_agents_have_descriptions(self):
        """Test that all agents have descriptions for observability."""
        agents = [
            create_research_agent(),
            create_strategy_agent(),
            create_content_generator_agent(),
            create_linkedin_optimization_agent(),
            create_review_agent(),
        ]

        for agent in agents:
            assert agent.description is not None
            assert len(agent.description) > 10  # Non-trivial description

    def test_agents_have_instructions(self):
        """Test that all agents have detailed instructions."""
        agents = [
            create_research_agent(),
            create_strategy_agent(),
            create_content_generator_agent(),
            create_linkedin_optimization_agent(),
            create_review_agent(),
        ]

        for agent in agents:
            assert agent.instruction is not None
            assert len(agent.instruction) > 100  # Detailed instruction


class TestAgentConfiguration:
    """Tests for agent configuration and settings."""

    def test_agents_use_config_constants(self):
        """Test that agents use configuration constants."""
        from src.config import (
            CONTENT_GENERATOR_AGENT_NAME,
            RESEARCH_AGENT_NAME,
            REVIEW_AGENT_NAME,
            STRATEGY_AGENT_NAME,
        )

        research = create_research_agent()
        strategy = create_strategy_agent()
        content = create_content_generator_agent()
        review = create_review_agent()

        assert research.name == RESEARCH_AGENT_NAME
        assert strategy.name == STRATEGY_AGENT_NAME
        assert content.name == CONTENT_GENERATOR_AGENT_NAME
        assert review.name == REVIEW_AGENT_NAME

    def test_pipeline_uses_root_agent_name(self):
        """Test that pipeline uses ROOT_AGENT_NAME from config."""
        from src.config import ROOT_AGENT_NAME

        pipeline = create_content_generation_pipeline()
        assert pipeline.name == ROOT_AGENT_NAME
