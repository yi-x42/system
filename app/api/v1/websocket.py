"""
WebSocket 端點
提供即時數據更新和檢測串流
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.routing import APIRouter

from app.core.logger import api_logger
from app.services.camera_service import CameraService
from app.services.task_service import TaskService
from app.services.analytics_service import AnalyticsService

websocket_router = APIRouter()

class ConnectionManager:
    """WebSocket 連接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "system_stats": set(),
            "detection_stream": set(),
            "task_updates": set(),
            "analytics": set()
        }
        self.camera_streams: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, connection_type: str, identifier: str = None):
        """連接WebSocket"""
        await websocket.accept()
        
        if connection_type == "camera_stream" and identifier:
            if identifier not in self.camera_streams:
                self.camera_streams[identifier] = set()
            self.camera_streams[identifier].add(websocket)
        elif connection_type in self.active_connections:
            self.active_connections[connection_type].add(websocket)
        
        api_logger.info(f"WebSocket 連接: {connection_type} {identifier or ''}")
    
    def disconnect(self, websocket: WebSocket, connection_type: str, identifier: str = None):
        """斷開WebSocket連接"""
        try:
            if connection_type == "camera_stream" and identifier:
                if identifier in self.camera_streams:
                    self.camera_streams[identifier].discard(websocket)
                    if not self.camera_streams[identifier]:
                        del self.camera_streams[identifier]
            elif connection_type in self.active_connections:
                self.active_connections[connection_type].discard(websocket)
            
            api_logger.info(f"WebSocket 斷開: {connection_type} {identifier or ''}")
        except Exception as e:
            api_logger.error(f"WebSocket 斷開錯誤: {e}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """發送個人消息"""
        try:
            # 檢查 WebSocket 連接狀態
            if websocket.client_state.name == "CONNECTED":
                await websocket.send_text(message)
        except Exception as e:
            api_logger.error(f"發送個人消息失敗: {e}")
            # 自動清理已斷開的連接
            self._cleanup_disconnected_websocket(websocket)
    
    async def broadcast_to_type(self, message: str, connection_type: str):
        """廣播消息到特定類型的連接"""
        if connection_type not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[connection_type]:
            try:
                # 檢查連接狀態
                if connection.client_state.name == "CONNECTED":
                    await connection.send_text(message)
                else:
                    disconnected.add(connection)
            except Exception as e:
                api_logger.error(f"廣播消息失敗: {e}")
                disconnected.add(connection)
        
        # 移除斷開的連接
        for connection in disconnected:
            self.active_connections[connection_type].discard(connection)
    
    def _cleanup_disconnected_websocket(self, websocket: WebSocket):
        """清理已斷開的 WebSocket 連接"""
        try:
            # 從所有連接類型中移除
            for connection_type in self.active_connections:
                self.active_connections[connection_type].discard(websocket)
            
            # 從攝影機串流中移除
            for camera_id in list(self.camera_streams.keys()):
                self.camera_streams[camera_id].discard(websocket)
                if not self.camera_streams[camera_id]:
                    del self.camera_streams[camera_id]
        except Exception as e:
            api_logger.error(f"清理 WebSocket 連接失敗: {e}")
    
    async def broadcast_to_camera(self, message: str, camera_id: str):
        """廣播消息到特定攝影機的連接"""
        if camera_id not in self.camera_streams:
            return
        
        disconnected = set()
        for connection in self.camera_streams[camera_id]:
            try:
                # 檢查連接狀態
                if connection.client_state.name == "CONNECTED":
                    await connection.send_text(message)
                else:
                    disconnected.add(connection)
            except Exception as e:
                api_logger.error(f"廣播攝影機消息失敗: {e}")
                disconnected.add(connection)
        
        # 移除斷開的連接
        for connection in disconnected:
            self.camera_streams[camera_id].discard(connection)

# 全局連接管理器
manager = ConnectionManager()

@websocket_router.websocket("/ws/system-stats")
async def websocket_system_stats(websocket: WebSocket):
    """系統統計 WebSocket 端點"""
    try:
        await manager.connect(websocket, "system_stats")
        api_logger.info("系統統計 WebSocket 連接建立")
        
        while True:
            # 檢查 WebSocket 連接狀態
            if websocket.client_state.name != "CONNECTED":
                api_logger.info("WebSocket 連接已斷開，停止發送數據")
                break
            
            # 獲取真實的系統統計數據
            try:
                import psutil
                
                # 獲取基本系統資源使用率
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                memory_usage = memory.percent
                
                # 嘗試獲取 GPU 使用率
                gpu_usage = 0.0
                try:
                    import subprocess
                    result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        gpu_usage = float(result.stdout.strip())
                except:
                    gpu_usage = 0.0
                
                # 模擬任務和檢測數據（之後會從資料庫獲取）
                active_tasks = 0  # 之後從資料庫查詢
                total_detections = 0  # 之後從資料庫查詢
                
                stats_data = {
                    "type": "system_stats",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "cpu_usage": round(cpu_usage, 1),
                        "memory_usage": round(memory_usage, 1),
                        "gpu_usage": round(gpu_usage, 1),
                        "active_tasks": active_tasks,
                        "total_detections": total_detections
                    }
                }
                
                await manager.send_personal_message(json.dumps(stats_data), websocket)
                
            except Exception as e:
                api_logger.error(f"生成系統統計數據失敗: {e}")
            
            # 等待下次更新
            try:
                await asyncio.sleep(5)  # 每5秒更新一次
            except asyncio.CancelledError:
                break
                
    except WebSocketDisconnect:
        api_logger.info("系統統計 WebSocket 正常斷開")
    except Exception as e:
        api_logger.error(f"系統統計 WebSocket 錯誤: {e}")
    finally:
        try:
            manager.disconnect(websocket, "system_stats")
        except:
            pass

@websocket_router.websocket("/ws/detection/{camera_id}")
async def websocket_detection_stream(websocket: WebSocket, camera_id: str):
    """檢測串流 WebSocket 端點"""
    await manager.connect(websocket, "camera_stream", camera_id)
    
    camera_service = CameraService()
    
    try:
        # 檢查攝影機是否存在
        camera = await camera_service.get_camera_by_id(camera_id)
        if not camera:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"攝影機不存在: {camera_id}"
            }))
            return
        
        # 模擬檢測結果串流
        frame_count = 0
        while True:
            # 模擬檢測結果
            detection_data = {
                "type": "detection",
                "camera_id": camera_id,
                "frame_id": frame_count,
                "timestamp": datetime.now().isoformat(),
                "detections": [
                    {
                        "class_name": "person",
                        "confidence": 0.85,
                        "bbox": [100, 50, 200, 300],
                        "track_id": 1
                    },
                    {
                        "class_name": "car", 
                        "confidence": 0.92,
                        "bbox": [300, 100, 500, 250],
                        "track_id": 2
                    }
                ]
            }
            
            await manager.send_personal_message(json.dumps(detection_data), websocket)
            frame_count += 1
            await asyncio.sleep(0.1)  # 模擬10FPS
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "camera_stream", camera_id)
    except Exception as e:
        api_logger.error(f"檢測串流錯誤: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"檢測串流錯誤: {str(e)}"
        }))

@websocket_router.websocket("/ws/task-updates")
async def websocket_task_updates(websocket: WebSocket):
    """任務更新 WebSocket 端點"""
    await manager.connect(websocket, "task_updates")
    
    task_service = TaskService()
    
    try:
        while True:
            # 獲取任務統計
            task_stats = {
                "running": 3,
                "pending": 2,
                "completed": 156,
                "failed": 2
            }
            
            # 獲取活躍任務進度
            active_tasks = []
            for task_id, task in task_service.active_tasks.items():
                active_tasks.append({
                    "id": task_id,
                    "name": task["name"],
                    "status": task["status"],
                    "progress": task["progress"]
                })
            
            update_data = {
                "type": "task_update",
                "timestamp": datetime.now().isoformat(),
                "stats": task_stats,
                "active_tasks": active_tasks
            }
            
            await manager.send_personal_message(json.dumps(update_data), websocket)
            await asyncio.sleep(3)  # 每3秒更新一次
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "task_updates")

@websocket_router.websocket("/ws/analytics")
async def websocket_analytics(websocket: WebSocket):
    """分析數據 WebSocket 端點"""
    await manager.connect(websocket, "analytics")
    
    analytics_service = AnalyticsService()
    
    try:
        while True:
            # 獲取分析數據
            analytics_data = await analytics_service.get_analytics_data("1h")
            
            update_data = {
                "type": "analytics_update",
                "timestamp": datetime.now().isoformat(),
                "data": analytics_data
            }
            
            await manager.send_personal_message(json.dumps(update_data), websocket)
            await asyncio.sleep(30)  # 每30秒更新一次
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "analytics")
    except Exception as e:
        api_logger.error(f"分析數據 WebSocket 錯誤: {e}")

# 廣播函數（供其他服務調用）
async def broadcast_system_stats(stats_data: dict):
    """廣播系統統計數據"""
    message = json.dumps({
        "type": "system_stats_update",
        "timestamp": datetime.now().isoformat(),
        "data": stats_data
    })
    await manager.broadcast_to_type(message, "system_stats")

async def broadcast_task_update(task_data: dict):
    """廣播任務更新"""
    message = json.dumps({
        "type": "task_update",
        "timestamp": datetime.now().isoformat(),
        "data": task_data
    })
    await manager.broadcast_to_type(message, "task_updates")

async def broadcast_detection_result(camera_id: str, detection_data: dict):
    """廣播檢測結果"""
    message = json.dumps({
        "type": "detection_result",
        "timestamp": datetime.now().isoformat(),
        "camera_id": camera_id,
        "data": detection_data
    })
    await manager.broadcast_to_camera(message, camera_id)
