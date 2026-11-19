"""Multi-LLM routing layer for Google ADK (native Gemini + LiteLLM providers)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from google.adk.models.google_llm import Gemini

from .config import DEFAULT_PRO_MODEL, RETRY_CONFIG, ROLE_MODEL_PREFERENCES

try:
    from google.adk.models.lite_llm import LiteLlm
except ImportError:  # pragma: no cover - optional when litellm is not installed
    LiteLlm = None  # type: ignore[assignment]


PROVIDER_ENV_KEYS: dict[str, str] = {
    "google": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "xai": "XAI_API_KEY",
}


@dataclass(frozen=True)
class ModelResolution:
    """Resolved model metadata for a given pipeline role."""

    role: str
    model_name: str
    provider: str
    is_fallback: bool
    reason: str


def infer_provider(model_name: str) -> str:
    """Infer provider name from a Gemini or LiteLLM model identifier."""
    lower = model_name.lower()
    if lower.startswith("anthropic/") or "claude" in lower:
        return "anthropic"
    if lower.startswith("openai/") or lower.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    if lower.startswith("xai/") or "grok" in lower:
        return "xai"
    if lower.startswith("gemini/") or lower.startswith("gemini-"):
        return "google"
    return "google"


def is_provider_configured(provider: str, env: dict[str, str] | None = None) -> bool:
    """Check whether an API key is configured for the given provider."""
    lookup = env if env is not None else os.environ
    env_var = PROVIDER_ENV_KEYS.get(provider)
    if not env_var:
        return False
    value = lookup.get(env_var, "").strip()
    return bool(value) and not value.startswith("your_") and not value.endswith("_here")


class ModelRouter:
    """Routes each ADK agent role to the most appropriate available LLM.

    Features:
    - Per-role defaults (e.g., Gemini for research/visuals, Claude for LinkedIn/YouTube,
      Grok/GPT for X threads).
    - Environment overrides via ``MODEL_<ROLE>`` (e.g. ``MODEL_LINKEDIN``).
    - Runtime overrides (e.g. from Gradio Settings tab).
    - Cross-family judging: ``editorial_critic`` avoids the provider used by ``linkedin``
      whenever another configured provider is available.
    - Graceful fallback to Gemini if optional provider API keys are missing.
    """

    def __init__(
        self,
        overrides: dict[str, str] | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self._overrides = {k.lower(): v.strip() for k, v in (overrides or {}).items() if v.strip()}
        self._env = env

    def _get_env(self, key: str) -> str:
        lookup = self._env if self._env is not None else os.environ
        return lookup.get(key, "").strip()

    def resolve(self, role: str) -> ModelResolution:
        """Resolve which model name and provider should serve a pipeline role."""
        role_key = role.lower()

        # 1. Explicit runtime override
        if role_key in self._overrides:
            chosen = self._overrides[role_key]
            provider = infer_provider(chosen)
            if provider == "google" or (is_provider_configured(provider, self._env) and LiteLlm):
                return ModelResolution(
                    role=role_key,
                    model_name=chosen,
                    provider=provider,
                    is_fallback=False,
                    reason="runtime override",
                )

        # 2. Environment variable override (MODEL_<ROLE>)
        env_override = self._get_env(f"MODEL_{role_key.upper()}")
        if env_override:
            provider = infer_provider(env_override)
            if provider == "google" or (is_provider_configured(provider, self._env) and LiteLlm):
                return ModelResolution(
                    role=role_key,
                    model_name=env_override,
                    provider=provider,
                    is_fallback=False,
                    reason=f"env MODEL_{role_key.upper()}",
                )

        # 3. Preference list with optional cross-family bias for editorial_critic
        candidates = list(ROLE_MODEL_PREFERENCES.get(role_key, [DEFAULT_PRO_MODEL]))
        if role_key == "editorial_critic":
            writer_provider = self.resolve("linkedin").provider
            reordered = [m for m in candidates if infer_provider(m) != writer_provider]
            reordered.extend(m for m in candidates if infer_provider(m) == writer_provider)
            candidates = reordered

        primary = candidates[0]
        for idx, candidate in enumerate(candidates):
            provider = infer_provider(candidate)
            if provider == "google":
                return ModelResolution(
                    role=role_key,
                    model_name=candidate,
                    provider="google",
                    is_fallback=idx > 0,
                    reason=(
                        "primary preference"
                        if idx == 0
                        else f"fallback (preferred {primary} key missing)"
                    ),
                )
            if is_provider_configured(provider, self._env) and LiteLlm is not None:
                return ModelResolution(
                    role=role_key,
                    model_name=candidate,
                    provider=provider,
                    is_fallback=idx > 0,
                    reason=(
                        "primary preference"
                        if idx == 0
                        else f"fallback (preferred {primary} key missing)"
                    ),
                )

        # Ultimate fallback to default Gemini Pro
        return ModelResolution(
            role=role_key,
            model_name=DEFAULT_PRO_MODEL,
            provider="google",
            is_fallback=True,
            reason="default Gemini fallback",
        )

    def get_model(self, role: str) -> Any:
        """Return an ADK-compatible model instance (Gemini or LiteLlm) for ``role``."""
        resolution = self.resolve(role)
        if resolution.provider == "google":
            clean_name = resolution.model_name.removeprefix("gemini/")
            return Gemini(model=clean_name, retry_options=RETRY_CONFIG)

        if LiteLlm is None:  # pragma: no cover
            return Gemini(model=DEFAULT_PRO_MODEL, retry_options=RETRY_CONFIG)

        return LiteLlm(model=resolution.model_name)

    def get_provider_status(self) -> dict[str, bool]:
        """Return availability status of all supported LLM providers."""
        return {
            provider: is_provider_configured(provider, self._env) for provider in PROVIDER_ENV_KEYS
        }

    def get_active_routing_table(self) -> dict[str, dict[str, Any]]:
        """Return a human-readable routing table for CLI and Gradio UI display."""
        table: dict[str, dict[str, Any]] = {}
        for role in ROLE_MODEL_PREFERENCES:
            res = self.resolve(role)
            table[role] = {
                "model": res.model_name,
                "provider": res.provider,
                "is_fallback": res.is_fallback,
                "reason": res.reason,
            }
        return table

    def format_routing_summary(self) -> str:
        """Render a clean text table of active LLM routing for terminal output."""
        providers = self.get_provider_status()
        provider_line = " | ".join(
            f"{p}: {'OK' if ok else 'not set'}" for p, ok in providers.items()
        )
        lines = [
            "=== Active Multi-LLM Routing ===",
            f"Providers: {provider_line}",
            "",
            f"{'Role':<18} {'Provider':<11} {'Model':<38} {'Status'}",
            "-" * 85,
        ]
        for role, info in self.get_active_routing_table().items():
            status = "fallback" if info["is_fallback"] else info["reason"]
            lines.append(f"{role:<18} {info['provider']:<11} {info['model']:<38} {status}")
        return "\n".join(lines)
