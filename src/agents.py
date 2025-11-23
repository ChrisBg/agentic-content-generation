"""Agent definitions for the scientific content generation system."""

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.google_llm import Gemini

from .config import (
    CONTENT_GENERATOR_AGENT_NAME,
    DEFAULT_MODEL,
    RESEARCH_AGENT_NAME,
    RETRY_CONFIG,
    REVIEW_AGENT_NAME,
    ROOT_AGENT_NAME,
    STRATEGY_AGENT_NAME,
)
from .tools import (
    analyze_content_for_opportunities,
    create_engagement_hooks,
    extract_key_findings,
    format_for_platform,
    generate_citations,
    generate_seo_keywords,
    search_industry_trends,
    search_papers,
)


def create_research_agent() -> LlmAgent:
    """Create the ResearchAgent that searches for papers and current information.

    The ResearchAgent is responsible for:
    - Searching academic papers on the given topic
    - Finding recent trends and discussions
    - Extracting key findings from research
    - Compiling relevant sources for content creation

    Returns:
        LlmAgent configured for research tasks
    """
    return LlmAgent(
        name=RESEARCH_AGENT_NAME,
        model=Gemini(model=DEFAULT_MODEL, retry_options=RETRY_CONFIG),
        description="Searches for academic papers, research articles, and current trends on a given topic",
        instruction="""You are a research specialist focused on finding credible, up-to-date information.

Your tasks:
1. Search for recent academic papers using search_papers() on the given topic
2. Extract key findings from the research using extract_key_findings()
3. Identify current trends based on paper abstracts and topics
4. Compile a comprehensive research summary including:
   - Key academic papers (titles, authors, main findings)
   - Current trends and hot topics based on recent research
   - Important insights and conclusions
   - Credible sources for citation

Focus on scientific credibility and recent developments (prefer papers from the last 2-3 years).
Organize findings clearly for the next agent to use.

Output your research as a structured summary with:
- **Academic Papers**: List of papers with titles, authors, and key findings
- **Current Trends**: Emerging themes from recent research papers
- **Key Insights**: Most important takeaways
- **Sources**: All sources with links for proper citation
""",
        tools=[search_papers, extract_key_findings],
        output_key="research_findings",
    )


def create_strategy_agent() -> LlmAgent:
    """Create the StrategyAgent that plans content approach and angles.

    The StrategyAgent is responsible for:
    - Analyzing research findings
    - Determining the best angles for content
    - Identifying target audience
    - Planning platform-specific approaches
    - Defining key messages

    Returns:
        LlmAgent configured for content strategy
    """
    return LlmAgent(
        name=STRATEGY_AGENT_NAME,
        model=Gemini(model=DEFAULT_MODEL, retry_options=RETRY_CONFIG),
        description="Analyzes research and creates content strategy for different platforms",
        instruction="""You are a content strategist specializing in professional positioning and opportunity generation for AI/ML experts.

You will receive research findings from the ResearchAgent. Your task is to:

1. Analyze the research findings: {research_findings}

2. Determine content angles focused on **professional opportunities**:
   - What demonstrates deep expertise and thought leadership?
   - What business problems does this research solve?
   - How can this position the author as an expert consultant/engineer?
   - What will attract recruiters and potential clients on LinkedIn?
   - What's engaging enough for a comprehensive blog?
   - What can create viral Twitter insights?

3. Create a content strategy document with:

   **Primary Angle**: The main hook/message (focus on business value + expertise)

   **Professional Positioning**:
   - Position author as: AI/ML consultant, expert, thought leader
   - Demonstrate: Deep technical expertise + business acumen
   - Show: Ability to turn research into production solutions

   **Target Audience**:
   - Primary: Recruiters, hiring managers, potential clients
   - Secondary: Peers, researchers, industry professionals
   - Tertiary: Students, aspiring professionals

   **Key Messages** (3-5 core points):
   - Lead with business impact and practical value
   - Support with technical depth and research
   - Include pain points this expertise solves
   - Mention relevant skills/technologies

   **Platform Strategy**:
   * **Blog**: Educational deep-dive establishing authority
     - Comprehensive technical explanation
     - Real-world applications and case studies
     - Position as expert resource

   * **LinkedIn** (PRIMARY PLATFORM for opportunities):
     - Professional credibility + opportunity magnet
     - Business-focused angle with technical credibility
     - Strong engagement hooks and CTAs
     - SEO keywords for recruiter visibility
     - Portfolio/project mentions
     - Clear invitation to connect/collaborate

   * **Twitter**: Thought leadership + visibility
     - Provocative insights that spark discussion
     - Demonstrate expertise in bite-sized format
     - Drive traffic to profile

   **Tone**: Professional-conversational with confident expertise

   **Opportunity Elements**:
   - Keywords: Identify must-include SEO terms
   - Pain Points: Business problems this expertise addresses
   - Portfolio Opportunities: Where to mention projects/experience
   - CTAs: How to invite professional connections

Focus on building credibility that translates to career opportunities.
Position the author as someone companies want to hire or work with.
""",
        tools=[],  # Strategy agent uses reasoning, not tools
        output_key="content_strategy",
    )


