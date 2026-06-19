---
name: telegram-bot
description: Build Telegram bots with Python or Node.js - webhooks, commands, inline keyboards, FSM for conversations, and deployment. Use when creating bots for notifications, automation, small business tools, or user interaction.
tags:
  - telegram
  - bot
  - python
  - aiogram
  - automation
  - webhook
  - notifications
version: 1.1
---

# Telegram Bot - Claude Skill

> Webhook over polling. FSM over spaghetti handlers.
> Build bots that are reliable, maintainable, and actually useful.

---

## When to Use This Skill

Use when:
- Building a Telegram bot from scratch
- Adding bot functionality to an existing project
- Creating notification systems via Telegram
- Building small business tools (booking, orders, support)
- Automating workflows with Telegram as the interface

Do NOT use when:
- Building a full web app (Telegram is the interface, not the product)
- The bot needs real-time video/audio processing
- You need complex payment systems (use dedicated payment services)
- The audience is not on Telegram

---

## Core Philosophy

A Telegram bot is an interface, not a product.
The product is the value it delivers - notifications, automation, data access.
Keep the bot simple. Keep the logic in your code, not in Telegram's servers.

---

## Rules

### 1. Webhook over polling - always in production
- Polling: your server constantly asks Telegram "any updates?"
- Webhook: Telegram calls your server when something happens
- Polling is fine for local development only
- Webhook is faster, cheaper, more reliable in production

### 2. Use aiogram 3.x for Python
- Best async framework for Telegram bots in Python
- Built-in FSM (Finite State Machine) for conversations
- Middleware support for auth, logging, rate limiting
- Router-based architecture - clean and scalable

### 3. FSM for multi-step conversations
- Never use global variables to track conversation state
- Never nest handlers inside handlers
- Always use FSM states for any multi-step flow

### 4. One bot token per environment
- Development: separate bot token
- Production: separate bot token
- Never use production token in development
- Store tokens in .env, never in code

### 5. Handle errors gracefully
- Every handler must have error handling
- User should always get a response - never leave them waiting
- Log errors server-side, show friendly message to user

---

## Project Structure

```
bot/
├── main.py               # Entry point, webhook/polling setup
├── config.py             # Settings from environment
├── handlers/
│   ├── __init__.py
│   ├── start.py          # /start, /help commands
│   ├── main_menu.py      # Main flow handlers
│   └── admin.py          # Admin-only handlers
├── states/
│   └── forms.py          # FSM state groups
├── keyboards/
│   ├── inline.py         # Inline keyboards
│   └── reply.py          # Reply keyboards
├── middlewares/
│   └── auth.py           # User auth/whitelist
├── services/
│   └── database.py       # Data storage
├── .env                  # Tokens and config (never commit)
└── requirements.txt
```

---

## Basic Setup (aiogram 3.x)

```python
# config.py
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    BOT_TOKEN: str
    WEBHOOK_URL: str = ""
    WEBHOOK_SECRET: str = ""  # secret token for webhook security
    ADMIN_IDS: list[int] = []

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def split_ids(cls, v):
        # Allows both "123,456" and [123,456] formats in .env
        if isinstance(v, str):
            return [int(x) for x in v.split(",") if x.strip()]
        return v

    class Config:
        env_file = ".env"

settings = Settings()
```

```python
# main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import settings
from handlers import start, main_menu, add_car, admin

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Register ALL routers here - missing router = dead handler
dp.include_routers(
    start.router,
    main_menu.router,
    add_car.router,   # FSM handlers
    admin.router,     # Admin commands
)

def main():
    if settings.WEBHOOK_URL:
        # Production - webhook
        # IMPORTANT: web.run_app() manages its own event loop
        # Do NOT wrap in asyncio.run() - causes RuntimeError

        async def on_startup(app):
            await bot.set_webhook(
                f"{settings.WEBHOOK_URL}/webhook",
                secret_token=settings.WEBHOOK_SECRET,  # security
            )

        app = web.Application()
        app.on_startup.append(on_startup)
        SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=settings.WEBHOOK_SECRET,  # validates incoming requests
        ).register(app, path="/webhook")
        setup_application(app, dp, bot=bot)
        web.run_app(app, host="0.0.0.0", port=8080)  # blocking - no asyncio.run()
    else:
        # Development - polling
        asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    main()  # NOT asyncio.run(main())
```

---

## Commands Handler

