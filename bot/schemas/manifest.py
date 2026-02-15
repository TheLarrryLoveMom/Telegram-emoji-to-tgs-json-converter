from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class TgsMeta(BaseModel):
    w: int
    h: int
    fr: float
    ip: float
    op: float


class ManifestItem(BaseModel):
    index: int
    custom_emoji_id: str
    file_name: str
    mime: str = Field(default="application/x-tgsticker")
    sha256: str
    tgs_meta: TgsMeta


class ManifestSource(BaseModel):
    type: str
    url: str
    pack_name: str


class ManifestPack(BaseModel):
    title: str
    short_name: str
    emoji_count: int


class Manifest(BaseModel):
    schema_version: int = Field(default=1)
    exported_at: str
    source: ManifestSource
    pack: ManifestPack
    items: List[ManifestItem]