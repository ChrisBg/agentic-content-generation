"""Security regression tests: path sandboxing, LLM tool confinement, XML hardening, Gradio bind, secret scan."""

from __future__ import annotations

import inspect
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import src.security as security
from scripts.security_check import run_security_audit
from src.knowledge_base import get_voice_and_style_guide, retrieve_personal_evidence
from src.research_sources import (
    fetch_alphaxiv_overview,
    fetch_arxiv_pdf_text,
    fetch_industry_rss_feeds,
)
from src.security import resolve_safe_path
from src.tools import search_arxiv_papers
from src.video_assets import render_short_explainer_video
from src.visuals import (
    render_architecture_diagram,
    render_data_chart,
    render_demo_overlays,
    render_linkedin_carousel_pdf,
)
from ui_app import get_launch_config, save_human_edits


class TestPathSandboxing:
    """Ensure LLM-facing visual/video tools and UI edits cannot escape their sandbox."""

    def test_resolve_safe_path_blocks_traversal_and_absolute_escapes(self, tmp_path: Path):
        allowed = tmp_path / "sandbox"
        allowed.mkdir()

        # Legitimate relative path works
        ok = resolve_safe_path("chart.png", allowed)
        assert ok == (allowed / "chart.png").resolve()

        # Relative traversal blocked
        with pytest.raises(PermissionError):
            resolve_safe_path("../../etc/passwd", allowed)

        # Absolute path outside sandbox blocked
        with pytest.raises(PermissionError):
            resolve_safe_path("/etc/passwd", allowed)

        # Symlink escaping sandbox blocked
        outside = tmp_path / "secret.txt"
        outside.write_text("secret", encoding="utf-8")
        link = allowed / "evil_link.txt"
        link.symlink_to(outside)
        with pytest.raises(PermissionError):
            resolve_safe_path("evil_link.txt", allowed)

    def test_visual_tools_block_path_traversal(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(security, "SAFE_ASSET_ROOT", tmp_path / "assets")

        assert (
            render_data_chart(
                title="Test",
                labels=["A"],
                values=[1.0],
                output_path="../../evil.png",
            )["status"]
            == "error"
        )
        assert (
            render_architecture_diagram(
                title="Test",
                nodes=["A", "B"],
                output_path="/tmp/escape_arch.png",
            )["status"]
            == "error"
        )
        assert (
            render_linkedin_carousel_pdf(
                slides=[{"title": "Slide 1"}],
                output_path="../escape.pdf",
            )["status"]
            == "error"
        )
        assert (
            render_demo_overlays(
                cues=[{"label": "Step 1", "detail": "x"}],
                output_dir="../../escape_overlays",
            )["status"]
            == "error"
        )

    def test_video_tool_blocks_traversal_and_enforces_timeout(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(security, "SAFE_ASSET_ROOT", tmp_path / "assets")

        res_out = render_short_explainer_video(
            storyboard=[{"title": "Hook", "narration": "Test"}],
            output_path="../../escape.mp4",
        )
        assert res_out["status"] == "error"

        res_audio = render_short_explainer_video(
            storyboard=[{"title": "Hook", "narration": "Test"}],
            output_path="ok.mp4",
            audio_path="/etc/passwd",
        )
        assert res_audio["status"] == "error"

        # Verify FFmpeg timeout is handled cleanly
        with (
            patch("src.video_assets.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "src.video_assets.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=120),
            ),
        ):
            res_timeout = render_short_explainer_video(
                storyboard=[{"title": "Hook", "narration": "Test"}],
                output_path="timeout_test.mp4",
            )
            assert res_timeout["status"] == "error"
            assert "timed out" in res_timeout["error_message"].lower()

    def test_save_human_edits_blocks_escape_outside_output(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(security, "SAFE_OUTPUT_ROOT", tmp_path / "output")
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        msg, zip_out = save_human_edits(str(outside_dir), "hacked", "", "")
        assert "Blocked" in msg
        assert zip_out is None
        assert not (outside_dir / "linkedin_post.txt").exists()


class TestLLMToolConfinement:
    """Verify LLM tools do not expose filesystem path overrides."""

    def test_knowledge_base_llm_tools_expose_no_directory_param(self):
        assert "knowledge_dir" not in inspect.signature(retrieve_personal_evidence).parameters
        assert "knowledge_dir" not in inspect.signature(get_voice_and_style_guide).parameters


class TestXMLHardening:
    """Verify defusedxml blocks XXE / DTD entity expansion on arXiv responses."""

    @patch("src.tools.requests.get")
    def test_arxiv_blocks_xxe_payload(self, mock_get):
        xxe_payload = b"""<?xml version="1.0"?>
        <!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
        <feed xmlns="http://www.w3.org/2005/Atom"><entry><title>&xxe;</title></entry></feed>
        """
        mock_resp = MagicMock()
        mock_resp.content = xxe_payload
        mock_get.return_value = mock_resp

        res = search_arxiv_papers("security test")
        assert res["status"] == "error"

    @patch("src.research_sources.requests.get")
    def test_rss_feeds_block_xxe_payload(self, mock_get):
        xxe_rss = b"""<?xml version="1.0"?>
        <!DOCTYPE rss [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
        <rss><channel><item><title>&xxe;</title></item></channel></rss>
        """
        mock_resp = MagicMock()
        mock_resp.content = xxe_rss
        mock_get.return_value = mock_resp

        res = fetch_industry_rss_feeds(category="adtech")
        assert res["status"] == "success"
        assert res["items"] == []
        assert len(res["feed_errors"]) > 0


class TestResearchSourcesSSRFProtection:
    """Verify research source tools block arbitrary URLs / SSRF attempts."""

    def test_alphaxiv_and_arxiv_pdf_reject_ssrf_urls(self):
        assert (
            fetch_alphaxiv_overview("http://169.254.169.254/latest/meta-data")["status"] == "error"
        )
        assert fetch_arxiv_pdf_text("http://localhost:8080/internal.pdf")["status"] == "error"
        assert fetch_arxiv_pdf_text("../../etc/passwd")["status"] == "error"

    def test_rss_tool_exposes_no_arbitrary_url_parameter(self):
        assert "url" not in inspect.signature(fetch_industry_rss_feeds).parameters
        assert "feed_url" not in inspect.signature(fetch_industry_rss_feeds).parameters


class TestGradioNetworkSecurity:
    """Verify Gradio defaults to localhost and refuses unauthenticated 0.0.0.0 binds."""

    def test_gradio_defaults_to_localhost(self, monkeypatch):
        monkeypatch.delenv("GRADIO_SERVER_NAME", raising=False)
        monkeypatch.delenv("GRADIO_AUTH_USER", raising=False)
        monkeypatch.delenv("GRADIO_AUTH_PASSWORD", raising=False)

        cfg = get_launch_config()
        assert cfg["server_name"] == "127.0.0.1"
        assert cfg["share"] is False

    def test_gradio_blocks_unauthenticated_all_interfaces_bind(self, monkeypatch):
        monkeypatch.setenv("GRADIO_SERVER_NAME", "0.0.0.0")
        monkeypatch.delenv("GRADIO_AUTH_USER", raising=False)
        monkeypatch.delenv("GRADIO_AUTH_PASSWORD", raising=False)
        monkeypatch.delenv("ALLOW_UNAUTHENTICATED_LAN", raising=False)

        with pytest.raises(PermissionError):
            get_launch_config()

    def test_gradio_allows_non_localhost_when_basic_auth_configured(self, monkeypatch):
        monkeypatch.setenv("GRADIO_SERVER_NAME", "0.0.0.0")
        monkeypatch.setenv("GRADIO_AUTH_USER", "admin")
        monkeypatch.setenv("GRADIO_AUTH_PASSWORD", "strong-pass-123")

        cfg = get_launch_config()
        assert cfg["server_name"] == "0.0.0.0"
        assert cfg["auth"] == ("admin", "strong-pass-123")


class TestStaticSecurityAudit:
    """Run the repo-wide static security scanner as part of pytest."""

    def test_repo_passes_static_security_audit(self):
        assert run_security_audit() == []
