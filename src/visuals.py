"""PaperOrchestra-inspired visual asset engine (charts, architecture diagrams, LinkedIn carousels, video overlays).

Uses pure Python (Matplotlib + Pillow + fpdf2) with zero browser/Chromium dependencies
so it runs reliably on macOS, Linux, CI, and Hugging Face Spaces.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # Headless backend safe for CLI, Gradio, and pytest

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

from .security import get_safe_asset_root, resolve_safe_path

# Cohesive editorial dark/navy palette
PALETTE = {
    "bg": "#0F172A",
    "card": "#1E293B",
    "border": "#334155",
    "primary": "#38BDF8",
    "accent": "#F97316",
    "success": "#34D399",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
}

DEFAULT_WATERMARK = "Christophe Bourgoin, Ph.D. | AI Engineering & AdTech R&D"


def _ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _sanitize_latin1(text: str) -> str:
    """Replace Unicode characters unsupported by standard built-in PDF Helvetica font."""
    replacements = {
        "—": "-",
        "–": "-",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "€": "EUR",
        "→": "->",
        "←": "<-",
        "×": "x",
        "≤": "<=",
        "≥": ">=",
        "•": "-",
        "…": "...",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "ignore").decode("latin-1")


def render_data_chart(
    title: str,
    labels: list[str],
    values: list[float],
    chart_type: str = "bar",
    subtitle: str = "",
    y_label: str = "",
    source_note: str = "",
    output_path: str = "output/tmp_assets/chart.png",
) -> dict[str, Any]:
    """Generate a high-resolution (300 DPI) editorial chart from verified experimental data.

    Args:
        title: Main insight headline for the chart.
        labels: X-axis category labels (e.g. model names or versions).
        values: Numeric values corresponding to ``labels`` (must come from verified sources).
        chart_type: Either ``"bar"`` (default), ``"barh"``, or ``"line"``.
        subtitle: Optional explanatory subtitle.
        y_label: Optional axis unit/label.
        source_note: Source attribution shown in bottom-left footer.
        output_path: Destination PNG file path.

    Returns:
        Dictionary with status and saved file path.
    """
    if not labels or not values or len(labels) != len(values):
        return {
            "status": "error",
            "error_message": "labels and values must be non-empty lists of equal length.",
        }

    try:
        out = _ensure_parent(resolve_safe_path(output_path, get_safe_asset_root()))
    except (PermissionError, ValueError) as exc:
        return {"status": "error", "error_message": str(exc)}
    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=220)
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["card"])

    numeric_vals = [float(v) for v in values]
    colors = [
        PALETTE["accent"] if i == len(numeric_vals) - 1 else PALETTE["primary"]
        for i in range(len(numeric_vals))
    ]

    if chart_type == "barh":
        bars = ax.barh(labels, numeric_vals, color=colors, height=0.58, edgecolor="none")
        ax.invert_yaxis()
        ax.set_xlabel(y_label, color=PALETTE["muted"], fontsize=11, labelpad=8)
        for bar, val in zip(bars, numeric_vals, strict=True):
            ax.text(
                val + (max(numeric_vals) * 0.02 if max(numeric_vals) else 0.1),
                bar.get_y() + bar.get_height() / 2,
                f"{val:g}",
                va="center",
                ha="left",
                color=PALETTE["text"],
                fontsize=11,
                fontweight="bold",
            )
    elif chart_type == "line":
        ax.plot(
            labels,
            numeric_vals,
            color=PALETTE["primary"],
            linewidth=3,
            marker="o",
            markersize=8,
            markerfacecolor=PALETTE["accent"],
            markeredgecolor=PALETTE["text"],
        )
        ax.set_ylabel(y_label, color=PALETTE["muted"], fontsize=11, labelpad=8)
        for x_i, val in enumerate(numeric_vals):
            ax.annotate(
                f"{val:g}",
                (x_i, val),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                color=PALETTE["text"],
                fontsize=10,
                fontweight="bold",
            )
    else:
        bars = ax.bar(labels, numeric_vals, color=colors, width=0.55, edgecolor="none")
        ax.set_ylabel(y_label, color=PALETTE["muted"], fontsize=11, labelpad=8)
        for bar, val in zip(bars, numeric_vals, strict=True):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + (max(numeric_vals) * 0.02 if max(numeric_vals) else 0.1),
                f"{val:g}",
                ha="center",
                va="bottom",
                color=PALETTE["text"],
                fontsize=11,
                fontweight="bold",
            )

    ax.tick_params(colors=PALETTE["text"], labelsize=10)
    ax.grid(
        axis="x" if chart_type == "barh" else "y",
        color=PALETTE["border"],
        alpha=0.55,
        linestyle="--",
    )
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["bottom", "left"]:
        ax.spines[spine].set_color(PALETTE["border"])

    fig.suptitle(
        title, color=PALETTE["text"], fontsize=15, fontweight="bold", x=0.06, y=0.95, ha="left"
    )
    if subtitle:
        fig.text(0.06, 0.89, subtitle, color=PALETTE["muted"], fontsize=10.5, ha="left")

    footer_left = f"Source: {source_note}" if source_note else ""
    fig.text(0.06, 0.025, footer_left, color=PALETTE["muted"], fontsize=8.5, ha="left")
    fig.text(0.95, 0.025, DEFAULT_WATERMARK, color=PALETTE["muted"], fontsize=8.5, ha="right")

    plt.tight_layout(rect=[0.04, 0.06, 0.97, 0.86])
    fig.savefig(out, facecolor=PALETTE["bg"], dpi=220)
    plt.close(fig)

    return {"status": "success", "path": str(out), "chart_type": chart_type}


def render_architecture_diagram(
    title: str,
    nodes: list[str],
    subtitle: str = "",
    output_path: str = "output/tmp_assets/architecture.png",
) -> dict[str, Any]:
    """Generate a clean horizontal/grid architecture diagram PNG + Mermaid source (.mmd).

    Args:
        title: Diagram title.
        nodes: Ordered list of pipeline/system components (2 to 8 items).
        subtitle: Optional subtitle describing the flow.
        output_path: Destination PNG path (a matching ``.mmd`` file is also saved).

    Returns:
        Dictionary with status, png_path, and mermaid_path.
    """
    if not nodes or len(nodes) < 2:
        return {"status": "error", "error_message": "Provide at least 2 nodes for a diagram."}

    nodes = nodes[:8]
    try:
        out = _ensure_parent(resolve_safe_path(output_path, get_safe_asset_root()))
    except (PermissionError, ValueError) as exc:
        return {"status": "error", "error_message": str(exc)}
    mmd_path = out.with_suffix(".mmd")

    # Save Mermaid definition
    mmd_lines = ["flowchart LR"]
    for idx, label in enumerate(nodes):
        safe = label.replace('"', "'")
        mmd_lines.append(f'    N{idx}["{safe}"]')
    for idx in range(len(nodes) - 1):
        mmd_lines.append(f"    N{idx} --> N{idx + 1}")
    mmd_path.write_text("\n".join(mmd_lines) + "\n", encoding="utf-8")

    # Render clean visual boxes via Matplotlib
    cols = min(len(nodes), 4)
    rows = 1 if len(nodes) <= 4 else 2
    fig, ax = plt.subplots(figsize=(12, 4.4 if rows == 1 else 6.4), dpi=220)
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
    ax.set_xlim(0, cols * 3.0)
    ax.set_ylim(0, rows * 2.6 + 0.8)
    ax.axis("off")

    positions: list[tuple[float, float]] = []
    box_w, box_h = 2.25, 1.35
    for idx, label in enumerate(nodes):
        row = idx // 4
        col = idx % 4
        cx = col * 3.0 + 1.5
        cy = (rows - 1 - row) * 2.5 + 1.35
        positions.append((cx, cy))

        border_col = PALETTE["accent"] if idx in {0, len(nodes) - 1} else PALETTE["primary"]
        rect = patches.FancyBboxPatch(
            (cx - box_w / 2, cy - box_h / 2),
            box_w,
            box_h,
            boxstyle="round,pad=0.12,rounding_size=0.18",
            linewidth=2.2,
            edgecolor=border_col,
            facecolor=PALETTE["card"],
        )
        ax.add_patch(rect)

        step_badge = f"0{idx + 1}"
        ax.text(
            cx - box_w / 2 + 0.14,
            cy + box_h / 2 - 0.16,
            step_badge,
            color=border_col,
            fontsize=9,
            fontweight="bold",
            ha="left",
            va="top",
        )
        wrapped = "\n".join(textwrap.wrap(label, width=20))
        ax.text(
            cx,
            cy - 0.05,
            wrapped,
            color=PALETTE["text"],
            fontsize=10.5,
            fontweight="bold",
            ha="center",
            va="center",
        )

    # Draw arrows between consecutive nodes
    for idx in range(len(positions) - 1):
        x1, y1 = positions[idx]
        x2, y2 = positions[idx + 1]
        if abs(y1 - y2) < 0.1:
            ax.annotate(
                "",
                xy=(x2 - box_w / 2 - 0.14, y2),
                xytext=(x1 + box_w / 2 + 0.14, y1),
                arrowprops={"arrowstyle": "->", "color": PALETTE["muted"], "lw": 2.2},
            )
        else:
            ax.annotate(
                "",
                xy=(x2, y2 + box_h / 2 + 0.14),
                xytext=(x1, y1 - box_h / 2 - 0.14),
                arrowprops={
                    "arrowstyle": "->",
                    "color": PALETTE["muted"],
                    "lw": 2.0,
                    "connectionstyle": "arc3,rad=-0.15",
                },
            )

    fig.suptitle(
        title, color=PALETTE["text"], fontsize=15, fontweight="bold", x=0.04, y=0.95, ha="left"
    )
    if subtitle:
        fig.text(0.04, 0.87, subtitle, color=PALETTE["muted"], fontsize=10.5, ha="left")
    fig.text(0.96, 0.03, DEFAULT_WATERMARK, color=PALETTE["muted"], fontsize=8.5, ha="right")

    fig.savefig(out, facecolor=PALETTE["bg"], dpi=220, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)

    return {"status": "success", "png_path": str(out), "mermaid_path": str(mmd_path)}


def render_linkedin_carousel_pdf(
    slides: list[dict[str, Any]],
    output_path: str = "output/tmp_assets/linkedin_carousel.pdf",
    author_line: str = DEFAULT_WATERMARK,
    chart_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a ready-to-upload LinkedIn portrait PDF carousel (4:5 aspect ratio).

    Args:
        slides: List of slide dicts with ``title``, ``bullets`` (list[str]), optional
            ``metric_callout`` and ``footer_note``.
        output_path: Destination ``.pdf`` path.
        author_line: Brand footer shown on each slide.
        chart_paths: Optional PNG chart paths embedded on middle/data slides.

    Returns:
        Dictionary with status, path, and slide_count.
    """
    if not slides:
        return {"status": "error", "error_message": "At least one slide is required."}

    asset_root = get_safe_asset_root()
    try:
        out = _ensure_parent(resolve_safe_path(output_path, asset_root))
    except (PermissionError, ValueError) as exc:
        return {"status": "error", "error_message": str(exc)}

    valid_charts: list[Path] = []
    for raw_chart in chart_paths or []:
        try:
            safe_chart = resolve_safe_path(raw_chart, asset_root, must_exist=True)
            valid_charts.append(safe_chart)
        except (PermissionError, ValueError, FileNotFoundError):
            continue

    # Portrait 4:5 (108mm x 135mm matches 1080x1350 LinkedIn document standard)
    pdf = FPDF(orientation="P", unit="mm", format=(108, 135))
    pdf.set_auto_page_break(auto=False)

    total = len(slides)
    for idx, slide in enumerate(slides, start=1):
        pdf.add_page()
        # Dark navy canvas
        pdf.set_fill_color(15, 23, 42)
        pdf.rect(0, 0, 108, 135, style="F")

        # Top accent stripe
        if idx == 1 or idx == total:
            pdf.set_fill_color(249, 115, 22)
        else:
            pdf.set_fill_color(56, 189, 248)
        pdf.rect(0, 0, 108, 2.5, style="F")

        # Slide counter pill
        pdf.set_xy(8, 8)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(92, 5, f"{idx:02d} / {total:02d}", align="R")

        # Slide Title
        title_txt = _sanitize_latin1(str(slide.get("title", f"Slide {idx}")))
        pdf.set_xy(8, 16 if idx > 1 else 26)
        pdf.set_font("Helvetica", "B", 16 if idx == 1 else 13.5)
        pdf.set_text_color(248, 250, 252)
        pdf.multi_cell(92, 7.5 if idx == 1 else 6.5, title_txt)

        cur_y = pdf.get_y() + 4

        # Metric callout card if present
        metric = _sanitize_latin1(str(slide.get("metric_callout", "")).strip())
        if metric:
            pdf.set_fill_color(30, 41, 59)
            pdf.set_draw_color(56, 189, 248)
            pdf.rect(8, cur_y, 92, 14, style="DF")
            pdf.set_xy(11, cur_y + 3.5)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(56, 189, 248)
            pdf.multi_cell(86, 5.5, metric)
            cur_y += 18

        # Bullet points
        bullets = slide.get("bullets", [])
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(226, 232, 240)
        for bullet in bullets[:5]:
            b_txt = _sanitize_latin1(str(bullet).strip())
            if not b_txt:
                continue
            pdf.set_xy(10, cur_y)
            pdf.multi_cell(88, 5.5, f"- {b_txt}")
            cur_y = pdf.get_y() + 2.5
            if cur_y > 112:
                break

        # Embed one chart on slide 2 or 3 if space allows
        chart_idx = idx - 2
        if 0 <= chart_idx < len(valid_charts) and cur_y < 82:
            avail_h = min(44, 118 - cur_y)
            pdf.image(str(valid_charts[chart_idx]), x=8, y=cur_y + 2, w=92, h=avail_h)

        # Footer divider + watermark
        pdf.set_draw_color(51, 65, 85)
        pdf.line(8, 123, 100, 123)
        pdf.set_xy(8, 125)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(148, 163, 184)
        footer = _sanitize_latin1(str(slide.get("footer_note") or author_line))
        pdf.cell(92, 5, footer, align="L")

    pdf.output(str(out))
    return {"status": "success", "path": str(out), "slide_count": total}


