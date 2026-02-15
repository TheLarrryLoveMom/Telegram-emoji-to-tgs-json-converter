from __future__ import annotations

import json
from pathlib import Path

from bot.schemas.manifest import Manifest, ManifestItem, ManifestPack, ManifestSource
from bot.utils.time import utc_now_iso


def build_manifest(
    *,
    source_url: str,
    source_pack_name: str,
    pack_title: str,
    pack_short_name: str,
    items: list[ManifestItem],
) -> Manifest:
    return Manifest(
        exported_at=utc_now_iso(),
        source=ManifestSource(
            type="telegram_addemoji",
            url=source_url,
            pack_name=source_pack_name,
        ),
        pack=ManifestPack(
            title=pack_title,
            short_name=pack_short_name,
            emoji_count=len(items),
        ),
        items=items,
    )


def write_manifest(manifest: Manifest, path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
