"""
異步隊列管理器
處理從同步線程向異步操作發送資料的問題
"""

import asyncio
import queue
import threading
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from app.core.logger import get_logger
from app.websocket.push_service import push_yolo_detection
from app.services.new_database_service import DatabaseService

logger = get_logger(__name__)

class AsyncQueueManager:
    """異步隊列管理器，處理資料庫保存和 WebSocket 推送"""
    
    def __init__(self):
        self.websocket_queue = queue.Queue()
        self.database_queue = queue.Queue()
        self.running = False
        self.worker_threads = []
        self.event_loop = None
        
    def start(self):
        """啟動隊列處理器"""
        if self.running:
            return
            
        self.running = True
        
        # 啟動 WebSocket 推送處理線程
        websocket_thread = threading.Thread(
            target=self._websocket_worker,
            name="WebSocketWorker",
            daemon=True
        )
        websocket_thread.start()
        self.worker_threads.append(websocket_thread)
        
        # 啟動資料庫保存處理線程
        database_thread = threading.Thread(
            target=self._database_worker,
            name="DatabaseWorker", 
            daemon=True
        )
        database_thread.start()
        self.worker_threads.append(database_thread)
        
        logger.info("異步隊列管理器已啟動")
    
    def stop(self):
        """停止隊列處理器"""
        self.running = False
        
        # 發送停止信號
        self.websocket_queue.put(None)
        self.database_queue.put(None)
        
        # 等待線程結束
        for thread in self.worker_threads:
            thread.join(timeout=5.0)
        
        self.worker_threads.clear()
        logger.info("異步隊列管理器已停止")
    
    def push_websocket_data(self, task_id: int, frame_number: int, detections: List[Dict], processing_time: float = 0):
        """將 WebSocket 推送資料加入隊列"""
        try:
            data = {
                'task_id': task_id,
                'frame_number': frame_number, 
                'detections': detections,
                'processing_time': processing_time,
                'timestamp': time.time()
            }
            self.websocket_queue.put(data, block=False)
            logger.debug(f"WebSocket 推送資料已加入隊列: {task_id}")
        except queue.Full:
            logger.warning(f"WebSocket 隊列已滿，跳過推送: {task_id}")
        except Exception as e:
            logger.error(f"WebSocket 推送資料加入隊列失敗: {e}")
    
    def push_database_data(self, task_id: str, frame_number: int, objects: List[Dict], timestamp: datetime):
        """將資料庫保存資料加入隊列"""
        try:
            data = {
                'task_id': task_id,
                'frame_number': frame_number,
                'objects': objects,
                'timestamp': timestamp.isoformat(),
                'queue_time': time.time()
            }
            self.database_queue.put(data, block=False)
            logger.debug(f"資料庫保存資料已加入隊列: {task_id}")
        except queue.Full:
            logger.warning(f"資料庫隊列已滿，跳過保存: {task_id}")
        except Exception as e:
            logger.error(f"資料庫保存資料加入隊列失敗: {e}")
    
    def _websocket_worker(self):
        """WebSocket 推送工作線程"""
        logger.info("WebSocket 工作線程已啟動")
        
        # 創建新的事件循環
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            while self.running:
                try:
                    # 獲取隊列資料（阻塞等待）
                    data = self.websocket_queue.get(timeout=1.0)
                    
                    # 檢查停止信號
                    if data is None:
                        break
                    
                    # 執行異步推送
                    try:
                        loop.run_until_complete(self._push_websocket_async(data))
                        logger.debug(f"WebSocket 推送成功: {data['task_id']}")
                    except Exception as push_error:
                        logger.error(f"WebSocket 推送失敗: {push_error}")
                    
                    # 標記任務完成
                    self.websocket_queue.task_done()
                    
                except queue.Empty:
                    # 超時是正常的，繼續循環
                    continue
                except Exception as e:
                    logger.error(f"WebSocket 工作線程錯誤: {e}")
                    
        finally:
            loop.close()
            logger.info("WebSocket 工作線程已結束")
    
    def _database_worker(self):
        """資料庫保存工作線程"""
        logger.info("資料庫工作線程已啟動")
        
        # 創建新的事件循環
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 在工作線程中創建獨立的資料庫引擎和會話工廠
        try:
            from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
            from app.core.config import settings
            
            # 創建線程專用的異步引擎
            thread_engine = create_async_engine(
                settings.DATABASE_URL,
                pool_size=2,  # 較小的連接池
                max_overflow=0,
                echo=False,
                future=True
            )
            
            # 創建線程專用的會話工廠
            ThreadSessionLocal = async_sessionmaker(
                bind=thread_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("資料庫工作線程引擎已創建")
            
        except Exception as engine_error:
            logger.error(f"資料庫引擎創建失敗: {engine_error}")
            return
        
        try:
            while self.running:
                try:
                    # 獲取隊列資料（阻塞等待）
                    data = self.database_queue.get(timeout=1.0)
                    
                    # 檢查停止信號
                    if data is None:
                        break
                    
                    # 執行異步保存
                    try:
                        loop.run_until_complete(
                            self._save_database_async_thread_safe(data, ThreadSessionLocal)
                        )
                        logger.debug(f"資料庫保存成功: {data['task_id']}")
                    except Exception as save_error:
                        logger.error(f"資料庫保存失敗: {save_error}")
                    
                    # 標記任務完成
                    self.database_queue.task_done()
                    
                except queue.Empty:
                    # 超時是正常的，繼續循環
                    continue
                except Exception as e:
                    logger.error(f"資料庫工作線程錯誤: {e}")
                    
        finally:
            # 清理資源
            try:
                loop.run_until_complete(thread_engine.dispose())
                logger.info("資料庫引擎已關閉")
            except Exception as cleanup_error:
                logger.error(f"資料庫引擎清理失敗: {cleanup_error}")
            
            loop.close()
            logger.info("資料庫工作線程已停止")
    
    async def _save_database_async_thread_safe(self, data: Dict, SessionLocal):
        """線程安全的異步資料庫保存方法"""
        try:
            logger.debug(f"開始保存檢測結果: {data['task_id']}")
            
            if not data.get('objects'):
                logger.debug("沒有檢測結果需要保存")
                return
                
            # 準備檢測結果資料
            detection_data = []
            for obj in data['objects']:
                detection_data.append({
                    'frame_number': data['frame_number'],
                    'timestamp': datetime.fromisoformat(data['timestamp']),
                    'object_type': obj.get('class', obj.get('class_name', 'unknown')),
                    'confidence': obj.get('confidence', 0.0),
                    'bbox_x1': obj.get('bbox', [0, 0, 0, 0])[0] if obj.get('bbox') else 0,
                    'bbox_y1': obj.get('bbox', [0, 0, 0, 0])[1] if obj.get('bbox') else 0,
                    'bbox_x2': obj.get('bbox', [0, 0, 0, 0])[2] if obj.get('bbox') else 0,
                    'bbox_y2': obj.get('bbox', [0, 0, 0, 0])[3] if obj.get('bbox') else 0,
                    'center_x': obj.get('center', {}).get('x', 0) if obj.get('center') else 0,
                    'center_y': obj.get('center', {}).get('y', 0) if obj.get('center') else 0
                })
            
            # 創建資料庫服務實例
            from app.services.new_database_service import DatabaseService
            db_service = DatabaseService()
            
            # 使用線程專用的會話工廠
            async with SessionLocal() as session:
                result = await db_service.save_detection_results(
                    session=session,
                    task_id=int(data['task_id']), 
                    detections=detection_data
                )
                logger.debug(f"檢測結果保存成功: {result}")
                return result
            
        except Exception as e:
            logger.error(f"資料庫保存異步執行失敗: {e}")
            raise
            logger.info("資料庫工作線程已結束")
    
    async def _push_websocket_async(self, data: Dict):
        """異步執行 WebSocket 推送"""
        try:
            await push_yolo_detection(
                task_id=data['task_id'],
                frame_number=data['frame_number'],
                detections=data['detections'],
                processing_time=data['processing_time']
            )
        except Exception as e:
            logger.error(f"WebSocket 推送異步執行失敗: {e}")
            raise

# 全局隊列管理器實例
_queue_manager = None

def get_queue_manager() -> AsyncQueueManager:
    """獲取全局隊列管理器實例"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = AsyncQueueManager()
    return _queue_manager

def start_queue_manager():
    """啟動全局隊列管理器"""
    manager = get_queue_manager()
    manager.start()

def stop_queue_manager():
    """停止全局隊列管理器"""
    global _queue_manager
    if _queue_manager is not None:
        _queue_manager.stop()
        _queue_manager = None
