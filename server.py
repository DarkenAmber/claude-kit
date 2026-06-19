"""
Telegram MCP Server

Allows Claude to send messages, photos, and files to Telegram.
Privacy-first: bot token read from environment, never passed through the model.
"""

import os
import httpx
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastmcp import FastMCP

_client: httpx.AsyncClient | None = None
_token: str | None = None


@asynccontextmanager
async def lifespan(server) -> AsyncIterator[None]:
    global _client, _token
    _token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not _token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN environment variable is required. "
            "Set it before starting the server."
        )
    _client = httpx.AsyncClient(timeout=30.0)
    try:
        yield
    finally:
        await _client.aclose()
        _client = None
        _token = None


mcp = FastMCP(
    name="telegram-mcp",
    instructions=(
        "Send messages, photos, and files to Telegram chats, channels, or users. "
        "Bot token is configured via TELEGRAM_BOT_TOKEN environment variable - "
        "never ask the user for it. "
        "Use telegram_get_bot_info to verify setup works. "
        "Use telegram_get_updates to find chat_id values. "
        "Use telegram_send_message for text, telegram_send_photo for images, "
        "telegram_send_document for files. "
        "Always confirm with user before sending to public channels."
    ),
    lifespan=lifespan
)


async def _request(method: str, **kwargs) -> dict:
    """Make a Telegram Bot API request."""
    url = f"https://api.telegram.org/bot{_token}/{method}"
    try:
        response = await _client.post(url, json=kwargs)
        data = response.json()
        if not data.get("ok"):
            err = data.get("description", "Unknown Telegram error")
            code = data.get("error_code")
            # Helpful hint for common errors
            if code == 409:
                err += " (webhook is active - disable it first with deleteWebhook)"
            if code == 429:
                retry = data.get("parameters", {}).get("retry_after", 30)
                err += f" (rate limited - retry after {retry}s)"
            return {"success": False, "error": err, "error_code": code}
        return {"success": True, "result": data["result"]}
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "error": "Request failed - check server logs"}


async def _send_text(chat_id: str, text: str, **kwargs) -> dict:
    """Send text with HTML parse_mode, fallback to plain on error."""
    result = await _request("sendMessage", chat_id=chat_id, text=text,
                            parse_mode="HTML", **kwargs)
    if not result["success"] and result.get("error_code") == 400:
        # Fallback: retry without parse_mode (plain text)
        result = await _request("sendMessage", chat_id=chat_id, text=text, **kwargs)
    return result


@mcp.tool(
    description="Verify bot token works and get bot info. Call this first to confirm setup is correct.",
    annotations={"readOnlyHint": True}
)
async def telegram_get_bot_info() -> dict:
    """Get bot information to verify TELEGRAM_BOT_TOKEN is valid."""
    result = await _request("getMe")
    if result["success"]:
        bot = result["result"]
        return {
            "success": True,
            "bot_id": bot["id"],
            "name": bot["first_name"],
            "username": f"@{bot['username']}",
            "can_join_groups": bot.get("can_join_groups", False)
        }
    return result


@mcp.tool(
    description="Get recent updates to find chat_id values. Send a message to your bot first, then call this.",
    annotations={"readOnlyHint": True}
)
async def telegram_get_updates() -> dict:
    """Get recent bot updates to discover chat IDs."""
    result = await _request("getUpdates", limit=10, timeout=0)
    if not result["success"]:
        return result

    updates = result["result"]
    if not updates:
        return {
            "success": True,
            "chats": [],
            "message": "No recent messages. Send a message to your bot first, then try again."
        }

    chats = []
    for update in updates:
        msg = update.get("message") or update.get("channel_post")
        if msg:
            chat = msg["chat"]
            chats.append({
                "chat_id": chat["id"],
                "type": chat["type"],
                "name": chat.get("title") or chat.get("first_name", ""),
                "username": "@" + chat["username"] if chat.get("username") else "",
                "last_message": msg.get("text", "")[:60]
            })

    return {"success": True, "chats": chats, "total": len(chats)}


