"""Hybrid Multi-LLM Google ADK pipeline (Sequential -> Parallel -> Parallel -> Loop).

Inspired by google-research/paper-orchestra:
1. OutlineBlueprintAgent: Synthesizes raw materials + human seed into angle, biblio plan, visual & video blueprint.
2. ParallelEnrichmentStage (ParallelAgent):
   - HybridLiteratureAgent (arXiv + Semantic Scholar verification + BibTeX)
   - PersonalEvidenceAgent (Local Knowledge Base: Case Studies + Voice DNA)
   - VisualAssetAgent (Matplotlib charts + Architecture diagrams + Demo overlays)
3. ParallelChannelWritersStage (ParallelAgent, Multi-LLM routed):
   - LinkedInWriterAgent (Claude Sonnet by default)
   - XThreadWriterAgent (Grok / GPT-4.1 by default)
   - YouTubeWriterAgent (Claude Sonnet by default)
   - NewsletterWriterAgent (optional)
4. QualityRefinementLoop (LoopAgent, max_iterations=3):
   - ParallelCriticsStage: FactCheckerCritic + EditorialAntiSlopCritic (cross-family LLMs + deterministic linter)
   - ContentRefinerAgent: Refines drafts, renders final PDF carousel & MP4 short videos, calls exit_loop when passed.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent, LoopAgent, ParallelAgent, SequentialAgent

from .channels import create_channel_writer_agent, get_channel_plugin
from .config import (
    DEFAULT_CHANNELS,
    EDITORIAL_CRITIC_AGENT_NAME,
    FACT_CHECKER_AGENT_NAME,
    MAX_REFINEMENT_ITERATIONS,
    OUTLINE_AGENT_NAME,
    PERSONAL_CONTEXT_AGENT_NAME,
    REFINER_AGENT_NAME,
    RESEARCH_AGENT_NAME,
    ROOT_AGENT_NAME,
    VISUAL_AGENT_NAME,
)
from .knowledge_base import get_voice_and_style_guide, retrieve_personal_evidence
from .llm_router import ModelRouter
from .tools import (
    exit_loop,
    generate_bibtex,
    search_arxiv_papers,
    search_industry_context,
    search_semantic_scholar,
    search_web,
    validate_deliverables_deterministic,
    verify_citation_semantic_scholar,
)
from .video_assets import render_short_explainer_video
from .visuals import (
    render_architecture_diagram,
    render_data_chart,
    render_demo_overlays,
    render_linkedin_carousel_pdf,
)


def create_outline_blueprint_agent(router: ModelRouter | None = None) -> LlmAgent:
    """Stage 1: Synthesize topic, human seed, and raw materials into a structured blueprint."""
    router = router or ModelRouter()
    return LlmAgent(
        name=OUTLINE_AGENT_NAME,
        model=router.get_model("outline"),
        description="Plans the editorial angle, dual literature search queries, and visual/video blueprint.",
        instruction="""You are a Chief Editorial Strategist & Research Director (PaperOrchestra-style Outline Agent).

