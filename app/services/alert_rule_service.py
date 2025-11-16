"""警報規則服務 - 儲存於 system_config 表"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import SystemConfig

ALERT_RULE_TYPE = "alert_rule"


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _rule_to_dict(entity: SystemConfig) -> Dict[str, Any]:
    payload = entity.payload or {}
    cameras = payload.get("cameras")
    if not cameras:
        cameras = [entity.camera_id] if entity.camera_id else []
    return {
        "id": entity.config_key,
        "name": entity.name or payload.get("name") or "未命名規則",
        "rule_type": payload.get("rule_type", "custom"),
        "severity": payload.get("severity", "中"),
        "enabled": bool(entity.enabled),
        "cameras": cameras,
        "trigger_values": payload.get("trigger_values") or {},
        "actions": payload.get("actions")
        or {"email": False, "push": False, "sms": False},
        "created_at": entity.created_at.isoformat() if entity.created_at else None,
        "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
    }


async def list_rules(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(
        select(SystemConfig)
        .where(SystemConfig.config_type == ALERT_RULE_TYPE)
        .order_by(SystemConfig.updated_at.desc())
    )
    return [_rule_to_dict(rule) for rule in result.scalars().all()]


async def create_rule(session: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
    rule_id = payload.get("id") or uuid.uuid4().hex
    cameras = payload.get("cameras") or []
    camera_id = cameras[0] if cameras else None
    entity = SystemConfig(
        config_key=rule_id,
        config_type=ALERT_RULE_TYPE,
        name=payload.get("name", "未命名規則"),
        camera_id=camera_id,
        payload={
            "rule_type": payload.get("rule_type", "custom"),
            "severity": payload.get("severity", "中"),
            "cameras": cameras,
            "trigger_values": payload.get("trigger_values") or {},
            "actions": payload.get("actions")
            or {"email": False, "push": False, "sms": False},
        },
        enabled=bool(payload.get("enabled", True)),
        description=payload.get("description"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(entity)
    await session.commit()
    await session.refresh(entity)
    return _rule_to_dict(entity)


async def update_rule(
    session: AsyncSession, rule_id: str, payload: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    result = await session.execute(
        select(SystemConfig).where(
            SystemConfig.config_type == ALERT_RULE_TYPE,
            SystemConfig.config_key == rule_id,
        )
    )
    entity = result.scalar_one_or_none()
    if not entity:
        return None

    data = entity.payload or {}
    data.update({k: v for k, v in payload.items() if v is not None})
    cameras = data.get("cameras") or []
    entity.camera_id = cameras[0] if cameras else None
    entity.payload = data
    if "name" in payload:
        entity.name = payload["name"]
    if "enabled" in payload:
        entity.enabled = bool(payload["enabled"])
    entity.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(entity)
    return _rule_to_dict(entity)


async def toggle_rule(
    session: AsyncSession, rule_id: str, enabled: bool
) -> Optional[Dict[str, Any]]:
    result = await session.execute(
        update(SystemConfig)
        .where(
            SystemConfig.config_type == ALERT_RULE_TYPE,
            SystemConfig.config_key == rule_id,
        )
        .values(enabled=enabled, updated_at=datetime.utcnow())
        .returning(SystemConfig)
    )
    entity = result.scalar_one_or_none()
    if not entity:
        return None
    await session.commit()
    return _rule_to_dict(entity)


async def delete_rule(session: AsyncSession, rule_id: str) -> bool:
    result = await session.execute(
        delete(SystemConfig).where(
            SystemConfig.config_type == ALERT_RULE_TYPE,
            SystemConfig.config_key == rule_id,
        )
    )
    await session.commit()
    return result.rowcount > 0
