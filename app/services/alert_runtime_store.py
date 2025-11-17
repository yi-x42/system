"""警報規則執行時設定儲存。

將前端指定的任務警報規則存放在 uploads/alerts/runtime/<task_id>.json，
讓即時偵測子行程可以讀取/重新載入。
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.core.paths import get_base_dir

_RUNTIME_DIR = get_base_dir() / "uploads" / "alerts" / "runtime"
_LOCK = threading.Lock()


def _ensure_dir() -> None:
    _RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def get_alert_runtime_path(task_id: str | int) -> Path:
    """取得指定任務的設定檔路徑（不保證檔案存在）。"""
    _ensure_dir()
    return _RUNTIME_DIR / f"{task_id}.json"


def ensure_alert_runtime_file(task_id: str | int) -> Path:
    """確保任務設定檔存在（若不存在則建立空設定）。"""
    path = get_alert_runtime_path(task_id)
    if not path.exists():
        save_alert_runtime_rules(task_id, [])
    return path


def save_alert_runtime_rules(
    task_id: str | int, rules: List[Dict[str, Any]] | None
) -> Path:
    """儲存任務警報規則，回傳檔案路徑。"""
    payload = {
        "updated_at": datetime.utcnow().isoformat(),
        "rules": rules or [],
    }
    path = get_alert_runtime_path(task_id)
    with _LOCK:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_alert_runtime_rules(task_id: str | int) -> List[Dict[str, Any]]:
    """讀取任務的警報規則列表，若不存在則回傳空陣列。"""
    path = get_alert_runtime_path(task_id)
    if not path.exists():
        return []
    with _LOCK:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
    if isinstance(raw, dict):
        rules = raw.get("rules")
    else:
        rules = raw
    return rules if isinstance(rules, list) else []


__all__ = [
    "get_alert_runtime_path",
    "ensure_alert_runtime_file",
    "save_alert_runtime_rules",
    "load_alert_runtime_rules",
]

