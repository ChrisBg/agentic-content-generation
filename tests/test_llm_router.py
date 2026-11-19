"""Unit tests for Multi-LLM routing, fallbacks, overrides, and cross-family judging."""

from __future__ import annotations

from src.llm_router import ModelRouter, infer_provider, is_provider_configured


class TestModelRouter:
    """Tests for ModelRouter resolution logic."""

    def test_infer_provider(self):
        assert infer_provider("gemini-2.5-pro") == "google"
        assert infer_provider("anthropic/claude-sonnet-4-5-20250929") == "anthropic"
        assert infer_provider("openai/gpt-4.1") == "openai"
        assert infer_provider("xai/grok-3") == "xai"

    def test_placeholder_keys_treated_as_unconfigured(self):
        env = {
            "GOOGLE_API_KEY": "real-google-key",
            "ANTHROPIC_API_KEY": "your_anthropic_api_key_here",
            "OPENAI_API_KEY": "",
        }
        assert is_provider_configured("google", env) is True
        assert is_provider_configured("anthropic", env) is False
        assert is_provider_configured("openai", env) is False

    def test_gemini_only_graceful_fallback(self):
        router = ModelRouter(env={"GOOGLE_API_KEY": "real-google-key"})
        li = router.resolve("linkedin")
        x = router.resolve("x")
        yt = router.resolve("youtube")

        assert li.provider == "google"
        assert li.is_fallback is True
        assert x.provider == "google"
        assert x.is_fallback is True
        assert yt.provider == "google"
        assert yt.is_fallback is True

    def test_multi_provider_routes_each_channel_optimally(self):
        env = {
            "GOOGLE_API_KEY": "real-g",
            "ANTHROPIC_API_KEY": "real-a",
            "OPENAI_API_KEY": "real-o",
            "XAI_API_KEY": "real-x",
        }
        router = ModelRouter(env=env)
        assert router.resolve("research").provider == "google"
        assert router.resolve("linkedin").provider == "anthropic"
        assert router.resolve("youtube").provider == "anthropic"
        assert router.resolve("x").provider == "xai"
        # Cross-family judging: LinkedIn is Anthropic, so editorial critic picks OpenAI (not Anthropic)
        assert router.resolve("editorial_critic").provider == "openai"

    def test_env_and_runtime_overrides(self):
        env = {
            "GOOGLE_API_KEY": "real-g",
            "OPENAI_API_KEY": "real-o",
            "MODEL_LINKEDIN": "openai/gpt-4.1",
        }
        router_env = ModelRouter(env=env)
        assert router_env.resolve("linkedin").model_name == "openai/gpt-4.1"
        assert "env MODEL_LINKEDIN" in router_env.resolve("linkedin").reason

        router_rt = ModelRouter(overrides={"linkedin": "gemini-2.5-pro"}, env=env)
        assert router_rt.resolve("linkedin").model_name == "gemini-2.5-pro"
        assert router_rt.resolve("linkedin").reason == "runtime override"

    def test_format_routing_summary(self):
        summary = ModelRouter(env={"GOOGLE_API_KEY": "real-g"}).format_routing_summary()
        assert "Active Multi-LLM Routing" in summary
        assert "linkedin" in summary
        assert "youtube" in summary
