"""Tests for session manager functionality."""

from unittest.mock import patch

from src.session_manager import (
    delete_session,
    format_session_list,
    get_session_info,
    list_sessions,
)


class TestListSessions:
    """Test session listing functionality."""

    def test_list_sessions_empty_database(self, temp_session_db):
        """Test listing sessions from empty database."""
        with patch("src.session_manager.get_session_db_path", return_value=temp_session_db):
            sessions = list_sessions()
            assert sessions == []

    def test_list_sessions_returns_all_app_sessions(self, populated_session_db):
        """Test that list_sessions returns all sessions for the app."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            sessions = list_sessions(app_name="scientific-content-agent")

            assert len(sessions) == 2  # Should find session-1 and session-2
            session_ids = [s["session_id"] for s in sessions]
            assert "session-1" in session_ids
            assert "session-2" in session_ids
            assert "session-3" not in session_ids  # Different app

    def test_list_sessions_includes_metadata(self, populated_session_db):
        """Test that sessions include metadata."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            sessions = list_sessions()

            assert len(sessions) > 0
            first_session = sessions[0]

            # Check required fields
            assert "session_id" in first_session
            assert "app_name" in first_session
            assert "user_id" in first_session
            assert "created_at" in first_session
            assert "updated_at" in first_session
            assert "message_count" in first_session

    def test_list_sessions_counts_messages_correctly(self, populated_session_db):
        """Test that message count is accurate."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            sessions = list_sessions()

            session_1 = next(s for s in sessions if s["session_id"] == "session-1")
            session_2 = next(s for s in sessions if s["session_id"] == "session-2")

            assert session_1["message_count"] == 3  # 3 messages in session-1
            assert session_2["message_count"] == 1  # 1 message in session-2

    def test_list_sessions_nonexistent_database(self, temp_dir):
        """Test listing sessions when database doesn't exist."""
        nonexistent_db = temp_dir / "nonexistent.db"
        with patch("src.session_manager.get_session_db_path", return_value=nonexistent_db):
            sessions = list_sessions()
            assert sessions == []


class TestDeleteSession:
    """Test session deletion functionality."""

    def test_delete_existing_session(self, populated_session_db):
        """Test deleting an existing session."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            result = delete_session("session-1")

            assert result["status"] == "success"
            assert "session-1" in result["message"]
            assert "3 message(s)" in result["message"]

            # Verify session is gone
            sessions = list_sessions()
            session_ids = [s["session_id"] for s in sessions]
            assert "session-1" not in session_ids

    def test_delete_nonexistent_session(self, populated_session_db):
        """Test deleting a session that doesn't exist."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            result = delete_session("nonexistent-session")

            assert result["status"] == "error"
            assert "not found" in result["message"].lower()

    def test_delete_session_wrong_app(self, populated_session_db):
        """Test deleting a session from a different app."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            # session-3 belongs to "other-app"
            result = delete_session("session-3", app_name="scientific-content-agent")

            assert result["status"] == "error"
            assert "not found" in result["message"].lower()

    def test_delete_session_removes_messages(self, populated_session_db):
        """Test that deleting a session removes its messages."""
        import sqlite3

        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            # Count messages before deletion
            conn = sqlite3.connect(populated_session_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", ("session-1",))
            count_before = cursor.fetchone()[0]
            conn.close()

            assert count_before == 3  # session-1 has 3 messages

            # Delete session
            result = delete_session("session-1")
            assert result["status"] == "success"

            # Count messages after deletion
            conn = sqlite3.connect(populated_session_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", ("session-1",))
            count_after = cursor.fetchone()[0]
            conn.close()

            assert count_after == 0  # All messages deleted

    def test_delete_session_nonexistent_database(self, temp_dir):
        """Test deleting session when database doesn't exist."""
        nonexistent_db = temp_dir / "nonexistent.db"
        with patch("src.session_manager.get_session_db_path", return_value=nonexistent_db):
            result = delete_session("session-1")

            assert result["status"] == "error"
            assert "not found" in result["message"].lower()


class TestGetSessionInfo:
    """Test getting detailed session information."""

    def test_get_existing_session_info(self, populated_session_db):
        """Test getting info for an existing session."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            info = get_session_info("session-1")

            assert info is not None
            assert info["session_id"] == "session-1"
            assert info["app_name"] == "scientific-content-agent"
            assert info["user_id"] == "Test User"
            assert "messages" in info
            assert len(info["messages"]) == 3
            assert info["message_count"] == 3

    def test_get_session_info_includes_messages(self, populated_session_db):
        """Test that session info includes message details."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            info = get_session_info("session-1")

            assert info is not None
            messages = info["messages"]

            # Check first message
            assert messages[0]["content"] == "Hello"
            assert messages[0]["role"] == "user"
            assert "created_at" in messages[0]

    def test_get_nonexistent_session_info(self, populated_session_db):
        """Test getting info for nonexistent session."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            info = get_session_info("nonexistent-session")

            assert info is None

    def test_get_session_info_wrong_app(self, populated_session_db):
        """Test getting session info for wrong app."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            # session-3 belongs to "other-app"
            info = get_session_info("session-3", app_name="scientific-content-agent")

            assert info is None


class TestFormatSessionList:
    """Test session list formatting."""

    def test_format_empty_list(self):
        """Test formatting an empty session list."""
        formatted = format_session_list([])
        assert "No sessions found" in formatted

    def test_format_session_list_includes_headers(self, populated_session_db):
        """Test that formatted list includes headers."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            sessions = list_sessions()
            formatted = format_session_list(sessions)

            assert "Session ID" in formatted
            assert "User" in formatted
            assert "Messages" in formatted
            assert "Last Updated" in formatted

    def test_format_session_list_includes_data(self, populated_session_db):
        """Test that formatted list includes session data."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            sessions = list_sessions()
            formatted = format_session_list(sessions)

            assert "session-1" in formatted
            assert "session-2" in formatted
            assert "Test User" in formatted

    def test_format_session_list_shows_message_counts(self, populated_session_db):
        """Test that formatted list shows message counts."""
        with patch("src.session_manager.get_session_db_path", return_value=populated_session_db):
            sessions = list_sessions()
            formatted = format_session_list(sessions)

            # session-1 has 3 messages
            assert "3" in formatted
            # session-2 has 1 message
            assert "1" in formatted

    def test_format_session_list_truncates_long_ids(self):
        """Test that long session IDs are truncated."""
        long_session = {
            "session_id": "a" * 100,  # Very long ID
            "user_id": "Test User",
            "message_count": 5,
            "updated_at": "2024-01-01T10:00:00Z",
        }

        formatted = format_session_list([long_session])

        # Should truncate to ~40 chars
        assert len([line for line in formatted.split("\n") if "aaa" in line][0]) < 120
