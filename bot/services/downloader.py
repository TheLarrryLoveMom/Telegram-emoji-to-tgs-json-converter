from __future__ import annotations

import asyncio
import logging

from bot.services.provider_base import DownloadError, EmojiItem, EmojiPackProvider


async def download_with_retry(
    provider: EmojiPackProvider,
    item: EmojiItem,
    timeout_s: int,
    retries: int,
    backoff_base: float,
    logger: logging.Logger,
) -> bytes:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await asyncio.wait_for(provider.download_emoji(item), timeout=timeout_s)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= retries:
                break
            sleep_s = backoff_base * (2 ** (attempt - 1))
            logger.warning(
                "download failed, retrying",
                extra={"attempt": attempt, "sleep_s": sleep_s, "error": str(exc)},
            )
            await asyncio.sleep(sleep_s)

    raise DownloadError("не удалось скачать файл после нескольких попыток") from last_exc