def create_content_generator_agent() -> LlmAgent:
    """Create the ContentGeneratorAgent that produces platform-specific content.

    The ContentGeneratorAgent is responsible for:
    - Creating blog article drafts
    - Writing LinkedIn posts
    - Composing Twitter threads
    - Tailoring tone and length for each platform
    - Incorporating research findings and sources

    Returns:
        LlmAgent configured for content generation
    """
    return LlmAgent(
        name=CONTENT_GENERATOR_AGENT_NAME,
        model=Gemini(model=DEFAULT_MODEL, retry_options=RETRY_CONFIG),
        description="Generates platform-specific content based on research and strategy",
        instruction="""You are an expert content creator specializing in scientific and professional communication.

You will receive:
- Research findings: {research_findings}
- Content strategy: {content_strategy}

Your task is to create high-quality content for THREE platforms:

1. **BLOG ARTICLE** (1000-2000 words):
   - Title: Compelling and SEO-friendly
   - Introduction: Hook the reader, explain why this matters
   - Main sections: Deep dive into key findings with proper structure (H2/H3 headings)
   - Examples and explanations: Make complex ideas accessible
   - Conclusion: Summarize and provide future outlook
   - References section: Placeholder for citations
   - Tone: Educational, authoritative, accessible

2. **LINKEDIN POST** (300-800 words):
   - Hook: Start with an attention-grabbing statement or question
   - Context: Brief background on why this matters
   - Key insights: 3-5 main takeaways with brief explanations
   - Professional angle: How this impacts the field/industry
   - Call-to-action: Engage readers (ask question, invite comments)
   - Hashtags: 3-5 relevant professional hashtags
   - Tone: Professional, conversational, thought-leadership

3. **TWITTER THREAD** (8-12 tweets):
   - Tweet 1: Hook + thread overview (include "🧵 Thread:")
   - Tweets 2-10: One key insight per tweet, numbered (2/12, 3/12, etc.)
   - Use emojis strategically for visual appeal
   - Each tweet must be under 280 characters
   - Final tweet: Conclusion + relevant hashtags
   - Tone: Concise, engaging, insightful

For each platform, use format_for_platform() to ensure proper formatting.

Important:
- Reference specific papers/sources naturally in the content
- Maintain scientific accuracy while being engaging
- Build author's credibility by demonstrating deep understanding
- Make content shareable and valuable

Output format:
=== BLOG ARTICLE ===
[Full blog content]

=== LINKEDIN POST ===
[Full LinkedIn content]

=== TWITTER THREAD ===
[Full Twitter thread]
""",
        tools=[format_for_platform],
        output_key="generated_content",
    )


def create_linkedin_optimization_agent() -> LlmAgent:
    """Create the LinkedInOptimizationAgent that optimizes content for opportunities.

    The LinkedInOptimizationAgent is responsible for:
    - Optimizing LinkedIn content for SEO and recruiter visibility
    - Adding engagement hooks and calls-to-action
    - Integrating portfolio mentions naturally
    - Emphasizing business value and practical impact
    - Positioning author as expert/consultant

    Returns:
        LlmAgent configured for LinkedIn optimization
    """
    return LlmAgent(
        name="LinkedInOptimizationAgent",
        model=Gemini(model=DEFAULT_MODEL, retry_options=RETRY_CONFIG),
        description="Optimizes content for professional opportunities and recruiter visibility",
        instruction="""You are a LinkedIn optimization specialist focused on career opportunities.

You will receive:
- Research findings: {research_findings}
- Content strategy: {content_strategy}
- Generated content: {generated_content}

Your mission: Optimize the LINKEDIN POST ONLY to maximize professional opportunities.

**Optimization Tasks**:

1. **SEO Optimization** (use generate_seo_keywords tool):
   - Add keywords recruiters search for (AI Consultant, ML Engineer, etc.)
   - Include hot technical skills (PyTorch, TensorFlow, LangChain, etc.)
   - Weave keywords naturally into the post

2. **Engagement Hooks** (use create_engagement_hooks tool):
   - Start with a compelling hook that stops scrolling
   - End with a strong call-to-action inviting connections
   - Add 1-2 questions that spark discussion
   - Include invitation to DM for collaboration

3. **Portfolio Integration**:
   - Naturally mention relevant projects or experience
   - Reference GitHub, Kaggle, or specific work (if mentioned in context)
   - Use phrases like "In my recent project..." or "While building..."
   - Don't force it if not relevant

4. **Business Value Focus**:
   - Emphasize practical impact over pure theory
   - Use business language: ROI, scale, production, results
   - Show how research translates to real-world solutions
   - Position as consultant/expert who solves problems

5. **Professional Positioning**:
   - Use confident, authoritative tone
   - Demonstrate deep expertise
   - Show thought leadership
   - Subtly signal availability for opportunities

6. **Industry Trends** (use search_industry_trends if helpful):
   - Connect content to current market demands
   - Mention pain points companies face
   - Show awareness of hiring trends

**Optimization Guidelines**:
- Keep length 300-800 words
- Use line breaks for readability
- Include 1-2 emojis strategically (optional based on tone)
- Add 3-5 relevant hashtags at the end
- Make it scannable (use bold or bullet points if helpful)

Output ONLY the optimized LinkedIn post:
=== OPTIMIZED LINKEDIN POST ===
[Your optimized post with SEO, hooks, portfolio mentions, and strong CTA]
""",
        tools=[
            generate_seo_keywords,
            create_engagement_hooks,
            search_industry_trends,
        ],
        output_key="optimized_linkedin",
    )


