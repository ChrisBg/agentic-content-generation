"""Unit tests for custom tools in src/tools.py."""

from src.tools import (
    analyze_content_for_opportunities,
    create_engagement_hooks,
    extract_key_findings,
    format_for_platform,
    generate_citations,
    generate_seo_keywords,
    search_industry_trends,
    search_papers,
)


class TestSearchPapers:
    """Tests for the search_papers tool."""

    def test_search_papers_success(self):
        """Test successful paper search."""
        result = search_papers("machine learning", max_results=2)

        assert result["status"] == "success"
        assert "papers" in result
        assert len(result["papers"]) <= 2
        assert result["count"] > 0

        # Check paper structure
        if result["papers"]:
            paper = result["papers"][0]
            assert "title" in paper
            assert "authors" in paper
            assert "summary" in paper
            assert "link" in paper

    def test_search_papers_with_max_results(self):
        """Test that max_results is respected."""
        result = search_papers("deep learning", max_results=3)

        assert result["status"] == "success"
        assert len(result["papers"]) <= 3

    def test_search_papers_empty_topic(self):
        """Test handling of empty topic."""
        # Empty topic might still work with arXiv API, or it might fail gracefully
        result = search_papers("", max_results=1)
        # Should either return error or handle gracefully
        assert result["status"] in ["success", "error"]


class TestFormatForPlatform:
    """Tests for the format_for_platform tool."""

    def test_format_blog(self):
        """Test blog formatting."""
        content = "This is test content about AI."
        result = format_for_platform(content, "blog", "Artificial Intelligence")

        assert result["status"] == "success"
        assert result["platform"] == "blog"
        assert "formatted_content" in result
        assert "metadata" in result
        assert "# Artificial Intelligence" in result["formatted_content"]
        assert "## References" in result["formatted_content"]

    def test_format_linkedin(self):
        """Test LinkedIn formatting."""
        content = "LinkedIn post content about ML."
        result = format_for_platform(content, "linkedin", "Machine Learning")

        assert result["status"] == "success"
        assert result["platform"] == "linkedin"
        assert "Key Takeaways" in result["formatted_content"]
        assert "#Research" in result["formatted_content"]

    def test_format_twitter(self):
        """Test Twitter thread formatting."""
        content = "Twitter thread about AI agents."
        result = format_for_platform(content, "twitter", "AI Agents")

        assert result["status"] == "success"
        assert result["platform"] == "twitter"
        assert "🧵 Thread:" in result["formatted_content"]
        assert "#Research" in result["formatted_content"]

    def test_format_unsupported_platform(self):
        """Test error handling for unsupported platform."""
        result = format_for_platform("content", "tiktok", "AI")

        assert result["status"] == "error"
        assert "Unsupported platform" in result["error_message"]

    def test_format_case_insensitive(self):
        """Test that platform names are case-insensitive."""
        result = format_for_platform("content", "BLOG", "AI")

        assert result["status"] == "success"
        assert result["platform"] == "blog"


class TestGenerateCitations:
    """Tests for the generate_citations tool."""

    def test_generate_citations_apa(self):
        """Test APA citation generation."""
        sources = [
            {
                "title": "Deep Learning",
                "authors": "Goodfellow et al.",
                "link": "https://arxiv.org/abs/1234.5678",
                "year": "2016",
            }
        ]
        result = generate_citations(sources, "apa")

        assert result["status"] == "success"
        assert result["style"] == "apa"
        assert len(result["citations"]) == 1
        assert "Goodfellow et al." in result["citations"][0]
        assert "(2016)" in result["citations"][0]

    def test_generate_citations_mla(self):
        """Test MLA citation generation."""
        sources = [{"title": "AI Paper", "authors": "Smith, J.", "link": "url", "year": "2020"}]
        result = generate_citations(sources, "mla")

        assert result["status"] == "success"
        assert result["style"] == "mla"
        assert "Smith, J." in result["citations"][0]

    def test_generate_citations_chicago(self):
        """Test Chicago citation generation."""
        sources = [{"title": "ML Study", "authors": "Jones, A.", "link": "url"}]
        result = generate_citations(sources, "chicago")

        assert result["status"] == "success"
        assert result["style"] == "chicago"

    def test_generate_citations_empty_sources(self):
        """Test error handling for empty sources."""
        result = generate_citations([], "apa")

        assert result["status"] == "error"
        assert "No sources provided" in result["error_message"]

    def test_generate_citations_default_style(self):
        """Test that invalid style defaults to APA."""
        sources = [{"title": "Test", "authors": "Author", "link": "url"}]
        result = generate_citations(sources, "invalid_style")

        assert result["status"] == "success"
        assert result["style"] == "apa"


