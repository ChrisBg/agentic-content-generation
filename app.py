"""Entry point for Hugging Face Spaces deployment."""

from ui_app import create_ui

if __name__ == "__main__":
    app = create_ui()
    app.queue()  # Enable queueing for concurrent users
    app.launch()
