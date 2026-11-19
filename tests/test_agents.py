"""Unit tests for the v2 Hybrid Multi-LLM ADK pipeline in src/agents.py."""

from __future__ import annotations

from google.adk.agents import LoopAgent, ParallelAgent, SequentialAgent

from src.agents import (
    create_content_generation_pipeline,
    create_editorial_critic,
    create_fact_checker_critic,
    create_literature_agent,
    create_outline_blueprint_agent,
    create_personal_context_agent,
    create_refiner_agent,
    create_visual_asset_agent,
)
from src.config import MAX_REFINEMENT_ITERATIONS, ROOT_AGENT_NAME
from src.llm_router import ModelRouter


class TestIndividualAgents:
    """Verify individual stage agents and their tools/output keys."""

    def test_outline_blueprint_agent(self):
        agent = create_outline_blueprint_agent(ModelRouter(env={"GOOGLE_API_KEY": "test-key"}))
        assert agent.output_key == "content_blueprint"
        assert agent.tools == []

    def test_literature_agent_tools(self):
        agent = create_literature_agent(ModelRouter(env={"GOOGLE_API_KEY": "test-key"}))
        tool_names = [t.__name__ for t in agent.tools]
        assert "search_semantic_scholar" in tool_names
        assert "verify_citation_semantic_scholar" in tool_names
        assert "search_arxiv_papers" in tool_names
        assert "generate_bibtex" in tool_names
        assert agent.output_key == "verified_research"

    def test_personal_context_agent_tools(self):
        agent = create_personal_context_agent(ModelRouter(env={"GOOGLE_API_KEY": "test-key"}))
        tool_names = [t.__name__ for t in agent.tools]
        assert "retrieve_personal_evidence" in tool_names
        assert "get_voice_and_style_guide" in tool_names
        assert agent.output_key == "personal_context"

    def test_visual_asset_agent_tools(self):
        agent = create_visual_asset_agent(ModelRouter(env={"GOOGLE_API_KEY": "test-key"}))
        tool_names = [t.__name__ for t in agent.tools]
        assert "render_data_chart" in tool_names
        assert "render_architecture_diagram" in tool_names
        assert "render_demo_overlays" in tool_names
        assert agent.output_key == "generated_visuals"

    def test_critics_and_refiner(self):
        router = ModelRouter(env={"GOOGLE_API_KEY": "test-key"})
        channels = ["linkedin", "x", "youtube"]

        fc = create_fact_checker_critic(channels, router)
        ed = create_editorial_critic(channels, router)
        ref = create_refiner_agent(channels, router)

        assert fc.output_key == "fact_check_report"
        assert "{draft_linkedin}" in fc.instruction
        assert "{draft_x}" in fc.instruction
        assert "{draft_youtube}" in fc.instruction

        assert ed.output_key == "editorial_critique"
        assert "validate_deliverables_deterministic" in [t.__name__ for t in ed.tools]

        ref_tools = [t.__name__ for t in ref.tools]
        assert "exit_loop" in ref_tools
        assert "render_linkedin_carousel_pdf" in ref_tools
        assert "render_short_explainer_video" in ref_tools
        assert ref.output_key == "final_content"


class TestHybridPipeline:
    """Verify the 4-stage Sequential -> Parallel -> Parallel -> Loop ADK architecture."""

    def test_default_pipeline_structure(self):
        pipeline = create_content_generation_pipeline()
        assert isinstance(pipeline, SequentialAgent)
        assert pipeline.name == ROOT_AGENT_NAME
        assert len(pipeline.sub_agents) == 4

        stage1, stage2, stage3, stage4 = pipeline.sub_agents
        assert stage1.name == "OutlineBlueprintAgent"
        assert isinstance(stage2, ParallelAgent)
        assert len(stage2.sub_agents) == 3

        assert isinstance(stage3, ParallelAgent)
        writer_names = [a.name for a in stage3.sub_agents]
        assert writer_names == ["LinkedInWriterAgent", "XThreadWriterAgent", "YouTubeWriterAgent"]

        assert isinstance(stage4, LoopAgent)
        assert stage4.max_iterations == MAX_REFINEMENT_ITERATIONS
        assert len(stage4.sub_agents) == 2
        assert isinstance(stage4.sub_agents[0], ParallelAgent)
        assert stage4.sub_agents[1].name == "ContentRefinerAgent"

    def test_pipeline_supports_optional_newsletter_and_subsets(self):
        pipeline = create_content_generation_pipeline(channels=["linkedin", "newsletter"])
        writers_stage = pipeline.sub_agents[2]
        writer_names = [a.name for a in writers_stage.sub_agents]
        assert writer_names == ["LinkedInWriterAgent", "NewsletterWriterAgent"]