class TestExtractKeyFindings:
    """Tests for the extract_key_findings tool."""

    def test_extract_key_findings_success(self):
        """Test successful key findings extraction."""
        text = """
        Recent research found that deep learning models achieve 95% accuracy.
        The study demonstrated improved performance on benchmark datasets.
        Results showed that attention mechanisms are crucial for NLP tasks.
        Experiments revealed that larger models generally perform better.
        The analysis concluded that data quality impacts model robustness.
        """
        result = extract_key_findings(text, max_findings=3)

        assert result["status"] == "success"
        assert len(result["findings"]) <= 3
        assert result["count"] <= 3

    def test_extract_key_findings_with_indicators(self):
        """Test that indicator words are detected."""
        text = "The research found significant improvements. The study showed remarkable results."
        result = extract_key_findings(text, max_findings=5)

        assert result["status"] == "success"
        assert len(result["findings"]) > 0

    def test_extract_key_findings_insufficient_text(self):
        """Test error handling for insufficient text."""
        result = extract_key_findings("short", max_findings=5)

        assert result["status"] == "error"
        assert "Insufficient research text" in result["error_message"]

    def test_extract_key_findings_empty_text(self):
        """Test error handling for empty text."""
        result = extract_key_findings("", max_findings=5)

        assert result["status"] == "error"


class TestSearchIndustryTrends:
    """Tests for the search_industry_trends tool."""

    def test_search_industry_trends_ml(self):
        """Test industry trends for ML field."""
        result = search_industry_trends("Machine Learning", region="US", max_results=3)

        assert result["status"] == "success"
        assert "trends" in result
        assert "hot_skills" in result
        assert "pain_points" in result
        assert len(result["trends"]) <= 3
        assert result["region"] == "US"
        assert result["field"] == "Machine Learning"

    def test_search_industry_trends_nlp(self):
        """Test industry trends for NLP field."""
        result = search_industry_trends("NLP")

        assert result["status"] == "success"
        assert any(
            "Transformers" in skill or "LangChain" in skill for skill in result["hot_skills"]
        )

    def test_search_industry_trends_cv(self):
        """Test industry trends for Computer Vision."""
        result = search_industry_trends("Computer Vision")

        assert result["status"] == "success"
        assert any("OpenCV" in skill or "YOLO" in skill for skill in result["hot_skills"])

    def test_search_industry_trends_unknown_field(self):
        """Test handling of unknown field."""
        result = search_industry_trends("Quantum Computing")

        assert result["status"] == "success"
        # Should still return generic skills
        assert len(result["hot_skills"]) > 0


class TestGenerateSEOKeywords:
    """Tests for the generate_seo_keywords tool."""

    def test_generate_seo_keywords_consultant(self):
        """Test SEO keywords for consultant role."""
        result = generate_seo_keywords("Machine Learning", role="AI Consultant")

        assert result["status"] == "success"
        assert "primary_keywords" in result
        assert "technical_keywords" in result
        assert "action_keywords" in result
        assert "combined_phrases" in result
        assert any("Consultant" in kw for kw in result["primary_keywords"])

    def test_generate_seo_keywords_engineer(self):
        """Test SEO keywords for engineer role."""
        result = generate_seo_keywords("Deep Learning", role="ML Engineer")

        assert result["status"] == "success"
        assert any("Engineer" in kw for kw in result["primary_keywords"])

    def test_generate_seo_keywords_with_topic(self):
        """Test that topic influences technical keywords."""
        result = generate_seo_keywords("Natural Language Processing", role="AI Expert")

        assert result["status"] == "success"
        # Should include NLP-related keywords
        assert any(
            kw in result["technical_keywords"]
            for kw in ["NLP", "LLM", "Transformers", "GPT", "BERT"]
        )

    def test_generate_seo_keywords_structure(self):
        """Test the structure of returned keywords."""
        result = generate_seo_keywords("AI", role="Specialist")

        assert result["status"] == "success"
        assert len(result["primary_keywords"]) <= 5
        assert len(result["technical_keywords"]) <= 5
        assert len(result["action_keywords"]) <= 5
        assert len(result["combined_phrases"]) > 0


class TestCreateEngagementHooks:
    """Tests for the create_engagement_hooks tool."""

    def test_create_engagement_hooks_opportunities(self):
        """Test engagement hooks for opportunities goal."""
        result = create_engagement_hooks("AI Agents", goal="opportunities")

        assert result["status"] == "success"
        assert result["goal"] == "opportunities"
        assert len(result["opening_hooks"]) == 3
        assert len(result["closing_ctas"]) == 3
        assert len(result["discussion_questions"]) == 3
        assert len(result["portfolio_prompts"]) == 3

        # Check that hooks are relevant
        assert any("AI Agents" in hook for hook in result["opening_hooks"])

    def test_create_engagement_hooks_discussion(self):
        """Test engagement hooks for discussion goal."""
        result = create_engagement_hooks("Machine Learning", goal="discussion")

        assert result["status"] == "success"
        assert result["goal"] == "discussion"

    def test_create_engagement_hooks_credibility(self):
        """Test engagement hooks for credibility goal."""
        result = create_engagement_hooks("NLP", goal="credibility")

        assert result["status"] == "success"
        assert result["goal"] == "credibility"

    def test_create_engagement_hooks_visibility(self):
        """Test engagement hooks for visibility goal."""
        result = create_engagement_hooks("Computer Vision", goal="visibility")

        assert result["status"] == "success"
        assert result["goal"] == "visibility"

    def test_create_engagement_hooks_default_goal(self):
        """Test default goal handling."""
        result = create_engagement_hooks("AI", goal="invalid_goal")

        assert result["status"] == "success"
        # Should default to credibility
        assert len(result["opening_hooks"]) > 0


