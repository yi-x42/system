"""路徑集中管理

統一處理 uploads 下 models / videos 目錄，並提供模型路徑解析。
避免在程式中寫死絕對路徑，方便跨機器部署。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import os

_BASE_DIR = Path(__file__).resolve().parents[2]


def get_base_dir() -> Path:
    return _BASE_DIR


def get_models_dir(create: bool = False) -> Path:
    env_dir = os.getenv("YOLO_MODELS_DIR") or os.getenv("MODELS_DIR")
    if env_dir:
        p = Path(env_dir).expanduser()
        if create:
            p.mkdir(parents=True, exist_ok=True)
        return p
    p = _BASE_DIR / "uploads" / "models"
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return p


def get_videos_dir(create: bool = False) -> Path:
    env_dir = os.getenv("VIDEOS_DIR") or os.getenv("UPLOADS_VIDEOS_DIR")
    if env_dir:
        p = Path(env_dir).expanduser()
        if create:
            p.mkdir(parents=True, exist_ok=True)
        return p
    p = _BASE_DIR / "uploads" / "videos"
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return p


def resolve_model_path(model_id_or_path: Optional[str]) -> Optional[str]:
    """將傳入模型名稱/路徑轉為實際路徑；若是官方模型代號則保持原樣。

    規則：
    - None -> None
    - 實際存在的檔案 (絕對/相對) -> 轉成絕對路徑
    - 僅檔名 (含 .pt) -> 於 models 目錄尋找
    - 無副檔名 -> 嘗試補 .pt
    - 找不到 -> 回傳原字串 (允許 Ultralytics 自動下載)
    """
    if not model_id_or_path:
        return None

    raw = Path(model_id_or_path)
    # 已存在
    if raw.exists() and raw.is_file():
        return str(raw.resolve())

    models_dir = get_models_dir()

    # 含副檔名 .pt
    if raw.suffix == ".pt":
        candidate = models_dir / raw.name
        if candidate.exists():
            return str(candidate.resolve())
        return raw.name  # 官方模型代號或外部下載

    # 無副檔名補 .pt
    candidate_with_pt = models_dir / f"{raw.name}.pt"
    if candidate_with_pt.exists():
        return str(candidate_with_pt.resolve())

    return raw.name


__all__ = [
    "get_base_dir",
    "get_models_dir",
    "get_videos_dir",
    "resolve_model_path",
]
