"""Unit tests for the FFmpeg short demo video engine (16:9 X/YouTube & 9:16 Shorts) and shotlist."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import src.security as security
from src.video_assets import generate_demo_shotlist, render_short_explainer_video
from src.visuals import render_data_chart


@pytest.fixture(autouse=True)
def _sandbox_to_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(security, "SAFE_ASSET_ROOT", tmp_path)


class TestVideoAssets:
    """Tests for automated short demo MP4 generation and live demo shotlists."""

    def test_generate_demo_shotlist_fr_and_en(self):
        res_fr = generate_demo_shotlist(
            topic="Détection MFA hybride",
            steps=["Lancer le script de filtrage", "Afficher la matrice de coûts"],
            metrics=["94.7% recall", "<0.001 EUR/page"],
            language="fr",
        )
        assert res_fr["status"] == "success"
        assert "00:00 - 00:05" in res_fr["shotlist_markdown"]
        assert "94.7% recall" in res_fr["shotlist_markdown"]

        res_en = generate_demo_shotlist(
            topic="Hybrid MFA Detection",
            steps=["Run cascade CLI", "Compare P95 latency"],
            language="en",
        )
        assert res_en["status"] == "success"
        assert "Live Demo Runbook" in res_en["shotlist_markdown"]

    @pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg not installed")
    def test_render_short_explainer_video_16x9_and_9x16(self, tmp_path: Path):
        chart = tmp_path / "chart.png"
        render_data_chart(
            title="MFA Cost per 1k Pages",
            labels=["LLM", "Hybrid"],
            values=[14.8, 0.72],
            output_path=str(chart),
        )
        storyboard = [
            {
                "title": "Frontier LLMs Fail AdTech Unit Economics",
                "narration": "Moderating 15M pages/week with LLMs alone costs 14.8 EUR per 1k pages.",
                "metric": "14.80 EUR -> 0.72 EUR / 1k pages",
                "duration_sec": 2.5,
            },
            {
                "title": "Hybrid Cascade Benchmark",
                "narration": "Rules + XGBoost + selective agentic LLM keeps recall at 94.7%.",
                "image_path": str(chart),
                "duration_sec": 2.5,
            },
        ]

        for ratio, fname in [("16:9", "demo_16x9.mp4"), ("9:16", "short_9x16.mp4")]:
            out = tmp_path / fname
            res = render_short_explainer_video(
                storyboard=storyboard,
                output_path=str(out),
                aspect_ratio=ratio,
            )
            assert res["status"] == "success"
            assert out.exists()
            assert out.stat().st_size > 10_000
            srt = Path(res["srt_path"])
            assert srt.exists()
            assert "00:00:00,000 -->" in srt.read_text(encoding="utf-8")
