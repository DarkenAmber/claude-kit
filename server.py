"""
MemoryKit - Local memory for Claude

Stores facts, preferences, and context between sessions.
Privacy-first: all data stored locally in SQLite. No cloud, no registration.
"""

import sqlite3
import json
import time
import re
from pathlib import Path
from fastmcp import FastMCP

# Store DB in user's home directory
DB_PATH = Path.home() / ".memory-kit" / "memories.db"
DB_PATH.parent.mkdir(exist_ok=True)

mcp = FastMCP(
    name="memory-kit",
    instructions=(
        "MemoryKit gives you persistent memory between conversations. "
        "Use remember() to save important facts, recall() to find relevant memories, "
        "list_memories() to browse all memories, and forget() to delete specific ones. "
        "Always recall() at the start of conversations about ongoing projects. "
        "Categories: project, preference, person, fact, decision."
    )
)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'fact',
            tags TEXT DEFAULT '[]',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            access_count INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
        USING fts5(content, category, tags, content=memories, content_rowid=id)
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
            INSERT INTO memories_fts(rowid, content, category, tags)
            VALUES (new.id, new.content, new.category, new.tags);
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, content, category, tags)
            VALUES ('delete', old.id, old.content, old.category, old.tags);
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, content, category, tags)
            VALUES ('delete', old.id, old.content, old.category, old.tags);
            INSERT INTO memories_fts(rowid, content, category, tags)
            VALUES (new.id, new.content, new.category, new.tags);
        END
    """)
    conn.commit()
    return conn


def format_memory(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "content": row["content"],
        "category": row["category"],
        "tags": json.loads(row["tags"]) if row["tags"] else [],
        "created_at": row["created_at"],
        "access_count": row["access_count"],
    }


def format_time(ts: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


VALID_CATEGORIES = {"project", "preference", "person", "fact", "decision"}


@mcp.tool(
    description=(
        "Save a fact, preference, or context to memory. "
        "Use for: project decisions, user preferences, important facts, people info. "
        "category options: project, preference, person, fact, decision"
    )
)
def remember(
    content: str,
    category: str = "fact",
    tags: list[str] | None = None
) -> dict:
    """
    Save something to memory.

    Args:
        content: The fact or context to remember
        category: One of: project, preference, person, fact, decision
        tags: Optional list of tags for easier retrieval
    """
    if not content.strip():
        return {"error": "Content cannot be empty"}

    if category not in VALID_CATEGORIES:
        category = "fact"

    tags_list = tags or []
    now = time.time()

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO memories (content, category, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (content.strip(), category, json.dumps(tags_list), now, now)
        )
        memory_id = cursor.lastrowid

    return {
        "id": memory_id,
        "content": content.strip(),
        "category": category,
        "tags": tags_list,
        "saved_at": format_time(now),
        "message": f"Remembered! (id: {memory_id})"
    }


@mcp.tool(
    description=(
        "Search memories by keyword or phrase. "
        "Use at the start of conversations to load relevant context. "
        "Returns most relevant memories ranked by match quality."
    )
)
def recall(query: str, limit: int = 5) -> dict:
    """
    Find relevant memories by keyword search.

    Args:
        query: Search term or phrase
        limit: Max results to return (default 5)
    """
    if not query.strip():
        return {"error": "Query cannot be empty"}

    limit = max(1, min(limit, 20))

    with get_db() as conn:
        # Full-text search
        try:
            rows = conn.execute(
                """
                SELECT m.*, rank
                FROM memories_fts
                JOIN memories m ON memories_fts.rowid = m.id
                WHERE memories_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query.strip(), limit)
            ).fetchall()
        except sqlite3.OperationalError:
            # Fallback to LIKE if FTS fails
            rows = conn.execute(
                "SELECT * FROM memories WHERE content LIKE ? LIMIT ?",
                (f"%{query}%", limit)
            ).fetchall()

        # Update access count
        if rows:
            ids = [r["id"] for r in rows]
            conn.execute(
                f"UPDATE memories SET access_count = access_count + 1 WHERE id IN ({','.join('?' * len(ids))})",
                ids
            )
            conn.commit()

    if not rows:
        return {
            "query": query,
            "results": [],
            "total": 0,
            "message": f"No memories found for '{query}'. Use remember() to save context."
        }

    return {
        "query": query,
        "results": [format_memory(r) for r in rows],
        "total": len(rows)
    }


@mcp.tool(
    description="List all memories, optionally filtered by category. Use to browse what Claude remembers."
)
def list_memories(category: str | None = None) -> dict:
    """
    List stored memories.

    Args:
        category: Optional filter - project, preference, person, fact, decision
    """
    with get_db() as conn:
        if category and category in VALID_CATEGORIES:
            rows = conn.execute(
                "SELECT * FROM memories WHERE category = ? ORDER BY created_at DESC",
                (category,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY category, created_at DESC"
            ).fetchall()

        total = conn.execute("SELECT COUNT(*) as n FROM memories").fetchone()["n"]

    # Group by category
    grouped: dict = {}
    for row in rows:
        cat = row["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(format_memory(row))

    return {
        "filter": category or "all",
        "memories": grouped,
        "shown": len(rows),
        "total": total
    }


@mcp.tool(
    description="Delete a specific memory by ID. Use when information is outdated or no longer relevant."
)
def forget(memory_id: int) -> dict:
    """
    Delete a memory by ID.

    Args:
        memory_id: The ID of the memory to delete (get IDs from recall() or list_memories())
    """
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()

        if not row:
            return {
                "error": f"Memory {memory_id} not found",
                "suggestion": "Use list_memories() to see all memory IDs"
            }

        content_preview = row["content"][:60] + "..." if len(row["content"]) > 60 else row["content"]
        conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

    return {
        "id": memory_id,
        "deleted": True,
        "content_preview": content_preview,
        "message": f"Memory {memory_id} deleted."
    }


@mcp.tool(
    description="Show memory statistics - total count, categories breakdown, most accessed memories."
)
def memory_stats() -> dict:
    """Show statistics about stored memories."""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as n FROM memories").fetchone()["n"]

        by_category = conn.execute(
            "SELECT category, COUNT(*) as count FROM memories GROUP BY category ORDER BY count DESC"
        ).fetchall()

        most_accessed = conn.execute(
            "SELECT * FROM memories ORDER BY access_count DESC LIMIT 5"
        ).fetchall()

        oldest = conn.execute(
            "SELECT created_at FROM memories ORDER BY created_at ASC LIMIT 1"
        ).fetchone()

    return {
        "total_memories": total,
        "db_path": str(DB_PATH),
        "by_category": {r["category"]: r["count"] for r in by_category},
        "most_accessed": [
            {"id": r["id"], "content": r["content"][:80], "access_count": r["access_count"]}
            for r in most_accessed
        ],
        "oldest_memory": format_time(oldest["created_at"]) if oldest else None
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
