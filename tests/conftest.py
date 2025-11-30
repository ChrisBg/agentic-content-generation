"""Pytest configuration and fixtures for testing."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.profile import UserProfile


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_profile_dir(temp_dir):
    """Mock the PROFILE_DIR to use a temporary directory."""
    with (
        patch("src.profile.PROFILE_DIR", temp_dir),
        patch("src.profile.PROFILE_PATH", temp_dir / "profile.yaml"),
    ):
        yield temp_dir


@pytest.fixture
def valid_profile():
    """Create a valid test profile."""
    return UserProfile(
        name="Test User",
        target_role="AI Engineer",
        expertise_areas=["Machine Learning", "Deep Learning"],
        content_goals=["opportunities", "credibility"],
        region="US",
        languages=["English"],
        target_industries=["Technology"],
        github_username="testuser",
        linkedin_url="https://linkedin.com/in/testuser",
        portfolio_url="https://testuser.com",
        kaggle_username="testuser",
        notable_projects=[
            {
                "name": "Test Project",
                "description": "A test project",
                "technologies": "Python, TensorFlow",
                "url": "https://github.com/testuser/project",
            }
        ],
        primary_skills=["Python", "TensorFlow", "PyTorch"],
        content_tone="professional-conversational",
        use_emojis=True,
        posting_frequency="weekly",
        unique_value_proposition="I help companies test AI systems",
        key_differentiators=["Testing expertise", "Production focus"],
    )


@pytest.fixture
def invalid_profile():
    """Create an invalid test profile with validation errors."""
    return UserProfile(
        name="",  # Empty name
        target_role="AI Engineer",
        expertise_areas=[],  # Empty expertise
        content_tone="invalid-tone",  # Invalid tone
        linkedin_url="not-a-url",  # Invalid URL
        github_username="user/with/slashes",  # Invalid username
    )


@pytest.fixture
def default_profile():
    """Create a default profile (with default values)."""
    return UserProfile()


@pytest.fixture
def temp_session_db(temp_dir):
    """Create a temporary session database for testing."""
    db_path = temp_dir / "sessions.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create sessions table (matching ADK schema)
    cursor.execute(
        """
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY,
            app_name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """
    )

    # Create messages table
    cursor.execute(
        """
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            content TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """
    )

    conn.commit()
    conn.close()

    yield db_path


@pytest.fixture
def populated_session_db(temp_session_db):
    """Create a session database with test data."""
    conn = sqlite3.connect(temp_session_db)
    cursor = conn.cursor()

    # Insert test sessions
    test_sessions = [
        (
            "session-1",
            "scientific-content-agent",
            "Test User",
            "2024-01-01T10:00:00Z",
            "2024-01-01T11:00:00Z",
        ),
        (
            "session-2",
            "scientific-content-agent",
            "Test User",
            "2024-01-02T10:00:00Z",
            "2024-01-02T11:00:00Z",
        ),
        (
            "session-3",
            "other-app",
            "Other User",
            "2024-01-03T10:00:00Z",
            "2024-01-03T11:00:00Z",
        ),
    ]

    cursor.executemany(
        "INSERT INTO sessions VALUES (?, ?, ?, ?, ?)",
        test_sessions,
    )

    # Insert test messages
    test_messages = [
        ("session-1", "Hello", "user", "2024-01-01T10:00:00Z"),
        ("session-1", "Hi there", "assistant", "2024-01-01T10:01:00Z"),
        ("session-1", "How are you?", "user", "2024-01-01T10:02:00Z"),
        ("session-2", "Test message", "user", "2024-01-02T10:00:00Z"),
    ]

    cursor.executemany(
        "INSERT INTO messages (session_id, content, role, created_at) VALUES (?, ?, ?, ?)",
        test_messages,
    )

    conn.commit()
    conn.close()

    yield temp_session_db


@pytest.fixture
def mock_google_api():
    """Mock Google API key environment variable."""
    with patch("src.config.GOOGLE_API_KEY", "test-api-key"):
        yield


@pytest.fixture
def mock_arxiv_response():
    """Mock arXiv API response."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <title>Test Paper on Machine Learning</title>
    <summary>This is a test abstract about ML.</summary>
    <author><name>Test Author</name></author>
    <published>2023-01-01T00:00:00Z</published>
    <link href="http://arxiv.org/abs/2301.00001v1" />
  </entry>
</feed>"""


@pytest.fixture
def mock_requests_get(mock_arxiv_response):
    """Mock requests.get for tool testing."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_arxiv_response
    mock_response.content = mock_arxiv_response.encode()

    with patch("requests.get", return_value=mock_response):
        yield mock_response
