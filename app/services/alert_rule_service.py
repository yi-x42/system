"""警報規則儲存服務。"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.paths import get_base_dir

_RULES_PATH = get_base_dir() / "uploads" / "config" / "alert_rules.json"
_LOCK = threading.Lock()


def _ensure_file() -> None:
    _RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _RULES_PATH.exists():
        _RULES_PATH.write_text("[]", encoding="utf-8")


def _load_rules() -> List[Dict[str, Any]]:
    _ensure_file()
    try:
        with _RULES_PATH.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _save_rules(rules: List[Dict[str, Any]]) -> None:
    _ensure_file()
    with _RULES_PATH.open("w", encoding="utf-8") as fp:
        json.dump(rules, fp, ensure_ascii=False, indent=2)


def list_rules() -> List[Dict[str, Any]]:
    with _LOCK:
        return _load_rules()


def create_rule(payload: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow().isoformat()
    rule = {
        "id": payload.get("id") or uuid.uuid4().hex,
        "name": payload.get("name", "未命名規則"),
        "rule_type": payload.get("rule_type", "custom"),
        "severity": payload.get("severity", "中"),
        "enabled": bool(payload.get("enabled", True)),
        "cameras": payload.get("cameras") or [],
        "trigger_values": payload.get("trigger_values") or {},
        "actions": payload.get("actions") or {"email": False, "push": False, "sms": False},
        "created_at": now,
        "updated_at": now,
    }
    with _LOCK:
        rules = _load_rules()
        rules.append(rule)
        _save_rules(rules)
    return rule


def update_rule(rule_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    with _LOCK:
        rules = _load_rules()
        index = next((i for i, rule in enumerate(rules) if rule.get("id") == rule_id), None)
        if index is None:
            return None
        rule = rules[index]
        rule.update({k: v for k, v in payload.items() if v is not None})
        rule["updated_at"] = datetime.utcnow().isoformat()
        rules[index] = rule
        _save_rules(rules)
        return rule


def toggle_rule(rule_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
    return update_rule(rule_id, {"enabled": enabled})


def delete_rule(rule_id: str) -> bool:
    with _LOCK:
        rules = _load_rules()
        new_rules = [rule for rule in rules if rule.get("id") != rule_id]
        if len(new_rules) == len(rules):
            return False
        _save_rules(new_rules)
        return True
