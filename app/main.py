"""Application lifecycle; no Telegram polling starts during imports."""

import asyncio
import logging

from aiogram import Bot

from app.config import Settings
from app.context import BotContext
from app.db.repository import Store
from app.factory import create_dispatcher


async def main():
    settings = Settings.load()
    settings.validate()
    ctx = BotContext(settings, Store(settings.database_url))
    for attempt in range(6):
        try:
            await asyncio.to_thread(ctx.store.init)
            break
        except Exception:
            if attempt == 5:
                raise SystemExit(
                    "PostgreSQL bilan ulanish o‘rnatilmadi. DATABASE_URL va baza holatini tekshiring."
                ) from None
            logging.warning("PostgreSQL kutilmoqda (%s/6)", attempt + 1)
            await asyncio.sleep(3)
    dispatcher = create_dispatcher(ctx)
    async with Bot(settings.telegram_bot_token) as bot:
        me = await bot.get_me()
        print(f"Bot ishga tushdi: @{me.username}", flush=True)
        await dispatcher.start_polling(bot)


def run():
    logging.basicConfig(level=logging.WARNING)
    try:
        asyncio.run(main())
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