Analyze the user's request, including:
- Topic & target language / channels
- Human Seed (author's personal take — treat this as the central thesis!)
- Any ingested PaperOrchestra raw materials (LaTeX sections, tables, experimental metrics, notebooks, PDFs)
- Author profile & B2B positioning (CTOs, VP Data, AdTech/MarTech leaders, CIR/CII R&D)

Produce a crisp, structured **CONTENT & VISUAL BLUEPRINT** containing:
1. **Core Thesis & Contrarian Angle**: One sharp sentence that stands out in a crowded AI feed.
2. **Editorial Pillar**: Map to one of the author's pillars (Production AI/Agents, AdTech/MFA/Ad Fraud, or Build-in-Public R&D).
3. **Dual Literature Search Plan** (PaperOrchestra pattern):
   - 2 macro industry/context search queries (market, production adoption, costs).
   - 2 micro academic search queries (specific papers, methods, benchmarks for Semantic Scholar & arXiv).
4. **Personal Evidence Queries**: Which of the author's past projects/metrics should be retrieved to anchor the narrative.
5. **Visual & Short-Demo Blueprint**:
   - Chart Spec (ONLY using real numbers from raw materials or verified research — never invent numbers!).
   - Architecture Diagram Spec (3 to 6 concrete pipeline blocks).
   - 45-60s Short Demo / Explainer Video angle (what visual hook appears in the first 3 seconds).

Be concise, structured, and concrete. Output this blueprint as your final response.
""",
        tools=[],
        output_key="content_blueprint",
    )


def create_literature_agent(router: ModelRouter | None = None) -> LlmAgent:
    """Stage 2a: Hybrid literature discovery + Semantic Scholar citation verification."""
    router = router or ModelRouter()
    return LlmAgent(
        name=RESEARCH_AGENT_NAME,
        model=router.get_model("research"),
        description="Discovers academic papers & industry signals and verifies citations via Semantic Scholar.",
        instruction="""You are a Hybrid Literature & Fact-Grounding Specialist (PaperOrchestra pattern).

Read the blueprint:
{content_blueprint}

Execute this rigorous workflow:
1. **Academic Discovery**:
   - Call `search_semantic_scholar()` on the micro academic queries (preferring well-cited or recent papers).
   - Call `search_arxiv_papers(..., sort_by="relevance")` for cutting-edge preprints.
2. **Citation Verification**:
   - For the top 2-4 papers you intend to cite, verify canonical title/year/authors via `verify_citation_semantic_scholar()` if they came only from arXiv or web snippets.
   - Call `generate_bibtex()` on the verified papers so a clean BibTeX block is ready for export and LaTeX reuse.
3. **Industry Grounding**:
   - Call `search_industry_context()` or `search_web()` for real-world deployment context.

Compile a structured **VERIFIED RESEARCH DOSSIER**:
- **Verified Academic Papers**: Title, Authors, EXACT Year, Venue, Citation Count, URL, and 2-3 bullet factual findings directly supported by the abstract.
- **Verified Benchmarks & Quantitative Facts**: Exact numbers with exact source attribution (never extrapolate).
- **Industry Context**: Practical market signals.
- **BibTeX Block**: The exact output of `generate_bibtex()`.

NEVER fabricate a paper, year, or percentage.
""",
        tools=[
            search_semantic_scholar,
            verify_citation_semantic_scholar,
            search_arxiv_papers,
            search_industry_context,
            search_web,
            generate_bibtex,
        ],
        output_key="verified_research",
    )


def create_personal_context_agent(router: ModelRouter | None = None) -> LlmAgent:
    """Stage 2b: Retrieve author's real case studies, metrics, Voice DNA, and banned clichés."""
    router = router or ModelRouter()
    return LlmAgent(
        name=PERSONAL_CONTEXT_AGENT_NAME,
        model=router.get_model("personal_context"),
        description="Retrieves verified personal case studies, metrics, and Voice DNA from the local knowledge base.",
        instruction="""You are the Author's Personal Knowledge & Voice Archivist.

Read the blueprint:
{content_blueprint}

Tasks:
1. Call `retrieve_personal_evidence()` with the main topic keywords to retrieve the author's most relevant real, quantified production case studies.
2. Call `get_voice_and_style_guide()` to load the author's Voice DNA, platform formatting constraints, and anti-AI-slop banned phrases list.

Return a concise **PERSONAL CONTEXT BRIEF** containing:
- The 1-3 most relevant real case studies and their EXACT verified metrics (never inflate or alter them).
- Key Voice DNA rules to follow.
- The exact list of banned phrases that MUST NOT appear anywhere in the drafts.
""",
        tools=[retrieve_personal_evidence, get_voice_and_style_guide],
        output_key="personal_context",
    )


def create_visual_asset_agent(router: ModelRouter | None = None) -> LlmAgent:
    """Stage 2c: Generate real charts, architecture diagrams, and demo overlays."""
    router = router or ModelRouter()
    return LlmAgent(
        name=VISUAL_AGENT_NAME,
        model=router.get_model("visual"),
        description="Renders high-resolution Matplotlib charts, architecture diagrams (.png + .mmd), and live demo overlays.",
        instruction="""You are a Technical Data Visualization & Diagram Engineer (PaperOrchestra Plotting Agent).

Read the blueprint:
{content_blueprint}

Tasks:
1. **Architecture Diagram**: Call `render_architecture_diagram()` using 4-6 clear technical blocks from the blueprint. Save under `output/tmp_assets/architecture.png`.
2. **Data Chart** (ONLY if real verified numeric series exist in the user's raw materials or blueprint): Call `render_data_chart()` saving under `output/tmp_assets/benchmark_chart.png`. NEVER invent fake benchmark numbers! If no real numeric series is available yet, skip the chart and explain why.
3. **Live Demo Overlays**: Call `render_demo_overlays()` with 3-4 crisp lower-third cues (key metric / step label) saved under `output/tmp_assets/overlays`.

Return a concise **GENERATED VISUALS MANIFEST** listing every exact file path created (`png_path`, `mermaid_path`, overlay paths) and a 1-line caption for each so channel writers can reference them accurately.
""",
        tools=[render_data_chart, render_architecture_diagram, render_demo_overlays],
        output_key="generated_visuals",
    )


def create_fact_checker_critic(
    channels: list[str],
    router: ModelRouter | None = None,
) -> LlmAgent:
    """Stage 4a: Scientific fact-checker verifying every statistic, claim, and citation."""
    router = router or ModelRouter()
    draft_refs = "\n".join(
        f"- {get_channel_plugin(ch).display_name}: {{{get_channel_plugin(ch).output_key}}}"
        for ch in channels
    )
    return LlmAgent(
        name=FACT_CHECKER_AGENT_NAME,
        model=router.get_model("fact_checker"),
        description="Audits all channel drafts for factual accuracy, verified citations, and unsourced statistics.",
        instruction=f"""You are a strict Scientific Peer-Reviewer & Fact-Checker.

Ground-truth sources:
- Verified Research: {{verified_research}}
- Verified Personal Case Studies: {{personal_context}}

Channel drafts to audit:
{draft_refs}

Audit checklist:
1. Every percentage, dollar/euro amount, latency figure, or benchmark claim MUST trace back to {{verified_research}}, {{personal_context}}, or the user's ingested raw materials. Flag ANY invented number (e.g. "slashes costs by 30%") as a BLOCKING issue.
2. Every cited paper must have real authors and a real year (NEVER "(n.d.)" if a year exists, NEVER hallucinated paper titles).
3. Ensure technical nuance is preserved (no exaggerated hype claims).

Output a concise **FACT-CHECK REPORT**:
- **FACT_CHECK_STATUS**: PASS or FAIL
- **BLOCKING_ISSUES**: bullet list (or "None")
- **SUGGESTED_FIXES**: exact replacements grounded in the verified sources.
""",
        tools=[],
        output_key="fact_check_report",
    )


def create_editorial_critic(
    channels: list[str],
    router: ModelRouter | None = None,
) -> LlmAgent:
    """Stage 4b: Cross-family CTO / Anti-AI-Slop critic with deterministic Python linting."""
    router = router or ModelRouter()
    draft_refs = "\n".join(
        f"- {get_channel_plugin(ch).display_name}: {{{get_channel_plugin(ch).output_key}}}"
        for ch in channels
    )
    return LlmAgent(
        name=EDITORIAL_CRITIC_AGENT_NAME,
        model=router.get_model("editorial_critic"),
        description="Skeptical CTO & social platform editor running deterministic lints and anti-AI-slop scoring.",
        instruction=f"""You are a skeptical CTO & Senior Social Media Editor reviewing drafts for a PhD AI Engineer with 30,000 LinkedIn connections.

Author Voice DNA & Banned Phrases:
{{personal_context}}

Channel drafts to audit:
{draft_refs}

MANDATORY STEP 1:
Call `validate_deliverables_deterministic()` passing the LinkedIn post text (if present), the list of individual X tweets (if present), and the YouTube script (if present).

MANDATORY STEP 2:
Score the package out of 100 on:
- **Anti-Slop & Voice Authenticity** (zero hype clichés, sounds like a battle-tested PhD practitioner)
- **B2B / R&D Positioning** (speaks to CTOs, VP Data, AdTech leaders — NOT generic HR recruiters)
- **Platform Native Craft** (LinkedIn plain text without `**`, every X tweet <= 280 chars, YouTube hook & `[VISUAL]` cues)

Output a concise **EDITORIAL CRITIQUE**:
- **DETERMINISTIC_LINT_PASSED**: True or False (exact result from tool)
- **EDITORIAL_SCORE**: X/100
- **BLOCKING_ISSUES**: exact list of tool violations + any tone/positioning issues
- **IMPROVEMENTS**: concrete line-level edits.
""",
        tools=[validate_deliverables_deterministic],
        output_key="editorial_critique",
    )


def create_refiner_agent(
    channels: list[str],
    router: ModelRouter | None = None,
) -> LlmAgent:
    """Stage 4c: Refines drafts based on both critics, builds PDF/MP4 assets, and exits loop when passing."""
    router = router or ModelRouter()
    draft_refs = "\n".join(
        f"- {get_channel_plugin(ch).display_name}: {{{get_channel_plugin(ch).output_key}}}"
        for ch in channels
    )
    return LlmAgent(
        name=REFINER_AGENT_NAME,
        model=router.get_model("refiner"),
        description="Applies fact-check and anti-slop fixes, renders final carousel PDF & short MP4 videos, and exits loop once quality gates pass.",
        instruction=f"""You are the Final Editorial Refiner & Media Packager.

Inputs:
- Verified Research (incl. BibTeX): {{verified_research}}
- Generated Visuals: {{generated_visuals}}
- Channel Drafts:
{draft_refs}
- Fact-Check Report: {{fact_check_report}}
- Editorial Critique: {{editorial_critique}}

Decision Logic:
1. Check whether BOTH:
   - `FACT_CHECK_STATUS` is `PASS` (zero unsourced numbers or hallucinated citations), AND
   - `DETERMINISTIC_LINT_PASSED` is `True` AND `EDITORIAL_SCORE` >= 85.
2. **If NOT passed yet**:
   - Rewrite ONLY the failing parts cleanly (strip any `**` from LinkedIn, shorten tweets > 280 chars, remove banned clichés/placeholders, fix unsourced claims).
   - Output the full updated deliverables clearly delimited with the markers below so the next iteration verifies them. Do NOT call `exit_loop` yet.
3. **If PASSED (or after applying clean final fixes when only minor warnings remain)**:
   - If LinkedIn carousel slides were drafted, call `render_linkedin_carousel_pdf()` saving to `output/tmp_assets/linkedin_carousel.pdf` (passing any generated chart PNG paths).
   - If a video storyboard was drafted for X / YouTube, call `render_short_explainer_video()` for `16:9` (`output/tmp_assets/demo_explainer_16x9.mp4`) and `9:16` (`output/tmp_assets/short_9x16.mp4`).
   - Call `exit_loop()` to finish the refinement loop.
   - Output the COMPLETE, READY-TO-PUBLISH bundle using these EXACT section headers (omit channels not requested):

=== FINAL LINKEDIN POST ===
[Clean plain-text LinkedIn post — ZERO Markdown bold **, ZERO placeholders]

=== FINAL X THREAD ===
[Clean numbered tweets, each <= 280 chars]

=== FINAL X STANDALONE POSTS ===
[2 short standalone posts]

=== FINAL YOUTUBE PACKAGE ===
[CTR titles, thumbnail briefs, long script with [VISUAL] cues, 60s Short script, live demo shotlist, SEO description]

=== FINAL NEWSLETTER ===
[Only if newsletter channel was requested]

=== BIBTEX REFERENCES ===
[Verified BibTeX entries]

=== GENERATED MEDIA MANIFEST ===
[Exact file paths to PNG figures, PDF carousel, MP4 videos, SRT subtitles]

=== QUALITY REPORT ===
[Final Fact-Check status, Editorial score, models/checks summary]
""",
        tools=[
            render_linkedin_carousel_pdf,
            render_short_explainer_video,
            exit_loop,
        ],
        output_key="final_content",
    )


def create_content_generation_pipeline(
    channels: list[str] | None = None,
    model_overrides: dict[str, str] | None = None,
) -> SequentialAgent:
    """Create the v2 Hybrid Multi-LLM ADK Pipeline.

    Pipeline structure:
        Stage 1: OutlineBlueprintAgent (Sequential)
        Stage 2: ParallelEnrichmentStage (HybridLiterature + PersonalEvidence + VisualAsset)
        Stage 3: ParallelChannelWritersStage (LinkedIn + X + YouTube [+ Newsletter], Multi-LLM)
        Stage 4: QualityRefinementLoop (LoopAgent, max 3 turns: ParallelCritics -> ContentRefiner)

    Args:
        channels: List of target channel keys (default: ``["linkedin", "x", "youtube"]``).
        model_overrides: Optional per-role model overrides for ``ModelRouter``.

    Returns:
        Configured ADK ``SequentialAgent`` root pipeline.
    """
    active_channels = [get_channel_plugin(c).key for c in (channels or DEFAULT_CHANNELS)]
    # Deduplicate preserving order
    active_channels = list(dict.fromkeys(active_channels))

    router = ModelRouter(overrides=model_overrides)

    # Stage 1: Outline & Visual Blueprint
    outline_agent = create_outline_blueprint_agent(router)

    # Stage 2: Parallel Enrichment (Literature + Personal Evidence + Visuals)
    enrichment_stage = ParallelAgent(
        name="ParallelEnrichmentStage",
        description="Runs verified literature search, personal case-study retrieval, and visual generation in parallel.",
        sub_agents=[
            create_literature_agent(router),
            create_personal_context_agent(router),
            create_visual_asset_agent(router),
        ],
    )

    # Stage 3: Parallel Multi-LLM Channel Writers
    channel_writers = [create_channel_writer_agent(ch, router) for ch in active_channels]
    writers_stage = ParallelAgent(
        name="ParallelChannelWritersStage",
        description="Generates native deliverables for each target social channel in parallel using optimal LLMs.",
        sub_agents=channel_writers,
    )

    # Stage 4: Iterative Simulated Peer-Review & Anti-AI-Slop Loop
    critics_stage = ParallelAgent(
        name="ParallelCriticsStage",
        description="Runs scientific fact-checking and cross-family anti-AI-slop editorial critique concurrently.",
        sub_agents=[
            create_fact_checker_critic(active_channels, router),
            create_editorial_critic(active_channels, router),
        ],
    )
    refiner_agent = create_refiner_agent(active_channels, router)

    refinement_loop = LoopAgent(
        name="QualityRefinementLoop",
        description="Iteratively refines drafts until fact-checking, anti-slop, and formatting gates pass.",
        sub_agents=[critics_stage, refiner_agent],
        max_iterations=MAX_REFINEMENT_ITERATIONS,
    )

    return SequentialAgent(
        name=ROOT_AGENT_NAME,
        description="Multi-LLM Research-to-Brand pipeline (LinkedIn, X, YouTube) with PaperOrchestra ingestion and peer-review loop.",
        sub_agents=[
            outline_agent,
            enrichment_stage,
            writers_stage,
            refinement_loop,
        ],
    )
