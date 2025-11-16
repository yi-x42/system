"""通知設定儲存服務。

目前僅處理郵件通知相關設定，資料存放於 uploads/config/notification_settings.json。
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict

from app.core.paths import get_base_dir

_CONFIG_PATH = get_base_dir() / "uploads" / "config" / "notification_settings.json"
_CONFIG_LOCK = threading.Lock()

DEFAULT_EMAIL_SETTINGS: Dict[str, Any] = {
    "enabled": False,
    "address": "",
    "confidence": 0.5,
    "cooldown_seconds": 30,
}

DEFAULT_SETTINGS: Dict[str, Any] = {
    "email": DEFAULT_EMAIL_SETTINGS,
}


def _ensure_parent_dir() -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _merge_email_settings(data: Dict[str, Any]) -> Dict[str, Any]:
    merged_email = dict(DEFAULT_EMAIL_SETTINGS)
    merged_email.update(data.get("email") or {})
    return {"email": merged_email}


def _load_raw() -> Dict[str, Any]:
    _ensure_parent_dir()
    if not _CONFIG_PATH.exists():
        return DEFAULT_SETTINGS.copy()
    try:
        with _CONFIG_PATH.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        if isinstance(data, dict):
            return data
        return DEFAULT_SETTINGS.copy()
    except Exception:
        return DEFAULT_SETTINGS.copy()


def _save_raw(payload: Dict[str, Any]) -> None:
    _ensure_parent_dir()
    with _CONFIG_PATH.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


def get_email_settings() -> Dict[str, Any]:
    """取得郵件通知設定（已套用預設值）。"""
    with _CONFIG_LOCK:
        stored = _load_raw()
        merged = _merge_email_settings(stored)
        return merged["email"]


def update_email_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    """更新郵件通知設定並回傳最新狀態。"""
    with _CONFIG_LOCK:
        stored = _load_raw()
        stored_email = _merge_email_settings(stored)["email"]

        for key in ("enabled", "address", "confidence", "cooldown_seconds"):
            if key in payload and payload[key] is not None:
                stored_email[key] = payload[key]

        stored["email"] = stored_email
        _save_raw(stored)
        return stored_email