def render_demo_overlays(
    cues: list[dict[str, str]],
    output_dir: str = "output/tmp_assets/overlays",
) -> dict[str, Any]:
    """Render transparent RGBA PNG lower-third overlays for live screen-recorded demos.

    Args:
        cues: List of dicts with ``label`` (short headline) and ``detail`` (metric/subtitle).
        output_dir: Directory where overlay PNG files will be written.

    Returns:
        Dictionary with status and list of generated overlay paths.
    """
    if not cues:
        return {"status": "error", "error_message": "At least one overlay cue is required."}

    try:
        out_dir = resolve_safe_path(output_dir, get_safe_asset_root())
    except (PermissionError, ValueError) as exc:
        return {"status": "error", "error_message": str(exc)}
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []

    font_lg = ImageFont.load_default()
    font_sm = ImageFont.load_default()

    for idx, cue in enumerate(cues[:8], start=1):
        img = Image.new("RGBA", (1280, 200), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Semi-transparent dark lower-third pill
        draw.rounded_rectangle(
            [(40, 30), (920, 165)],
            radius=18,
            fill=(15, 23, 42, 225),
            outline=(56, 189, 248, 255),
            width=3,
        )
        draw.rectangle([(40, 30), (54, 165)], fill=(249, 115, 22, 255))

        headline = str(cue.get("label", f"Step {idx}"))[:70]
        detail = str(cue.get("detail", ""))[:110]
        draw.text((76, 54), headline, fill=(248, 250, 252, 255), font=font_lg)
        if detail:
            draw.text((76, 102), detail, fill=(148, 163, 184, 255), font=font_sm)

        out_file = out_dir / f"overlay_{idx:02d}.png"
        img.save(out_file)
        paths.append(str(out_file))

    return {"status": "success", "paths": paths, "count": len(paths)}
