"""Entry point for Hugging Face Spaces / cloud deployment with optional Basic Auth."""

from __future__ import annotations

import os

import gradio as gr

from ui_app import create_ui

if __name__ == "__main__":
    app = create_ui()
    app.queue()
    auth_user = os.getenv("GRADIO_AUTH_USER", "").strip()
    auth_pass = os.getenv("GRADIO_AUTH_PASSWORD", "").strip()
    auth = (auth_user, auth_pass) if (auth_user and auth_pass) else None
    app.launch(auth=auth, share=False, theme=gr.themes.Soft())
