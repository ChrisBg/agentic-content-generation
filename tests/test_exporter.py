"""Unit tests for structured ready-to-post bundle exporter and ZIP packaging."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from src.exporter import export_content_bundle, parse_final_sections

SAMPLE_FINAL_CONTENT = """
=== FINAL LINKEDIN POST ===
Modérer 15M de pages par semaine sous 0,001 EUR/page demande une architecture hybride.

#AIEngineering #AdTech #MLOps

=== FINAL X THREAD ===
1/ Frontier LLMs alone break AdTech unit economics.
2/ A hybrid cascade achieves 94.7% recall at 0.72 EUR per 1k pages.

=== FINAL X STANDALONE POSTS ===
POST A: Production AI is won on unit economics, not leaderboard scores.

=== FINAL YOUTUBE PACKAGE ===
Titles:
1. How to Moderate 15M Web Pages/Week Under 0.001 EUR/Page

=== BIBTEX REFERENCES ===
@misc{song2026paperorchestra,
  title = {PaperOrchestra},
  author = {Yiwen Song},
  year = {2026},
}

=== QUALITY REPORT ===
FACT_CHECK_STATUS: PASS
EDITORIAL_SCORE: 92/100
"""


class TestBundleExporter:
    """Tests for parsing sections, exporting assets, and creating ZIP archives."""

    def test_parse_final_sections(self):
        sections = parse_final_sections(SAMPLE_FINAL_CONTENT)
        assert "linkedin" in sections
        assert "x_thread" in sections
        assert "x_standalone" in sections
        assert "youtube" in sections
        assert "bibtex" in sections
        assert "quality_report" in sections

    def test_export_content_bundle_and_zip(self, tmp_path: Path):
        tmp_assets = tmp_path / "tmp_assets"
        (tmp_assets / "overlays").mkdir(parents=True)
        (tmp_assets / "chart.png").write_bytes(b"PNGDATA")
        (tmp_assets / "linkedin_carousel.pdf").write_bytes(b"%PDF-1.4")
        (tmp_assets / "demo_explainer_16x9.mp4").write_bytes(b"MP4DATA")
        (tmp_assets / "overlays" / "overlay_01.png").write_bytes(b"OVL")

        exported = export_content_bundle(
            topic="Frugal MFA Detection",
            final_content=SAMPLE_FINAL_CONTENT,
            channels=["linkedin", "x", "youtube"],
            language="fr",
            routing_table={"linkedin": {"model": "anthropic/claude-sonnet-4-5-20250929"}},
            tmp_assets_dir=tmp_assets,
            base_output_dir=tmp_path / "out",
        )

        bundle_dir = Path(exported["bundle_dir"])
        assert (bundle_dir / "linkedin_post.txt").exists()
        assert (bundle_dir / "x_thread.md").exists()
        assert (bundle_dir / "youtube_package.md").exists()
        assert (bundle_dir / "references.bib").exists()
        assert (bundle_dir / "quality_report.md").exists()
        assert (bundle_dir / "linkedin_carousel.pdf").exists()
        assert (bundle_dir / "figures" / "chart.png").exists()
        assert (bundle_dir / "figures" / "overlays" / "overlay_01.png").exists()
        assert (bundle_dir / "videos" / "demo_explainer_16x9.mp4").exists()

        meta = json.loads((bundle_dir / "bundle.json").read_text(encoding="utf-8"))
        assert meta["topic"] == "Frugal MFA Detection"
        assert meta["channels"] == ["linkedin", "x", "youtube"]

        zip_path = Path(exported["zip_path"])
        assert zip_path.exists()
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert "linkedin_post.txt" in names
            assert "references.bib" in names
            assert "figures/chart.png" in names
