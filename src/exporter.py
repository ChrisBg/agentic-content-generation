"""Structured ready-to-post bundle exporter (Markdown, plain text, BibTeX, PNG, PDF, MP4, ZIP)."""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import DEFAULT_OUTPUT_DIR

SECTION_PATTERNS: dict[str, str] = {
    "linkedin": r"===\s*FINAL LINKEDIN POST\s*===",
    "x_thread": r"===\s*FINAL X THREAD\s*===",
    "x_standalone": r"===\s*FINAL X STANDALONE POSTS\s*===",
    "youtube": r"===\s*FINAL YOUTUBE PACKAGE\s*===",
    "newsletter": r"===\s*FINAL NEWSLETTER\s*===",
    "bibtex": r"===\s*BIBTEX REFERENCES\s*===",
    "media_manifest": r"===\s*GENERATED MEDIA MANIFEST\s*===",
    "quality_report": r"===\s*QUALITY REPORT\s*===",
}


def slugify(text: str, max_len: int = 50) -> str:
    """Create a filesystem-safe slug from a topic string."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return (slug[:max_len].strip("_")) or "content_bundle"


def parse_final_sections(raw_text: str) -> dict[str, str]:
    """Extract named deliverable sections from the refiner agent's output."""
    if not raw_text:
        return {}

    combined = "|".join(f"(?P<{name}>{pat})" for name, pat in SECTION_PATTERNS.items())
    matches = list(re.finditer(combined, raw_text, flags=re.IGNORECASE))
    if not matches:
        return {"raw_output": raw_text.strip()}

    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        name = match.lastgroup
        if not name:
            continue
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_text)
        body = raw_text[start:end].strip()
        if body:
            sections[name] = body
    return sections


def _copy_if_exists(src: Path, dest_dir: Path) -> Path | None:
    if not src.exists() or not src.is_file():
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / src.name
    shutil.copy2(src, target)
    return target


def export_content_bundle(
    topic: str,
    final_content: str,
    channels: list[str],
    language: str = "fr",
    routing_table: dict[str, Any] | None = None,
    tmp_assets_dir: Path | None = None,
    base_output_dir: Path | None = None,
) -> dict[str, Any]:
    """Write a complete, ready-to-post bundle directory under ``output/YYYY-MM-DD_<slug>/``.

    Returns:
        Dictionary containing ``bundle_dir``, ``files``, ``sections``, and ``zip_path``.
    """
    out_root = base_output_dir or DEFAULT_OUTPUT_DIR
    date_prefix = datetime.now().strftime("%Y-%m-%d_%H%M")
    bundle_dir = out_root / f"{date_prefix}_{slugify(topic)}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    sections = parse_final_sections(final_content)
    written_files: dict[str, Any] = {
        "figures": [],
        "videos": [],
        "overlays": [],
    }

    # Always write full raw output as backup
    full_path = bundle_dir / "full_output.md"
    full_path.write_text(final_content, encoding="utf-8")
    written_files["full_output"] = str(full_path)

    # LinkedIn post (plain text ready to copy-paste)
    if "linkedin" in sections:
        p = bundle_dir / "linkedin_post.txt"
        p.write_text(sections["linkedin"] + "\n", encoding="utf-8")
        written_files["linkedin_post"] = str(p)

    # X Thread + Standalone posts
    if "x_thread" in sections or "x_standalone" in sections:
        x_parts: list[str] = []
        if "x_thread" in sections:
            x_parts.append("# X Thread\n\n" + sections["x_thread"])
        if "x_standalone" in sections:
            x_parts.append("# Standalone Posts\n\n" + sections["x_standalone"])
        p = bundle_dir / "x_thread.md"
        p.write_text("\n\n---\n\n".join(x_parts) + "\n", encoding="utf-8")
        written_files["x_thread"] = str(p)

    # YouTube package
    if "youtube" in sections:
        p = bundle_dir / "youtube_package.md"
        p.write_text(sections["youtube"] + "\n", encoding="utf-8")
        written_files["youtube_package"] = str(p)

    # Optional Newsletter
    if "newsletter" in sections:
        p = bundle_dir / "newsletter_draft.md"
        p.write_text(sections["newsletter"] + "\n", encoding="utf-8")
        written_files["newsletter"] = str(p)

    # Verified BibTeX
    if "bibtex" in sections:
        p = bundle_dir / "references.bib"
        p.write_text(sections["bibtex"] + "\n", encoding="utf-8")
        written_files["bibtex"] = str(p)

    # Quality report
    if "quality_report" in sections:
        p = bundle_dir / "quality_report.md"
        p.write_text(sections["quality_report"] + "\n", encoding="utf-8")
        written_files["quality_report"] = str(p)

    # Collect generated visual/video/carousel assets from tmp_assets_dir
    assets_src = tmp_assets_dir or (DEFAULT_OUTPUT_DIR / "tmp_assets")
    if assets_src.exists():
        for file_path in sorted(assets_src.rglob("*")):
            if not file_path.is_file():
                continue
            suffix = file_path.suffix.lower()
            if "overlays" in file_path.parts and suffix == ".png":
                copied = _copy_if_exists(file_path, bundle_dir / "figures" / "overlays")
                if copied:
                    written_files["overlays"].append(str(copied))
            elif suffix in {".png", ".svg", ".mmd"}:
                copied = _copy_if_exists(file_path, bundle_dir / "figures")
                if copied:
                    written_files["figures"].append(str(copied))
            elif suffix == ".pdf":
                copied = _copy_if_exists(file_path, bundle_dir)
                if copied:
                    written_files["linkedin_carousel_pdf"] = str(copied)
            elif suffix in {".mp4", ".srt"}:
                copied = _copy_if_exists(file_path, bundle_dir / "videos")
                if copied:
                    written_files["videos"].append(str(copied))

    # Structured metadata JSON
    metadata = {
        "topic": topic,
        "language": language,
        "channels": channels,
        "created_at": datetime.now().isoformat(),
        "routing_table": routing_table or {},
        "files": written_files,
        "sections_present": list(sections.keys()),
    }
    meta_path = bundle_dir / "bundle.json"
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    written_files["bundle_json"] = str(meta_path)

    zip_path = zip_bundle(bundle_dir)

    return {
        "bundle_dir": str(bundle_dir),
        "zip_path": str(zip_path),
        "files": written_files,
        "sections": sections,
        "metadata": metadata,
    }


def zip_bundle(bundle_dir: Path) -> Path:
    """Create a downloadable ZIP archive of an exported bundle directory."""
    bundle_dir = Path(bundle_dir)
    zip_path = bundle_dir.parent / f"{bundle_dir.name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(bundle_dir.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, arcname=file_path.relative_to(bundle_dir))
    return zip_path
