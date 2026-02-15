from __future__ import annotations

import asyncio
import logging
import os
import re
import tempfile
import time

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError, TelegramRetryAfter
from aiogram.types import FSInputFile, Message, MessageEntity

from bot.config import Settings
from bot.handlers.ui import build_back_kb, get_state, send_menu, safe_answer, with_signature
from bot.schemas.manifest import ManifestItem, TgsMeta
from bot.services.downloader import download_with_retry
from bot.services.manifest_builder import build_manifest, write_manifest
from bot.services.provider_base import DownloadError, EmojiPackProvider, ProviderError
from bot.services.tgs_validator import TgsValidationError, validate_tgs
from bot.services.zipper import build_zip
from bot.utils.files import ensure_dir, sha256_hex
from bot.utils.time import utc_now_filename

router = Router()
logger = logging.getLogger(__name__)

ADD_EMOJI_RE = re.compile(r"(?:https?://)?t\.me/addemoji/([A-Za-z0-9_]+)")


class ExportError(Exception):
    pass


def parse_addemoji_url(text: str) -> str | None:
    match = ADD_EMOJI_RE.search(text.strip())
    if not match:
        return None
    return match.group(1)


def extract_custom_emoji_ids(message: Message) -> list[str]:
    ids: list[str] = []

    def collect(entities: list[MessageEntity] | None) -> None:
        if not entities:
            return
        for ent in entities:
            if ent.type == "custom_emoji" and ent.custom_emoji_id:
                ids.append(str(ent.custom_emoji_id))

    collect(message.entities)
    collect(message.caption_entities)

    seen: set[str] = set()
    result: list[str] = []
    for item in ids:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


async def do_export(
    *,
    message: Message,
    config: Settings,
    provider: EmojiPackProvider,
    ui_store: dict[int, dict],
    items: list,
    source_url: str,
    source_pack_name: str,
    pack_title: str,
    pack_short_name: str,
    export_name: str,
    export_format: str,
) -> None:
    user_id = message.from_user.id if message.from_user else 0
    state = get_state(ui_store, user_id)

    status_message_id = state.get("menu_message_id")
    status_chat_id = state.get("menu_chat_id")

    if not status_message_id or not status_chat_id:
        status = await safe_answer(message, text="получаю список эмодзи…", reply_markup=build_back_kb())
        if status is None:
            return
        status_message_id = status.message_id
        status_chat_id = status.chat.id
        state["menu_message_id"] = status_message_id
        state["menu_chat_id"] = status_chat_id

    last_text = ""
    last_edit_ts = 0.0
    min_interval_s = 1.2

    async def update_status(text: str, *, force: bool = False) -> None:
        nonlocal last_text, last_edit_ts
        if text == last_text:
            return
        now = time.monotonic()
        if not force and (now - last_edit_ts) < min_interval_s:
            return
        try:
            await message.bot.edit_message_text(
                with_signature(text),
                chat_id=status_chat_id,
                message_id=status_message_id,
                reply_markup=build_back_kb(),
            )
            last_text = text
            last_edit_ts = time.monotonic()
        except TelegramRetryAfter as exc:
            if not force:
                return
            await asyncio.sleep(exc.retry_after)
            try:
                await message.bot.edit_message_text(
                    with_signature(text),
                    chat_id=status_chat_id,
                    message_id=status_message_id,
                    reply_markup=build_back_kb(),
                )
                last_text = text
                last_edit_ts = time.monotonic()
            except (TelegramBadRequest, TelegramNetworkError):
                return
        except (TelegramBadRequest, TelegramNetworkError):
            return

    await update_status("получаю список эмодзи…", force=True)

    try:
        if len(items) > config.max_emojis_per_pack:
            raise ExportError(
                f"слишком много эмодзи: {len(items)} (лимит {config.max_emojis_per_pack})"
            )

        total_limit_bytes = config.max_total_zip_mb * 1024 * 1024
        items_manifest: list[ManifestItem] = []

        with tempfile.TemporaryDirectory() as tmpdir:
            assets_dir = os.path.join(tmpdir, "assets")
            ensure_dir(assets_dir)

            total_bytes = 0
            total = len(items)

            for index, item in enumerate(items):
                await update_status(f"скачиваю ({index + 1}/{total})…")

                data = await download_with_retry(
                    provider=provider,
                    item=item,
                    timeout_s=config.download_timeout,
                    retries=config.download_retries,
                    backoff_base=config.retry_backoff_base,
                    logger=logger,
                )

                await update_status("проверяю tgs…")

                try:
                    result = validate_tgs(data)
                except TgsValidationError as exc:
                    raise ExportError(f"ошибка в tgs: {exc}") from exc

                if export_format == "json":
                    payload = result.json_bytes
                    ext = "json"
                    mime = "application/json"
                else:
                    payload = data
                    ext = "tgs"
                    mime = "application/x-tgsticker"

                total_bytes += len(payload)
                if total_bytes > total_limit_bytes:
                    raise ExportError("превышен лимит размера архива")

                file_name = f"{index:04d}.{ext}"
                file_path = os.path.join(assets_dir, file_name)
                with open(file_path, "wb") as file_handle:
                    file_handle.write(payload)

                items_manifest.append(
                    ManifestItem(
                        index=index,
                        custom_emoji_id=item.custom_emoji_id,
                        file_name=f"assets/{file_name}",
                        mime=mime,
                        sha256=sha256_hex(payload),
                        tgs_meta=TgsMeta(
                            w=result.meta.w,
                            h=result.meta.h,
                            fr=result.meta.fr,
                            ip=result.meta.ip,
                            op=result.meta.op,
                        ),
                    )
                )

            await update_status("собираю архив…")

            manifest = build_manifest(
                source_url=source_url,
                source_pack_name=source_pack_name,
                pack_title=pack_title,
                pack_short_name=pack_short_name,
                items=items_manifest,
            )
            manifest_path = os.path.join(tmpdir, "manifest.json")
            write_manifest(manifest, manifest_path)

            zip_name = f"export_{export_name}_{utc_now_filename()}.zip"
            zip_path = os.path.join(tmpdir, zip_name)
            build_zip(zip_path, manifest_path, assets_dir)

            try:
                await message.answer_document(
                    FSInputFile(zip_path, filename=zip_name), caption=with_signature("")
                )
            except TelegramRetryAfter as exc:
                await asyncio.sleep(exc.retry_after)
                await message.answer_document(
                    FSInputFile(zip_path, filename=zip_name), caption=with_signature("")
                )
            except TelegramNetworkError as exc:
                raise ExportError("ошибка сети при отправке архива") from exc

            state["awaiting"] = False
            await update_status("готово ✅", force=True)

    except (ProviderError, DownloadError, ExportError) as exc:
        state["awaiting"] = False
        await update_status(f"экспорт прерван: {exc}", force=True)
    except Exception:  # noqa: BLE001
        logger.exception("unexpected export error")
        state["awaiting"] = False
        await update_status("экспорт прерван: неизвестная ошибка", force=True)


