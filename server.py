"""
claude-skills MCP Server

Allows Claude to automatically load and apply skills from the DarkenAmber/claude-skills repository.
"""

import time
import re
import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import httpx
from fastmcp import FastMCP

BASE_URL = "https://raw.githubusercontent.com/DarkenAmber/claude-skills/main"

SKILLS = {
    "single-file-app": {
        "name": "single-file-app",
        "description": "Build complete web tools as a single HTML file - vanilla JS, inline CSS, localStorage, offline-first.",
        "tags": ["html", "vanilla-js", "offline", "single-file", "no-framework", "tool", "calculator", "generator", "dashboard", "editor", "converter", "tracker", "browser", "invoice", "web"],
        "version": "1.3",
        "use_when": "Building calculators, dashboards, generators, or any standalone browser tool without a backend."
    },
    "ship-it": {
        "name": "ship-it",
        "description": "Bias toward shipping over planning when building an early-stage MVP or prototype before first revenue.",
        "tags": ["productivity", "indie-dev", "micro-saas", "mvp", "shipping", "launch", "startup", "validate", "prototype", "fast", "quick", "saas"],
        "version": "1.3",
        "use_when": "Validating an idea with no paying users yet. Not for production systems with payments, auth, or licensing."
    }
}

# TTL cache with version key
_cache: dict = {}
_CACHE_TTL = 600  # 10 minutes
_fetch_locks: dict[str, asyncio.Lock] = {}

# Lazy HTTP client
_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(server) -> AsyncIterator[None]:
    """Manage HTTP client lifecycle."""
    global _client
    _client = httpx.AsyncClient(timeout=10.0)
    try:
        yield
    finally:
        await _client.aclose()
        _client = None


mcp = FastMCP(
    name="claude-skills",
    instructions="Load and apply Claude skills from the DarkenAmber/claude-skills repository. Use list_skills to see available skills, get_skill to load one, search_skills to find by keyword, export_skill to get a ready-to-use file.",
    lifespan=lifespan
)


def _cache_get(key: str) -> str | None:
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < _CACHE_TTL:
        return entry["value"]
    return None


def _cache_set(key: str, value: str) -> None:
    _cache[key] = {"value": value, "ts": time.time()}


def _word_match(text: str, query: str) -> bool:
    """Match whole words only — avoids 'form' matching 'information'."""
    if not query.strip():
        return False
    pattern = r'\b' + re.escape(query.lower()) + r'\b'
    return bool(re.search(pattern, text.lower()))


async def _fetch_skill_md(name: str) -> str:
    """
    Fetch skill content from GitHub with caching and stampede protection.
    Raises ValueError on fetch failure.
    """
    version = SKILLS[name]["version"]
    cache_key = f"{name}@{version}"

    cached = _cache_get(cache_key)
    if cached:
        return cached

    # Stampede protection - one request per skill at a time
    if name not in _fetch_locks:
        _fetch_locks[name] = asyncio.Lock()

    async with _fetch_locks[name]:
        # Re-check after acquiring lock
        cached = _cache_get(cache_key)
        if cached:
            return cached

        url = f"{BASE_URL}/{name}/SKILL.md"
        try:
            response = await _client.get(url)
            response.raise_for_status()
            content = response.text
        except httpx.HTTPStatusError as e:
            raise ValueError(f"HTTP {e.response.status_code} fetching {url}")
        except httpx.RequestError as e:
            raise ValueError(f"Network error fetching {url}: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error fetching {url}: {e}")

        _cache_set(cache_key, content)
        return content


@mcp.tool(
    description="List all available Claude skills with descriptions and tags. Call this first to discover available skills."
)
def list_skills() -> dict:
    """Returns all available skills with metadata."""
    return {
        "skills": [
            {
                "name": s["name"],
                "description": s["description"],
                "tags": s["tags"],
                "version": s["version"],
                "use_when": s["use_when"]
            }
            for s in SKILLS.values()
        ],
        "total": len(SKILLS),
        "install_docs": "https://github.com/DarkenAmber/claude-skills"
    }


@mcp.tool(
    description="Load the full content of a specific skill by name. Returns complete SKILL.md content ready to apply."
)
async def get_skill(name: str) -> dict:
    """
    Load a skill by name.

    Args:
        name: Skill name (e.g. 'single-file-app', 'ship-it')
    """
    if name not in SKILLS:
        return {
            "error": f"Skill '{name}' not found.",
            "available": list(SKILLS.keys())
        }

    try:
        content = await _fetch_skill_md(name)
    except ValueError as e:
        return {"error": str(e)}

    meta = SKILLS[name]
    return {
        "name": meta["name"],
        "version": meta["version"],
        "description": meta["description"],
        "content": content,
        "instruction": f"Apply this skill for the current task. Rules in this skill now govern '{name}' related work."
    }


