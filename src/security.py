"""Centralized security helpers for path sandboxing and untrusted input hardening."""

from __future__ import annotations

from pathlib import Path

from .config import DEFAULT_OUTPUT_DIR, PROJECT_ROOT

# Dedicated sandbox roots for LLM-invoked tools and human bundle exports
SAFE_OUTPUT_ROOT = DEFAULT_OUTPUT_DIR.resolve()
SAFE_ASSET_ROOT = (DEFAULT_OUTPUT_DIR / "tmp_assets").resolve()


def resolve_safe_path(
    user_path: str | Path,
    allowed_root: Path | None = None,
    *,
    must_exist: bool = False,
) -> Path:
    """Resolve ``user_path`` and verify it stays strictly within ``allowed_root``.

    Prevents path traversal (``..``), absolute path escapes, and symlink escapes
    when paths originate from LLM tool calls or UI inputs.

    Args:
        user_path: Target path (relative to ``allowed_root`` or ``PROJECT_ROOT``).
        allowed_root: Root directory boundary (defaults to ``SAFE_ASSET_ROOT``).
        must_exist: If True, raises ``FileNotFoundError`` when the resolved path does not exist.

    Returns:
        Resolved ``Path`` guaranteed to be inside ``allowed_root``.

    Raises:
        PermissionError: If the resolved path escapes ``allowed_root``.
        ValueError: If ``user_path`` is empty or contains null bytes.
    """
    raw = str(user_path).strip()
    if not raw or "\x00" in raw:
        raise ValueError("Invalid or empty file path.")

    root = (allowed_root or SAFE_ASSET_ROOT).resolve()
    candidate = Path(raw)

    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        # Support both bare filenames ("chart.png") and project-relative ("output/tmp_assets/chart.png")
        proj_candidate = (PROJECT_ROOT / candidate).resolve()
        if proj_candidate.is_relative_to(root):
            resolved = proj_candidate
        else:
            resolved = (root / candidate).resolve()

    if not resolved.is_relative_to(root):
        raise PermissionError(
            f"SecurityError: Path '{user_path}' escapes allowed directory '{root}'."
        )

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"File not found inside allowed root: {resolved}")

    return resolved


def get_safe_asset_root() -> Path:
    """Return the active LLM asset sandbox root (supports monkeypatching in tests)."""
    return SAFE_ASSET_ROOT


def get_safe_output_root() -> Path:
    """Return the active output directory root (supports monkeypatching in tests)."""
    return SAFE_OUTPUT_ROOT