@router.message()
async def export_link(
    message: Message,
    config: Settings,
    provider: EmojiPackProvider,
    ui_store: dict[int, dict],
) -> None:
    text = message.text or ""
    pack_name = parse_addemoji_url(text) if text else None
    custom_emoji_ids = extract_custom_emoji_ids(message)

    if not pack_name and not custom_emoji_ids:
        return

    user_id = message.from_user.id if message.from_user else 0
    state = get_state(ui_store, user_id)

    if not state.get("awaiting"):
        await send_menu(message, ui_store, note="Сначала выберите формат экспорта кнопкой ниже.")
        return

    export_format = state.get("format", "tgs")

    if pack_name:
        source_url = f"https://t.me/addemoji/{pack_name}"
        export_name = pack_name
        try:
            pack = await provider.get_pack(pack_name)
        except ProviderError as exc:
            await send_menu(message, ui_store, note=str(exc))
            return
        pack_title = pack.title
        pack_short_name = pack.short_name
        items = pack.items
        source_pack_name = pack_name
    else:
        source_url = f"message:{message.chat.id}:{message.message_id}"
        export_name = f"custom_emoji_{message.message_id}"
        pack_title = "Custom Emoji Message"
        pack_short_name = "custom_emoji_message"
        source_pack_name = pack_short_name
        try:
            items = await provider.get_custom_emoji_items(custom_emoji_ids)
        except ProviderError as exc:
            await send_menu(message, ui_store, note=str(exc))
            return

    if not items:
        await send_menu(message, ui_store, note="Не найдено эмодзи для экспорта.")
        return

    await do_export(
        message=message,
        config=config,
        provider=provider,
        ui_store=ui_store,
        items=items,
        source_url=source_url,
        source_pack_name=source_pack_name,
        pack_title=pack_title,
        pack_short_name=pack_short_name,
        export_name=export_name,
        export_format=export_format,
    )