```python
# handlers/start.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from keyboards.reply import main_menu_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"Hello, {message.from_user.first_name}!\n"
        "Choose an option:",
        reply_markup=main_menu_kb()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Available commands:\n"
        "/start - Main menu\n"
        "/help - This message"
    )
```

---

## FSM - Multi-step Conversations

```python
# states/forms.py
from aiogram.fsm.state import State, StatesGroup

class CarForm(StatesGroup):
    waiting_for_plate = State()
    waiting_for_vin   = State()
    waiting_for_year  = State()
    confirm           = State()
```

```python
# handlers/add_car.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from states.forms import CarForm
from keyboards.inline import confirm_kb

router = Router()

@router.message(F.text == "Add car")
async def add_car_start(message: Message, state: FSMContext):
    await state.set_state(CarForm.waiting_for_plate)
    await message.answer("Enter license plate:")

@router.message(CarForm.waiting_for_plate)
async def process_plate(message: Message, state: FSMContext):
    await state.update_data(plate=message.text)
    await state.set_state(CarForm.waiting_for_vin)
    await message.answer("Enter VIN code:")

@router.message(CarForm.waiting_for_vin)
async def process_vin(message: Message, state: FSMContext):
    await state.update_data(vin=message.text)
    data = await state.get_data()
    await state.set_state(CarForm.confirm)
    await message.answer(
        f"Confirm:\nPlate: {data['plate']}\nVIN: {message.text}",
        reply_markup=confirm_kb()
    )

@router.callback_query(CarForm.confirm, F.data == "confirm_yes")
async def process_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # save car to database
    await state.clear()
    await callback.answer("Car added!")  # always answer callback first
    # callback.message can be InaccessibleMessage for old messages
    if callback.message and hasattr(callback.message, "edit_text"):
        await callback.message.edit_text("Car added successfully!")
    else:
        await callback.bot.send_message(callback.from_user.id, "Car added successfully!")
```

---

## Keyboards

```python
# keyboards/reply.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Add car"), KeyboardButton(text="My cars")],
            [KeyboardButton(text="Settings")],
        ],
        resize_keyboard=True
    )
```

```python
# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Yes", callback_data="confirm_yes"),
            InlineKeyboardButton(text="No",  callback_data="confirm_no"),
        ]
    ])
```

---

## Middleware - Auth

```python
# middlewares/auth.py
from aiogram import BaseMiddleware
from aiogram.types import Message
from config import settings

class AdminMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        if event.from_user.id not in settings.ADMIN_IDS:
            await event.answer("Access denied.")
            return
        return await handler(event, data)
```

Register middleware on the admin router - not globally:

```python
# handlers/admin.py
from aiogram import Router
from middlewares.auth import AdminMiddleware

router = Router()
router.message.middleware(AdminMiddleware())  # protects all handlers in this router

# Now all handlers in this router require admin access
```

---

## Sending Notifications

```python
# services/notifier.py
from aiogram import Bot
from config import settings

async def notify_admin(bot: Bot, message: str):
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, message)
        except Exception as e:
            print(f"Failed to notify {admin_id}: {e}")

# Usage - from anywhere in your app
await notify_admin(bot, "New order received!")
```

---

## Deployment

### Free options
- **Railway** - free tier, easy webhook setup
- **Render** - free tier, auto-deploy from GitHub
- **Fly.io** - free tier, good performance

### Environment variables needed
```
BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=https://your-app.railway.app
WEBHOOK_SECRET=random_secret_string_here
ADMIN_IDS=123456789,987654321
```

### Set webhook after deploy
```bash
curl "https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}/webhook"
```

---

## Pre-ship Checklist

- [ ] Bot token in .env, not in code
- [ ] .env in .gitignore
- [ ] Webhook set for production
- [ ] /start command works
- [ ] /help command lists all commands
- [ ] Error handling in all handlers
- [ ] Unknown messages handled gracefully
- [ ] Admin commands protected by middleware (registered on admin router, not globally)
- [ ] Bot tested with real Telegram account

---

## Anti-Patterns

- Never use polling in production
- Never store bot token in code or git
- Never use global variables for conversation state - use FSM
- Never block async handlers with sync code - use asyncio
- Never ignore callback_query - always call callback.answer()
- Never send more than 30 messages/second - Telegram will ban your bot
- Never hardcode user IDs - use config or database

---

## Essential Packages

```
aiogram==3.13.0
pydantic-settings==2.0.0
aiohttp==3.9.0
python-dotenv==1.0.0
```

---

*A bot that replies is better than a bot that is perfect.*
