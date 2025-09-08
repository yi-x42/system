"""
即時資料推送服務
負責將 YOLO 檢測結果即時推送到 WebSocket 用戶端
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

from .manager import websocket_manager

# 設定日誌
logger = logging.getLogger(__name__)

class RealtimePushService:
    """即時推送服務"""
    
    def __init__(self):
        self.is_running = False
        self.push_queue = asyncio.Queue()
        self.task_subscriptions: Dict[int, List[str]] = {}  # task_id -> [connection_ids]
    
    async def start(self):
        """啟動推送服務"""
        if not self.is_running:
            self.is_running = True
            # 啟動背景推送任務
            asyncio.create_task(self._push_worker())
            logger.info("🚀 即時推送服務已啟動")
    
    async def stop(self):
        """停止推送服務"""
        self.is_running = False
        logger.info("⏹️ 即時推送服務已停止")
    
    async def _push_worker(self):
        """背景推送工作者"""
        while self.is_running:
            try:
                # 從佇列取得待推送資料
                push_data = await asyncio.wait_for(self.push_queue.get(), timeout=1.0)
                
                # 根據資料類型進行推送
                await self._handle_push_data(push_data)
                
            except asyncio.TimeoutError:
                # 定期發送心跳
                await self._send_heartbeat()
            except Exception as e:
                logger.error(f"推送工作者錯誤: {e}")
    
    async def _handle_push_data(self, push_data: dict):
        """處理推送資料"""
        data_type = push_data.get("type", "")
        
        if data_type == "detection":
            await self._push_detection_result(push_data)
        elif data_type == "task_status":
            await self._push_task_status(push_data)
        elif data_type == "system_alert":
            await self._push_system_alert(push_data)
        else:
            logger.warning(f"未知的推送資料類型: {data_type}")
    
    async def _push_detection_result(self, detection_data: dict):
        """推送檢測結果"""
        # 格式化檢測結果
        formatted_data = {
            "type": "detection",
            "task_id": detection_data.get("task_id"),
            "frame_number": detection_data.get("frame_number"),
            "timestamp": detection_data.get("timestamp", datetime.now().isoformat()),
            "objects": detection_data.get("objects", []),
            "image_info": detection_data.get("image_info", {}),
            "processing_time": detection_data.get("processing_time")
        }
        
        # 推送到檢測群組
        await websocket_manager.broadcast_to_group(formatted_data, "detection")
        
        # 推送到分析群組
        await websocket_manager.broadcast_to_group(formatted_data, "analytics")
        
        logger.debug(f"已推送檢測結果: Task {formatted_data['task_id']}, Frame {formatted_data['frame_number']}")
    
    async def _push_task_status(self, task_data: dict):
        """推送任務狀態"""
        formatted_data = {
            "type": "task_status",
            "task_id": task_data.get("task_id"),
            "status": task_data.get("status"),
            "progress": task_data.get("progress", 0.0),
            "message": task_data.get("message", ""),
            "timestamp": datetime.now().isoformat(),
            "details": task_data.get("details", {})
        }
        
        # 推送到任務群組
        await websocket_manager.broadcast_to_group(formatted_data, "task")
        
        logger.info(f"已推送任務狀態: Task {formatted_data['task_id']} - {formatted_data['status']}")
    
    async def _push_system_alert(self, alert_data: dict):
        """推送系統警報"""
        formatted_data = {
            "type": "system_alert",
            "level": alert_data.get("level", "info"),
            "message": alert_data.get("message"),
            "details": alert_data.get("details", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        # 推送到系統群組
        await websocket_manager.broadcast_to_group(formatted_data, "system")
        
        logger.warning(f"已推送系統警報: {formatted_data['level']} - {formatted_data['message']}")
    
    async def _send_heartbeat(self):
        """發送心跳檢測"""
        await websocket_manager.send_heartbeat()
    
    # 公開方法 - 供其他模組調用
    
    async def push_detection_result(self, task_id: int, frame_number: int, objects: List[Dict], 
                                   image_info: Optional[Dict] = None, processing_time: Optional[float] = None):
        """推送檢測結果"""
        detection_data = {
            "type": "detection",
            "task_id": task_id,
            "frame_number": frame_number,
            "objects": objects,
            "image_info": image_info or {},
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.push_queue.put(detection_data)
    
    async def push_task_status_update(self, task_id: int, status: str, progress: float = 0.0, 
                                     message: str = "", details: Optional[Dict] = None):
        """推送任務狀態更新"""
        task_data = {
            "type": "task_status",
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "message": message,
            "details": details or {}
        }
        
        await self.push_queue.put(task_data)
    
    async def push_system_alert(self, level: str, message: str, details: Optional[Dict] = None):
        """推送系統警報"""
        alert_data = {
            "type": "system_alert",
            "level": level,
            "message": message,
            "details": details or {}
        }
        
        await self.push_queue.put(alert_data)
    
    def get_queue_size(self) -> int:
        """取得推送佇列大小"""
        return self.push_queue.qsize()
    
    def get_status(self) -> dict:
        """取得推送服務狀態"""
        return {
            "is_running": self.is_running,
            "queue_size": self.get_queue_size(),
            "websocket_stats": websocket_manager.get_stats()
        }

# 建立全域推送服務實例
realtime_push_service = RealtimePushService()

# 便利函數 - 供其他模組快速調用

async def push_yolo_detection(task_id: int, frame_number: int, detections: List[Dict], 
                             processing_time: Optional[float] = None):
    """
    推送 YOLO 檢測結果
    
    Args:
        task_id: 分析任務ID
        frame_number: 幀編號
        detections: 檢測結果列表，格式如下:
            [
                {
                    "object_type": "person",
                    "confidence": 0.92,
                    "bbox_x1": 100, "bbox_y1": 150,
                    "bbox_x2": 200, "bbox_y2": 350,
                    "center_x": 150, "center_y": 250
                }
            ]
        processing_time: 處理時間（秒）
    """
    await realtime_push_service.push_detection_result(
        task_id=task_id,
        frame_number=frame_number,
        objects=detections,
        processing_time=processing_time
    )

async def push_task_started(task_id: int, task_type: str, source_info: Dict):
    """推送任務開始"""
    await realtime_push_service.push_task_status_update(
        task_id=task_id,
        status="started",
        message=f"任務已開始: {task_type}",
        details={"task_type": task_type, "source_info": source_info}
    )

async def push_task_completed(task_id: int, results_summary: Optional[Dict] = None):
    """推送任務完成"""
    await realtime_push_service.push_task_status_update(
        task_id=task_id,
        status="completed",
        progress=1.0,
        message="任務已完成",
        details=results_summary or {}
    )

async def push_task_failed(task_id: int, error_message: str):
    """推送任務失敗"""
    await realtime_push_service.push_task_status_update(
        task_id=task_id,
        status="failed",
        message=f"任務失敗: {error_message}",
        details={"error": error_message}
    )

async def push_system_warning(message: str, details: Optional[Dict] = None):
    """推送系統警告"""
    await realtime_push_service.push_system_alert("warning", message, details)

async def push_system_error(message: str, details: Optional[Dict] = None):
    """推送系統錯誤"""
    await realtime_push_service.push_system_alert("error", message, details)
