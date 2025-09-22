"""
手動更新 analysis_tasks.source_info 的影像原始解析度。

用法（Windows PowerShell）：
    python yolo_backend/tools/update_task_resolution.py --task-id 123
    # 或指定來源：
    python yolo_backend/tools/update_task_resolution.py --task-id 123 --source "rtsp://user:pass@host:554/stream"

說明：
    - 優先使用 --source；若未提供，將依據任務 source_info 推導：
        - video_file: 使用 source_info.file_path
        - realtime_camera: 優先 camera_config.rtsp_url，其次 url，再次 (ip, port)
    - 解析度由 app.utils.media_info.probe_resolution() 量測，失敗不覆蓋既有值。
"""

import argparse
import asyncio
import json
from typing import Any, Dict, Optional, Tuple

from app.core.database import AsyncSessionLocal
from app.models.database import AnalysisTask
from sqlalchemy import update, select
from app.utils.media_info import probe_resolution


def _derive_camera_source(config: Dict[str, Any]) -> Optional[str]:
    if not config:
        return None
    # 常見鍵名：rtsp_url/url/ip/port
    if isinstance(config, dict):
        if config.get("rtsp_url"):
            return config.get("rtsp_url")
        if config.get("url"):
            return config.get("url")
        ip = config.get("ip")
        port = config.get("port")
        if ip and port:
            return f"http://{ip}:{port}"
    return None


async def _update_task(task_id: int, override_source: Optional[str]) -> int:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
        task = res.scalar_one_or_none()
        if not task:
            print(f"❌ 找不到任務: {task_id}")
            return 1

        source_info = task.source_info or {}

        # 推導來源
        source: Optional[str] = override_source
        if not source:
            if task.task_type == "video_file":
                source = (source_info or {}).get("file_path")
            elif task.task_type == "realtime_camera":
                source = _derive_camera_source((source_info or {}).get("camera_config") or {})

        if not source:
            print("❌ 無法推導來源，請使用 --source 指定或確認任務 source_info")
            return 2

        w, h = probe_resolution(source)
        if not w or not h:
            print("❌ 量測解析度失敗，未更新")
            return 3

        # 寫回 source_info
        new_info = dict(source_info or {})
        new_info["frame_width"] = int(w)
        new_info["frame_height"] = int(h)

        await session.execute(
            update(AnalysisTask)
            .where(AnalysisTask.id == task_id)
            .values(source_info=new_info)
        )
        await session.commit()

        print(f"✅ 任務 {task_id} 已更新解析度: {w}x{h}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="更新任務來源解析度")
    parser.add_argument("--task-id", type=int, required=True, help="analysis_tasks.id")
    parser.add_argument("--source", type=str, required=False, help="覆寫來源路徑或 URL（選填）")
    args = parser.parse_args()

    return asyncio.run(_update_task(args.task_id, args.source))


if __name__ == "__main__":
    raise SystemExit(main())
