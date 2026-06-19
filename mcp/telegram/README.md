# Telegram MCP

> Let Claude send messages, photos, and files to Telegram directly from your conversation.
> Privacy-first: your bot token stays local. No third-party services.

## Tools

| Tool | Description |
|------|-------------|
| `get_bot_info(token)` | Verify bot token works |
| `get_updates(token)` | Find chat IDs |
| `send_message(...)` | Send text with Markdown |
| `send_photo(...)` | Send photo with caption |
| `send_document(...)` | Send file or PDF |

## Quick Start

**1. Create a bot**
- Open Telegram, find @BotFather
- Send `/newbot`, follow instructions
- Copy your bot token

**2. Find your chat_id**
- Send any message to your bot
- Call `get_updates(token)` — Claude will show your chat_id

**3. Install**
```bash
cd mcp/telegram
pip install -r requirements.txt
```

**4. Add to Claude Desktop**
```json
{
  "mcpServers": {
    "telegram": {
      "command": "python",
      "args": ["/path/to/claude-kit/mcp/telegram/server.py"]
    }
  }
}
```

## Usage examples

```
"Send me a summary of what we did today to Telegram"
→ send_message(token, chat_id, "Today's summary: ...")

"Send this report to my channel"
→ send_document(token, "@mychannel", "report.pdf")

"Notify me when the task is done"
→ send_message(token, chat_id, "✅ Task completed!")
```

## Security

- Bot token is passed per-request - never stored by the server
- Only your bot can send to chats it's a member of
- For channels: bot must be added as admin