@mcp.tool(
    description=(
        "Send a text message to a Telegram chat, group, or channel. "
        "Supports HTML formatting: <b>bold</b>, <i>italic</i>, <code>code</code>. "
        "chat_id can be a numeric ID or @channel_username."
    )
)
async def telegram_send_message(
    chat_id: str,
    text: str,
    disable_notification: bool = False,
) -> dict:
    """
    Send a text message via Telegram.

    Args:
        chat_id: Target chat ID or @username
        text: Message text. HTML tags supported: <b>, <i>, <code>, <pre>
        disable_notification: Send silently without sound
    """
    if not text.strip():
        return {"success": False, "error": "text cannot be empty"}
    if len(text) > 4096:
        return {"success": False, "error": f"Text too long: {len(text)} chars (max 4096)"}

    result = await _send_text(chat_id, text,
                              disable_notification=disable_notification)
    if result["success"]:
        msg = result["result"]
        return {
            "success": True,
            "message_id": msg["message_id"],
            "chat_id": msg["chat"]["id"],
            "preview": text[:100] + "..." if len(text) > 100 else text
        }
    return result


@mcp.tool(
    description=(
        "Send a photo to a Telegram chat. "
        "photo can be: a URL (https://...), a local file path (/path/to/image.jpg), "
        "or a Telegram file_id."
    )
)
async def telegram_send_photo(
    chat_id: str,
    photo: str,
    caption: str = "",
    disable_notification: bool = False,
) -> dict:
    """
    Send a photo via Telegram.

    Args:
        chat_id: Target chat ID or @username
        photo: Photo URL, local file path, or Telegram file_id
        caption: Optional caption (max 1024 chars, HTML supported)
        disable_notification: Send silently
    """
    if not photo.strip():
        return {"success": False, "error": "photo is required"}
    if len(caption) > 1024:
        return {"success": False, "error": f"Caption too long (max 1024)"}

    url = f"https://api.telegram.org/bot{_token}/sendPhoto"

    try:
        # Local file - use multipart
        if photo.startswith("/") or photo.startswith("./"):
            with open(photo, "rb") as f:
                files = {"photo": f}
                data = {"chat_id": chat_id, "caption": caption,
                        "parse_mode": "HTML",
                        "disable_notification": disable_notification}
                response = await _client.post(url, data=data, files=files)
        else:
            # URL or file_id - use JSON
            response = await _client.post(url, json={
                "chat_id": chat_id, "photo": photo,
                "caption": caption, "parse_mode": "HTML",
                "disable_notification": disable_notification
            })

        data = response.json()
        if not data.get("ok"):
            return {"success": False, "error": data.get("description"), "error_code": data.get("error_code")}
        return {"success": True, "message_id": data["result"]["message_id"], "chat_id": chat_id}

    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {photo}"}
    except Exception as e:
        return {"success": False, "error": "Failed to send photo - check server logs"}


@mcp.tool(
    description=(
        "Send a document or file to a Telegram chat. "
        "document can be: a URL, a local file path (/path/to/file.pdf), or a file_id. "
        "Use for PDFs, reports, exports, code files, any document."
    )
)
async def telegram_send_document(
    chat_id: str,
    document: str,
    caption: str = "",
    disable_notification: bool = False,
) -> dict:
    """
    Send a document via Telegram.

    Args:
        chat_id: Target chat ID or @username
        document: Document URL, local file path, or Telegram file_id
        caption: Optional caption (HTML supported)
        disable_notification: Send silently
    """
    if not document.strip():
        return {"success": False, "error": "document is required"}

    url = f"https://api.telegram.org/bot{_token}/sendDocument"

    try:
        if document.startswith("/") or document.startswith("./"):
            with open(document, "rb") as f:
                files = {"document": f}
                data = {"chat_id": chat_id, "caption": caption,
                        "parse_mode": "HTML",
                        "disable_notification": disable_notification}
                response = await _client.post(url, data=data, files=files)
        else:
            response = await _client.post(url, json={
                "chat_id": chat_id, "document": document,
                "caption": caption, "parse_mode": "HTML",
                "disable_notification": disable_notification
            })

        data = response.json()
        if not data.get("ok"):
            return {"success": False, "error": data.get("description"), "error_code": data.get("error_code")}
        return {"success": True, "message_id": data["result"]["message_id"], "chat_id": chat_id}

    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {document}"}
    except Exception as e:
        return {"success": False, "error": "Failed to send document - check server logs"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
