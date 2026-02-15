from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.handlers.ui import (
    build_back_kb,
    build_menu_kb,
    get_state,
    help_text,
    menu_text,
    safe_answer,
    safe_edit,
    send_menu,
)

router = Router()


@router.message(Command("start"))
async def start(message: Message, ui_store: dict[int, dict]) -> None:
    await send_menu(message, ui_store)


@router.message(Command("help"))
async def help_cmd(message: Message, ui_store: dict[int, dict]) -> None:
    user_id = message.from_user.id if message.from_user else 0
    state = get_state(ui_store, user_id)
    msg = await safe_answer(message, text=help_text(), reply_markup=build_back_kb())
    if msg:
        state["menu_message_id"] = msg.message_id
        state["menu_chat_id"] = msg.chat.id
    state["awaiting"] = False


@router.callback_query()
async def callbacks(callback: CallbackQuery, ui_store: dict[int, dict]) -> None:
    if not callback.data or not callback.message:
        return

    user_id = callback.from_user.id if callback.from_user else 0
    state = get_state(ui_store, user_id)

    if callback.data == "menu":
        await safe_edit(
            callback.message, text=menu_text(state["format"]), reply_markup=build_menu_kb()
        )
        state["awaiting"] = False
    elif callback.data == "help":
        await safe_edit(callback.message, text=help_text(), reply_markup=build_back_kb())
        state["awaiting"] = False
    elif callback.data.startswith("fmt:"):
        fmt = callback.data.split(":", 1)[1]
        if fmt in ("tgs", "json"):
            state["format"] = fmt
            state["awaiting"] = True
            await safe_edit(
                callback.message,
                text=(
                    f"Выбран формат: {fmt}.\n"
                    "Отправьте ссылку на addemoji-пак или просто эмодзи в одном сообщении."
                ),
                reply_markup=build_back_kb(),
            )

    state["menu_message_id"] = callback.message.message_id
    state["menu_chat_id"] = callback.message.chat.id
    try:
        await callback.answer()
    except Exception:
        return