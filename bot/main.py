from __future__ import annotations

import asyncio
import logging
import os
import sys

if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aiogram import Bot, Dispatcher

from bot.config import load_settings
from bot.handlers.export_link import router as export_router
from bot.handlers.start import router as start_router
from bot.logging_setup import setup_logging
from bot.services.provider_base import EmojiPackProvider, create_provider


async def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(export_router)

    provider: EmojiPackProvider = create_provider(settings, bot)
    dp["provider"] = provider
    dp["ui_store"] = {}

    async def on_shutdown(_: Dispatcher) -> None:
        await provider.close()
        await bot.session.close()
        logging.getLogger(__name__).info("shutdown complete")

    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot, config=settings)


if __name__ == "__main__":
    asyncio.run(main())