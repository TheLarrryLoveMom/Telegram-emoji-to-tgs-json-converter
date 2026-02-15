from __future__ import annotations

import gzip
import json
from dataclasses import dataclass


@dataclass
class TgsMeta:
    w: int
    h: int
    fr: float
    ip: float
    op: float


@dataclass
class TgsValidationResult:
    meta: TgsMeta
    json_bytes: bytes


class TgsValidationError(Exception):
    pass


def validate_tgs(data: bytes) -> TgsValidationResult:
    if len(data) < 3 or data[:3] != b"\x1f\x8b\x08":
        raise TgsValidationError("неверная сигнатура gzip")

    try:
        raw = gzip.decompress(data)
    except Exception as exc:  # noqa: BLE001
        raise TgsValidationError("ошибка распаковки gzip") from exc

    try:
        payload = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        raise TgsValidationError("некорректный JSON в tgs") from exc

    required = ["w", "h", "fr", "ip", "op", "layers"]
    if any(key not in payload for key in required):
        raise TgsValidationError("в tgs отсутствуют обязательные ключи Lottie")

    meta = TgsMeta(
        w=int(payload["w"]),
        h=int(payload["h"]),
        fr=float(payload["fr"]),
        ip=float(payload["ip"]),
        op=float(payload["op"]),
    )
    return TgsValidationResult(meta=meta, json_bytes=raw)