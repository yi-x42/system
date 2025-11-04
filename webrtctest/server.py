import asyncio
import logging
from typing import Set

import av
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack

from camera_stream import CameraStream

logger = logging.getLogger("webrtctest.server")


class Offer(BaseModel):
    sdp: str
    type: str


class CameraVideoTrack(VideoStreamTrack):
    """將 CameraStream 的影格餵給 WebRTC PeerConnection。"""

    def __init__(self, stream: CameraStream, *, fps: int = 30) -> None:
        super().__init__()  # 初始化時間戳管理
        self.stream = stream
        self.frame_interval = 1 / fps if fps else 1 / 30

    async def recv(self) -> av.VideoFrame:
        pts, time_base = await self.next_timestamp()

        frame = self.stream.read()
        while frame is None:
            await asyncio.sleep(self.frame_interval)
            frame = self.stream.read()

        video_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame


camera_stream = CameraStream()
pcs: Set[RTCPeerConnection] = set()

app = FastAPI(title="WebRTC Camera Streaming")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    camera_stream.start()
    logger.info("Camera stream started.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    camera_stream.stop()
    await asyncio.gather(*(pc.close() for pc in pcs), return_exceptions=True)
    pcs.clear()
    logger.info("Server shutdown complete.")


async def cleanup_pc(pc: RTCPeerConnection) -> None:
    await pc.close()
    pcs.discard(pc)


@app.post("/offer")
async def handle_offer(offer: Offer):
    frame = camera_stream.read()
    if frame is None:
        # 嘗試再啟動一次，避免攝影機意外停用。
        try:
            camera_stream.start()
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info("PeerConnection state: %s", pc.connectionState)
        if pc.connectionState in {"failed", "closed", "disconnected"}:
            await cleanup_pc(pc)

    video_track = CameraVideoTrack(camera_stream)
    pc.addTrack(video_track)

    try:
        rtc_offer = RTCSessionDescription(sdp=offer.sdp, type=offer.type)
        await pc.setRemoteDescription(rtc_offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
    except Exception as exc:  # pylint: disable=broad-except
        await cleanup_pc(pc)
        logger.exception("處理 offer 時失敗：%s", exc)
        raise HTTPException(status_code=500, detail="處理 SDP 失敗") from exc

    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type,
    }


# 將工作目錄作為靜態檔案目錄對外提供，以便存取 index.html
app.mount("/", StaticFiles(directory=".", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
