"""
WebSocket 路由定義
提供不同功能的 WebSocket 端點
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Optional
import json
import asyncio
from datetime import datetime
import logging

from .manager import websocket_manager, WebSocketHandler
from ..services.database_service import DatabaseService

# 設定日誌
logger = logging.getLogger(__name__)

# 建立路由器
router = APIRouter()

class DetectionWebSocketHandler(WebSocketHandler):
    """即時檢測結果處理器"""
    
    async def handle_message(self, message: dict, connection_id: str):
        """處理檢測相關訊息"""
        message_type = message.get("type", "")
        
        if message_type == "subscribe_task":
            # 訂閱特定任務的檢測結果
            task_id = message.get("task_id")
            if task_id:
                await self.manager.send_personal_message({
                    "type": "subscription_confirmed",
                    "task_id": task_id,
                    "message": f"已訂閱任務 {task_id} 的檢測結果"
                }, connection_id)
        
        elif message_type == "get_latest":
            # 請求最新的檢測結果
            await self.send_latest_detection(connection_id)
    
    async def send_latest_detection(self, connection_id: str):
        """發送最新檢測結果"""
        # 這裡可以從資料庫查詢最新結果
        # 暫時發送模擬資料
        sample_detection = {
            "type": "detection",
            "task_id": 1,
            "frame_number": 1234,
            "timestamp": datetime.now().isoformat(),
            "objects": [
                {
                    "object_type": "person",
                    "confidence": 0.92,
                    "bbox": [100, 150, 200, 350],
                    "center": [150, 250]
                },
                {
                    "object_type": "car", 
                    "confidence": 0.85,
                    "bbox": [300, 100, 500, 280],
                    "center": [400, 190]
                }
            ]
        }
        
        await self.manager.send_personal_message(sample_detection, connection_id)

class TaskWebSocketHandler(WebSocketHandler):
    """任務狀態處理器"""
    
    async def handle_message(self, message: dict, connection_id: str):
        """處理任務相關訊息"""
        message_type = message.get("type", "")
        
        if message_type == "get_tasks":
            # 請求任務列表
            await self.send_task_list(connection_id)
        
        elif message_type == "subscribe_task":
            # 訂閱特定任務狀態
            task_id = message.get("task_id")
            if task_id:
                await self.manager.send_personal_message({
                    "type": "task_subscription",
                    "task_id": task_id,
                    "status": "subscribed"
                }, connection_id)
    
    async def send_task_list(self, connection_id: str):
        """發送任務列表"""
        # 模擬任務資料
        tasks = [
            {
                "task_id": 1,
                "task_type": "realtime_camera",
                "status": "running",
                "progress": 0.75,
                "start_time": "2025-09-02T10:00:00Z",
                "source_info": {"camera_id": "cam_01", "name": "大廳攝影機"}
            },
            {
                "task_id": 2,
                "task_type": "video_file",
                "status": "completed", 
                "progress": 1.0,
                "start_time": "2025-09-02T09:30:00Z",
                "end_time": "2025-09-02T09:45:00Z",
                "source_info": {"file_path": "/videos/test.mp4"}
            }
        ]
        
        response = {
            "type": "task_list",
            "tasks": tasks,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.manager.send_personal_message(response, connection_id)

class SystemWebSocketHandler(WebSocketHandler):
    """系統狀態處理器"""
    
    async def handle_message(self, message: dict, connection_id: str):
        """處理系統狀態相關訊息"""
        message_type = message.get("type", "")
        
        if message_type == "get_status":
            await self.send_system_status(connection_id)
    
    async def send_system_status(self, connection_id: str):
        """發送系統狀態"""
        import psutil
        
        try:
            # 取得系統資源資訊
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_status = {
                "type": "system_status",
                "cpu_usage": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"取得系統狀態失敗: {e}")
            system_status = {
                "type": "system_status",
                "error": "無法取得系統狀態",
                "timestamp": datetime.now().isoformat()
            }
        
        await self.manager.send_personal_message(system_status, connection_id)

# 建立處理器實例
detection_handler = DetectionWebSocketHandler(websocket_manager)
task_handler = TaskWebSocketHandler(websocket_manager)
system_handler = SystemWebSocketHandler(websocket_manager)

@router.websocket("/ws/detection")
async def websocket_detection(websocket: WebSocket):
    """即時檢測結果 WebSocket 端點"""
    await detection_handler.handle_connection(websocket, "detection")

@router.websocket("/ws/task")
async def websocket_task(websocket: WebSocket):
    """任務狀態 WebSocket 端點"""
    await task_handler.handle_connection(websocket, "task")

@router.websocket("/ws/system")
async def websocket_system(websocket: WebSocket):
    """系統狀態 WebSocket 端點"""
    await system_handler.handle_connection(websocket, "system")

@router.websocket("/ws/analytics")
async def websocket_analytics(websocket: WebSocket):
    """分析數據 WebSocket 端點"""
    await WebSocketHandler(websocket_manager).handle_connection(websocket, "analytics")

# WebSocket 統計 API
@router.get("/ws/stats")
async def get_websocket_stats():
    """取得 WebSocket 連線統計"""
    return websocket_manager.get_stats()

# 測試廣播 API
@router.post("/ws/broadcast/{group}")
async def broadcast_test_message(group: str, message: dict):
    """測試廣播訊息到指定群組"""
    test_message = {
        "type": "test_broadcast",
        "group": group,
        "content": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if group == "all":
        await websocket_manager.broadcast_to_all(test_message)
    else:
        await websocket_manager.broadcast_to_group(test_message, group)
    
    return {"status": "sent", "group": group, "message": test_message}
