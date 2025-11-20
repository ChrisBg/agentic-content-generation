"""Session management utilities for the content generation agent."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from src.profile import PROFILE_DIR


def get_session_db_path() -> Path:
    """Get the path to the session database.

    Returns:
        Path to sessions.db
    """
    return PROFILE_DIR / "sessions.db"


def list_sessions(app_name: str = "scientific-content-agent") -> list[dict[str, Any]]:
    """List all sessions in the database.

    Args:
        app_name: Application name to filter sessions

    Returns:
        List of session dictionaries with metadata
    """
    db_path = get_session_db_path()

    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query sessions table
        # Note: ADK's DatabaseSessionService uses these columns
        query = """
            SELECT
                session_id,
                app_name,
                user_id,
                created_at,
                updated_at
            FROM sessions
            WHERE app_name = ?
            ORDER BY updated_at DESC
        """

        cursor.execute(query, (app_name,))
        rows = cursor.fetchall()

        sessions = []
        for row in rows:
            session = {
                "session_id": row["session_id"],
                "app_name": row["app_name"],
                "user_id": row["user_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

            # Count messages in this session
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM messages
                WHERE session_id = ?
            """,
                (row["session_id"],),
            )
            message_row = cursor.fetchone()
            session["message_count"] = message_row["count"] if message_row else 0

            sessions.append(session)

        conn.close()
        return sessions

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []


def delete_session(session_id: str, app_name: str = "scientific-content-agent") -> dict[str, Any]:
    """Delete a session and its messages.

    Args:
        session_id: The session ID to delete
        app_name: Application name for verification

    Returns:
        Dictionary with status and message
    """
    db_path = get_session_db_path()

    if not db_path.exists():
        return {"status": "error", "message": "Session database not found"}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verify session exists and belongs to this app
        cursor.execute(
            """
            SELECT session_id
            FROM sessions
            WHERE session_id = ? AND app_name = ?
        """,
            (session_id, app_name),
        )

        if not cursor.fetchone():
            conn.close()
            return {"status": "error", "message": f"Session '{session_id}' not found"}

        # Delete messages first (foreign key constraint)
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        messages_deleted = cursor.rowcount

        # Delete session
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        session_deleted = cursor.rowcount

        conn.commit()
        conn.close()

        if session_deleted > 0:
            return {
                "status": "success",
                "message": f"Deleted session '{session_id}' and {messages_deleted} message(s)",
            }
        return {"status": "error", "message": "Failed to delete session"}

    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


def get_session_info(
    session_id: str, app_name: str = "scientific-content-agent"
) -> dict[str, Any] | None:
    """Get detailed information about a specific session.

    Args:
        session_id: The session ID to query
        app_name: Application name for verification

    Returns:
        Dictionary with session details or None if not found
    """
    db_path = get_session_db_path()

    if not db_path.exists():
        return None

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get session info
        cursor.execute(
            """
            SELECT
                session_id,
                app_name,
                user_id,
                created_at,
                updated_at
            FROM sessions
            WHERE session_id = ? AND app_name = ?
        """,
            (session_id, app_name),
        )

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        session = dict(row)

        # Get messages
        cursor.execute(
            """
            SELECT
                content,
                role,
                created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
        """,
            (session_id,),
        )

        messages = [dict(msg) for msg in cursor.fetchall()]
        session["messages"] = messages
        session["message_count"] = len(messages)

        conn.close()
        return session

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def format_session_list(sessions: list[dict[str, Any]]) -> str:
    """Format sessions list as a pretty table.

    Args:
        sessions: List of session dictionaries

    Returns:
        Formatted string table
    """
    if not sessions:
        return "No sessions found."

    # Calculate column widths
    max_user_len = max((len(s.get("user_id", "")) for s in sessions), default=10)
    max_user_len = max(max_user_len, 10)  # Minimum width

    output = []
    output.append("\n" + "=" * 100)
    output.append(
        f"{'Session ID':<40} {'User':<{max_user_len}} {'Messages':<10} {'Last Updated':<20}"
    )
    output.append("=" * 100)

    for session in sessions:
        session_id = session["session_id"][:37] + "..."  # Truncate long UUIDs
        user_id = session.get("user_id", "Unknown")[:max_user_len]
        message_count = str(session.get("message_count", 0))
        updated_at = session.get("updated_at", "Unknown")

        # Parse timestamp if it's in ISO format
        try:
            if "T" in updated_at:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                updated_at = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            pass

        output.append(
            f"{session_id:<40} {user_id:<{max_user_len}} {message_count:<10} {updated_at:<20}"
        )

    output.append("=" * 100 + "\n")

    return "\n".join(output)