@mcp.tool(
    description="Search skills by keyword or tag. Returns ranked matches."
)
def search_skills(query: str) -> dict:
    """
    Search skills by keyword or tag.

    Args:
        query: Search keyword (e.g. 'html', 'offline', 'mvp', 'shipping')
    """
    if not query.strip():
        return {"error": "Query cannot be empty", "suggestion": "Use list_skills() to see all skills."}

    matches = []
    for skill in SKILLS.values():
        score = 0
        if _word_match(skill["name"], query): score += 3
        if _word_match(skill["description"], query): score += 2
        for tag in skill["tags"]:
            if _word_match(tag, query): score += 2
        if _word_match(skill["use_when"], query): score += 1

        if score > 0:
            matches.append({
                "name": skill["name"],
                "description": skill["description"],
                "tags": skill["tags"],
                "version": skill["version"],
                "relevance_score": score
            })

    matches.sort(key=lambda x: x["relevance_score"], reverse=True)

    if not matches:
        return {
            "query": query,
            "matches": [],
            "message": f"No skills found for '{query}'. Try list_skills() to see all skills."
        }

    return {"query": query, "matches": matches, "total": len(matches)}


@mcp.tool(
    description="Get skill recommendations for a task. Analyzes task and suggests relevant skills based on skill tags and descriptions."
)
def recommend_skills(task: str) -> dict:
    """
    Get skill recommendations for a task.

    Args:
        task: Description of what you are building
    """
    if not task.strip():
        return {"error": "Task description cannot be empty"}

    scored = []
    for skill in SKILLS.values():
        score = 0
        # Match against tags
        for tag in skill["tags"]:
            if _word_match(task, tag):
                score += 2
        # Match against use_when
        words = task.lower().split()
        for word in words:
            if len(word) > 3 and _word_match(skill["use_when"], word):
                score += 1

        if score > 0:
            scored.append((score, skill))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return {
            "task": task,
            "recommendations": [],
            "message": "No specific skills matched. Use list_skills() to browse all available skills."
        }

    recommendations = []
    top_score = scored[0][0]
    for score, skill in scored:
        recommendations.append({
            "skill": skill["name"],
            "reason": skill["use_when"],
            "priority": "primary" if score == top_score else "secondary"
        })

    return {
        "task": task,
        "recommendations": recommendations,
        "next_step": f"Call get_skill('{recommendations[0]['skill']}') to load the top skill."
    }


@mcp.tool(
    description=(
        "Export a skill as a ready-to-use file. "
        "format: 'claude' (CLAUDE.md), 'cursor' (.cursorrules), 'json' (with metadata), 'combined' (merge multiple skills). "
        "combine_with: list of additional skill names to merge (only for 'combined' format)."
    )
)
async def export_skill(
    name: str,
    format: str = "claude",
    combine_with: list[str] | None = None
) -> dict:
    """
    Export a skill as a ready-to-use file.

    Args:
        name: Primary skill name
        format: 'claude', 'cursor', 'json', or 'combined'
        combine_with: Additional skills to merge (for 'combined' format only)
    """
    valid_formats = {"claude", "cursor", "json", "combined"}
    if format not in valid_formats:
        return {"error": f"Invalid format '{format}'", "valid_formats": list(valid_formats)}

    if name not in SKILLS:
        return {"error": f"Skill '{name}' not found.", "available": list(SKILLS.keys())}

    try:
        content = await _fetch_skill_md(name)
    except ValueError as e:
        return {"error": str(e)}

    # Combined format
    if format == "combined":
        skills_to_merge = [name] + [s for s in (combine_with or []) if s in SKILLS]
        merged_parts = []
        failed = []

        for skill_name in skills_to_merge:
            try:
                skill_content = await _fetch_skill_md(skill_name)
                merged_parts.append(f"# === {skill_name} ===\n\n{skill_content}")
            except ValueError as e:
                failed.append({"skill": skill_name, "error": str(e)})

        if not merged_parts:
            return {"error": "All skills failed to fetch", "failed": failed}

        header = (
            f"# Combined Claude Skills\n"
            f"# Skills: {', '.join(skills_to_merge)}\n"
            f"# Source: https://github.com/DarkenAmber/claude-skills\n\n"
        )

        result = {
            "format": "combined",
            "skills": skills_to_merge,
            "filename": "CLAUDE.md",
            "install_command": "Save as CLAUDE.md in your project root",
            "content": header + "\n\n---\n\n".join(merged_parts)
        }
        if failed:
            result["failed"] = failed
            result["warning"] = f"{len(failed)} skill(s) failed to fetch"
        return result

    # JSON format
    if format == "json":
        meta = SKILLS[name]
        return {
            "format": "json",
            "filename": f"{name}.skill.json",
            "content": {
                "name": meta["name"],
                "version": meta["version"],
                "description": meta["description"],
                "tags": meta["tags"],
                "use_when": meta["use_when"],
                "source": f"{BASE_URL}/{name}/SKILL.md",
                "skill_content": content
            }
        }

    # Claude / Cursor
    filename = "CLAUDE.md" if format == "claude" else ".cursorrules"
    return {
        "format": format,
        "skill": name,
        "version": SKILLS[name]["version"],
        "filename": filename,
        "install_command": f"curl -o {filename} {BASE_URL}/{name}/SKILL.md",
        "content": content,
        "instruction": f"Save as '{filename}' in your project root to activate the skill."
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
