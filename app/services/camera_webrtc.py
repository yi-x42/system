import asyncio
from typing import Optional

import av
from aiortc import MediaStreamTrack
from aiortc.mediastreams import MediaStreamError
import numpy as np

from app.services.camera_stream_manager import (
    FrameData,
    StreamConsumer,
    camera_stream_manager,
)


class CameraStreamTrack(MediaStreamTrack):
    """將 CameraStreamManager 的影格透過 WebRTC 推送給前端。"""

    kind = "video"

    def __init__(self, camera_id: str) -> None:
        super().__init__()
        self.camera_id = camera_id
        self._loop = asyncio.get_running_loop()
        self._queue: asyncio.Queue[Optional[np.ndarray]] = asyncio.Queue(maxsize=2)
        self._consumer_id = f"webrtc_{camera_id}_{id(self)}"
        self._consumer: Optional[StreamConsumer] = None
        self._closed = False
        self._loop = asyncio.get_running_loop()

        def _on_frame(frame_data: FrameData) -> None:
            if self._closed:
                return

            def _deliver() -> None:
                if self._closed:
                    return
                try:
                    if self._queue.full():
                        try:
                            self._queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                    # 使用副本避免與其他消費者共享同一個 numpy 陣列
                    self._queue.put_nowait(frame_data.frame.copy())
                except asyncio.QueueFull:
                    pass

            try:
                self._loop.call_soon_threadsafe(_deliver)
            except RuntimeError:
                # 事件迴圈可能已經關閉
                pass

        self._consumer = StreamConsumer(self._consumer_id, _on_frame)
        added = camera_stream_manager.add_consumer(self.camera_id, self._consumer)
        if not added:
            self._closed = True
            raise RuntimeError(f"無法註冊攝影機 {self.camera_id} 的 WebRTC 消費者")

    async def recv(self) -> av.VideoFrame:
        if self._closed:
            raise MediaStreamError("Stream closed")

        frame = await self._queue.get()
        if frame is None:
            raise MediaStreamError("Stream closed")

        pts, time_base = await self.next_timestamp()
        video_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame = video_frame.reformat(format="yuv420p")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

    def stop(self) -> None:
        if self._closed:
            return

        self._closed = True

        try:
            self._loop.call_soon_threadsafe(self._signal_stop)
        except RuntimeError:
            self._signal_stop()

        if self._consumer is not None:
            camera_stream_manager.remove_consumer(self.camera_id, self._consumer_id)
            self._consumer = None

        super().stop()

    def _signal_stop(self) -> None:
        try:
            while True:
                self._queue.get_nowait()
        except asyncio.QueueEmpty:
            pass

        try:
            self._queue.put_nowait(None)
        except asyncio.QueueFull:
            pass
