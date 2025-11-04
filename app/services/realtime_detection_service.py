"""
實時攝影機檢測服務
整合 YOLOv11 推理、WebSocket 推送和資料庫記錄
使用共享視訊流避免攝影機資源衝突
"""

import asyncio
import threading
import time
import base64
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import cv2

from fastapi import WebSocket
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
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    external_source: bool = False
    db_service: Optional[DatabaseService] = None


class RealtimeDetectionService:
    """實時檢測服務 - 使用共享視訊流"""
    
    def __init__(self, queue_manager=None):
        self.yolo_service = YOLOService()
        self.active_sessions: Dict[str, RealtimeSession] = {}
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="RealTimeDetection")
        self.queue_manager = queue_manager
        self.preview_clients: Dict[str, Set[WebSocket]] = {}
        self.preview_payloads: Dict[str, Dict[str, Any]] = {}
        self.preview_payload_lock = threading.Lock()
        self.preview_last_sent: Dict[str, float] = {}
        self.preview_interval = 1.0 / 10.0
        self.preview_clients_lock: Optional[asyncio.Lock] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
    def set_queue_manager(self, queue_manager):
        """設置隊列管理器"""
        self.queue_manager = queue_manager
        detection_logger.info("隊列管理器已設置")
        
    async def start_realtime_detection(
        self, 
        task_id: str, 
        camera_id: str,
        device_index: int,
        db_service: DatabaseService = None,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        model_path: Optional[str] = None,
        external_source: bool = False,
    ) -> bool:
        """開始實時檢測 - 使用共享視訊流（支援動態模型切換）"""
        try:
            detection_logger.debug(
                f"[start_realtime_detection] 收到啟動請求 task_id={task_id} camera_id={camera_id} device_index={device_index} "
                f"conf={confidence_threshold} iou={iou_threshold} model_path={model_path} external={external_source}"
            )
            if task_id in self.active_sessions:
                detection_logger.warning(f"任務已存在: {task_id}")
                return False
                
            # 模型載入 / 切換
            target_model_path = model_path or settings.model_path
            if (not self.yolo_service.is_loaded) or (self.yolo_service._model_path != target_model_path):
                detection_logger.info(f"載入/切換 YOLO 模型: {target_model_path}")
                loaded = await self.yolo_service.load_model(target_model_path)
                if not loaded:
                    detection_logger.error(f"YOLO 模型載入失敗: {target_model_path}")
                    return False
            else:
                detection_logger.info(f"沿用已載入模型: {self.yolo_service._model_path}")
            
            session = RealtimeSession(
                task_id=task_id,
                camera_id=camera_id,
                running=True,
                start_time=datetime.now(),
                consumer_id=f"detection_{task_id}",
                confidence_threshold=confidence_threshold,
                iou_threshold=iou_threshold,
                external_source=external_source,
                db_service=db_service,
            )
            
            if external_source:
                session.consumer_id = None
                self.active_sessions[task_id] = session
                detection_logger.info(f"實時檢測啟動成功 (等待客戶端影像): {task_id}, 模型: {target_model_path}")
                return True

            # 確保攝影機流正在運行
            if not camera_stream_manager.is_stream_running(camera_id):
                detection_logger.info(f"啟動攝影機流: {camera_id}")
                success = camera_stream_manager.start_stream(camera_id, device_index)
                if not success:
                    detection_logger.error(f"攝影機流啟動失敗: {camera_id}")
                    return False
            
            consumer = StreamConsumer(
                consumer_id=session.consumer_id,
                callback=self._create_frame_callback(session, db_service)
            )
            
            success = camera_stream_manager.add_consumer(camera_id, consumer)
            if not success:
                detection_logger.error(f"無法添加檢測消費者到攝影機流 {camera_id}")
                return False
            
            self.active_sessions[task_id] = session
            detection_logger.info(f"實時檢測啟動成功: {task_id}, 攝影機: {camera_id}, 模型: {target_model_path}")
            detection_logger.debug(
                f"[start_realtime_detection] 建立會話: task_id={task_id} consumer_id={session.consumer_id} "
                f"active_sessions={list(self.active_sessions.keys())}"
            )
            return True
            
        except Exception as e:
            detection_logger.error(f"實時檢測啟動失敗: {e}")
            return False

    def _create_frame_callback(self, session: RealtimeSession, db_service: DatabaseService = None):
        """創建幀處理回調函數"""
        def frame_callback(frame_data: FrameData):
            try:
                detection_logger.debug(
                    f"[frame_callback] task_id={session.task_id} 收到幀 frame_number={frame_data.frame_number} "
                    f"camera_id={frame_data.camera_id} consumers={len(camera_stream_manager.streams.get(frame_data.camera_id).consumers) if camera_stream_manager.streams.get(frame_data.camera_id) else 'NA'}"
                )
            except Exception:
                pass
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

    async def register_preview_client(self, task_id: str, websocket: WebSocket) -> None:
        """註冊即時預覽 WebSocket 客戶端"""
        if self.preview_clients_lock is None:
            self.preview_clients_lock = asyncio.Lock()

        await websocket.accept()

        if self.loop is None:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = None

        async with self.preview_clients_lock:
            clients = self.preview_clients.setdefault(task_id, set())
            clients.add(websocket)

        with self.preview_payload_lock:
            payload = self.preview_payloads.get(task_id)

        if payload:
            try:
                await websocket.send_json(payload)
            except Exception as e:
                detection_logger.debug(f"推送歷史預覽給客戶端失敗: {e}")

    async def unregister_preview_client(self, task_id: str, websocket: WebSocket) -> None:
        """移除即時預覽 WebSocket 客戶端"""
        if self.preview_clients_lock is None:
            return

        async with self.preview_clients_lock:
            clients = self.preview_clients.get(task_id)
            if clients and websocket in clients:
                clients.discard(websocket)
                if not clients:
                    self.preview_clients.pop(task_id, None)
                    self.preview_last_sent.pop(task_id, None)

    async def _close_preview_clients(self, task_id: str) -> None:
        if self.preview_clients_lock is None:
            return

        async with self.preview_clients_lock:
            clients = list(self.preview_clients.pop(task_id, set()))
            self.preview_last_sent.pop(task_id, None)

        for websocket in clients:
            try:
                await websocket.close()
            except Exception:
                pass

        with self.preview_payload_lock:
            self.preview_payloads.pop(task_id, None)

    async def _broadcast_preview(self, task_id: str, payload: Dict[str, Any]) -> None:
        if self.preview_clients_lock is None:
            return

        async with self.preview_clients_lock:
            clients = list(self.preview_clients.get(task_id, set()))

        if not clients:
            return

        stale_clients: List[WebSocket] = []
        for websocket in clients:
            try:
                await websocket.send_json(payload)
            except Exception as e:
                detection_logger.debug(f"推送即時預覽失敗: {e}")
                stale_clients.append(websocket)

        if stale_clients and self.preview_clients_lock:
            async with self.preview_clients_lock:
                client_set = self.preview_clients.get(task_id)
                if client_set:
                    for websocket in stale_clients:
                        client_set.discard(websocket)
                    if not client_set:
                        self.preview_clients.pop(task_id, None)

    def _schedule_preview_broadcast(self, task_id: str, payload: Dict[str, Any]) -> None:
        if not self.loop:
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self._broadcast_preview(task_id, payload),
                self.loop,
            )
        except Exception as e:
            detection_logger.debug(f"排程預覽推播失敗: {e}")

    async def ingest_external_frame(self, task_id: str, frame_bytes: bytes, db_service: Optional[DatabaseService] = None) -> bool:
        """處理來自客戶端上傳的影像幀"""
        session = self.active_sessions.get(task_id)
        if not session:
            detection_logger.warning(f"[ingest_external_frame] 任務不存在: {task_id}")
            return False

        if not session.external_source:
            detection_logger.warning(f"[ingest_external_frame] 任務 {task_id} 非外部來源，忽略傳入影像")
            return False

        if not session.running:
            detection_logger.debug(f"[ingest_external_frame] 任務 {task_id} 已停止，忽略影像")
            return False

        np_data = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
        if frame is None:
            detection_logger.debug(f"[ingest_external_frame] 任務 {task_id} 影像解碼失敗")
            return False

        frame_data = FrameData(
            frame=frame,
            timestamp=datetime.now(),
            frame_number=session.frame_count + 1,
            camera_id=session.camera_id,
        )

        loop = asyncio.get_running_loop()
        db_instance = db_service or session.db_service or DatabaseService()
        session.db_service = db_instance

        try:
            await loop.run_in_executor(
                self.executor,
                self._process_frame,
                session,
                frame_data,
                db_instance,
            )
            return True
        except Exception as e:
            detection_logger.error(f"[ingest_external_frame] 任務 {task_id} 處理影像失敗: {e}")
            return False

    def _process_frame(self, session: RealtimeSession, frame_data: FrameData, db_service: DatabaseService = None):
        """處理單一幀數據"""
        try:
            # 檢查會話狀態
            if not session.running:
                return
            
            # 檢查任務的資料庫狀態（每30幀檢查一次，避免頻繁查詢）
            if session.frame_count % 30 == 0:
                if db_service:
                    try:
                        task_status = db_service.get_task_status_sync(session.task_id)
                        
                        # 🔥 修復：如果任務不存在或已停止，立即停止檢測
                        if task_status is None:
                            detection_logger.warning(f"任務 {session.task_id} 不存在，停止檢測處理")
                            session.running = False
                            return
                        
                        if task_status in ['paused', 'completed', 'failed', 'stopped']:
                            detection_logger.info(f"任務 {session.task_id} 狀態為 {task_status}，停止處理幀")
                            if task_status == 'paused':
                                # 暫停狀態：停止處理但不清理會話，等待恢復
                                detection_logger.info(f"任務 {session.task_id} 已暫停，跳過幀處理")
                                return
                            else:
                                # 其他狀態：停止會話
                                session.running = False
                                return
                    except Exception as e:
                        detection_logger.error(f"檢查任務狀態失敗: {e}")
                        # 出現異常時，為安全起見，停止處理
                        detection_logger.warning(f"由於無法檢查任務狀態，停止任務 {session.task_id} 的處理")
                        session.running = False
                        return
            
            frame = frame_data.frame
            timestamp = frame_data.timestamp
            timestamp_seconds = (
                timestamp.timestamp() if hasattr(timestamp, "timestamp") else time.time()
            )
            
            # 更新幀計數
            session.frame_count += 1
            if session.frame_count <= 5 or session.frame_count % 30 == 0:
                detection_logger.debug(
                    f"[_process_frame] task_id={session.task_id} 處理幀 frame_count={session.frame_count} timestamp={timestamp.isoformat()} "
                    f"frame_shape={frame.shape if hasattr(frame, 'shape') else 'NA'}"
                )
            
            # 執行 YOLO 推理 - 使用會話中的信心度閾值
            predictions = self.yolo_service.predict_frame(
                frame, 
                conf_threshold=session.confidence_threshold,
                iou_threshold=session.iou_threshold
            )
            if session.frame_count <= 5 or session.frame_count % 30 == 0:
                detection_logger.debug(
                    f"[_process_frame] task_id={session.task_id} 預測完成 幀={session.frame_count} 預測數={len(predictions) if predictions else 0}"
                )
            
            should_send_preview = False
            preview_payload: Optional[Dict[str, Any]] = None
            now_monotonic = time.time()
            last_sent = self.preview_last_sent.get(session.task_id, 0.0)
            if now_monotonic - last_sent >= self.preview_interval:
                should_send_preview = True
            
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
                        if len(detection_results) > 0 and (session.frame_count <=5 or session.frame_count % 30 == 0):
                            detection_logger.debug(
                                f"[_process_frame] 第一筆檢測樣本: {detection_results[0]}"
                            )
                        
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
                                    if len(detection_results) > 0 and (session.frame_count <=5 or session.frame_count % 30 == 0):
                                        detection_logger.debug(
                                            f"[save_detections] 插入完成 樣本 task_id={session.task_id} frame={session.frame_count}"
                                        )
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

            if should_send_preview:
                if hasattr(frame, "shape") and len(frame.shape) >= 2:
                    frame_height = int(frame.shape[0])
                    frame_width = int(frame.shape[1])
                else:
                    frame_height = 0
                    frame_width = 0

                prediction_list = predictions or []
                preview_detections: List[Dict[str, Any]] = []
                for detection in prediction_list:
                    bbox = detection.get("bbox") or detection.get("bbox_detailed")
                    if not bbox or len(bbox) != 4:
                        continue
                    x1, y1, x2, y2 = bbox
                    preview_detections.append(
                        {
                            "bbox": [
                                float(max(0, min(frame_width, x1))),
                                float(max(0, min(frame_height, y1))),
                                float(max(0, min(frame_width, x2))),
                                float(max(0, min(frame_height, y2))),
                            ],
                            "label": detection.get("class") or detection.get("class_name"),
                            "confidence": detection.get("confidence"),
                            "class_id": detection.get("class_id"),
                            "tracker_id": detection.get("tracker_id"),
                        }
                    )

                encoded_image: Optional[str] = None
                if not session.external_source:
                    try:
                        frame_to_draw = frame.copy()
                        for detection in preview_detections:
                            bbox = detection.get("bbox", [0.0, 0.0, 0.0, 0.0])
                            x1, y1, x2, y2 = map(int, bbox)
                            cv2.rectangle(frame_to_draw, (x1, y1), (x2, y2), (34, 211, 238), 2)

                            label_parts = []
                            label_text = detection.get("label")
                            if label_text:
                                label_parts.append(str(label_text))
                            confidence = detection.get("confidence")
                            if isinstance(confidence, (int, float)):
                                label_parts.append(f"{confidence * 100:.0f}%")
                            label_str = " • ".join(label_parts)
                            if label_str:
                                cv2.rectangle(
                                    frame_to_draw,
                                    (x1, max(0, y1 - 24)),
                                    (x1 + max(60, int(len(label_str) * 9)), y1),
                                    (15, 23, 42),
                                    cv2.FILLED,
                                )
                                cv2.putText(
                                    frame_to_draw,
                                    label_str,
                                    (x1 + 4, y1 - 6),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.45,
                                    (248, 250, 252),
                                    1,
                                    cv2.LINE_AA,
                                )

                        success, buffer = cv2.imencode(".jpg", frame_to_draw, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        if success:
                            encoded_image = base64.b64encode(buffer).decode("ascii")
                    except Exception as encode_error:
                        detection_logger.debug(f"預覽影像編碼失敗: {encode_error}")

                preview_payload = {
                    "type": "frame",
                    "task_id": session.task_id,
                    "frame_number": session.frame_count,
                    "timestamp": timestamp_seconds,
                    "width": frame_width,
                    "height": frame_height,
                    "detections": preview_detections,
                }

                if encoded_image:
                    preview_payload["image"] = encoded_image

                with self.preview_payload_lock:
                    self.preview_payloads[session.task_id] = preview_payload
                    self.preview_last_sent[session.task_id] = now_monotonic

                self._schedule_preview_broadcast(session.task_id, preview_payload)
                
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

            await self._close_preview_clients(task_id)
            
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






