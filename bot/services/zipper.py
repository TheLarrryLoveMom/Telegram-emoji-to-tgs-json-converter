from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def build_zip(zip_path: str | Path, manifest_path: str | Path, assets_dir: str | Path) -> None:
    assets_dir = Path(assets_dir)
    with ZipFile(zip_path, mode="w", compression=ZIP_DEFLATED) as zf:
        zf.write(manifest_path, arcname="manifest.json")
        for asset in sorted(p for p in assets_dir.iterdir() if p.is_file()):
            zf.write(asset, arcname=f"assets/{asset.name}")