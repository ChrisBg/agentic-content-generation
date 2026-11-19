#!/usr/bin/env python3
"""Automated static security & secret leak gate for pre-commit and CI merges.

Checks:
1. Secret leakage patterns in git-tracked and staged files (API keys, private keys).
2. Dangerous code patterns (shell=True, eval/exec, unsafe yaml.load, pickle.load,
   raw xml.etree.ElementTree, unguarded Gradio 0.0.0.0 / share=True).
3. Sensitive private files (.env, knowledge/*) must NEVER be tracked by git.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_-]{30,}")),
    ("Anthropic API key", re.compile(r"sk-ant-[0-9A-Za-z_-]{20,}")),
    ("OpenAI API key", re.compile(r"sk-(?:proj-)?[0-9A-Za-z_-]{32,}")),
    ("xAI API key", re.compile(r"xai-[0-9A-Za-z_-]{20,}")),
    ("GitHub PAT", re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[0-9A-Za-z]{30,}")),
    ("Private Key Header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

PLACEHOLDER_HINTS = (
    "your_actual_key",
    "your_api_key",
    "your_google_api_key",
    "example",
    "redacted",
    "dummy",
)

DANGEROUS_CODE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("subprocess with shell=True", re.compile(r"\bshell\s*=\s*True\b")),
    ("unsafe eval()", re.compile(r"(?<![.\w])eval\s*\(")),
    ("unsafe exec()", re.compile(r"(?<![.\w])exec\s*\(")),
    ("unsafe pickle deserialization", re.compile(r"\bpickle\.loads?\s*\(")),
    ("unsafe yaml.load() without SafeLoader", re.compile(r"\byaml\.load\s*\(")),
    ("raw xml.etree.ElementTree (use defusedxml)", re.compile(r"\bxml\.etree\.ElementTree\b")),
    ("public Gradio share=True", re.compile(r"\bshare\s*=\s*True\b")),
    ("hardcoded 0.0.0.0 bind", re.compile(r'server_name\s*=\s*["\']0\.0\.0\.0["\']')),
]

FORBIDDEN_TRACKED_PREFIXES = (
    ".env",
    "knowledge/",
)


def _git_files() -> list[Path]:
    """Return tracked + untracked non-ignored files in the repository."""
    git_bin = shutil.which("git")
    if not git_bin:
        return [
            p
            for p in REPO_ROOT.rglob("*")
            if p.is_file() and ".git" not in p.parts and ".venv" not in p.parts
        ]
    proc = subprocess.run(  # noqa: S603
        [git_bin, "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if proc.returncode != 0:
        return [
            p
            for p in REPO_ROOT.rglob("*")
            if p.is_file() and ".git" not in p.parts and ".venv" not in p.parts
        ]
    return [REPO_ROOT / line for line in proc.stdout.splitlines() if line.strip()]


def _git_tracked_files() -> list[str]:
    git_bin = shutil.which("git")
    if not git_bin:
        return []
    proc = subprocess.run(  # noqa: S603
        [git_bin, "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def run_security_audit() -> list[str]:
    """Execute all static security checks and return a list of findings."""
    findings: list[str] = []

    # 1. Verify no sensitive files are tracked by Git
    for rel in _git_tracked_files():
        if rel == ".env.example":
            continue
        for prefix in FORBIDDEN_TRACKED_PREFIXES:
            if rel == prefix or rel.startswith(prefix):
                findings.append(f"[GIT TRACKING] Sensitive path must not be tracked: {rel}")

    # 2. Scan files for secrets and dangerous Python constructs
    text_exts = {".py", ".yaml", ".yml", ".json", ".toml", ".md", ".txt", ".sh", ".env", ".cfg"}
    for path in _git_files():
        if not path.is_file() or path.suffix.lower() not in text_exts:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        # Skip this scanner script itself for pattern literals
        if rel == "scripts/security_check.py":
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for line_no, line in enumerate(content.splitlines(), start=1):
            lower_line = line.lower()
            for label, regex in SECRET_PATTERNS:
                if regex.search(line) and not any(h in lower_line for h in PLACEHOLDER_HINTS):
                    findings.append(f"[SECRET] Potential {label} in {rel}:{line_no}")

            if path.suffix.lower() == ".py" and not rel.startswith("tests/"):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for label, regex in DANGEROUS_CODE_PATTERNS:
                    if regex.search(line):
                        findings.append(f"[CODE] {label} detected in {rel}:{line_no}")

    return findings


def main() -> int:
    findings = run_security_audit()
    if findings:
        print("SECURITY CHECK FAILED:")
        for item in findings:
            print(f"  - {item}")
        return 1
    print("SECURITY CHECK PASSED: 0 secrets leaked, 0 forbidden patterns, git tracking clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