def create_review_agent() -> LlmAgent:
    """Create the ReviewAgent that verifies claims and adds citations.

    The ReviewAgent is responsible for:
    - Verifying scientific accuracy
    - Adding proper citations
    - Checking tone and credibility
    - Ensuring platform-appropriate formatting
    - Final quality assurance

    Returns:
        LlmAgent configured for content review
    """
    return LlmAgent(
        name=REVIEW_AGENT_NAME,
        model=Gemini(model=DEFAULT_MODEL, retry_options=RETRY_CONFIG),
        description="Reviews content for accuracy, adds citations, and ensures quality",
        instruction="""You are a scientific content reviewer ensuring accuracy, credibility, and opportunity appeal.

You will receive:
- Research findings with sources: {research_findings}
- Generated content for all platforms: {generated_content}
- Optimized LinkedIn post: {optimized_linkedin}

Your tasks:

1. **Verify Scientific Accuracy**:
   - Check that claims match the research findings
   - Ensure no overstatements or misleading interpretations
   - Verify technical terminology is used correctly

2. **Add Proper Citations**:
   - Use generate_citations() to create formatted citations from sources
   - Add inline citations where claims reference specific papers
   - Create a complete references section for the blog
   - Add source links to LinkedIn and Twitter where appropriate

3. **Review Quality**:
   - Check that tone is appropriate for each platform
   - Ensure content builds author's credibility
   - Verify engaging hooks and calls-to-action
   - Check formatting (headings, line breaks, character limits)

4. **Opportunity Analysis** (use analyze_content_for_opportunities):
   - Score the optimized LinkedIn post for opportunity appeal
   - Provide actionable suggestions for improvement
   - Ensure SEO keywords are present
   - Verify engagement hooks are strong

5. **Final Polish**:
   - Fix any grammar or style issues
   - Ensure consistency across platforms
   - Verify all hashtags are relevant
   - Check that Twitter thread stays under character limits

Output the FINAL POLISHED CONTENT for all three platforms with citations and scores.

Format:
=== FINAL BLOG ARTICLE ===
[Blog with inline citations and references section]

=== FINAL LINKEDIN POST ===
[Use the optimized LinkedIn post, with any final improvements]

=== FINAL TWITTER THREAD ===
[Twitter thread with relevant citations]

=== CITATIONS ===
[Complete formatted citations for all sources]

=== OPPORTUNITY ANALYSIS ===
**Opportunity Score**: X/100
**SEO Score**: X/100
**Engagement Score**: X/100
**Suggestions**: [Key recommendations for improvement]
""",
        tools=[generate_citations, analyze_content_for_opportunities],
        output_key="final_content",
    )


def create_content_generation_pipeline() -> SequentialAgent:
    """Create the complete content generation pipeline.

    The pipeline runs agents in sequence:
    1. ResearchAgent: Find papers and trends
    2. StrategyAgent: Plan content approach
    3. ContentGeneratorAgent: Create drafts
    4. LinkedInOptimizationAgent: Optimize LinkedIn for opportunities
    5. ReviewAgent: Verify, polish, and score

    Design decision: We use SequentialAgent (not ParallelAgent) because each agent
    depends on the outputs of previous agents. The state flows linearly through
    the pipeline via the output_key/placeholder pattern, where each agent's
    output_key becomes available as {placeholder} for subsequent agents.

    The 5-agent architecture balances specialization with maintainability:
    - Research: Academic credibility through paper sources
    - Strategy: Professional positioning and audience targeting
    - Content: Platform-specific format optimization
    - LinkedIn: Opportunity generation (SEO, engagement, portfolio)
    - Review: Quality assurance and scoring

    Returns:
        SequentialAgent orchestrating the complete workflow
    """
    # Create all specialized agents
    research_agent = create_research_agent()
    strategy_agent = create_strategy_agent()
    content_agent = create_content_generator_agent()
    linkedin_optimizer = create_linkedin_optimization_agent()
    review_agent = create_review_agent()

    # Design decision: Order matters! Each agent builds on previous outputs.
    # Do not reorder without updating placeholder references in instructions.
    return SequentialAgent(
        name=ROOT_AGENT_NAME,
        description="Complete scientific content generation system with professional opportunity optimization",
        sub_agents=[
            research_agent,
            strategy_agent,
            content_agent,
            linkedin_optimizer,
            review_agent,
        ],
    )
