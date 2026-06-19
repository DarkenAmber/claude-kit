"""
GitHub MCP Server

Allows Claude to read and write GitHub issues, PRs, and comments.
Closes the development loop: issue → code → PR without leaving Claude.
Token read from GITHUB_TOKEN environment variable.
"""

import os
import httpx
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastmcp import FastMCP

_client: httpx.AsyncClient | None = None
_token: str | None = None
_headers: dict | None = None


@asynccontextmanager
async def lifespan(server) -> AsyncIterator[None]:
    global _client, _token, _headers
    _token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not _token:
        raise RuntimeError(
            "GITHUB_TOKEN environment variable is required. "
            "Create one at https://github.com/settings/tokens"
        )
    _headers = {
        "Authorization": f"Bearer {_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    _client = httpx.AsyncClient(timeout=30.0, headers=_headers)
    try:
        yield
    finally:
        await _client.aclose()
        _client = None
        _token = None
        _headers = None


mcp = FastMCP(
    name="github-mcp",
    instructions=(
        "Read and write GitHub issues, PRs, and comments. "
        "Token is configured via GITHUB_TOKEN environment variable. "
        "repo format is 'owner/repo' (e.g. 'DarkenAmber/claude-kit'). "
        "Use github_list_issues to see open issues, github_create_pr to open a PR, "
        "github_create_issue to log bugs or features. "
        "Always confirm with user before creating or modifying anything."
    ),
    lifespan=lifespan
)

BASE = "https://api.github.com"

VALID_STATES = {"open", "closed", "all"}


def _validate_repo(repo: str) -> str | None:
    """Validate repo format 'owner/repo'. Returns error string or None if valid."""
    parts = repo.strip().split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return "repo must be in 'owner/repo' format (e.g. 'DarkenAmber/claude-kit')"
    if ".." in repo or repo.startswith("/"):
        return "invalid repo format"
    return None


async def _get(path: str, params: dict | None = None) -> dict:
    try:
        response = await _client.get(f"{BASE}{path}", params=params)
        if response.status_code == 404:
            return {"success": False, "error": "Not found - check repo name and permissions"}
        if response.status_code == 401:
            return {"success": False, "error": "Unauthorized - check GITHUB_TOKEN"}
        if not response.is_success:
            return {"success": False, "error": f"HTTP {response.status_code}", "detail": response.text[:200]}
        return {"success": True, "data": response.json()}
    except Exception:
        return {"success": False, "error": "Request failed - check server logs"}


async def _post(path: str, body: dict) -> dict:
    try:
        response = await _client.post(f"{BASE}{path}", json=body)
        if response.status_code == 401:
            return {"success": False, "error": "Unauthorized - check GITHUB_TOKEN"}
        if response.status_code == 403:
            return {"success": False, "error": "Forbidden - token lacks required permissions"}
        if response.status_code == 422:
            return {"success": False, "error": "Validation failed", "detail": response.json()}
        if not response.is_success:
            return {"success": False, "error": f"HTTP {response.status_code}", "detail": response.text[:200]}
        return {"success": True, "data": response.json()}
    except Exception:
        return {"success": False, "error": "Request failed - check server logs"}


# --- REPO ---

@mcp.tool(
    description="Get repository info - stars, forks, open issues count, description, default branch.",
    annotations={"readOnlyHint": True}
)
async def github_get_repo(repo: str) -> dict:
    """
    Get repository information.

    Args:
        repo: Repository in 'owner/repo' format (e.g. 'DarkenAmber/claude-kit')
    """
    err = _validate_repo(repo)
    if err: return {"success": False, "error": err}

    result = await _get(f"/repos/{repo}")
    if not result["success"]:
        return result
    d = result["data"]
    return {
        "success": True,
        "name": d["full_name"],
        "description": d.get("description", ""),
        "stars": d["stargazers_count"],
        "forks": d["forks_count"],
        "open_issues": d["open_issues_count"],
        "default_branch": d["default_branch"],
        "language": d.get("language", ""),
        "url": d["html_url"],
    }


# --- ISSUES ---

@mcp.tool(
    description="List open issues in a repository. Returns title, number, labels, and author.",
    annotations={"readOnlyHint": True}
)
async def github_list_issues(
    repo: str,
    state: str = "open",
    limit: int = 10,
) -> dict:
    """
    List repository issues.

    Args:
        repo: Repository in 'owner/repo' format
        state: 'open', 'closed', or 'all'
        limit: Max issues to return (default 10, max 30)
    """
    err = _validate_repo(repo)
    if err: return {"success": False, "error": err}
    if state not in VALID_STATES:
        return {"success": False, "error": f"state must be one of: {', '.join(VALID_STATES)}"}

    limit = max(1, min(limit, 30))
    result = await _get(f"/repos/{repo}/issues", params={"state": state, "per_page": limit})
    if not result["success"]:
        return result

    all_items = result["data"]
    issues = [i for i in all_items if "pull_request" not in i]

    result_dict = {
        "success": True,
        "repo": repo,
        "state": state,
        "issues": [
            {
                "number": i["number"],
                "title": i["title"],
                "state": i["state"],
                "author": i["user"]["login"],
                "labels": [l["name"] for l in i["labels"]],
                "comments": i["comments"],
                "created_at": i["created_at"][:10],
                "url": i["html_url"],
            }
            for i in issues
        ],
        "total": len(issues),
    }

    # Inform user if PRs were filtered out
    filtered = len(all_items) - len(issues)
    if filtered > 0:
        result_dict["note"] = (
            f"{filtered} pull request(s) were excluded from results. "
            f"Use github_list_prs to see pull requests."
        )

    return result_dict


@mcp.tool(
    description="Get full details of a specific issue including body and comments count.",
    annotations={"readOnlyHint": True}
)
async def github_get_issue(repo: str, issue_number: int) -> dict:
    """
    Get issue details.

    Args:
        repo: Repository in 'owner/repo' format
        issue_number: Issue number
    """
    err = _validate_repo(repo)
    if err: return {"success": False, "error": err}

    result = await _get(f"/repos/{repo}/issues/{issue_number}")
    if not result["success"]:
        return result
    d = result["data"]
    is_pr = "pull_request" in d
    return {
        "success": True,
        "number": d["number"],
        "title": d["title"],
        "state": d["state"],
        "type": "pull_request" if is_pr else "issue",
        "author": d["user"]["login"],
        "body": d.get("body") or "",
        "labels": [l["name"] for l in d["labels"]],
        "comments": d["comments"],
        "created_at": d["created_at"][:10],
        "url": d["html_url"],
    }


@mcp.tool(
    description="Create a new issue in a repository. Use for bug reports, feature requests, or tasks."
)
async def github_create_issue(
    repo: str,
    title: str,
    body: str = "",
    labels: list[str] | None = None,
) -> dict:
    """
    Create a new issue.

    Args:
        repo: Repository in 'owner/repo' format
        title: Issue title
        body: Issue description (Markdown supported)
        labels: Optional list of label names
    """
    err = _validate_repo(repo)
    if err: return {"success": False, "error": err}
    if not title.strip():
        return {"success": False, "error": "title cannot be empty"}

    payload = {"title": title.strip(), "body": body}
    if labels:
        payload["labels"] = labels

    result = await _post(f"/repos/{repo}/issues", payload)
    if not result["success"]:
        return result
    d = result["data"]
    return {
        "success": True,
        "number": d["number"],
        "title": d["title"],
        "url": d["html_url"],
        "message": f"Issue #{d['number']} created"
    }


@mcp.tool(
    description="Add a comment to an issue or pull request."
)
async def github_create_comment(
    repo: str,
    issue_number: int,
    body: str,
) -> dict:
    """
    Add a comment to an issue or PR.

    Args:
        repo: Repository in 'owner/repo' format
        issue_number: Issue or PR number
        body: Comment text (Markdown supported)
    """
    err = _validate_repo(repo)
    if err: return {"success": False, "error": err}
    if not body.strip():
        return {"success": False, "error": "comment body cannot be empty"}

    result = await _post(f"/repos/{repo}/issues/{issue_number}/comments", {"body": body})
    if not result["success"]:
        return result
    d = result["data"]
    return {
        "success": True,
        "comment_id": d["id"],
        "url": d["html_url"],
        "message": f"Comment added to #{issue_number}"
    }


# --- PULL REQUESTS ---

@mcp.tool(
    description="List pull requests in a repository.",
    annotations={"readOnlyHint": True}
)
async def github_list_prs(
    repo: str,
    state: str = "open",
    limit: int = 10,
) -> dict:
    """
    List pull requests.

    Args:
        repo: Repository in 'owner/repo' format
        state: 'open', 'closed', or 'all'
        limit: Max PRs to return (default 10)
    """
    err = _validate_repo(repo)
    if err: return {"success": False, "error": err}
    if state not in VALID_STATES:
        return {"success": False, "error": f"state must be one of: {', '.join(VALID_STATES)}"}

    limit = max(1, min(limit, 30))
    result = await _get(f"/repos/{repo}/pulls", params={"state": state, "per_page": limit})
    if not result["success"]:
        return result

    return {
        "success": True,
        "repo": repo,
        "prs": [
            {
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "author": pr["user"]["login"],
                "head": pr["head"]["ref"],
                "base": pr["base"]["ref"],
                "draft": pr.get("draft", False),
                "created_at": pr["created_at"][:10],
                "url": pr["html_url"],
            }
            for pr in result["data"]
        ],
        "total": len(result["data"]),
    }


@mcp.tool(
    description="Get full details of a specific pull request including description and review status.",
    annotations={"readOnlyHint": True}
)
async def github_get_pr(repo: str, pr_number: int) -> dict:
    """
    Get pull request details.

    Args:
        repo: Repository in 'owner/repo' format
        pr_number: PR number
    """
    err = _validate_repo(repo)
    if err: return {"success": False, "error": err}

    result = await _get(f"/repos/{repo}/pulls/{pr_number}")
    if not result["success"]:
        return result
    d = result["data"]
    return {
        "success": True,
        "number": d["number"],
        "title": d["title"],
        "state": d["state"],
        "author": d["user"]["login"],
        "body": d.get("body") or "",
        "head": d["head"]["ref"],
        "base": d["base"]["ref"],
        "draft": d.get("draft", False),
        "mergeable": d.get("mergeable"),
        "additions": d.get("additions", 0),
        "deletions": d.get("deletions", 0),
        "changed_files": d.get("changed_files", 0),
        "url": d["html_url"],
    }


@mcp.tool(
    description=(
        "Create a pull request. "
        "head branch must already exist in the repo with commits ahead of base. "
        "Use after pushing code changes to a feature branch."
    )
)
async def github_create_pr(
    repo: str,
    title: str,
    head: str,
    base: str,
    body: str = "",
    draft: bool = False,
) -> dict:
    """
    Create a pull request.

    Args:
        repo: Repository in 'owner/repo' format
        title: PR title
        head: Source branch name (the branch with your changes)
        base: Target branch name (usually 'main')
        body: PR description (Markdown supported)
        draft: Create as draft PR
    """
    err = _validate_repo(repo)
    if err: return {"success": False, "error": err}
    if not title.strip():
        return {"success": False, "error": "title cannot be empty"}
    if not head.strip() or not base.strip():
        return {"success": False, "error": "head and base branches are required"}

    result = await _post(f"/repos/{repo}/pulls", {
        "title": title.strip(),
        "head": head,
        "base": base,
        "body": body,
        "draft": draft,
    })
    if not result["success"]:
        return result
    d = result["data"]
    return {
        "success": True,
        "number": d["number"],
        "title": d["title"],
        "url": d["html_url"],
        "draft": d.get("draft", False),
        "message": f"PR #{d['number']} created"
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
