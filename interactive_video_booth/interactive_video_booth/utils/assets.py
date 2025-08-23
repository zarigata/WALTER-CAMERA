from __future__ import annotations
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests  # type: ignore

from .logger import get_logger, write_error_log
from .errors import StageError


@dataclass
class Asset:
    id: str
    filename: str
    urls: List[str]
    sha256: Optional[str] = None
    size: Optional[int] = None


def _read_manifest(base_dir: Path) -> Dict[str, Asset]:
    cfg = base_dir / "configs" / "models_manifest.json"
    if not cfg.exists():
        # Default manifest with YOLOv8n ONNX; sha256 omitted
        defaults = {
            "yolov8n": Asset(
                id="yolov8n",
                filename="yolov8n.onnx",
                urls=[
                    "https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.onnx",
                    "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.onnx",
                ],
                sha256=None,
                size=None,
            )
        }
        return defaults
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
        out: Dict[str, Asset] = {}
        for item in data.get("assets", []):
            aid = str(item.get("id"))
            if not aid:
                continue
            out[aid] = Asset(
                id=aid,
                filename=str(item.get("filename")),
                urls=list(item.get("urls", [])),
                sha256=item.get("sha256"),
                size=item.get("size"),
            )
        return out
    except Exception:
        raise StageError(20, "Failed to parse models_manifest.json")


def _sha256_of(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_with_retries(urls: List[str], dest: Path, retries: int = 2, timeout: int = 30) -> None:
    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        for url in urls:
            try:
                with requests.get(url, stream=True, timeout=timeout) as r:
                    r.raise_for_status()
                    with dest.open("wb") as f:
                        for part in r.iter_content(chunk_size=1 << 20):
                            if part:
                                f.write(part)
                return
            except Exception as e:
                last_err = e
                time.sleep(0.5)
                continue
    raise StageError(20, f"Failed to download asset: {last_err}")


def prepare_models(base_dir: Path, allow_download: bool = True) -> Dict[str, Path]:
    """Ensure models exist locally under models/ using the manifest.

    If allow_download is False, only verifies presence and integrity.
    Returns a mapping id -> local path.
    """
    stage_label = "ASSETS"
    log = get_logger(stage_label, base_dir)

    assets = _read_manifest(base_dir)
    models_dir = base_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, Path] = {}
    for aid, asset in assets.items():
        target = models_dir / asset.filename
        # Verify existing
        if target.exists() and target.stat().st_size > 0:
            if asset.sha256:
                try:
                    digest = _sha256_of(target)
                    if digest.lower() != asset.sha256.lower():
                        log.info(f"Hash mismatch for {asset.filename}; re-fetch required")
                        if not allow_download:
                            raise StageError(20, f"Asset {asset.filename} invalid; run --prepare-models online")
                        _download_with_retries(asset.urls, target)
                    else:
                        results[aid] = target
                        continue
                except StageError:
                    raise
                except Exception:
                    if not allow_download:
                        raise StageError(20, f"Asset {asset.filename} validation failed; run --prepare-models online")
            else:
                results[aid] = target
                continue

        # Missing or invalid
        if not allow_download:
            raise StageError(20, f"Asset missing: {asset.filename}; run --prepare-models online")

        log.info(f"Downloading asset: {asset.filename}")
        _download_with_retries(asset.urls, target)
        results[aid] = target

    return results
