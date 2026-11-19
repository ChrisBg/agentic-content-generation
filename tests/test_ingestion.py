"""Unit tests for the PaperOrchestra-compatible raw material ingestion bridge."""

from __future__ import annotations

import json
from pathlib import Path

from src.ingestion import ingest_materials


class TestPaperOrchestraIngestion:
    """Tests for ingesting .tex, .bib, .ipynb, .json, .csv, and .md files."""

    def test_ingest_latex_and_json_directory(self, tmp_path: Path):
        tex_file = tmp_path / "manuscript.tex"
        tex_file.write_text(
            r"""
            \title{Frugal MFA Detection with Hybrid Agents}
            \begin{abstract}
            Hybrid cascade keeps cost under 0.001 EUR/page at 94.7\% recall.
            \end{abstract}
            \section{Results}
            \begin{tabular}{lcc}
            \toprule
            Model & Recall & Cost \\
            \midrule
            Rules & 51.2 & 0.05 \\
            Hybrid & 94.7 & 0.72 \\
            \bottomrule
            \end{tabular}
            """,
            encoding="utf-8",
        )

        bib_file = tmp_path / "refs.bib"
        bib_file.write_text(
            "@misc{song2026paperorchestra,\n  title={PaperOrchestra},\n  author={Song, Yiwen},\n  year={2026}\n}\n",
            encoding="utf-8",
        )

        json_file = tmp_path / "metrics.json"
        json_file.write_text(
            json.dumps(
                {
                    "weekly_pages": 15000000,
                    "runs": [
                        {"model": "Rules", "recall": 51.2},
                        {"model": "Hybrid", "recall": 94.7},
                    ],
                }
            ),
            encoding="utf-8",
        )

        bundle = ingest_materials(
            input_paths=[tmp_path],
            topic="",
            human_seed="Unit economics beat leaderboard scores in AdTech.",
        )

        # Infers topic from LaTeX title when topic is empty
        assert "Frugal MFA Detection" in bundle.topic
        assert "0.001 EUR/page" in bundle.latex_abstract
        assert "Results" in bundle.sections
        assert len(bundle.tables) >= 2  # LaTeX tabular + JSON runs table
        assert len(bundle.bibtex_entries) == 1
        assert any(m.name == "weekly_pages" and m.value == 15000000 for m in bundle.metrics)

        prompt_ctx = bundle.to_prompt_context()
        assert "HUMAN SEED" in prompt_ctx
        assert "VERIFIED EXPERIMENTAL METRICS" in prompt_ctx
        assert "PRE-VERIFIED BIBTEX" in prompt_ctx

    def test_ingest_notebook_and_csv(self, tmp_path: Path):
        nb = {
            "cells": [
                {"cell_type": "markdown", "source": ["# MFA Experiment Notes\n", "Key finding."]},
                {
                    "cell_type": "code",
                    "source": ["print('recall: 94.7%')"],
                    "outputs": [{"text": ["recall: 94.7%\n"]}],
                },
            ]
        }
        (tmp_path / "exp.ipynb").write_text(json.dumps(nb), encoding="utf-8")
        (tmp_path / "bench.csv").write_text(
            "model,cost\nrules,0.05\nhybrid,0.72\n", encoding="utf-8"
        )

        bundle = ingest_materials(input_paths=[tmp_path], topic="MFA Benchmark")
        assert len(bundle.code_snippets) == 1
        assert any(m.name == "recall" and m.value == 94.7 for m in bundle.metrics)
        assert any(t.source_file == "bench.csv" for t in bundle.tables)
