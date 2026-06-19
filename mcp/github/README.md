# GitHub MCP

> Close the development loop. Read issues, create PRs, add comments — without leaving Claude.

## Tools

| Tool | Description |
|------|-------------|
| `github_get_repo` | Get repo info - stars, issues, branches |
| `github_list_issues` | List open/closed issues |
| `github_get_issue` | Get issue details and body |
| `github_create_issue` | Create a new issue |
| `github_create_comment` | Comment on issue or PR |
| `github_list_prs` | List pull requests |
| `github_get_pr` | Get PR details |
| `github_create_pr` | Create a pull request |

## Setup

**1. Create a GitHub token**
- Go to https://github.com/settings/tokens
- Create token with `repo` scope

**2. Install**
```bash
cd mcp/github
pip install -r requirements.txt
```

**3. Add to Claude Desktop**
```json
{
  "mcpServers": {
    "claude-kit-github": {
      "command": "python",
      "args": ["/path/to/claude-kit/mcp/github/server.py"],
      "env": {
        "GITHUB_TOKEN": "your_token_here"
      }
    }
  }
}
```

## Usage

```
"Show me open issues in DarkenAmber/claude-kit"
→ github_list_issues("DarkenAmber/claude-kit")

"Create an issue for the memory-kit bug"
→ github_create_issue("DarkenAmber/claude-kit", "memory-kit: cache not clearing", "...")

"Create a PR from feature branch to main"
→ github_create_pr("DarkenAmber/claude-kit", "Add docs-writer skill", "feature/docs-writer", "main")
```

## Required token scopes

- `repo` — full access to private and public repos
- `public_repo` — only public repos (enough for open source)
