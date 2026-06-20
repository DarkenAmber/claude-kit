# claude-kit

> Build software with Claude like a system, not prompts.

Every time you start a new chat with Claude, it forgets everything and defaults to bad habits — over-engineering simple tools, ignoring your preferences, starting from scratch.

**Skills fix the habits. MCP fixes the memory.**

---

## Why this exists

Claude is powerful. But without context it defaults to complexity — React for a calculator, a database for a to-do list, weeks of planning for a weekend project.

`claude-kit` gives Claude the context it needs to work the way you think. One file changes how it reasons. One server gives it memory. Together they turn Claude from a generic assistant into a specialized tool that knows your workflow.

---

## How it works

```
You
 ↓
Claude Code / Cursor / Claude.ai
 ↓
Skills        — tell Claude how to think
 ↓
Memory        — what to remember between sessions
 ↓
MCP Servers   — what tools to use
 ↓
Ship faster
```

---

## Quick start (5 minutes)

**What is CLAUDE.md?** It is a file that Claude Code reads automatically when you start it in a project. Skills go inside this file — that is how Claude learns your rules.

```bash
# 1. Pick a skill and install it
curl -o CLAUDE.md https://raw.githubusercontent.com/DarkenAmber/claude-kit/main/skills/ship-it/SKILL.md

# 2. Start Claude Code in your project folder
claude

# 3. Claude now ships instead of over-engineers
```

That is it. No config, no registration, no cloud.

---

## What's inside

```
claude-kit/
├── skills/   — copy SKILL.md to your project. No install needed.
└── mcp/      — run server.py to give Claude new capabilities.
```

| Type | What it does | How to use |
|------|-------------|------------|
| 📋 Skill | Changes how Claude thinks | Copy SKILL.md to project |
| 🔌 MCP | Gives Claude new capabilities | Run server.py |

---

## Skills

| Skill | Description | Best for |
|-------|-------------|---------|
| [single-file-app](./skills/single-file-app/SKILL.md) | Build complete web tools as a single HTML file | Calculators, dashboards, generators |
| [ship-it](./skills/ship-it/SKILL.md) | Bias toward shipping over planning | MVPs, side projects, validation |
| [flutter-app](./skills/flutter-app/SKILL.md) | Build Flutter Android apps - offline-first, Google Drive sync | Mobile apps, cross-platform tools |
| [indie-builder](./skills/indie-builder/SKILL.md) | Build and launch micro-SaaS as a solo developer | Pricing, distribution, first revenue |
| [telegram-bot](./skills/telegram-bot/SKILL.md) | Build Telegram bots with aiogram 3.x - webhook, FSM, deployment | Notifications, automation, bots |

### Install a skill

**Claude Code** — saves as `CLAUDE.md` in your project root. Claude reads it automatically.
```bash
# single skill
curl -o CLAUDE.md https://raw.githubusercontent.com/DarkenAmber/claude-kit/main/skills/ship-it/SKILL.md

# combine multiple skills into one file
curl https://raw.githubusercontent.com/DarkenAmber/claude-kit/main/skills/single-file-app/SKILL.md > CLAUDE.md
curl https://raw.githubusercontent.com/DarkenAmber/claude-kit/main/skills/ship-it/SKILL.md >> CLAUDE.md
```

**Cursor / Windsurf** — saves as `.cursorrules` in your project root.
```bash
curl https://raw.githubusercontent.com/DarkenAmber/claude-kit/main/skills/single-file-app/SKILL.md > .cursorrules
```

**Claude.ai Projects** — go to your Project → Settings → Project Instructions → paste the contents of any `SKILL.md`.

---

## MCP Servers

| Server | Description | Requires |
|--------|-------------|---------|
| [skills-server](./mcp/skills-server/) | Load and apply skills automatically | Python |
| [memory-kit](./mcp/memory-kit/) | Persistent local memory between sessions | Python |
| [telegram](./mcp/telegram/) | Send messages, photos, and files to Telegram | Python + bot token |
| [github](./mcp/github/) | Read issues, create PRs, manage repos | Python + GitHub token |

### Install MCP servers

**Step 1 — Clone the repo**
```bash
git clone https://github.com/DarkenAmber/claude-kit.git
cd claude-kit
```

**Step 2 — Install a server**
```bash
# skills-server
cd mcp/skills-server
pip install -r requirements.txt
python server.py

# memory-kit
cd mcp/memory-kit
pip install -r requirements.txt
python server.py

# telegram (requires bot token from @BotFather)
cd mcp/telegram
pip install -r requirements.txt
TELEGRAM_BOT_TOKEN=your_token_here python server.py

# github (requires token from github.com/settings/tokens)
cd mcp/github
pip install -r requirements.txt
GITHUB_TOKEN=your_token_here python server.py
```

**Step 3 — Add to Claude Desktop**

Open `claude_desktop_config.json`:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "claude-kit-skills": {
      "command": "python",
      "args": ["C:/Users/yourname/claude-kit/mcp/skills-server/server.py"]
    },
    "claude-kit-memory": {
      "command": "python",
      "args": ["C:/Users/yourname/claude-kit/mcp/memory-kit/server.py"]
    },
    "claude-kit-telegram": {
      "command": "python",
      "args": ["C:/Users/yourname/claude-kit/mcp/telegram/server.py"],
      "env": {
        "TELEGRAM_BOT_TOKEN": "your_token_here"
      }
    },
    "claude-kit-github": {
      "command": "python",
      "args": ["C:/Users/yourname/claude-kit/mcp/github/server.py"],
      "env": {
        "GITHUB_TOKEN": "your_token_here"
      }
    }
  }
}
```

> Replace `C:/Users/yourname/claude-kit/` with your actual path.
> On Mac use `/Users/yourname/claude-kit/` instead.

Restart Claude Desktop after editing the config.

---

## Built with claude-kit

| Project | Skills used |
|---------|------------|
| [DarkenAmber IT Tools](https://github.com/DarkenAmber/DarkenAmber-it-tools) | single-file-app |
| [ZeroOffice](https://github.com/DarkenAmber/ZeroOffice) | single-file-app |
| [PrivacyKit](https://github.com/DarkenAmber/privacykit) | single-file-app |
| ElectroKit | single-file-app + ship-it |

---

## Contributing

New skills and MCP servers welcome. Each skill should:
- Solve one specific problem
- Have a clear `When to Use` and `Do NOT use when` section
- Include a pre-ship checklist
- Pass a code review before merging

---

## License

MIT - use it, modify it, share it.

---

*If this helped you ship something - star the repo ⭐*
