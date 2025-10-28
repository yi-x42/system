import asyncio
from typing import Optional

from aiortc import MediaStreamTrack
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame


class LivePersonCameraVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.queue: Optional[asyncio.Queue] = None
        self._closed = False

    async def recv(self) -> VideoFrame:
        if self._closed:
            raise MediaStreamError("Stream closed")

        if self.queue is None:
            self.queue = await self.service.register_webrtc_consumer()

        frame = await self.queue.get()
        if frame is None:
            raise MediaStreamError("Stream closed")

        return frame

    async def stop(self) -> None:
        if self._closed:
            return

        self._closed = True

        if self.queue is not None:
            await self.service.unregister_webrtc_consumer(self.queue)
            self.queue = None

        await super().stop()
