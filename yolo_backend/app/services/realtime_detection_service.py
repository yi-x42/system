"""
實時攝影機檢測服務
整合 YOLOv11 推理、WebSocket 推送和資料庫記錄
使用共享視訊流避免攝影機資源衝突
"""

import asyncio
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from app.services.yolo_service import YOLOService
from app.services.camera_stream_manager import camera_stream_manager, StreamConsumer, FrameData
from app.services.new_database_service import DatabaseService
from app.websocket.push_service import push_yolo_detection
from app.core.logger import detection_logger
from app.core.config import settings


@dataclass
class RealtimeSession:
    """實時檢測會話"""
    task_id: str
    camera_id: str
    running: bool = False
    start_time: Optional[datetime] = None
    frame_count: int = 0
    detection_count: int = 0
    last_detection_time: Optional[datetime] = None
    consumer_id: Optional[str] = None


class RealtimeDetectionService:
    """實時檢測服務 - 使用共享視訊流"""
    
    def __init__(self, queue_manager=None):
        self.yolo_service = YOLOService()
        self.active_sessions: Dict[str, RealtimeSession] = {}
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="RealTimeDetection")
        self.queue_manager = queue_manager
        
    def set_queue_manager(self, queue_manager):
        """設置隊列管理器"""
        self.queue_manager = queue_manager
        detection_logger.info("隊列管理器已設置")
        
    async def start_realtime_detection(
        self, 
        task_id: str, 
        camera_id: str,
        device_index: int,
        db_service: DatabaseService = None
    ) -> bool:
        """開始實時檢測 - 使用共享視訊流"""
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
            
            # 確保攝影機流正在運行
            if not camera_stream_manager.is_stream_running(camera_id):
                detection_logger.info(f"啟動攝影機流: {camera_id}")
                success = camera_stream_manager.start_stream(camera_id, device_index)
                if not success:
                    detection_logger.error(f"攝影機流啟動失敗: {camera_id}")
                    return False
            
            # 創建檢測會話
            session = RealtimeSession(
                task_id=task_id,
                camera_id=camera_id,
                running=True,
                start_time=datetime.now(),
                consumer_id=f"detection_{task_id}"
            )
            
            # 創建流消費者
            consumer = StreamConsumer(
                consumer_id=session.consumer_id,
                callback=self._create_frame_callback(session, db_service)
            )
            
            # 將消費者添加到攝影機流
            success = camera_stream_manager.add_consumer(camera_id, consumer)
            if not success:
                detection_logger.error(f"無法添加檢測消費者到攝影機流 {camera_id}")
                return False
            
            self.active_sessions[task_id] = session
            
            detection_logger.info(f"實時檢測啟動成功: {task_id}, 攝影機: {camera_id}")
            return True
            
        except Exception as e:
            detection_logger.error(f"實時檢測啟動失敗: {e}")
            return False

    def _create_frame_callback(self, session: RealtimeSession, db_service: DatabaseService = None):
        """創建幀處理回調函數"""
        def frame_callback(frame_data: FrameData):
            self._process_frame(session, frame_data, db_service)
        return frame_callback

    def _push_detection_async(self, detection_data: dict):
        """異步推送檢測結果"""
        try:
            # 在新的事件循環中執行異步函數
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 解構檢測數據，傳遞正確的參數
                task_id = detection_data.get('task_id')
                frame_number = detection_data.get('frame_number')
                detections = detection_data.get('detections', [])
                
                loop.run_until_complete(
                    push_yolo_detection(
                        task_id=int(task_id),
                        frame_number=frame_number,
                        detections=detections
                    )
                )
            finally:
                loop.close()
        except Exception as e:
            detection_logger.error(f"WebSocket 推送執行失敗: {e}")

    def _process_frame(self, session: RealtimeSession, frame_data: FrameData, db_service: DatabaseService = None):
        """處理單一幀數據"""
        try:
            frame = frame_data.frame
            timestamp = frame_data.timestamp
            
            # 更新幀計數
            session.frame_count += 1
            
            # 執行 YOLO 推理
            predictions = self.yolo_service.predict_frame(frame)
            
            if predictions and len(predictions) > 0:
                session.detection_count += len(predictions)
                session.last_detection_time = timestamp
                
                # 準備檢測結果
                detection_data = {
                    'task_id': session.task_id,
                    'timestamp': timestamp.isoformat(),
                    'frame_number': session.frame_count,
                    'detections': predictions,
                    'frame_shape': frame.shape
                }
                
                # WebSocket 推送（使用線程池處理）
                try:
                    # 使用執行器來處理異步操作
                    self.executor.submit(self._push_detection_async, detection_data)
                except Exception as e:
                    detection_logger.error(f"WebSocket 推送提交失敗: {e}")
                
                # 資料庫記錄
                if db_service:
                    try:
                        # 準備檢測結果數據
                        detection_results = []
                        for detection in predictions:
                            detection_data = {
                                'task_id': session.task_id,
                                'frame_number': session.frame_count,
                                'timestamp': timestamp,
                                'object_type': detection.get('class', 'unknown'),
                                'confidence': detection.get('confidence', 0.0),
                                'bbox_x1': detection.get('bbox', [0, 0, 0, 0])[0],
                                'bbox_y1': detection.get('bbox', [0, 0, 0, 0])[1],
                                'bbox_x2': detection.get('bbox', [0, 0, 0, 0])[2],
                                'bbox_y2': detection.get('bbox', [0, 0, 0, 0])[3],
                                'center_x': (detection.get('bbox', [0, 0, 0, 0])[0] + detection.get('bbox', [0, 0, 0, 0])[2]) / 2,
                                'center_y': (detection.get('bbox', [0, 0, 0, 0])[1] + detection.get('bbox', [0, 0, 0, 0])[3]) / 2
                            }
                            detection_results.append(detection_data)
                        
                        # 儲存檢測結果到資料庫
                        detection_logger.debug(f"準備儲存 {len(detection_results)} 個檢測結果到任務 {session.task_id}")
                        
                        # 使用執行器避免阻塞主循環
                        try:
                            # 在線程池中執行資料庫操作
                            def save_detections():
                                try:
                                    # 使用新的同步儲存方法
                                    local_db = DatabaseService()
                                    for detection_result in detection_results:
                                        success = local_db.create_detection_result_sync(detection_result)
                                        if not success:
                                            detection_logger.error(f"儲存檢測結果失敗: {detection_result}")
                                    detection_logger.debug(f"成功提交儲存 {len(detection_results)} 個檢測結果")
                                except Exception as e:
                                    detection_logger.error(f"線程中儲存檢測結果失敗: {e}")
                            
                            # 在執行器中非同步執行
                            self.executor.submit(save_detections)
                            
                        except Exception as e:
                            detection_logger.error(f"提交資料庫儲存任務失敗: {e}")
                            
                    except Exception as e:
                        detection_logger.error(f"資料庫保存失敗: {e}")
                
                detection_logger.debug(
                    f"檢測結果 [{session.task_id}] 幀:{session.frame_count} "
                    f"物件數量:{len(predictions)}"
                )
                
        except Exception as e:
            detection_logger.error(f"幀處理失敗 [{session.task_id}]: {e}")
    
    async def stop_realtime_detection(self, task_id: str) -> bool:
        """停止實時檢測"""
        try:
            session = self.active_sessions.get(task_id)
            if not session:
                detection_logger.warning(f"未找到會話: {task_id}")
                return False
            
            # 標記會話為停止狀態
            session.running = False
            
            # 從攝影機流中移除消費者
            if session.consumer_id:
                camera_stream_manager.remove_consumer(session.camera_id, session.consumer_id)
            
            # 移除會話
            del self.active_sessions[task_id]
            
            detection_logger.info(f"實時檢測已停止: {task_id}")
            return True
            
        except Exception as e:
            detection_logger.error(f"停止實時檢測失敗: {e}")
            return False
    
    def get_session_stats(self, task_id: str) -> Optional[Dict[str, Any]]:
        """獲取會話統計信息"""
        session = self.active_sessions.get(task_id)
        if not session:
            return None
            
        runtime = 0
        if session.start_time:
            runtime = (datetime.now() - session.start_time).total_seconds()
            
        return {
            'task_id': task_id,
            'camera_id': session.camera_id,
            'running': session.running,
            'runtime_seconds': runtime,
            'frame_count': session.frame_count,
            'detection_count': session.detection_count,
            'last_detection_time': session.last_detection_time.isoformat() if session.last_detection_time else None
        }
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """列出所有活動會話"""
        return [
            self.get_session_stats(task_id) 
            for task_id in self.active_sessions.keys()
        ]
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """獲取所有會話（與 list_active_sessions 相同）"""
        return self.list_active_sessions()
    
    def cleanup(self):
        """清理資源"""
        # 停止所有活動會話
        for task_id in list(self.active_sessions.keys()):
            # 使用同步方式清理
            try:
                session = self.active_sessions.get(task_id)
                if session and session.consumer_id:
                    camera_stream_manager.remove_consumer(session.camera_id, session.consumer_id)
                del self.active_sessions[task_id]
            except Exception as e:
                detection_logger.error(f"清理會話 {task_id} 失敗: {e}")
        
        # 關閉執行器
        self.executor.shutdown(wait=False)
        detection_logger.info("實時檢測服務已清理")


# 全域服務實例
realtime_detection_service = RealtimeDetectionService()

def get_realtime_detection_service() -> RealtimeDetectionService:
    """獲取實時檢測服務實例"""
    return realtime_detection_service

def set_queue_manager_for_realtime_service(queue_manager):
    """為實時檢測服務設置隊列管理器"""
    realtime_detection_service.set_queue_manager(queue_manager)
