from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from bot.config import Settings


class ProviderError(Exception):
    pass


class DownloadError(Exception):
    pass


@dataclass
class EmojiItem:
    custom_emoji_id: str
    file_id: str | None = None
    document: Any | None = None


@dataclass
class EmojiPack:
    title: str
    short_name: str
    items: list[EmojiItem]


class EmojiPackProvider(ABC):
    @abstractmethod
    async def get_pack(self, pack_name: str) -> EmojiPack:
        raise NotImplementedError

    @abstractmethod
    async def download_emoji(self, item: EmojiItem) -> bytes:
        raise NotImplementedError

    async def get_custom_emoji_items(self, custom_emoji_ids: list[str]) -> list[EmojiItem]:
        raise ProviderError("получение эмодзи из сообщения не поддерживается этим режимом")

    async def close(self) -> None:
        return None


def create_provider(settings: Settings, bot) -> EmojiPackProvider:
    from bot.services.provider_botapi import BotApiEmojiPackProvider

    return BotApiEmojiPackProvider(bot)
