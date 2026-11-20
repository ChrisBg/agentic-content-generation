"""Unit tests for v2.1 extended research sources (OpenAlex, HuggingFace Daily, alphaXiv, HAL, arXiv PDF, RSS)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.research_sources import (
    MAX_PDF_BYTES,
    fetch_alphaxiv_overview,
    fetch_arxiv_pdf_text,
    fetch_industry_rss_feeds,
    search_hal_papers,
    search_huggingface_daily_papers,
    search_openalex_papers,
    validate_arxiv_id,
)

SAMPLE_RSS_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>AdExchanger</title>
    <item>
      <title>Tackling Made-For-Advertising Fraud With Agentic AI</title>
      <link>https://www.adexchanger.com/mfa-agentic-ai</link>
      <pubDate>Thu, 19 Nov 2026 10:00:00 GMT</pubDate>
      <description>&lt;p&gt;Programmatic buyers adopt hybrid ML cascades to cut MFA spend.&lt;/p&gt;</description>
    </item>
  </channel>
</rss>
"""


class TestArxivIdValidation:
    """Tests for strict arXiv ID normalization & SSRF prevention."""

    def test_valid_ids_and_canonical_urls(self):
        assert validate_arxiv_id("2604.05018") == "2604.05018"
        assert validate_arxiv_id("2604.05018v2") == "2604.05018v2"
        assert validate_arxiv_id("arXiv:2604.05018") == "2604.05018"
        assert validate_arxiv_id("https://arxiv.org/abs/2604.05018v1") == "2604.05018v1"
        assert validate_arxiv_id("https://www.alphaxiv.org/overview/2604.05018.md") == "2604.05018"

    def test_rejects_ssrf_and_malformed_ids(self):
        for bad in [
            "http://169.254.169.254/latest/meta-data",
            "../../etc/passwd",
            "2604.05018?foo=bar",
            "https://evil.com/abs/2604.05018",
            "not-an-id",
        ]:
            with pytest.raises(ValueError):
                validate_arxiv_id(bad)


class TestOpenAlex:
    """Tests for OpenAlex works search and inverted-index abstract reconstruction."""

    @patch("src.research_sources.requests.get")
    def test_search_openalex_reconstructs_abstract_and_bibtex(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [
                {
                    "display_name": "Econometric Detection of Programmatic Ad Fraud",
                    "publication_year": 2025,
                    "cited_by_count": 37,
                    "doi": "https://doi.org/10.1000/adfraud",
                    "authorships": [
                        {"author": {"display_name": "Christophe Bourgoin"}},
                        {"author": {"display_name": "Jane Doe"}},
                    ],
                    "abstract_inverted_index": {
                        "Hybrid": [0],
                        "econometric": [1],
                        "models": [2],
                        "detect": [3],
                        "MFA": [4],
                        "domains.": [5],
                    },
                    "primary_location": {
                        "landing_page_url": "https://example.org/adfraud",
                        "source": {"display_name": "Journal of Marketing Science"},
                    },
                    "open_access": {"oa_url": "https://example.org/adfraud.pdf"},
                }
            ]
        }
        mock_get.return_value = mock_resp

        res = search_openalex_papers("ad fraud econometrics", max_results=3, year_from=2022)
        assert res["status"] == "success"
        assert res["count"] == 1
        paper = res["papers"][0]
        assert paper["year"] == 2025
        assert paper["citation_count"] == 37
        assert paper["abstract"] == "Hybrid econometric models detect MFA domains."
        assert paper["open_access_pdf"] == "https://example.org/adfraud.pdf"
        assert paper["source"] == "openalex"
        assert "year = {2025}" in paper["bibtex"]


class TestHuggingFaceDailyPapers:
    """Tests for Hugging Face Daily Papers feed + filtering."""

    @patch("src.research_sources.requests.get")
    def test_search_hf_daily_papers_with_query_filter(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "paper": {
                    "id": "2604.05018",
                    "title": "PaperOrchestra: Multi-Agent Research Writing",
                    "summary": "Multi-agent orchestration for scientific manuscripts.",
                    "authors": [{"name": "Yiwen Song"}],
                    "publishedAt": "2026-04-06T00:00:00Z",
                    "upvotes": 148,
                },
                "githubUrl": "https://github.com/google-research/paper-orchestra",
            },
            {
                "paper": {
                    "id": "2604.09999",
                    "title": "Unrelated 3D Mesh Rendering",
                    "summary": "Graphics pipeline.",
                    "authors": [{"name": "Someone"}],
                    "publishedAt": "2026-04-05T00:00:00Z",
                    "upvotes": 12,
                }
            },
        ]
        mock_get.return_value = mock_resp

        res = search_huggingface_daily_papers(query="multi-agent", max_results=5)
        assert res["status"] == "success"
        assert res["count"] == 1
        p = res["papers"][0]
        assert p["arxiv_id"] == "2604.05018"
        assert p["upvotes"] == 148
        assert p["github_url"] == "https://github.com/google-research/paper-orchestra"
        assert p["alphaxiv_url"] == "https://www.alphaxiv.org/abs/2604.05018"