class TestAnalyzeContentForOpportunities:
    """Tests for the analyze_content_for_opportunities tool."""

    def test_analyze_high_quality_content(self):
        """Test analysis of high-quality optimized content."""
        content = """
        As an AI Consultant specializing in Machine Learning and Deep Learning,
        I help companies scale their ML solutions to production using PyTorch and TensorFlow.

        Recent projects demonstrate ROI through improved business outcomes and optimized workflows.
        Let's connect to discuss how I can help solve your AI challenges.

        What are your thoughts on this approach? Have you implemented similar solutions?
        Follow for more insights on production ML engineering.

        #MachineLearning #AIConsulting #MLOps #Python #DeepLearning
        """
        result = analyze_content_for_opportunities(content, target_role="AI Consultant")

        assert result["status"] == "success"
        assert result["opportunity_score"] >= 60
        assert result["seo_score"] > 0
        assert result["engagement_score"] > 0
        assert result["value_score"] > 0
        assert "suggestions" in result
        assert result["grade"] in ["Excellent", "Good", "Needs Improvement"]

    def test_analyze_low_quality_content(self):
        """Test analysis of basic content without optimization."""
        # Need at least 100 chars for analysis
        content = "This is a short post about AI. " * 5  # Make it long enough
        result = analyze_content_for_opportunities(content, target_role="AI Consultant")

        assert result["status"] == "success"
        assert result["opportunity_score"] < 60
        assert len(result["suggestions"]) > 0

    def test_analyze_with_seo_keywords(self):
        """Test that SEO keywords improve score."""
        content_with_seo = (
            """
        AI Engineer specializing in Machine Learning, Deep Learning, PyTorch, and TensorFlow.
        ML expert in neural networks and Python development.
        """
            * 2
        )  # Make it longer
        result = analyze_content_for_opportunities(content_with_seo, target_role="AI Engineer")

        assert result["status"] == "success"
        assert result["seo_score"] > 50

    def test_analyze_with_engagement_hooks(self):
        """Test that engagement hooks improve score."""
        content_with_hooks = (
            """
        Let's discuss AI solutions. What's your experience with ML?
        Connect with me to share your thoughts. Have you tried this approach?
        Follow for more insights. DM me to collaborate.
        """
            * 2
        )
        result = analyze_content_for_opportunities(content_with_hooks)

        assert result["status"] == "success"
        assert result["engagement_score"] > 50

    def test_analyze_with_business_value(self):
        """Test that business value language improves score."""
        content_with_value = (
            """
        Our production ML solution delivered significant ROI through optimized scale.
        The business impact was measurable with improved results across all metrics.
        This solution addresses key challenges in production systems.
        """
            * 2
        )
        result = analyze_content_for_opportunities(content_with_value)

        assert result["status"] == "success"
        assert result["value_score"] > 50

    def test_analyze_too_short(self):
        """Test error handling for too-short content."""
        result = analyze_content_for_opportunities("short")

        assert result["status"] == "error"
        assert "too short" in result["error_message"].lower()

    def test_analyze_empty_content(self):
        """Test error handling for empty content."""
        result = analyze_content_for_opportunities("")

        assert result["status"] == "error"


class TestToolsIntegration:
    """Integration tests for tools working together."""

    def test_paper_search_to_citations(self):
        """Test workflow: search papers -> generate citations."""
        # Search papers
        papers_result = search_papers("transformer models", max_results=2)
        assert papers_result["status"] == "success"

        # Convert to citation format
        if papers_result["papers"]:
            sources = [
                {
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "link": paper["link"],
                    "year": "2024",
                }
                for paper in papers_result["papers"]
            ]

            # Generate citations
            citations_result = generate_citations(sources, "apa")
            assert citations_result["status"] == "success"
            assert len(citations_result["citations"]) == len(sources)

    def test_content_formatting_to_analysis(self):
        """Test workflow: format content -> analyze for opportunities."""
        # Format content
        raw_content = "AI and Machine Learning innovations for business solutions."
        format_result = format_for_platform(raw_content, "linkedin", "AI")
        assert format_result["status"] == "success"

        # Analyze formatted content
        analysis_result = analyze_content_for_opportunities(
            format_result["formatted_content"], target_role="AI Consultant"
        )
        assert analysis_result["status"] == "success"

    def test_seo_keywords_to_engagement_hooks(self):
        """Test workflow: generate SEO keywords -> create engagement hooks."""
        # Generate keywords
        seo_result = generate_seo_keywords("Deep Learning", role="ML Engineer")
        assert seo_result["status"] == "success"

        # Create hooks
        hooks_result = create_engagement_hooks("Deep Learning", goal="opportunities")
        assert hooks_result["status"] == "success"

        # Both should be relevant to the topic
        combined_text = (
            " ".join(seo_result["technical_keywords"])
            + " "
            + " ".join(hooks_result["opening_hooks"])
        )
        assert "learning" in combined_text.lower()
