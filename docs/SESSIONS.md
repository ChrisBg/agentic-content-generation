# Session Management Guide

This guide explains how to manage conversation sessions with the Scientific Content Generation Agent.

## Table of Contents

- [What are Sessions?](#what-are-sessions)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [Session Database](#session-database)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## What are Sessions?

Sessions allow you to:
- **Resume conversations**: Pick up where you left off
- **Track history**: Review past content generation
- **Iterate on content**: Refine and improve generated content
- **Organize work**: Keep different topics separate

Each session stores:
- Session ID (UUID)
- User ID (from your profile)
- Creation and update timestamps
- Full conversation history (messages)

### Session Lifecycle

```
1. CREATE    → Generate content (auto-creates session)
2. RESUME    → Continue conversation with --session-id
3. LIST      → View all sessions
4. DELETE    → Remove old/unwanted sessions
```

---

## Quick Start

### Creating a Session

Sessions are created automatically when you generate content:

```bash
# This creates a new session
python main.py --topic "AI Agents"

# Output includes:
# 🆕 Starting new session: 550e8400-e29b-41d4-a716-446655440000
```

Save the session ID if you want to resume later!

### Resuming a Session

```bash
# Resume a previous conversation
python main.py --session-id 550e8400-e29b-41d4-a716-446655440000

# Can also specify a new topic
python main.py --topic "Related Topic" --session-id <SESSION_ID>
```

### Listing Sessions

```bash
# View all your sessions
python main.py --list-sessions

# Output:
# ================================================================================
# Session ID                               User      Messages   Last Updated
# ================================================================================
# 550e8400-e29b-41d4-a716-446655440...     Jane      5          2024-11-20 10:30:00
# 7c9e6679-7425-40de-944b-e07fc1f9...     Jane      12         2024-11-19 15:45:00
# ================================================================================
# Total: 2 session(s)
```

### Deleting a Session

```bash
# Delete a specific session
python main.py --delete-session 550e8400-e29b-41d4-a716-446655440000

# Output:
# 🗑️  Deleting session: 550e8400...
# ✅ Deleted session '550e8400...' and 5 message(s)
```

---

## CLI Commands

### `--list-sessions`

**List all saved sessions with metadata.**

```bash
python main.py --list-sessions
```

**Output includes:**
- Session ID (truncated for readability)
- User name (from profile)
- Message count
- Last updated timestamp

**Example:**
```
Session ID                               User          Messages   Last Updated
550e8400-e29b-41d4-a716-446655440...     Jane Smith    5          2024-11-20 10:30:00
```

**Tips:**
- Sessions are sorted by most recently updated
- Empty database shows: "No sessions found"
- Copy session ID for resumption

---

### `--session-id <ID>`

**Resume a specific conversation session.**

```bash
python main.py --session-id 550e8400-e29b-41d4-a716-446655440000
```

**Behavior:**
- Loads full conversation history
- Continues from last message
- Uses same user profile
- Maintains context across runs

**Example workflow:**
```bash
# Day 1: Generate initial content
python main.py --topic "AI Agents in Production"
# Save the session ID from output: 550e8400...

# Day 2: Refine the content
python main.py --session-id 550e8400... --topic "Add deployment section"
```

---

### `--delete-session <ID>`

**Delete a specific session and all its messages.**

```bash
python main.py --delete-session 550e8400-e29b-41d4-a716-446655440000
```

**What gets deleted:**
- Session metadata
- All messages in the session
- Cannot be undone!

**Safety:**
- Confirms session belongs to current app
- Shows message count before deletion
- Fails gracefully if session doesn't exist

---

## Session Database

### Database Location

```
~/.agentic-content-generation/sessions.db
```

This is a SQLite database managed by Google ADK's `DatabaseSessionService`.

### Database Schema

#### `sessions` table
| Column | Type | Description |
|--------|------|-------------|
| `session_id` | TEXT | UUID (primary key) |
| `app_name` | TEXT | Application name |
| `user_id` | TEXT | User name from profile |
| `created_at` | TEXT | ISO 8601 timestamp |
| `updated_at` | TEXT | ISO 8601 timestamp |

#### `messages` table
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-increment (primary key) |
| `session_id` | TEXT | Foreign key to sessions |
| `content` | TEXT | Message content (JSON) |
| `role` | TEXT | user/assistant/system |
| `created_at` | TEXT | ISO 8601 timestamp |

### Inspecting the Database

```bash
# Open database with sqlite3
sqlite3 ~/.agentic-content-generation/sessions.db

# List all sessions
SELECT session_id, user_id, created_at FROM sessions;

# Count messages per session
SELECT session_id, COUNT(*) as msg_count
FROM messages
GROUP BY session_id;

# Exit
.quit
```

### Backup and Export

```bash
# Backup database
cp ~/.agentic-content-generation/sessions.db ~/sessions_backup.db

# Export sessions to CSV
sqlite3 -header -csv ~/.agentic-content-generation/sessions.db \
  "SELECT * FROM sessions" > sessions.csv
```

---

## Best Practices

### 1. Use Descriptive Topics

When creating sessions, use descriptive topics so you can identify them later:

❌ **Bad:**
```bash
python main.py --topic "test"
```

✅ **Good:**
```bash
python main.py --topic "LLM Fine-tuning for Customer Service - Blog Series"
```

### 2. Clean Up Old Sessions

Delete sessions you no longer need:

```bash
# List sessions
python main.py --list-sessions

# Delete old ones
python main.py --delete-session <OLD_SESSION_ID>
```

### 3. Resume for Refinement

Use sessions to iteratively improve content:

```bash
# First pass
python main.py --topic "AI Ethics" --session-id <ID>

# Add more depth
python main.py --topic "Add case studies on bias" --session-id <ID>

# Polish
python main.py --topic "Improve conclusion" --session-id <ID>
```

### 4. Organize by Project

Create separate sessions for different projects:

```
Session 1: Blog series on MLOps
Session 2: LinkedIn posts about AI trends
Session 3: Twitter thread on latest papers
```

### 5. Regular Maintenance

```bash
# Monthly cleanup
python main.py --list-sessions
# Review and delete unused sessions
```

---

## Use Cases

### Use Case 1: Content Series

Generate a series of related blog posts:

```bash
# Part 1
python main.py --topic "Intro to Transformers"
# Session: abc123...

# Part 2 (references Part 1)
python main.py --topic "Transformer Architectures Deep Dive" --session-id abc123

# Part 3 (builds on Parts 1-2)
python main.py --topic "Transformers in Production" --session-id abc123
```

### Use Case 2: Multi-Platform Campaign

Generate content for multiple platforms on the same topic:

```bash
# Initial research and blog post
python main.py --topic "AI Model Compression"
# Session: xyz789...

# Generate LinkedIn version
python main.py --topic "Create LinkedIn post from this" --session-id xyz789

# Generate Twitter thread
python main.py --topic "Create Twitter thread highlighting key points" --session-id xyz789
```

### Use Case 3: Iterative Refinement

Improve content through multiple iterations:

```bash
# Draft
python main.py --topic "Future of AI"
# Session: def456...

# Feedback round 1
python main.py --topic "Add more technical depth" --session-id def456

# Feedback round 2
python main.py --topic "Make it more accessible for non-technical audience" --session-id def456
```

---

## Advanced Topics

### Session Persistence

Sessions are stored in SQLite and persist across:
- Multiple runs of the agent
- System restarts
- Different terminals/environments (same home directory)

### Session Isolation

Each session is isolated:
- Different sessions don't share context
- Messages are scoped to session_id
- User ID is stored with each session

### Concurrent Sessions

You can work on multiple sessions simultaneously:
```bash
# Terminal 1: Blog series
python main.py --topic "Part 3" --session-id abc123

# Terminal 2: LinkedIn posts
python main.py --topic "Weekly update" --session-id xyz789
```

### Session in Code

Access sessions programmatically:

```python
from src.session_manager import list_sessions, get_session_info

# List all sessions
sessions = list_sessions()
for s in sessions:
    print(f"{s['session_id']}: {s['message_count']} messages")

# Get session details
info = get_session_info("550e8400-...")
print(f"User: {info['user_id']}")
print(f"Messages: {len(info['messages'])}")
```

---

## Troubleshooting

### "Session not found"

**Problem:** Trying to resume or delete a non-existent session.

**Solution:**
```bash
# List available sessions
python main.py --list-sessions

# Copy the correct session ID
```

### Database locked

**Problem:** Another process is using the database.

**Solution:**
1. Close other running instances of the agent
2. Stop any ADK web servers
3. Try again

### Session history too large

**Problem:** Session has too many messages, slowing down resumption.

**Solution:**
- Start a new session for the next topic
- Delete old messages manually in SQLite
- Or delete and start fresh

### Lost session ID

**Problem:** Didn't save the session ID from output.

**Solution:**
```bash
# List all sessions
python main.py --list-sessions

# Look for recent sessions by timestamp
# Copy the ID and resume
```

### Wrong user in session

**Problem:** Session shows different user name.

**Solution:**
- Sessions use the user ID from when they were created
- To use current profile, start a new session
- Session user ID doesn't update automatically

---

## FAQ

**Q: How long are sessions stored?**
A: Indefinitely until manually deleted.

**Q: Can I share sessions with others?**
A: No, sessions are local to your machine. You could share the database file, but it's not recommended.

**Q: What's the maximum session size?**
A: Practically unlimited, but very large sessions (100+ messages) may slow down.

**Q: Can I rename a session?**
A: Not directly. Sessions are identified by UUID. Use descriptive topics instead.

**Q: Do sessions expire?**
A: No automatic expiration. Clean up manually.

**Q: Can I export a session?**
A: Yes, using SQLite commands (see [Backup and Export](#backup-and-export)).

**Q: What happens if I delete sessions.db?**
A: All session history is lost. A new database will be created on next run.

---

## See Also

- [PROFILES.md](PROFILES.md) - User profile configuration guide
- [README.md](../README.md) - Main documentation
- [Google ADK Sessions Documentation](https://google.github.io/adk-docs/sessions/)
