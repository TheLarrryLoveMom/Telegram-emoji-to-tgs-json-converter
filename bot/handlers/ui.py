from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from aiogram.types import InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError, TelegramRetryAfter

logger = logging.getLogger(__name__)

SIGNATURE = "powered by @Larrygraphics"


def with_signature(text: str) -> str:
    if not text:
        return SIGNATURE
    return f"{text}\n\n{SIGNATURE}"


def get_state(store: dict[int, dict[str, Any]], user_id: int) -> dict[str, Any]:
    return store.setdefault(
        user_id,
        {
            "format": "tgs",
            "awaiting": False,
            "menu_message_id": None,
            "menu_chat_id": None,
        },
    )


def menu_text(fmt: str) -> str:
    return (
        "Главное меню\n"
        f"Текущий формат: {fmt}\n\n"
        "Выберите формат кнопкой ниже, затем отправьте ссылку на addemoji-пак."
    )


def help_text() -> str:
    return (
        "Справка\n\n"
        "1) Нажмите кнопку 'Экспорт TGS' или 'Экспорт JSON'\n"
        "2) Отправьте ссылку вида https://t.me/addemoji/<pack_name>\n\n"
        "Бот скачает эмодзи, провалидирует и вернет ZIP."
    )


def build_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Экспорт TGS", callback_data="fmt:tgs")
    builder.button(text="Экспорт JSON", callback_data="fmt:json")
    builder.button(text="Справка", callback_data="help")
    return builder.adjust(2, 1).as_markup()


def build_back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Меню", callback_data="menu")
    return builder.as_markup()


async def send_menu(message: Message, store: dict[int, dict[str, Any]], note: str | None = None) -> Message:
    user_id = message.from_user.id if message.from_user else 0
    state = get_state(store, user_id)
    text = menu_text(state["format"])
    if note:
        text = f"{note}\n\n{text}"
    msg = await safe_answer(message, text=text, reply_markup=build_menu_kb())
    if msg is None:
        # Fallback: keep state but no menu message available
        state["awaiting"] = False
        return message
    state["menu_message_id"] = msg.message_id
    state["menu_chat_id"] = msg.chat.id
    state["awaiting"] = False
    return msg


async def safe_answer(
    message: Message, *, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> Optional[Message]:
    text = with_signature(text)
    try:
        return await message.answer(text, reply_markup=reply_markup)
    except TelegramRetryAfter as exc:
        await asyncio.sleep(exc.retry_after)
        try:
            return await message.answer(text, reply_markup=reply_markup)
        except (TelegramBadRequest, TelegramNetworkError) as retry_exc:
            logger.warning("safe_answer failed after retry: %s", retry_exc)
            return None
    except (TelegramBadRequest, TelegramNetworkError) as exc:
        logger.warning("safe_answer failed: %s", exc)
        return None


async def safe_edit(
    message: Message, *, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> bool:
    text = with_signature(text)
    try:
        await message.edit_text(text, reply_markup=reply_markup)
        return True
    except TelegramRetryAfter as exc:
        await asyncio.sleep(exc.retry_after)
        try:
            await message.edit_text(text, reply_markup=reply_markup)
            return True
        except (TelegramBadRequest, TelegramNetworkError) as retry_exc:
            logger.warning("safe_edit failed after retry: %s", retry_exc)
            return False
    except (TelegramBadRequest, TelegramNetworkError) as exc:
        logger.warning("safe_edit failed: %s", exc)
        return False
