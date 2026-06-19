# claude-kit

> Stop re-explaining yourself to Claude. Skills and MCP servers that make Claude work the way you think.

Every time you start a new chat with Claude, it forgets everything and defaults to bad habits — over-engineering simple tools, ignoring your preferences, starting from scratch.

**Skills fix the habits. MCP fixes the memory.**

One file, five minutes, Claude starts working the way you want.

---

## What's inside

```
claude-kit/
├── skills/        — copy SKILL.md to your project. No install needed.
└── mcp/           — run server.py to give Claude new capabilities.
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
| [telegram-bot](./skills/telegram-bot/SKILL.md) | Build Telegram bots with aiogram 3.x - webhook, FSM, deployment | Notifications, automation, small business tools |

### Install a skill

**Claude Code:**
```bash
# single skill
curl -o CLAUDE.md https://raw.githubusercontent.com/DarkenAmber/claude-kit/main/skills/single-file-app/SKILL.md

# combine multiple skills
curl https://raw.githubusercontent.com/DarkenAmber/claude-kit/main/skills/single-file-app/SKILL.md > CLAUDE.md
curl https://raw.githubusercontent.com/DarkenAmber/claude-kit/main/skills/ship-it/SKILL.md >> CLAUDE.md
```

**Cursor / Windsurf:**
```bash
curl https://raw.githubusercontent.com/DarkenAmber/claude-kit/main/skills/single-file-app/SKILL.md > .cursorrules
```

**Claude.ai Projects:**
Copy the contents of any `SKILL.md` into your **Project Instructions**.

---

## MCP Servers

| Server | Description | Requires |
|--------|-------------|---------|
| [skills-server](./mcp/skills-server/) | Load and apply skills automatically | Python |
| [memory-kit](./mcp/memory-kit/) | Persistent local memory between sessions | Python |
| [telegram](./mcp/telegram/) | Send messages, photos, and files to Telegram | Python + bot token |

### Install MCP servers

```bash
# skills-server
cd mcp/skills-server
pip install -r requirements.txt
python server.py

# memory-kit
cd mcp/memory-kit
pip install -r requirements.txt
python server.py

# telegram (set bot token first)
export TELEGRAM_BOT_TOKEN=your_token_here
cd mcp/telegram
pip install -r requirements.txt
python server.py
```

**Add to Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "claude-kit-skills": {
      "command": "python",
      "args": ["/path/to/claude-kit/mcp/skills-server/server.py"]
    },
    "claude-kit-memory": {
      "command": "python",
      "args": ["/path/to/claude-kit/mcp/memory-kit/server.py"]
    },
    "claude-kit-telegram": {
      "command": "python",
      "args": ["/path/to/claude-kit/mcp/telegram/server.py"],
      "env": {
        "TELEGRAM_BOT_TOKEN": "your_token_here"
      }
    }
  }
}
```

---

## Built with claude-kit

| Project | Skills used |
|---------|------------|
| [DarkenAmber IT Tools](https://github.com/DarkenAmber/DarkenAmber-it-tools) | single-file-app |
| [ZeroOffice](https://github.com/DarkenAmber/ZeroOffice) | single-file-app |
| [PrivacyKit](https://github.com/DarkenAmber/privacykit) | single-file-app |
| ElectroKit | single-file-app + ship-it |

---

## License

MIT - use it, modify it, share it.

---

*If this helped you ship something - star the repo*
