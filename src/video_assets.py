"""Short demo & explainer video engine (MP4 16:9 for X/YouTube + 9:16 for Shorts/LinkedIn).

Uses Pillow/Matplotlib slide frames + local FFmpeg to generate crisp, anti-AI-slop
animated data/architecture videos with synchronized .srt subtitles and a live demo
screen-recording shotlist.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from .security import get_safe_asset_root, resolve_safe_path
from .visuals import DEFAULT_WATERMARK

logger = logging.getLogger(__name__)
FFMPEG_TIMEOUT_SECONDS = 120

ASPECT_DIMENSIONS: dict[str, tuple[int, int]] = {
    "16:9": (1280, 720),
    "9:16": (1080, 1920),
}


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a crisp system TrueType font on macOS/Linux, falling back to Pillow default."""
    candidates = (
        [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _format_srt_timestamp(seconds: float) -> str:
    ms = int(round((seconds - int(seconds)) * 1000))
    total_sec = int(seconds)
    hrs = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"


def _render_video_scene_frame(
    scene: dict[str, Any],
    scene_index: int,
    total_scenes: int,
    size: tuple[int, int],
    output_path: Path,
) -> Path:
    """Render a single clean editorial video card (16:9 or 9:16) with optional embedded figure."""
    width, height = size
    is_vertical = height > width
    img = Image.new("RGB", (width, height), (15, 23, 42))
    draw = ImageDraw.Draw(img)

    # Top accent bar
    accent_rgb = (249, 115, 22) if scene_index in {1, total_scenes} else (56, 189, 248)
    draw.rectangle([(0, 0), (width, 10)], fill=accent_rgb)

    margin = int(width * 0.07)
    content_w = width - 2 * margin

    title_font = _load_font(54 if is_vertical else 44, bold=True)
    body_font = _load_font(34 if is_vertical else 26, bold=False)
    metric_font = _load_font(42 if is_vertical else 34, bold=True)
    meta_font = _load_font(22 if is_vertical else 18, bold=False)

    # Progress badge
    draw.text(
        (margin, int(height * 0.045)),
        f"STEP {scene_index:02d}/{total_scenes:02d}",
        fill=accent_rgb,
        font=meta_font,
    )

    # Scene title
    title = str(scene.get("title", f"Scene {scene_index}")).strip()
    wrap_chars = 24 if is_vertical else 38
    wrapped_title = textwrap.wrap(title, width=wrap_chars)
    cur_y = int(height * 0.10)
    for line in wrapped_title[:3]:
        draw.text((margin, cur_y), line, fill=(248, 250, 252), font=title_font)
        cur_y += 66 if is_vertical else 54

    cur_y += 18

    # Optional metric badge
    metric = str(scene.get("metric", "")).strip()
    if metric:
        box_h = 90 if is_vertical else 72
        draw.rounded_rectangle(
            [(margin, cur_y), (margin + content_w, cur_y + box_h)],
            radius=16,
            fill=(30, 41, 59),
            outline=(56, 189, 248),
            width=3,
        )
        draw.text((margin + 24, cur_y + 18), metric[:52], fill=(56, 189, 248), font=metric_font)
        cur_y += box_h + 26

    # Optional embedded figure/chart PNG (strictly confined inside SAFE_ASSET_ROOT)
    fig_path_str = str(scene.get("image_path", "")).strip()
    if fig_path_str:
        try:
            safe_fig = resolve_safe_path(fig_path_str, get_safe_asset_root(), must_exist=True)
            fig_img = Image.open(safe_fig).convert("RGB")
            max_fig_h = int(height * (0.42 if is_vertical else 0.48))
            fig_img.thumbnail((content_w, max_fig_h), Image.Resampling.LANCZOS)
            fx = margin + (content_w - fig_img.width) // 2
            img.paste(fig_img, (fx, cur_y))
            cur_y += fig_img.height + 24
        except Exception as exc:
            logger.warning("Skipped unsafe or unreadable video figure '%s': %s", fig_path_str, exc)

    # Caption / Narration text
    narration = str(scene.get("narration") or scene.get("caption") or "").strip()
    if narration:
        narr_wrap = textwrap.wrap(narration, width=36 if is_vertical else 62)
        for line in narr_wrap[:5]:
            if cur_y > height - 120:
                break
            draw.text((margin, cur_y), line, fill=(203, 213, 225), font=body_font)
            cur_y += 46 if is_vertical else 36

    # Footer watermark
    draw.line([(margin, height - 76), (width - margin, height - 76)], fill=(51, 65, 85), width=2)
    draw.text((margin, height - 56), DEFAULT_WATERMARK, fill=(148, 163, 184), font=meta_font)

    img.save(output_path)
    return output_path


def render_short_explainer_video(
    storyboard: list[dict[str, Any]],
    output_path: str = "output/tmp_assets/demo_explainer_16x9.mp4",
    aspect_ratio: str = "16:9",
    audio_path: str | None = None,
) -> dict[str, Any]:
    """Assemble a crisp 30-60s MP4 explainer video + synchronized .srt subtitles via FFmpeg.

    Args:
        storyboard: Ordered list of scene dicts with keys:
            - ``title`` (str): Scene headline
            - ``narration`` (str): Caption / subtitle / spoken line
            - ``duration_sec`` (float, optional): Scene duration (default 5.0s)
            - ``metric`` (str, optional): Highlighted metric badge
            - ``image_path`` (str, optional): Path to PNG chart or architecture diagram
        output_path: Destination ``.mp4`` file path.
        aspect_ratio: ``"16:9"`` (X / YouTube) or ``"9:16"`` (YouTube Shorts / LinkedIn mobile).
        audio_path: Optional path to narration audio (.mp3/.wav) to mux into the video.

    Returns:
        Dictionary with status, video_path, srt_path, duration_sec, and aspect_ratio.
    """
    if not storyboard:
        return {"status": "error", "error_message": "Storyboard must contain at least one scene."}

    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return {
            "status": "error",
            "error_message": "FFmpeg is not installed on PATH. Install with `brew install ffmpeg`.",
        }

    asset_root = get_safe_asset_root()
    try:
        out_mp4 = resolve_safe_path(output_path, asset_root)
    except (PermissionError, ValueError) as exc:
        return {"status": "error", "error_message": str(exc)}

    safe_audio: Path | None = None
    if audio_path:
        try:
            safe_audio = resolve_safe_path(audio_path, asset_root, must_exist=True)
        except (PermissionError, ValueError, FileNotFoundError) as exc:
            return {"status": "error", "error_message": str(exc)}

    size = ASPECT_DIMENSIONS.get(aspect_ratio, ASPECT_DIMENSIONS["16:9"])
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    out_srt = out_mp4.with_suffix(".srt")

    srt_blocks: list[str] = []
    elapsed = 0.0

    with tempfile.TemporaryDirectory(prefix="video_build_") as tmp:
        tmp_dir = Path(tmp)
        concat_lines: list[str] = []
        total = len(storyboard)

        for idx, scene in enumerate(storyboard, start=1):
            duration = max(2.0, min(float(scene.get("duration_sec", 5.0)), 15.0))
            frame_path = tmp_dir / f"scene_{idx:02d}.png"
            _render_video_scene_frame(scene, idx, total, size, frame_path)

            concat_lines.append(f"file '{frame_path.as_posix()}'")
            concat_lines.append(f"duration {duration:.2f}")

            caption = str(scene.get("narration") or scene.get("title") or "").strip()
            srt_blocks.append(
                f"{idx}\n"
                f"{_format_srt_timestamp(elapsed)} --> {_format_srt_timestamp(elapsed + duration)}\n"
                f"{caption}\n"
            )
            elapsed += duration

        # FFmpeg concat demuxer requires repeating the last frame file
        last_frame = tmp_dir / f"scene_{total:02d}.png"
        concat_lines.append(f"file '{last_frame.as_posix()}'")

        concat_file = tmp_dir / "concat.txt"
        concat_file.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
        out_srt.write_text("\n".join(srt_blocks), encoding="utf-8")

        cmd = [
            ffmpeg_bin,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
        ]
        if safe_audio is not None:
            cmd.extend(["-i", str(safe_audio), "-c:a", "aac", "-shortest"])

        cmd.extend(
            [
                "-vf",
                "fps=30,format=yuv420p",
                "-c:v",
                "libx264",
                "-movflags",
                "+faststart",
                str(out_mp4),
            ]
        )

        try:
            proc = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=FFMPEG_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error_message": f"FFmpeg timed out after {FFMPEG_TIMEOUT_SECONDS}s.",
            }
        if proc.returncode != 0:
            return {
                "status": "error",
                "error_message": f"FFmpeg failed ({proc.returncode}): {proc.stderr[-400:]}",
            }

    return {
        "status": "success",
        "video_path": str(out_mp4),
        "srt_path": str(out_srt),
        "duration_sec": round(elapsed, 2),
        "aspect_ratio": aspect_ratio,
        "scenes": len(storyboard),
    }


def generate_demo_shotlist(
    topic: str,
    steps: list[str],
    metrics: list[str] | None = None,
    language: str = "fr",
) -> dict[str, Any]:
    """Generate a second-by-second Live Demo recording runbook (for Screen Studio / OBS).

    Designed for real 45-60s developer/AI demos on X and YouTube Shorts ("Show, don't tell").
    """
    is_fr = language.lower().startswith("fr")
    header = (
        f"# Kit Live Demo (60s) — {topic}\n\n"
        if is_fr
        else f"# Live Demo Runbook (60s) — {topic}\n\n"
    )
    metric_line = (
        ", ".join(metrics[:3])
        if metrics
        else ("résultat chiffré clé" if is_fr else "key verified metric")
    )

    lines = [
        header,
        "| Timecode | Plan / Écran à montrer | Action & Overlay | Objectif |"
        if is_fr
        else "| Timecode | Screen / Visual | Action & Overlay | Goal |",
        "| :--- | :--- | :--- | :--- |",
        f"| `00:00 - 00:05` | Résultat final ou graphe d'impact | Overlay #1 (`{metric_line}`) | Hook immédiat (Show, don't tell) |"
        if is_fr
        else f"| `00:00 - 00:05` | Final result or benchmark chart | Overlay #1 (`{metric_line}`) | Immediate visual hook |",
    ]

    sec = 5
    step_span = max(8, 40 // max(1, len(steps)))
    for idx, step in enumerate(steps[:5], start=1):
        end_sec = min(50, sec + step_span)
        lines.append(
            f"| `00:{sec:02d} - 00:{end_sec:02d}` | Démo live étape {idx} | {step} (Overlay #{idx + 1}) | Preuve technique concrète |"
            if is_fr
            else f"| `00:{sec:02d} - 00:{end_sec:02d}` | Live demo step {idx} | {step} (Overlay #{idx + 1}) | Concrete engineering proof |"
        )
        sec = end_sec

    lines.append(
        "| `00:50 - 01:00` | Schéma d'architecture + lien repo/papier | CTA sobre (commentaire / DM / GitHub) | Conversion B2B / abonnés |"
        if is_fr
        else "| `00:50 - 01:00` | Architecture diagram + repo/paper link | Subtle CTA (comment / DM / GitHub) | Audience & B2B conversion |"
    )

    markdown = "\n".join(lines) + "\n"
    return {"status": "success", "shotlist_markdown": markdown}
