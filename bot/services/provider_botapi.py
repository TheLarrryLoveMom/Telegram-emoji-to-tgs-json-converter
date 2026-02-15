from __future__ import annotations

from io import BytesIO

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from bot.services.provider_base import EmojiItem, EmojiPack, EmojiPackProvider, ProviderError


class BotApiEmojiPackProvider(EmojiPackProvider):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def get_pack(self, pack_name: str) -> EmojiPack:
        try:
            sticker_set = await self.bot.get_sticker_set(name=pack_name)
        except TelegramBadRequest as exc:
            raise ProviderError(
                "не удалось получить набор через Bot API (проверьте pack_name)"
            ) from exc

        items: list[EmojiItem] = []
        for sticker in sticker_set.stickers:
            if not sticker.file_id:
                continue
            custom_id = (
                sticker.custom_emoji_id
                if sticker.custom_emoji_id
                else (sticker.file_unique_id or sticker.file_id)
            )
            items.append(EmojiItem(custom_emoji_id=str(custom_id), file_id=sticker.file_id))

        return EmojiPack(
            title=sticker_set.title,
            short_name=sticker_set.name,
            items=items,
        )

    async def get_custom_emoji_items(self, custom_emoji_ids: list[str]) -> list[EmojiItem]:
        if not custom_emoji_ids:
            return []
        try:
            stickers = await self.bot.get_custom_emoji_stickers(custom_emoji_ids=custom_emoji_ids)
        except TelegramBadRequest as exc:
            raise ProviderError("не удалось получить эмодзи по id") from exc

        by_id: dict[str, EmojiItem] = {}
        for sticker in stickers:
            if not sticker.file_id:
                continue
            custom_id = (
                sticker.custom_emoji_id
                if sticker.custom_emoji_id
                else (sticker.file_unique_id or sticker.file_id)
            )
            by_id[str(custom_id)] = EmojiItem(custom_emoji_id=str(custom_id), file_id=sticker.file_id)

        items: list[EmojiItem] = []
        for custom_id in custom_emoji_ids:
            item = by_id.get(str(custom_id))
            if not item:
                raise ProviderError("не удалось получить данные по части эмодзи")
            items.append(item)

        return items

    async def download_emoji(self, item: EmojiItem) -> bytes:
        if not item.file_id:
            raise ProviderError("отсутствует file_id для скачивания")

        file = await self.bot.get_file(item.file_id)
        if not file.file_path:
            raise ProviderError("не удалось получить file_path для файла")

        buffer = BytesIO()
        await self.bot.download_file(file.file_path, destination=buffer)
        return buffer.getvalue()