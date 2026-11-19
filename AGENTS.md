# Project Rules — `agentic-content-generation`

## Mandatory Security & Quality Gate (After Every Change & Before Commit/Merge)

After making code changes in this repository — and before any `git commit` or merge — ALWAYS run and verify:

1. **Static Security & Secret Scan**:
   ```bash
   python scripts/security_check.py
   ```
2. **Formatting & Security Linting (Ruff + flake8-bandit `S` rules)**:
   ```bash
   ruff format --check src/ scripts/ main.py ui_app.py app.py tests/
   ruff check src/ scripts/ main.py ui_app.py app.py tests/
   ```
3. **Security Regression & Unit Tests**:
   ```bash
   pytest tests/test_security.py -v
   pytest tests/ -v
   ```

Never claim a task is complete or approve a commit/merge if any of these checks fail.

## Security Invariants (Multi-Agent, LLM Tools & Gradio)

- **Sandbox all LLM-facing file paths**: Every tool callable by an ADK agent (e.g., `src/visuals.py`, `src/video_assets.py`) and every UI file-write handler (`ui_app.py`) MUST validate input and output paths through `resolve_safe_path()` in `src/security.py` against `SAFE_ASSET_ROOT` or `SAFE_OUTPUT_ROOT`.
- **Confine Knowledge Base tools**: Never expose arbitrary directory or file path parameters on LLM-callable tools in `src/knowledge_base.py`.
- **Safe Gradio networking**: Always bind Gradio to `127.0.0.1` by default, keep `share=False`, and require Basic Auth (`GRADIO_AUTH_USER` / `GRADIO_AUTH_PASSWORD`) before allowing any non-localhost bind.
- **Hardened parsing & subprocesses**:
  - Parse all external XML (e.g., arXiv API) with `defusedxml` — never raw `xml.etree.ElementTree`.
  - Always resolve binaries via `shutil.which()`, avoid `shell=True`, and set an explicit `timeout` on every `subprocess.run()` call.
  - Never use `eval()`, `exec()`, `pickle.load()`, or unsafe `yaml.load()` (always `yaml.safe_load()`).
- **Secrets & Privacy**: Never commit `.env`, API keys, or private `knowledge/` files. Only generic templates belong in `knowledge.example/`.

## Toolchain Compatibility Invariants

- **FFmpeg 8+**: Use `-vf "fps=30,format=yuv420p"` instead of conflicting `-vsync vfr` + `-r 30` flags.
- **Gradio 6+**: Pass `theme=` to `launch(...)` rather than `gr.Blocks(...)`, and avoid removed parameters such as `show_copy_button` on `gr.Textbox`.
- **Multi-LLM ADK Routing**: Route models through `ModelRouter` (`src/llm_router.py`) with graceful fallback to Gemini when optional provider keys are absent.
