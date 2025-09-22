"""
WebSocket 連線管理器
管理多用戶連線、分組廣播、即時資料推送
"""
import json
import asyncio
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import logging

# 設定日誌
logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket 連線管理器"""
    
    def __init__(self):
        # 儲存所有活躍連線
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 分組管理 - 按功能分組
        self.groups: Dict[str, Set[str]] = {
            "detection": set(),      # 即時辨識結果
            "task": set(),          # 任務進度狀態
            "system": set(),        # 系統狀態監控
            "analytics": set(),     # 分析數據
        }
        
        # 連線元資料
        self.connection_meta: Dict[str, Dict[str, Any]] = {}
    
    def generate_connection_id(self, websocket: WebSocket) -> str:
        """產生唯一連線ID"""
        client_host = websocket.client.host if websocket.client else "unknown"
        client_port = websocket.client.port if websocket.client else 0
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"{client_host}_{client_port}_{timestamp}"
    
    async def connect(self, websocket: WebSocket, group: str = "detection") -> str:
        """建立新連線"""
        await websocket.accept()
        
        # 產生連線ID
        connection_id = self.generate_connection_id(websocket)
        
        # 儲存連線
        self.active_connections[connection_id] = websocket
        
        # 加入指定群組
        if group in self.groups:
            self.groups[group].add(connection_id)
        
        # 儲存連線元資料
        self.connection_meta[connection_id] = {
            "group": group,
            "connected_at": datetime.now().isoformat(),
            "client_info": {
                "host": websocket.client.host if websocket.client else "unknown",
                "port": websocket.client.port if websocket.client else 0
            }
        }
        
        logger.info(f"✅ 新連線建立: {connection_id} 加入群組 {group}")
        
        # 發送歡迎訊息
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "connection_id": connection_id,
            "group": group,
            "timestamp": datetime.now().isoformat(),
            "message": f"已成功連線到 {group} 群組"
        }, connection_id)
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """斷開連線"""
        if connection_id in self.active_connections:
            # 從所有群組移除
            for group_name, group_connections in self.groups.items():
                group_connections.discard(connection_id)
            
            # 移除連線資料
            del self.active_connections[connection_id]
            del self.connection_meta[connection_id]
            
            logger.info(f"❌ 連線已斷開: {connection_id}")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """發送個人訊息"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"發送個人訊息失敗 {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_to_group(self, message: dict, group: str):
        """廣播訊息到指定群組"""
        if group not in self.groups:
            logger.warning(f"群組不存在: {group}")
            return
        
        # 添加廣播元資料
        message.update({
            "broadcast_to": group,
            "broadcast_time": datetime.now().isoformat()
        })
        
        message_text = json.dumps(message, ensure_ascii=False)
        
        # 記錄要移除的無效連線
        invalid_connections = []
        
        for connection_id in self.groups[group].copy():
            if connection_id in self.active_connections:
                try:
                    websocket = self.active_connections[connection_id]
                    await websocket.send_text(message_text)
                except Exception as e:
                    logger.error(f"廣播失敗 {connection_id}: {e}")
                    invalid_connections.append(connection_id)
        
        # 清理無效連線
        for connection_id in invalid_connections:
            self.disconnect(connection_id)
        
        active_count = len(self.groups[group])
        logger.info(f"📡 群組 {group} 廣播完成，活躍連線: {active_count}")
    
    async def broadcast_to_all(self, message: dict):
        """廣播訊息到所有連線"""
        message.update({
            "broadcast_to": "all",
            "broadcast_time": datetime.now().isoformat()
        })
        
        message_text = json.dumps(message, ensure_ascii=False)
        invalid_connections = []
        
        # 創建字典的副本以避免在遍歷時修改
        connections_copy = dict(self.active_connections)
        
        for connection_id, websocket in connections_copy.items():
            try:
                await websocket.send_text(message_text)
            except Exception as e:
                logger.error(f"全域廣播失敗 {connection_id}: {e}")
                invalid_connections.append(connection_id)
        
        # 清理無效連線
        for connection_id in invalid_connections:
            self.disconnect(connection_id)
        
        active_count = len(self.active_connections)
        logger.info(f"📡 全域廣播完成，活躍連線: {active_count}")
    
    def get_stats(self) -> dict:
        """取得連線統計"""
        return {
            "total_connections": len(self.active_connections),
            "groups": {
                group: len(connections) 
                for group, connections in self.groups.items()
            },
            "connections": {
                connection_id: meta 
                for connection_id, meta in self.connection_meta.items()
            }
        }
    
    async def send_heartbeat(self):
        """發送心跳檢測"""
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat(),
            "server_status": "online"
        }
        
        await self.broadcast_to_all(heartbeat_message)

# 創建全域連線管理器實例
websocket_manager = ConnectionManager()

class WebSocketHandler:
    """WebSocket 處理器基類"""
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
    
    async def handle_connection(self, websocket: WebSocket, group: str):
        """處理 WebSocket 連線"""
        connection_id = await self.manager.connect(websocket, group)
        
        try:
            while True:
                # 等待客戶端訊息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 處理客戶端訊息
                await self.handle_message(message, connection_id)
                
        except WebSocketDisconnect:
            logger.info(f"客戶端主動斷開連線: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket 錯誤 {connection_id}: {e}")
        finally:
            self.manager.disconnect(connection_id)
    
    async def handle_message(self, message: dict, connection_id: str):
        """處理客戶端訊息 - 子類應覆寫此方法"""
        logger.info(f"收到訊息 {connection_id}: {message}")
        
        # 回應確認訊息
        response = {
            "type": "message_received",
            "original_message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.manager.send_personal_message(response, connection_id)
