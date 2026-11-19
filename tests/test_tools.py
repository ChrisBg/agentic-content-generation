"""Unit tests for v2 grounded research, BibTeX, deterministic linter, and loop tools."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.tools import (
    exit_loop,
    generate_bibtex,
    search_arxiv_papers,
    search_semantic_scholar,
    validate_deliverables_deterministic,
    verify_citation_semantic_scholar,
)

SAMPLE_ARXIV_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2604.05018v1</id>
    <published>2026-04-06T12:00:00Z</published>
    <title>PaperOrchestra: A Multi-Agent Framework for Automated AI Research Paper Writing</title>
    <summary>We introduce PaperOrchestra, a multi-agent framework that transforms unstructured pre-writing materials into submission-ready LaTeX manuscripts with verified Semantic Scholar citations and automated plotting.</summary>
    <author><name>Yiwen Song</name></author>
    <author><name>Jinsung Yoon</name></author>
  </entry>
</feed>
"""


class TestSemanticScholarTools:
    """Tests for Semantic Scholar search and citation verification."""

    @patch("src.tools.requests.get")
    def test_search_semantic_scholar_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {
                    "title": "PaperOrchestra: Automated AI Research Paper Writing",
                    "authors": [{"name": "Yiwen Song"}, {"name": "Jinsung Yoon"}],
                    "year": 2026,
                    "venue": "arXiv",
                    "citationCount": 42,
                    "abstract": "Multi-agent framework for scientific manuscripts.",
                    "url": "https://www.semanticscholar.org/paper/abc123",
                    "externalIds": {"ArXiv": "2604.05018", "DOI": "10.1234/example"},
                }
            ]
        }
        mock_get.return_value = mock_resp

        result = search_semantic_scholar("PaperOrchestra", max_results=3, year_from=2025)
        assert result["status"] == "success"
        assert result["count"] == 1
        paper = result["papers"][0]
        assert paper["year"] == 2026
        assert paper["citation_count"] == 42
        assert paper["arxiv_id"] == "2604.05018"
        assert "@misc{" in paper["bibtex"] or "@inproceedings{" in paper["bibtex"]

    def test_search_semantic_scholar_empty_query(self):
        result = search_semantic_scholar("   ")
        assert result["status"] == "error"

    @patch("src.tools.search_semantic_scholar")
    def test_verify_citation_semantic_scholar_match(self, mock_search):
        mock_search.return_value = {
            "status": "success",
            "papers": [
                {
                    "title": "Attention Is All You Need",
                    "authors": ["Ashish Vaswani"],
                    "year": 2017,
                }
            ],
        }
        res = verify_citation_semantic_scholar("Attention Is All You Need")
        assert res["status"] == "success"
        assert res["verified"] is True
        assert res["similarity"] >= 0.95

    @patch("src.tools.search_semantic_scholar")
    def test_verify_citation_semantic_scholar_mismatch(self, mock_search):
        mock_search.return_value = {
            "status": "success",
            "papers": [
                {"title": "Completely Unrelated Biology Study", "authors": ["X"], "year": 2020}
            ],
        }
        res = verify_citation_semantic_scholar("Frugal Ad Fraud Multi-Agent Cascade")
        assert res["status"] == "success"
        assert res["verified"] is False


class TestArxivTools:
    """Tests for relevance-sorted arXiv search."""

    @patch("src.tools.requests.get")
    def test_search_arxiv_papers_parses_year_and_full_abstract(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_ARXIV_XML
        mock_get.return_value = mock_resp

        res = search_arxiv_papers("PaperOrchestra", max_results=2)
        assert res["status"] == "success"
        assert res["count"] == 1
        paper = res["papers"][0]
        assert paper["year"] == 2026
        assert paper["arxiv_id"] == "2604.05018v1"
        assert "Semantic Scholar" in paper["abstract"]
        assert "sortBy" in mock_get.call_args.kwargs["params"]
        assert mock_get.call_args.kwargs["params"]["sortBy"] == "relevance"


class TestBibTeXGeneration:
    """Tests for BibTeX bibliography builder."""

    def test_generate_bibtex_deduplicates_entries(self):
        papers = [
            {
                "title": "Hybrid MFA Detection",
                "authors": ["Christophe Bourgoin"],
                "year": 2026,
                "venue": "ICLR",
                "url": "https://example.org/mfa",
            },
            {
                "title": "Hybrid MFA Detection",
                "authors": ["Christophe Bourgoin"],
                "year": 2026,
            },
        ]
        res = generate_bibtex(papers)
        assert res["status"] == "success"
        assert res["count"] == 1
        assert "@inproceedings{bourgoin2026hybrid," in res["bibtex"]
        assert "year = {2026}" in res["bibtex"]

    def test_generate_bibtex_empty_error(self):
        assert generate_bibtex([])["status"] == "error"


class TestDeterministicLinter:
    """Tests for the anti-AI-slop & platform format deterministic gate."""

    def test_clean_bundle_passes(self):
        linkedin = (
            "Modérer 15M de pages par semaine avec un LLM frontier coûte trop cher.\n\n"
            "Dans notre benchmark interne, une cascade hybride règles statistiques + XGBoost "
            "ramène le coût unitaire sous 0,001€ par page tout en gardant 94,7% de rappel MFA.\n\n"
            "Comment arbitrez-vous coût d'inférence et précision dans vos pipelines IA en prod ?\n\n"
            "#AIEngineering #AdTech #MLOps"
        )
        tweets = [
            "1/ Running frontier LLMs on 15M web pages/week burns budget fast. A hybrid cascade hits 94.7% MFA recall at <0.001 EUR/page.",
            "2/ Rules filter obvious noise in 12ms; XGBoost scores ambiguous domains; the LLM agent only audits the top 3% edge cases.",
        ]
        yt_script = "[00:00] Hook: Here is why frontier-only LLM moderation breaks unit economics. [VISUAL #1: Benchmark Chart]"

        res = validate_deliverables_deterministic(
            linkedin_post=linkedin,
            x_tweets=tweets,
            youtube_script=yt_script,
        )
        assert res["passed"] is True
        assert res["violations"] == []

    def test_catches_broken_linkedin_markdown_placeholders_and_cliches(self):
        bad_linkedin = (
            "🚀 **Navigating the Next Wave** of AI! This is a game-changing moment.\n"
            "In my work on [mention a relevant project], we saw great results. TODO add link."
        )
        res = validate_deliverables_deterministic(linkedin_post=bad_linkedin)
        assert res["passed"] is False
        joined = " ".join(res["violations"])
        assert "Markdown bold" in joined
        assert "placeholder" in joined.lower()
        assert "TODO" in joined
        assert "cliché" in joined.lower()

    def test_catches_tweet_over_280_chars(self):
        long_tweet = "1/ " + ("x" * 290)
        res = validate_deliverables_deterministic(x_tweets=[long_tweet])
        assert res["passed"] is False
        assert res["stats"]["x_over_280_count"] == 1

    def test_youtube_visual_cues_are_not_flagged_as_placeholders(self):
        yt = "[VISUAL #1: Architecture Diagram] [B-ROLL: Terminal Demo] Clean technical script."
        res = validate_deliverables_deterministic(youtube_script=yt)
        assert res["passed"] is True


class TestExitLoopTool:
    """Tests for ADK LoopAgent escalation tool."""

    def test_exit_loop_sets_escalate(self):
        ctx = SimpleNamespace(actions=SimpleNamespace(escalate=False))
        res = exit_loop(ctx)
        assert res["status"] == "success"
        assert ctx.actions.escalate is True
