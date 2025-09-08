"""
實時攝影機檢測服務
整合 YOLOv11 推理、WebSocket 推送和資料庫記錄
"""

import asyncio
import cv2
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from app.services.yolo_service import YOLOService
from app.services.camera_service import camera_manager
from app.services.new_database_service import DatabaseService
from app.websocket.push_service import push_yolo_detection
from app.core.logger import detection_logger
from app.core.config import settings


@dataclass
class RealtimeSession:
    """實時檢測會話"""
    task_id: str
    camera_index: int
    running: bool = False
    thread: Optional[threading.Thread] = None
    start_time: Optional[datetime] = None
    frame_count: int = 0
    detection_count: int = 0
    last_detection_time: Optional[datetime] = None


class RealtimeDetectionService:
    """實時檢測服務"""
    
    def __init__(self, queue_manager=None):
        self.yolo_service = YOLOService()
        self.active_sessions: Dict[str, RealtimeSession] = {}
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="RealTimeDetection")
        self.queue_manager = queue_manager  # 接收隊列管理器實例
        # 注意：push_service 不需要作為實例變量，我們直接使用函數調用
        
    def set_queue_manager(self, queue_manager):
        """設置隊列管理器"""
        self.queue_manager = queue_manager
        detection_logger.info("隊列管理器已設置")
        
    def __del__(self):
        """析構函數，確保資源清理"""
        # 不再負責停止隊列管理器，由 FastAPI 應用管理
        pass
        
    async def start_realtime_detection(
        self, 
        task_id: str, 
        camera_index: int,
        db_service: DatabaseService = None
    ) -> bool:
        """開始實時檢測"""
        try:
            if task_id in self.active_sessions:
                detection_logger.warning(f"任務已存在: {task_id}")
                return False
                
            # 載入 YOLO 模型
            if not self.yolo_service.is_loaded:
                model_loaded = await self.yolo_service.load_model(settings.model_path)
                if not model_loaded:
                    detection_logger.error("YOLO 模型載入失敗")
                    return False
            
            # 啟動攝影機（使用 camera_manager）
            camera_started = self._start_camera(task_id, camera_index)
            if not camera_started:
                detection_logger.error(f"攝影機啟動失敗: {camera_index}")
                return False
            
            # 創建檢測會話
            session = RealtimeSession(
                task_id=task_id,
                camera_index=camera_index,
                running=True,
                start_time=datetime.now()
            )
            
            # 啟動檢測線程
            session.thread = threading.Thread(
                target=self._detection_loop,
                args=(session, db_service),
                daemon=True
            )
            session.thread.start()
            
            self.active_sessions[task_id] = session
            
            detection_logger.info(f"實時檢測啟動成功: {task_id}, 攝影機: {camera_index}")
            
            # 推送啟動通知 - 直接使用函數調用而不是通過 self.push_service
            try:
                await push_yolo_detection(
                    task_id=task_id,
                    frame_number=0,
                    detections=[],
                    processing_time=0
                )
                print(f"✅ 推送啟動通知成功")
            except Exception as push_error:
                detection_logger.warning(f"推送啟動通知失敗: {push_error}")
            
            return True
            
        except Exception as e:
            detection_logger.error(f"實時檢測啟動失敗: {e}")
            return False
    
    async def stop_realtime_detection(self, task_id: str) -> bool:
        """停止實時檢測"""
        try:
            if task_id not in self.active_sessions:
                detection_logger.warning(f"檢測會話不存在: {task_id}")
                return False
            
            session = self.active_sessions[task_id]
            session.running = False
            
            # 等待線程結束
            if session.thread and session.thread.is_alive():
                session.thread.join(timeout=5.0)
            
            # 停止攝影機（使用 camera_manager）
            self._stop_camera(task_id)
            
            # 移除會話
            del self.active_sessions[task_id]
            
            detection_logger.info(f"實時檢測停止成功: {task_id}")
            
            # 推送停止通知 - 直接使用函數調用
            try:
                await push_yolo_detection(
                    task_id=task_id,
                    frame_number=session.frame_count,
                    detections=[],
                    processing_time=0
                )
                print(f"✅ 推送停止通知成功")
            except Exception as push_error:
                detection_logger.warning(f"推送停止通知失敗: {push_error}")
            
            return True
            
        except Exception as e:
            detection_logger.error(f"實時檢測停止失敗: {e}")
            return False
    
    def _detection_loop(self, session: RealtimeSession, db_service: DatabaseService = None):
        """檢測主循環（在獨立線程中運行）"""
        try:
            detection_logger.info(f"檢測循環啟動: {session.task_id}")
            
            while session.running:
                try:
                    # 從 camera_manager 獲取最新影格
                    camera_session = camera_manager._sessions.get(session.task_id)
                    if not camera_session:
                        detection_logger.warning(f"攝影機會話不存在: {session.task_id}")
                        time.sleep(0.1)
                        continue
                    
                    frame_data = camera_session.get_latest_frame()
                    if frame_data is None:
                        detection_logger.debug(f"無法獲取影格: {session.task_id}")
                        time.sleep(0.1)
                        continue
                    
                    timestamp, frame = frame_data
                    session.frame_count += 1
                    
                    # 每 N 幀檢測一次（控制檢測頻率）
                    detection_interval = getattr(settings, 'REALTIME_DETECTION_INTERVAL', 1)  # 改為每幀都檢測
                    if session.frame_count % detection_interval != 0:
                        continue
                    
                    detection_logger.debug(f"開始檢測第 {session.frame_count} 幀")
                    
                    # 執行 YOLO 檢測 - 使用超低的信心度閾值來提高檢測敏感度
                    detection_result = asyncio.run(
                        self.yolo_service.predict(
                            frame,
                            conf_threshold=0.1,  # 使用超低信心度閾值
                            iou_threshold=getattr(settings, 'iou_threshold', 0.45)
                        )
                    )
                    
                    detection_logger.debug(f"檢測結果: {detection_result}")
                    
                    if detection_result and detection_result.get('objects'):
                        session.detection_count += len(detection_result['objects'])
                        session.last_detection_time = datetime.now()
                        
                        detection_logger.info(f"檢測到 {len(detection_result['objects'])} 個物件")
                        
                        # 準備推送數據
                        push_data = {
                            "type": "detection",
                            "task_id": session.task_id,
                            "timestamp": session.last_detection_time.isoformat(),
                            "frame_number": session.frame_count,
                            "camera_index": session.camera_index,
                            "objects": detection_result['objects'],
                            "inference_time": detection_result.get('inference_time', 0),
                            "image_size": detection_result.get('image_size', [])
                        }
                        
                        # WebSocket 即時推送（透過隊列處理）
                        if self.queue_manager:
                            try:
                                self.queue_manager.push_websocket_data(
                                    task_id=int(session.task_id),
                                    frame_number=session.frame_count,
                                    detections=detection_result['objects'],
                                    processing_time=detection_result.get('inference_time', 0)
                                )
                                detection_logger.debug("WebSocket 推送資料已加入隊列")
                            except Exception as push_error:
                                detection_logger.error(f"WebSocket 推送失敗: {push_error}")
                        else:
                            detection_logger.warning("隊列管理器未設置，跳過 WebSocket 推送")
                        
                        # 資料庫記錄（透過隊列處理）
                        if db_service and self.queue_manager:
                            try:
                                self.queue_manager.push_database_data(
                                    task_id=session.task_id,
                                    frame_number=session.frame_count,
                                    objects=detection_result['objects'],
                                    timestamp=session.last_detection_time
                                )
                                detection_logger.debug("資料庫保存資料已加入隊列")
                            except Exception as save_error:
                                detection_logger.error(f"資料庫保存失敗: {save_error}")
                        else:
                            if not self.queue_manager:
                                detection_logger.warning("隊列管理器未設置，跳過資料庫保存")
                            elif not db_service:
                                detection_logger.error("保存檢測結果失敗: 無數據庫服務")
                    else:
                        detection_logger.debug(f"第 {session.frame_count} 幀未檢測到物件")
                    
                    # 控制檢測頻率
                    time.sleep(0.033)  # 約 30 FPS
                    
                except Exception as e:
                    detection_logger.error(f"檢測循環錯誤: {e}")
                    time.sleep(1)
            
            detection_logger.info(f"檢測循環結束: {session.task_id}")
            
        except Exception as e:
            detection_logger.error(f"檢測循環失敗: {e}")
    
    async def _save_detection_results(
        self, 
        task_id: str, 
        frame_number: int,
        objects: List[Dict],
        timestamp: datetime,
        db_service: DatabaseService
    ):
        """保存檢測結果到資料庫"""
        try:
            if not objects:
                detection_logger.debug("沒有檢測結果需要保存")
                return
                
            # 準備檢測結果資料
            detection_data = []
            for obj in objects:
                detection_data.append({
                    'frame_number': frame_number,
                    'timestamp': timestamp,
                    'object_type': obj.get('class', obj.get('class_name', 'unknown')),
                    'confidence': obj.get('confidence', 0.0),
                    'bbox_x1': obj.get('bbox', [0, 0, 0, 0])[0] if obj.get('bbox') else 0,
                    'bbox_y1': obj.get('bbox', [0, 0, 0, 0])[1] if obj.get('bbox') else 0,
                    'bbox_x2': obj.get('bbox', [0, 0, 0, 0])[2] if obj.get('bbox') else 0,
                    'bbox_y2': obj.get('bbox', [0, 0, 0, 0])[3] if obj.get('bbox') else 0,
                    'center_x': obj.get('center', {}).get('x', 0) if obj.get('center') else 0,
                    'center_y': obj.get('center', {}).get('y', 0) if obj.get('center') else 0
                })
            
            detection_logger.debug(f"準備保存 {len(detection_data)} 條檢測結果")
            
            # 使用正確的方法名稱和參數，創建資料庫會話
            from app.core.database import AsyncSessionLocal
            
            # 使用 try-except 處理併發問題
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    async with AsyncSessionLocal() as session:
                        result = await db_service.save_detection_results(
                            session=session,
                            task_id=int(task_id), 
                            detections=detection_data
                        )
                        detection_logger.debug(f"檢測結果保存成功: {result}")
                        return result
                except Exception as retry_error:
                    if attempt < max_retries - 1:
                        detection_logger.warning(f"保存重試 {attempt + 1}/{max_retries}: {retry_error}")
                        await asyncio.sleep(0.1)  # 短暫延遲
                    else:
                        raise retry_error
            
        except Exception as e:
            detection_logger.error(f"保存檢測結果失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _start_camera(self, task_id: str, camera_index: int) -> bool:
        """啟動攝影機（使用 camera_manager）"""
        try:
            session = camera_manager.create_session(
                task_id=task_id,
                camera_index=camera_index
            )
            return session is not None
        except Exception as e:
            detection_logger.error(f"攝影機啟動失敗: {e}")
            return False
    
    def _stop_camera(self, task_id: str):
        """停止攝影機（使用 camera_manager）"""
        try:
            camera_manager.stop(task_id)
        except Exception as e:
            detection_logger.error(f"攝影機停止失敗: {e}")
    
    def get_latest_frame(self, camera_index: int) -> Optional[tuple]:
        """獲取最新影格"""
        try:
            # 查找對應的攝影機會話
            for task_id, session in self.active_sessions.items():
                if session.camera_index == camera_index:
                    camera_session = camera_manager._sessions.get(task_id)
                    if camera_session:
                        return camera_session.get_latest_frame()
            return None
        except Exception as e:
            detection_logger.error(f"獲取影格失敗: {e}")
            return None
    
    def get_session_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """獲取檢測會話狀態"""
        if task_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[task_id]
        duration = (datetime.now() - session.start_time).total_seconds() if session.start_time else 0
        
        return {
            "task_id": session.task_id,
            "camera_index": session.camera_index,
            "running": session.running,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "duration_seconds": duration,
            "frame_count": session.frame_count,
            "detection_count": session.detection_count,
            "last_detection_time": session.last_detection_time.isoformat() if session.last_detection_time else None,
            "fps": session.frame_count / duration if duration > 0 else 0,
            "detection_rate": session.detection_count / session.frame_count if session.frame_count > 0 else 0
        }
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """獲取所有檢測會話狀態"""
        return [self.get_session_status(task_id) for task_id in self.active_sessions.keys()]
    
    async def cleanup(self):
        """清理資源"""
        # 停止所有檢測會話
        for task_id in list(self.active_sessions.keys()):
            await self.stop_realtime_detection(task_id)
        
        # 關閉線程池
        self.executor.shutdown(wait=True)
        
        detection_logger.info("實時檢測服務清理完成")


# 全域實例
_realtime_service = None

def get_realtime_detection_service() -> RealtimeDetectionService:
    """獲取實時檢測服務實例"""
    global _realtime_service
    if _realtime_service is None:
        _realtime_service = RealtimeDetectionService()
    return _realtime_service

def set_queue_manager_for_realtime_service(queue_manager):
    """為實時檢測服務設置隊列管理器"""
    service = get_realtime_detection_service()
    service.set_queue_manager(queue_manager)
