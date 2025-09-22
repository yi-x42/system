"""攝影機管理 API：提供掃描、啟動、列出、最新影格與停止功能。
此為替代移除的 /admin 攝影機管理功能的最小可行版本。
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Optional, List
import json
import os
import asyncpg
import base64

from app.services.camera_service import camera_manager

router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_SERVER", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "49679904"),
    "database": os.getenv("POSTGRES_DB", "yolo_analysis")
}

class StartCameraRequest(BaseModel):
    index: int
    name: Optional[str] = None
    backend: Optional[str] = None  # 可選指定後端 CAP_DSHOW / CAP_MSMF / DEFAULT

class AttemptRequest(BaseModel):
    index: int = 0
    warmup_frames: int = 3  # 減少預設暖機影格
    backends: Optional[List[str]] = None  # 若指定只測這些

def _do_scan(max_index: int = 6, warmup_frames: int = 3, force_probe: bool = False, retries: int = 1):  # 減少預設參數
    results = camera_manager.scan(max_index=max_index, warmup_frames=warmup_frames, force_probe=force_probe, retries=retries)
    # 提供新舊兩種格式
    simple_indices = [r['index'] for r in results if r.get('frame_ok', False)]
    return {
        "devices": results,  # 新格式：詳細資訊
        "available_indices": simple_indices,  # 舊格式：相容性
        "count": len(simple_indices)
    }

@router.get("/scan")
def scan_cameras(max_index: int = 6, warmup_frames: int = 3, force_probe: bool = False, retries: int = 1):  # 快速預設值
    """掃描本機可用攝影機 (回傳詳情: index, backend, frame_ok, width, height, source, attempts[])
    
    快速模式：預設 warmup_frames=3, retries=1, force_probe=False
    若需要更彻底掃描，可設定 force_probe=true&retries=3&warmup_frames=5
    """
    return _do_scan(max_index=max_index, warmup_frames=warmup_frames, force_probe=force_probe, retries=retries)

@router.post("/scan")
def scan_cameras_post(max_index: int = 6, warmup_frames: int = 3, force_probe: bool = False, retries: int = 1):  # 快速預設值
    """掃描本機可用攝影機 (POST 相容)"""
    return _do_scan(max_index=max_index, warmup_frames=warmup_frames, force_probe=force_probe, retries=retries)

@router.get("/scan/detailed")
def detailed_scan(max_index: int = 6, warmup_frames: int = 3):  # 快速預設值
    """詳細掃描：回傳各 index 多後端結果 + 暖機多幀嘗試"""
    data = camera_manager.detailed_scan(max_index=max_index, warmup_frames=warmup_frames)
    return {"results": data}

@router.get("/debug/{index}")
def debug_single_index(index: int):
    """針對單一 index 詳細嘗試開啟並讀取一幀"""
    import cv2, time
    attempts = []
    backends = [
        ("CAP_DSHOW", getattr(cv2, 'CAP_DSHOW', None)),
        ("CAP_MSMF", getattr(cv2, 'CAP_MSMF', None)),
        ("DEFAULT", None)
    ]
    for name, flag in backends:
        start = time.time()
        if flag is not None:
            cap = cv2.VideoCapture(index, flag)
        else:
            cap = cv2.VideoCapture(index)
        opened = cap.isOpened()
        frame_ok = False
        w = h = None
        if opened:
            ok, frame = cap.read()
            if ok and frame is not None:
                frame_ok = True
                h, w = frame.shape[:2]
        cap.release()
        attempts.append({
            "backend": name,
            "opened": opened,
            "frame_ok": frame_ok,
            "width": w,
            "height": h,
            "elapsed_ms": round((time.time()-start)*1000,2)
        })
    return {"index": index, "attempts": attempts}

async def _create_analysis_task(camera_index: int, width: int, height: int, name: Optional[str]):
    conn = await asyncpg.connect(**POSTGRES_CONFIG)
    try:
        source_info = {
            "camera_index": camera_index,
            "name": name or f"camera_{camera_index}"
        }
        # 使用新的解析度欄位格式
        row = await conn.fetchrow(
            """
            INSERT INTO analysis_tasks (task_type, status, source_info, source_width, source_height, source_fps, created_at)
            VALUES ($1, $2, $3::jsonb, $4, $5, $6, NOW()) RETURNING id
            """,
            "realtime_camera", "running", json.dumps(source_info), width, height, 30.0
        )
        return row["id"]
    finally:
        await conn.close()

@router.post("/start")
async def start_camera(req: StartCameraRequest):
    """啟動指定 index 的攝影機並建立 analysis_task。
    若提供 backend，優先使用；否則使用快取記錄或自動回退。"""
    import cv2
    # 先嘗試指定 backend
    backend_flag = None
    if req.backend:
        import cv2 as _cv
        backend_map = {
            'CAP_DSHOW': getattr(_cv, 'CAP_DSHOW', None),
            'CAP_MSMF': getattr(_cv, 'CAP_MSMF', None),
            'DEFAULT': None
        }
        backend_flag = backend_map.get(req.backend)
    cap = None
    if backend_flag is not None:
        cap = cv2.VideoCapture(req.index, backend_flag)
    else:
        cap = cv2.VideoCapture(req.index)
    if not cap.isOpened():
        cap.release()
        # fallback 走 create_session 裡面的多後端策略
        w = h = 0
    else:
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        cap.release()
    task_id = await _create_analysis_task(req.index, w, h, req.name)
    session = camera_manager.create_session(task_id=task_id, camera_index=req.index, preferred_backend=req.backend)
    return {
        "task_id": task_id,
        "camera_index": req.index,
        "frame_width": session.width,
        "frame_height": session.height,
        "fps": session.fps,
        "backend": session.backend_name
    }

@router.get("/sessions")
def list_sessions():
    """列出目前啟動中的攝影機任務"""
    return {"sessions": camera_manager.list()}

@router.get("/{task_id}/latest-frame")
def get_latest_frame(task_id: int):
    """取得最新影格 (JPEG)"""
    session = camera_manager.get(task_id)
    if not session:
        raise HTTPException(status_code=404, detail="攝影機任務不存在")
    data = session.get_latest_jpeg()
    if not data:
        raise HTTPException(status_code=404, detail="暫無影格")
    return Response(content=data, media_type="image/jpeg")

@router.post("/{task_id}/stop")
def stop_camera(task_id: int):
    """停止攝影機"""
    ok = camera_manager.stop(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="任務不存在或已停止")
    return {"stopped": task_id}

@router.get("/scan/advanced")
def advanced_scan():
    """使用 ffmpeg dshow 名稱進行進階掃描 (video=<name>)"""
    data = camera_manager.advanced_scan()
    return {"advanced": data}

@router.get("/scan/ffmpeg-devices")
def list_ffmpeg_devices():
    return {"devices": camera_manager.ffmpeg_list_devices()}

@router.get("/force-open")
def force_open(index: int = 0, warmup_frames: int = 10):
    """強制以多後端嘗試打開攝影機並回傳一張 Base64 影像 (便於快速驗證)。"""
    import cv2, time
    tried = []
    frame_b64 = None
    chosen_backend = None
    for name, flag in [("CAP_DSHOW", getattr(cv2,'CAP_DSHOW',None)), ("CAP_MSMF", getattr(cv2,'CAP_MSMF',None)), ("DEFAULT", None)]:
        if flag is not None:
            cap = cv2.VideoCapture(index, flag)
        else:
            cap = cv2.VideoCapture(index)
        opened = cap.isOpened()
        info = {"backend": name, "opened": opened, "frame_ok": False}
        if opened:
            for _ in range(warmup_frames):
                ok, frame = cap.read()
                if ok and frame is not None:
                    info["frame_ok"] = True
                    chosen_backend = name
                    _, buf = cv2.imencode('.jpg', frame)
                    frame_b64 = base64.b64encode(buf.tobytes()).decode('utf-8')
                    break
                time.sleep(0.04)
        cap.release()
        tried.append(info)
        if frame_b64:
            break
    if not frame_b64:
        raise HTTPException(status_code=500, detail={"message": "無法取得影格", "tried": tried})
    return {"index": index, "backend": chosen_backend, "tried": tried, "frame_base64_jpeg": frame_b64}

# ============ 診斷功能 ============
@router.get("/diagnostics/build")
def camera_build_info():
    """回傳 OpenCV 版本與可用後端關鍵字 (截斷 build info 避免過長)"""
    import cv2
    info = cv2.getBuildInformation()
    lower = info.lower()
    def has(token: str):
        return token.lower() in lower
    backends = {
        "media_foundation": has("Media Foundation"),
        "directshow": has("DirectShow"),
        "gstreamer": has("GStreamer"),
        "ffmpeg": has("FFMPEG"),
        "msmf": has("Media Foundation") or has("MSMF"),
    }
    return {
        "opencv_version": cv2.__version__,
        "python_version": os.sys.version.split()[0],
        "backends_detected": backends,
        "build_info_head": info.splitlines()[:40],  # 只取前 40 行
        "hints": [
            "若 directshow / media foundation 未啟用，可能需重裝 opencv-python (非 headless)",
            "Windows 13/11 隱私權：允許桌面應用程式使用攝影機", 
            "確認無其他程式 (Teams/Zoom/相機App) 正在使用鏡頭",
            "嘗試安裝: pip install --upgrade opencv-python opencv-contrib-python"
        ]
    }

@router.post("/diagnostics/attempt")
def attempt_open(req: AttemptRequest):
    import cv2, time
    backend_map = {
        "CAP_DSHOW": getattr(cv2, 'CAP_DSHOW', None),
        "CAP_MSMF": getattr(cv2, 'CAP_MSMF', None),
        "DEFAULT": None
    }
    order = req.backends or ["CAP_DSHOW", "CAP_MSMF", "DEFAULT"]
    results = []
    for name in order:
        flag = backend_map.get(name)
        start = time.time()
        if flag is not None:
            cap = cv2.VideoCapture(req.index, flag)
        else:
            cap = cv2.VideoCapture(req.index)
        opened = cap.isOpened()
        frames_ok = 0
        widths = set(); heights = set()
        if opened:
            for _ in range(max(1, req.warmup_frames)):
                ok, frame = cap.read()
                if ok and frame is not None:
                    frames_ok += 1
                    h, w = frame.shape[:2]
                    widths.add(w); heights.add(h)
                time.sleep(0.03)
        cap.release()
        results.append({
            "backend": name,
            "opened": opened,
            "frames_ok": frames_ok,
            "widths": list(widths),
            "heights": list(heights),
            "elapsed_ms": round((time.time()-start)*1000,2)
        })
    summary = {
        "any_opened": any(r['opened'] for r in results),
        "any_frame": any(r['frames_ok']>0 for r in results)
    }
    suggestions = []
    if not summary["any_opened"]:
        suggestions.append("所有後端打不開：1) 檢查 Windows 攝影機隱私權 2) 鏡頭是否被其他程式占用 3) 重新安裝 opencv-python")
    elif summary["any_opened"] and not summary["any_frame"]:
        suggestions.append("能開但無影格：增加 warmup_frames；或嘗試降權限 (以系統管理員執行)；或換 Python 3.11 環境測試。")
    return {"index": req.index, "results": results, "summary": summary, "suggestions": suggestions}
