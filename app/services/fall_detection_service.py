"""整合 FallSafe 模型的跌倒偵測服務。"""

from __future__ import annotations

import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import cv2
from ultralytics import YOLO

from app.core.config import settings
from app.core.logger import detection_logger
from app.core.paths import get_base_dir
from app.services.camera_stream_manager import camera_stream_manager, StreamConsumer
from app.services.email_notification_service import send_fall_email_alert
from app.services.notification_settings_service import get_email_settings


class FallDetectionWorker:
    """負責單一任務的跌倒偵測執行緒。"""

    def __init__(
        self,
        task_id: str,
        camera_id: str,
        device_index: int,
        confidence: Optional[float] = None,
        email_settings: Optional[dict] = None,
    ) -> None:
        self.task_id = str(task_id)
        self.camera_id = camera_id
        self.device_index = device_index
        self.confidence = confidence or settings.fall_confidence_default
        self.email_settings = email_settings or get_email_settings()
        self.model_path = settings.fall_detection_model
        self.consumer_id = f"fall-detector-{self.task_id}"
        self._queue: "queue.Queue[tuple]" = queue.Queue(maxsize=1)
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._running = threading.Event()
        self._model: Optional[YOLO] = None
        self._last_alert_time = 0.0
        self._cooldown = max(
            5.0, float(self.email_settings.get("cooldown_seconds", 30))
        )
        self._alerts_dir = (
            get_base_dir() / "uploads" / "alerts" / "fall" / self.task_id
        )
        self._alerts_dir.mkdir(parents=True, exist_ok=True)
        self._consumer = StreamConsumer(self.consumer_id, self._handle_frame)

    def _handle_frame(self, frame_data) -> None:
        if not self._running.is_set():
            return
        try:
            self._queue.put_nowait((frame_data.frame.copy(), frame_data.timestamp))
        except queue.Full:
            # 單純丟棄舊影格，保持最新
            pass

    def start(self) -> None:
        self._running.set()
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()
        try:
            self._queue.put_nowait((None, None))  # 喚醒 thread
        except queue.Full:
            pass
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _ensure_model(self) -> None:
        if self._model is None:
            self._model = YOLO(self.model_path)
            detection_logger.info(
                "跌倒偵測模型載入完成: %s", self.model_path
            )

    def _save_frame(self, frame, timestamp: datetime) -> str:
        filename = timestamp.strftime("fall_%Y%m%d_%H%M%S_%f.jpg")
        save_path = self._alerts_dir / filename
        cv2.imwrite(str(save_path), frame)
        return str(save_path)

    def _should_alert(self) -> bool:
        now = time.time()
        if now - self._last_alert_time < self._cooldown:
            return False
        self._last_alert_time = now
        return True

    def _run_loop(self) -> None:
        try:
            self._ensure_model()
        except Exception as exc:  # noqa: BLE001
            detection_logger.error(f"載入跌倒偵測模型失敗: {exc}")
            return

        model_names = {}
        if self._model and hasattr(self._model, "names"):
            model_names = self._model.names

        while self._running.is_set():
            try:
                frame_item = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            frame, timestamp = frame_item
            if frame is None:
                continue

            try:
                results = self._model.predict(
                    source=frame,
                    conf=self.confidence,
                    verbose=False,
                )
            except Exception as exc:  # noqa: BLE001
                detection_logger.error(f"跌倒偵測推論失敗: {exc}")
                continue

            if not results:
                continue

            boxes = results[0].boxes
            if boxes is None or boxes.cls is None:
                continue

            fall_detected = False
            confidences = boxes.conf.tolist() if boxes.conf is not None else []
            for idx, cls_tensor in enumerate(boxes.cls):
                class_id = int(cls_tensor.item())
                class_name = str(
                    model_names.get(class_id, str(class_id))
                    if isinstance(model_names, dict)
                    else class_id
                ).lower()
                conf_value = confidences[idx] if idx < len(confidences) else None
                if class_name == "fall" and conf_value is not None:
                    fall_detected = True
                    detected_conf = conf_value
                    break
            else:
                detected_conf = 0.0

            if fall_detected and self._should_alert():
                detection_logger.warning(
                    "[FallDetection] 任務 %s 偵測到跌倒，信心值 %.2f",
                    self.task_id,
                    detected_conf,
                )
                frame_path = self._save_frame(
                    frame,
                    timestamp if isinstance(timestamp, datetime) else datetime.utcnow(),
                )
                if self.email_settings.get("enabled") and self.email_settings.get("address"):
                    send_fall_email_alert(
                        confidence_score=detected_conf,
                        receiver_email=self.email_settings["address"],
                        frame_path=frame_path,
                    )
                else:
                    detection_logger.info(
                        "郵件通知關閉或未設定收件者，僅儲存影像: %s",
                        frame_path,
                    )

    @property
    def consumer(self) -> StreamConsumer:
        return self._consumer


class FallDetectionService:
    """管理多個跌倒偵測任務。"""

    def __init__(self) -> None:
        self._workers: Dict[str, FallDetectionWorker] = {}
        self._lock = threading.Lock()

    def start_monitoring(
        self,
        task_id: str,
        camera_id: str,
        device_index: int,
        confidence: Optional[float] = None,
    ) -> bool:
        with self._lock:
            if task_id in self._workers:
                detection_logger.info("跌倒偵測任務 %s 已在執行", task_id)
                return True

        email_settings = get_email_settings()
        worker = FallDetectionWorker(
            task_id=task_id,
            camera_id=camera_id,
            device_index=device_index,
            confidence=confidence,
            email_settings=email_settings,
        )

        success = camera_stream_manager.start_stream(camera_id, device_index)
        if not success:
            detection_logger.error("無法啟動攝影機流，跌倒偵測啟動失敗")
            return False

        if not camera_stream_manager.add_consumer(camera_id, worker.consumer):
            detection_logger.error("無法註冊跌倒偵測消費者")
            return False

        worker.start()
        with self._lock:
            self._workers[task_id] = worker
        detection_logger.info(
            "已啟動跌倒偵測任務 %s (攝影機 %s)", task_id, camera_id
        )
        return True

    def stop_monitoring(self, task_id: str) -> None:
        with self._lock:
            worker = self._workers.pop(task_id, None)

        if not worker:
            return

        worker.stop()
        camera_stream_manager.remove_consumer(worker.camera_id, worker.consumer_id)
        detection_logger.info("跌倒偵測任務 %s 已停止", task_id)


fall_detection_service = FallDetectionService()
