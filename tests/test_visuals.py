"""Unit tests for the visual asset engine (PNG charts, architecture diagrams, overlays, PDF carousels)."""

from __future__ import annotations

from pathlib import Path

import pytest

import src.security as security
from src.visuals import (
    render_architecture_diagram,
    render_data_chart,
    render_demo_overlays,
    render_linkedin_carousel_pdf,
)


@pytest.fixture(autouse=True)
def _sandbox_to_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(security, "SAFE_ASSET_ROOT", tmp_path)


class TestVisualAssetEngine:
    """Tests for real headless PNG/PDF visual generation."""

    def test_render_data_charts_bar_barh_line(self, tmp_path: Path):
        for kind in ["bar", "barh", "line"]:
            out = tmp_path / f"chart_{kind}.png"
            res = render_data_chart(
                title="MFA Detection Recall by Architecture",
                labels=["Rules Only", "LLM Only", "Hybrid Cascade"],
                values=[51.2, 93.4, 94.7],
                chart_type=kind,
                subtitle="100k labeled web domains",
                y_label="Recall (%)",
                source_note="Internal benchmark",
                output_path=str(out),
            )
            assert res["status"] == "success"
            assert out.exists()
            assert out.stat().st_size > 5_000

    def test_render_architecture_diagram_creates_png_and_mermaid(self, tmp_path: Path):
        out = tmp_path / "arch.png"
        res = render_architecture_diagram(
            title="Frugal Hybrid MFA Detection Pipeline",
            nodes=[
                "Web Crawler",
                "Statistical Rules",
                "XGBoost Classifier",
                "Agentic LLM Audit",
                "Blocklist API",
            ],
            subtitle="15M+ pages/week under 0.001 EUR/page",
            output_path=str(out),
        )
        assert res["status"] == "success"
        assert Path(res["png_path"]).exists()
        assert Path(res["mermaid_path"]).exists()
        assert "flowchart LR" in Path(res["mermaid_path"]).read_text(encoding="utf-8")

    def test_render_linkedin_carousel_pdf_with_embedded_chart(self, tmp_path: Path):
        chart = tmp_path / "bench.png"
        render_data_chart(
            title="Cost per 1k Pages (EUR)",
            labels=["LLM Only", "Hybrid"],
            values=[14.8, 0.72],
            output_path=str(chart),
        )
        pdf_path = tmp_path / "carousel.pdf"
        slides = [
            {
                "title": "Why Frontier LLMs Break AdTech Unit Economics",
                "bullets": ["15M pages/week moderated", "How to stay below 0.001 EUR/page"],
                "metric_callout": "-95% inference cost vs LLM-only",
            },
            {
                "title": "Benchmark: Cost per 1,000 Pages",
                "bullets": ["Hybrid cascade filters 97% of traffic before the LLM"],
            },
            {
                "title": "Takeaway for CTOs & AdTech Leaders",
                "bullets": ["Design for unit economics first", "DM to discuss AI/CIR R&D"],
            },
        ]
        res = render_linkedin_carousel_pdf(
            slides=slides,
            output_path=str(pdf_path),
            chart_paths=[str(chart)],
        )
        assert res["status"] == "success"
        assert res["slide_count"] == 3
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 5_000

    def test_render_demo_overlays(self, tmp_path: Path):
        res = render_demo_overlays(
            cues=[
                {"label": "Step 1: Statistical Filter", "detail": "12ms P95 latency"},
                {"label": "Step 2: Hybrid Cascade", "detail": "94.7% MFA recall at <0.001 EUR"},
            ],
            output_dir=str(tmp_path / "overlays"),
        )
        assert res["status"] == "success"
        assert res["count"] == 2
        for p in res["paths"]:
            assert Path(p).exists()
