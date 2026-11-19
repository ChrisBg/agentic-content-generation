"""PaperOrchestra-compatible raw material ingestion bridge.

Ingests unstructured pre-writing materials — LaTeX manuscripts (.tex), BibTeX (.bib),
Jupyter notebooks (.ipynb), PDF papers (.pdf), benchmark logs (.json, .csv), and
markdown/text notes — into a structured ``RawMaterialBundle`` so agents ground
every post, chart, and video demo in real experimental evidence.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from .schemas import ExtractedMetric, ExtractedTable, RawMaterialBundle

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None  # type: ignore[assignment]


SUPPORTED_EXTENSIONS = {
    ".tex",
    ".bib",
    ".ipynb",
    ".pdf",
    ".json",
    ".csv",
    ".md",
    ".txt",
    ".log",
}


def _strip_latex_commands(text: str) -> str:
    """Clean common LaTeX markup while keeping readable text and numbers."""
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\\(textbf|textit|emph|texttt|cite|citep|citet|ref)\{([^}]*)\}", r"\2", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", text).strip()


def parse_latex_file(path: Path) -> dict[str, Any]:
    """Extract title, abstract, sections, and tabular data from a LaTeX manuscript."""
    raw = path.read_text(encoding="utf-8", errors="ignore")

    title_match = re.search(r"\\title\{([^}]+)\}", raw, flags=re.DOTALL)
    title = _strip_latex_commands(title_match.group(1)) if title_match else ""

    abstract_match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", raw, flags=re.DOTALL)
    abstract = _strip_latex_commands(abstract_match.group(1)) if abstract_match else ""

    # Extract sections
    sections: dict[str, str] = {}
    sec_matches = list(re.finditer(r"\\section\*?\{([^}]+)\}", raw))
    for i, match in enumerate(sec_matches):
        sec_title = _strip_latex_commands(match.group(1))
        start = match.end()
        end = sec_matches[i + 1].start() if i + 1 < len(sec_matches) else len(raw)
        body = _strip_latex_commands(raw[start:end])
        if body:
            sections[sec_title] = body[:2500]

    # Extract tabular blocks
    tables: list[ExtractedTable] = []
    tabular_matches = re.finditer(
        r"\\begin\{tabular\}\{[^}]*\}(.*?)\\end\{tabular\}", raw, flags=re.DOTALL
    )
    for idx, tmatch in enumerate(tabular_matches, start=1):
        t_body = tmatch.group(1)
        raw_rows = [r.strip() for r in t_body.split("\\\\") if "&" in r]
        parsed_rows: list[list[str]] = []
        for r in raw_rows:
            cleaned = re.sub(r"\\(toprule|midrule|bottomrule|hline|cline\{[^}]*\})", "", r)
            cells = [_strip_latex_commands(c) for c in cleaned.split("&")]
            if any(cells):
                parsed_rows.append(cells)
        if parsed_rows:
            headers = parsed_rows[0]
            rows = parsed_rows[1:] if len(parsed_rows) > 1 else []
            tables.append(
                ExtractedTable(
                    title=f"LaTeX Table {idx}",
                    headers=headers,
                    rows=rows,
                    source_file=path.name,
                )
            )

    return {
        "title": title,
        "abstract": abstract,
        "sections": sections,
        "tables": tables,
    }


def parse_bibtex_file(path: Path) -> list[str]:
    """Extract individual BibTeX entries from a .bib file."""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    entries = re.findall(r"@\w+\s*\{[^@]+", raw, flags=re.DOTALL)
    return [e.strip() for e in entries if e.strip()]


def parse_notebook_file(path: Path) -> dict[str, Any]:
    """Extract markdown cells, key code cells, and text outputs from a Jupyter notebook."""
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    notes: list[str] = []
    code_snippets: list[str] = []
    metrics: list[ExtractedMetric] = []

    for cell in data.get("cells", []):
        cell_type = cell.get("cell_type")
        source = "".join(cell.get("source", [])).strip()
        if not source:
            continue

        if cell_type == "markdown":
            notes.append(source)
        elif cell_type == "code":
            if len(code_snippets) < 5:
                code_snippets.append(source[:800])
            # Inspect lightweight text outputs for printed metrics (e.g. "accuracy: 0.94")
            for output in cell.get("outputs", []):
                text_chunks: list[str] = []
                if "text" in output:
                    text_chunks.append("".join(output["text"]))
                elif "data" in output and "text/plain" in output["data"]:
                    text_chunks.append("".join(output["data"]["text/plain"]))
                combined = "\n".join(text_chunks)
                for line in combined.splitlines():
                    m = re.match(
                        r"^\s*([A-Za-z0-9_\-\s/%€$]{2,40})\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*([%€$a-zA-Z/]*)\s*$",
                        line,
                    )
                    if m:
                        metrics.append(
                            ExtractedMetric(
                                name=m.group(1).strip(),
                                value=float(m.group(2)),
                                unit=m.group(3).strip(),
                                source_file=path.name,
                            )
                        )
                if combined.strip():
                    notes.append(f"[Notebook output from {path.name}]\n{combined[:800]}")

    return {"notes": notes, "code_snippets": code_snippets, "metrics": metrics}


def parse_json_metrics_file(path: Path) -> dict[str, Any]:
    """Extract flat or nested benchmark metrics and comparison tables from JSON logs."""
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    metrics: list[ExtractedMetric] = []
    tables: list[ExtractedTable] = []
    notes: list[str] = []

    def _walk(obj: Any, prefix: str = "") -> None:
        if isinstance(obj, dict):
            # Detect structured comparison table: list of dicts under a key
            for k, v in obj.items():
                key_name = f"{prefix}.{k}" if prefix else str(k)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    metrics.append(ExtractedMetric(name=key_name, value=v, source_file=path.name))
                elif isinstance(v, list) and v and all(isinstance(item, dict) for item in v):
                    headers = list(v[0].keys())
                    rows = [[str(item.get(h, "")) for h in headers] for item in v]
                    tables.append(
                        ExtractedTable(
                            title=key_name,
                            headers=headers,
                            rows=rows,
                            source_file=path.name,
                        )
                    )
                elif isinstance(v, dict):
                    _walk(v, key_name)
                elif isinstance(v, str) and len(v) > 20:
                    notes.append(f"{key_name}: {v[:500]}")
        elif isinstance(obj, list) and obj and all(isinstance(item, dict) for item in obj):
            headers = list(obj[0].keys())
            rows = [[str(item.get(h, "")) for h in headers] for item in obj]
            tables.append(
                ExtractedTable(
                    title=path.stem,
                    headers=headers,
                    rows=rows,
                    source_file=path.name,
                )
            )

    _walk(data)
    return {"metrics": metrics, "tables": tables, "notes": notes}


def parse_csv_file(path: Path) -> ExtractedTable | None:
    """Extract headers and rows from a CSV benchmark file."""
    with open(path, encoding="utf-8", errors="ignore", newline="") as f:
        reader = list(csv.reader(f))
    if not reader:
        return None
    headers = [h.strip() for h in reader[0]]
    rows = [[cell.strip() for cell in row] for row in reader[1:51] if any(row)]
    return ExtractedTable(
        title=path.stem,
        headers=headers,
        rows=rows,
        source_file=path.name,
    )


def parse_pdf_file(path: Path, max_pages: int = 12) -> str:
    """Extract text from a PDF paper or report."""
    if PdfReader is None:
        return f"[PDF skipped: pypdf not installed for {path.name}]"
    reader = PdfReader(str(path))
    chunks: list[str] = []
    for page in reader.pages[:max_pages]:
        text = page.extract_text() or ""
        if text.strip():
            chunks.append(text.strip())
    return "\n\n".join(chunks)[:10000]


def discover_material_files(paths: list[Path]) -> list[Path]:
    """Expand files and directories into a deduplicated list of supported raw material files."""
    discovered: list[Path] = []
    seen: set[Path] = set()
    for p in paths:
        if not p.exists():
            continue
        candidates = sorted(p.rglob("*")) if p.is_dir() else [p]
        for candidate in candidates:
            if (
                candidate.is_file()
                and candidate.suffix.lower() in SUPPORTED_EXTENSIONS
                and not any(part.startswith(".") for part in candidate.parts)
            ):
                resolved = candidate.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    discovered.append(candidate)
    return discovered


def ingest_materials(
    input_paths: list[Path] | None = None,
    topic: str = "",
    human_seed: str = "",
) -> RawMaterialBundle:
    """Ingest raw materials (PaperOrchestra manuscripts, logs, notebooks, PDFs, notes).

    Args:
        input_paths: List of files or directories to ingest.
        topic: Main topic or research subject.
        human_seed: Author's personal angle, bullet points, or contrarian take.

    Returns:
        Structured ``RawMaterialBundle`` ready to feed into ``OutlineBlueprintAgent``.
    """
    files = discover_material_files(input_paths or [])
    bundle = RawMaterialBundle(
        topic=topic.strip() or "Untitled Research Topic",
        human_seed=human_seed.strip(),
        ingested_files=[f.name for f in files],
    )

    for file_path in files:
        suffix = file_path.suffix.lower()
        try:
            if suffix == ".tex":
                parsed = parse_latex_file(file_path)
                if parsed["title"] and not bundle.latex_title:
                    bundle.latex_title = parsed["title"]
                if parsed["abstract"] and not bundle.latex_abstract:
                    bundle.latex_abstract = parsed["abstract"]
                bundle.sections.update(parsed["sections"])
                bundle.tables.extend(parsed["tables"])
            elif suffix == ".bib":
                bundle.bibtex_entries.extend(parse_bibtex_file(file_path))
            elif suffix == ".ipynb":
                parsed = parse_notebook_file(file_path)
                bundle.notes.extend(parsed["notes"])
                bundle.code_snippets.extend(parsed["code_snippets"])
                bundle.metrics.extend(parsed["metrics"])
            elif suffix == ".json":
                parsed = parse_json_metrics_file(file_path)
                bundle.metrics.extend(parsed["metrics"])
                bundle.tables.extend(parsed["tables"])
                bundle.notes.extend(parsed["notes"])
            elif suffix == ".csv":
                table = parse_csv_file(file_path)
                if table:
                    bundle.tables.append(table)
            elif suffix == ".pdf":
                text = parse_pdf_file(file_path)
                if text:
                    bundle.notes.append(f"[PDF: {file_path.name}]\n{text[:4000]}")
            elif suffix in {".md", ".txt", ".log"}:
                text = file_path.read_text(encoding="utf-8", errors="ignore").strip()
                if text:
                    bundle.notes.append(f"[{file_path.name}]\n{text[:3000]}")
        except Exception as exc:
            bundle.notes.append(f"[Warning: failed to parse {file_path.name}: {exc}]")

    # Infer topic from LaTeX title if user didn't pass an explicit topic
    if bundle.topic == "Untitled Research Topic" and bundle.latex_title:
        bundle.topic = bundle.latex_title

    return bundle