class TestAlphaXiv:
    """Tests for alphaXiv Markdown overview fetching."""

    @patch("src.research_sources.requests.get")
    def test_fetch_alphaxiv_overview_markdown(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = (
            "# PaperOrchestra Overview\n\n## Core Problem\nAutomated scientific writing."
        )
        mock_get.return_value = mock_resp

        res = fetch_alphaxiv_overview("2604.05018")
        assert res["status"] == "success"
        assert res["arxiv_id"] == "2604.05018"
        assert "Core Problem" in res["overview_markdown"]
        assert res["alphaxiv_url"] == "https://www.alphaxiv.org/abs/2604.05018"

    @patch("src.research_sources.requests.get")
    def test_fetch_alphaxiv_rejects_html_fallback(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<!DOCTYPE html><html><body>SPA shell</body></html>"
        mock_get.return_value = mock_resp

        res = fetch_alphaxiv_overview("2604.05018")
        assert res["status"] == "error"


class TestHALArchive:
    """Tests for French HAL open archive search."""

    @patch("src.research_sources.requests.get")
    def test_search_hal_papers(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "response": {
                "docs": [
                    {
                        "title_s": ["Détection de fraude publicitaire par apprentissage hybride"],
                        "abstract_s": ["Étude économétrique et ML appliquée à l'AdTech."],
                        "authFullName_s": ["Christophe Bourgoin"],
                        "producedDateY_i": 2026,
                        "uri_s": "https://hal.science/hal-01234567",
                        "halId_s": "hal-01234567",
                        "doiId_s": "10.1234/hal",
                    }
                ]
            }
        }
        mock_get.return_value = mock_resp

        res = search_hal_papers("fraude publicitaire", max_results=3, year_from=2024)
        assert res["status"] == "success"
        assert res["count"] == 1
        p = res["papers"][0]
        assert p["year"] == 2026
        assert p["hal_id"] == "hal-01234567"
        assert p["source"] == "hal"


class TestArxivPdfReader:
    """Tests for in-memory arXiv full-text PDF extraction."""

    @patch("src.research_sources.PdfReader")
    @patch("src.research_sources.requests.get")
    def test_fetch_arxiv_pdf_text_success(self, mock_get, mock_pdf_cls):
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"%PDF-1.4 fake bytes"]
        mock_get.return_value = mock_resp

        fake_page = MagicMock()
        fake_page.extract_text.return_value = "Table 1: Hybrid Cascade reaches 94.7% recall."
        mock_pdf_cls.return_value.pages = [fake_page]

        res = fetch_arxiv_pdf_text("2604.05018", max_pages=4)
        assert res["status"] == "success"
        assert res["pages_extracted"] == 1
        assert "94.7% recall" in res["text"]

    @patch("src.research_sources.requests.get")
    def test_fetch_arxiv_pdf_enforces_size_cap(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"A" * (MAX_PDF_BYTES + 1024)]
        mock_get.return_value = mock_resp

        res = fetch_arxiv_pdf_text("2604.05018")
        assert res["status"] == "error"
        assert "maximum allowed size" in res["error_message"].lower()


class TestIndustryRSSFeeds:
    """Tests for curated allowlisted AdTech & AI Engineering RSS feeds."""

    @patch("src.research_sources.requests.get")
    def test_fetch_adtech_rss_with_query(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS_XML
        mock_get.return_value = mock_resp

        res = fetch_industry_rss_feeds(category="adtech", query="MFA", max_items=5)
        assert res["status"] == "success"
        assert res["count"] >= 1
        assert "Made-For-Advertising" in res["items"][0]["title"]

    def test_rejects_invalid_category(self):
        res = fetch_industry_rss_feeds(category="https://evil.com/feed.xml")
        assert res["status"] == "error"
