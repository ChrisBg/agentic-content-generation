"""Unit tests for personal Knowledge Base retrieval (Voice DNA & Case Studies)."""

from __future__ import annotations

from pathlib import Path

import src.knowledge_base as kb
from src.knowledge_base import (
    get_voice_and_style_guide,
    init_knowledge_base,
    retrieve_personal_evidence,
)


class TestKnowledgeBase:
    """Tests for local knowledge base initialization and retrieval."""

    def test_init_and_retrieve_personal_evidence(self, tmp_path: Path, monkeypatch):
        kb_dir = init_knowledge_base(tmp_path / "kb")
        monkeypatch.setattr(kb, "LOCAL_KNOWLEDGE_DIR", kb_dir)
        assert (kb_dir / "case_studies.yaml").exists()
        assert (kb_dir / "voice_dna.md").exists()
        assert (kb_dir / "banned_phrases.yaml").exists()

        res = retrieve_personal_evidence("fraud detection adtech xgboost")
        assert res["status"] == "success"
        assert res["count"] >= 1
        assert "fraud" in res["case_studies"][0]["title"].lower()

    def test_get_voice_and_style_guide(self, tmp_path: Path, monkeypatch):
        kb_dir = init_knowledge_base(tmp_path / "kb")
        monkeypatch.setattr(kb, "LOCAL_KNOWLEDGE_DIR", kb_dir)
        guide = get_voice_and_style_guide("fr")
        assert guide["status"] == "success"
        assert len(guide["banned_phrases"]) > 5
        assert "linkedin" in guide["platform_rules"]
        assert "x" in guide["platform_rules"]
        assert "youtube" in guide["platform_rules"]
