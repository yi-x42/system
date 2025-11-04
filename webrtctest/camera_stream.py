import threading
import time
from typing import Optional

import cv2
import numpy as np


class CameraStream:
    """以獨立線程持續從 OpenCV 攝影機擷取影格，供 WebRTC 取用。"""

    def __init__(self, device_index: int = 0, poll_delay: float = 0.01) -> None:
        self.device_index = device_index
        self.poll_delay = poll_delay
        self._capture: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._lock = threading.Lock()
        self._frame: Optional[np.ndarray] = None

    def start(self) -> None:
        """啟動攝影機線程，若已啟動則忽略。"""
        if self._thread and self._thread.is_alive():
            return

        capture = cv2.VideoCapture(self.device_index)
        if not capture.isOpened():
            raise RuntimeError(f"無法開啟攝影機 device_index={self.device_index}")

        self._capture = capture
        self._running.set()
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止線程並釋放攝影機資源。"""
        self._running.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

        if self._capture:
            self._capture.release()
            self._capture = None

        with self._lock:
            self._frame = None

    def read(self) -> Optional[np.ndarray]:
        """取得最新影格的複本，若暫無影格則回傳 None。"""
        with self._lock:
            if self._frame is None:
                return None
            return self._frame.copy()

    def _reader_loop(self) -> None:
        """線程主迴圈：持續讀取影格並儲存最新結果。"""
        assert self._capture is not None

        while self._running.is_set():
            success, frame = self._capture.read()
            if success:
                with self._lock:
                    self._frame = frame
            else:
                # 若讀取失敗稍候再試，避免忙碌等待。
                time.sleep(max(self.poll_delay, 0.05))
                continue

            time.sleep(self.poll_delay)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
