"""Pydantic schemas for structured inter-agent communication and export bundles."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ExtractedMetric(BaseModel):
    """Numeric benchmark or experimental result extracted from raw materials."""

    name: str
    value: float | str
    unit: str = ""
    baseline: float | str | None = None
    context: str = ""
    source_file: str = ""


class ExtractedTable(BaseModel):
    """Tabular dataset extracted from CSV, JSON, or LaTeX tabular blocks."""

    title: str
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    source_file: str = ""


class RawMaterialBundle(BaseModel):
    """Unified representation of PaperOrchestra-style pre-writing raw materials."""

    topic: str
    human_seed: str = ""
    ingested_files: list[str] = Field(default_factory=list)
    latex_title: str = ""
    latex_abstract: str = ""
    sections: dict[str, str] = Field(default_factory=dict)
    bibtex_entries: list[str] = Field(default_factory=list)
    tables: list[ExtractedTable] = Field(default_factory=list)
    metrics: list[ExtractedMetric] = Field(default_factory=list)
    code_snippets: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def to_prompt_context(self, max_chars: int = 12000) -> str:
        """Render a concise, structured summary suitable for LLM prompts."""
        parts: list[str] = [f"TOPIC: {self.topic}"]
        if self.human_seed:
            parts.append(
                f"\nHUMAN SEED (Author's personal angle — MUST be central):\n{self.human_seed}"
            )
        if self.ingested_files:
            parts.append(
                f"\nINGESTED RAW MATERIALS ({len(self.ingested_files)} files): {', '.join(self.ingested_files)}"
            )
        if self.latex_title:
            parts.append(f"\nMANUSCRIPT TITLE: {self.latex_title}")
        if self.latex_abstract:
            parts.append(f"\nABSTRACT:\n{self.latex_abstract}")
        if self.metrics:
            metric_lines = [
                f"- {m.name}: {m.value}{(' ' + m.unit) if m.unit else ''}"
                + (f" (baseline: {m.baseline})" if m.baseline is not None else "")
                + (f" [{m.source_file}]" if m.source_file else "")
                for m in self.metrics[:25]
            ]
            parts.append("\nVERIFIED EXPERIMENTAL METRICS:\n" + "\n".join(metric_lines))
        if self.tables:
            for tbl in self.tables[:4]:
                header_line = " | ".join(tbl.headers)
                row_lines = [" | ".join(r) for r in tbl.rows[:8]]
                parts.append(
                    f"\nTABLE ({tbl.title} from {tbl.source_file}):\n{header_line}\n"
                    + "\n".join(row_lines)
                )
        if self.sections:
            for sec_name, sec_body in list(self.sections.items())[:6]:
                snippet = sec_body[:1000] + ("..." if len(sec_body) > 1000 else "")
                parts.append(f"\nSECTION [{sec_name}]:\n{snippet}")
        if self.notes:
            combined_notes = "\n---\n".join(n[:1200] for n in self.notes[:5])
            parts.append(f"\nLAB NOTES & LOGS:\n{combined_notes}")
        if self.code_snippets:
            parts.append("\nCODE / COMMAND SNIPPETS:\n" + "\n\n".join(self.code_snippets[:3]))
        if self.bibtex_entries:
            parts.append(
                f"\nPRE-VERIFIED BIBTEX ENTRIES ({len(self.bibtex_entries)}):\n"
                + "\n".join(self.bibtex_entries[:10])
            )

        rendered = "\n".join(parts)
        if len(rendered) > max_chars:
            rendered = rendered[:max_chars] + "\n...[truncated to fit prompt budget]..."
        return rendered


class VerifiedPaper(BaseModel):
    """Academic paper metadata verified via Semantic Scholar or arXiv."""

    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    venue: str = ""
    citation_count: int | None = None
    abstract: str = ""
    url: str = ""
    arxiv_id: str = ""
    doi: str = ""
    source: Literal["semantic_scholar", "arxiv", "local_bib"] = "semantic_scholar"
    bibtex: str = ""


class VisualSpec(BaseModel):
    """Specification for an automated chart, diagram, or overlay visual."""

    visual_id: str
    kind: Literal["bar_chart", "line_chart", "architecture_diagram", "carousel"]
    title: str
    subtitle: str = ""
    data_payload: dict[str, Any] = Field(default_factory=dict)
    caption: str = ""
    target_channels: list[str] = Field(default_factory=lambda: ["linkedin", "x", "youtube"])
    output_path: str = ""


class CarouselSlide(BaseModel):
    """Single slide inside a LinkedIn PDF carousel."""

    title: str
    bullets: list[str] = Field(default_factory=list)
    metric_callout: str = ""
    footer_note: str = ""


class LinkedInDeliverable(BaseModel):
    """Native LinkedIn post + optional carousel slides."""

    language: str = "fr"
    post_text: str
    hashtags: list[str] = Field(default_factory=list)
    carousel_slides: list[CarouselSlide] = Field(default_factory=list)
    attached_visuals: list[str] = Field(default_factory=list)


class XDeliverable(BaseModel):
    """X / Twitter thread + standalone posts + short video hook."""

    language: str = "en"
    thread_tweets: list[str] = Field(default_factory=list)
    standalone_posts: list[str] = Field(default_factory=list)
    video_hook_caption: str = ""
    attached_visuals: list[str] = Field(default_factory=list)


class YouTubeDeliverable(BaseModel):
    """Complete YouTube long-form + Shorts production package."""

    language: str = "fr"
    titles_ctr: list[str] = Field(default_factory=list)
    thumbnail_briefs: list[str] = Field(default_factory=list)
    long_script_markdown: str = ""
    short_60s_script: str = ""
    demo_shotlist_markdown: str = ""
    seo_description: str = ""
    chapters: list[str] = Field(default_factory=list)


class DeterministicLintResult(BaseModel):
    """Result of deterministic Python quality and formatting checks."""

    passed: bool
    violations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)


class ContentExportBundle(BaseModel):
    """Final exported bundle written to disk and downloadable as ZIP."""

    topic: str
    language: str
    channels: list[str]
    created_at: str
    routing_table: dict[str, Any] = Field(default_factory=dict)
    linkedin: LinkedInDeliverable | None = None
    x: XDeliverable | None = None
    youtube: YouTubeDeliverable | None = None
    newsletter_markdown: str = ""
    bibtex: str = ""
    quality_report_markdown: str = ""
    figure_paths: list[str] = Field(default_factory=list)
    video_paths: list[str] = Field(default_factory=list)
    carousel_pdf_path: str = ""
    output_dir: str = ""
