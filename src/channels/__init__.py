"""Extensible social channel plugin registry (LinkedIn, X, YouTube, Newsletter)."""

from .registry import (
    CHANNEL_REGISTRY,
    ChannelPlugin,
    create_channel_writer_agent,
    get_channel_plugin,
    list_supported_channels,
)

__all__ = [
    "CHANNEL_REGISTRY",
    "ChannelPlugin",
    "create_channel_writer_agent",
    "get_channel_plugin",
    "list_supported_channels",
]
