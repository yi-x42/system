"""
YOLOv11 影片分析 API 端點 - 整合版本
將所有分析功能整合到統一的端點中，減少重複代碼
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from typing import Optional, Dict, Any, List
import shutil
import tempfile
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from app.services.video_analysis_service import video_analysis_service
from app.services.video_annotation_service import video_annotation_service
from app.core.logger import main_logger as logger

router = APIRouter(prefix="/analysis", tags=["Video Analysis"])

# 執行緒池用於後台處理
executor = ThreadPoolExecutor(max_workers=2)

# 支援的影片格式
SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}


def validate_video_file(file: UploadFile, max_size_mb: int = 100) -> None:
    """驗證上傳的影片檔案"""
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in SUPPORTED_VIDEO_FORMATS:
        raise HTTPException(
            status_code=400, 
            detail=f"不支援的檔案格式: {file_ext}。支援格式: {', '.join(SUPPORTED_VIDEO_FORMATS)}"
        )
    
    max_size = max_size_mb * 1024 * 1024
    if file.size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"檔案過大: {file.size / 1024 / 1024:.1f}MB，限制: {max_size_mb}MB"
        )


def validate_local_video(video_path: str) -> Path:
    """驗證本地影片檔案"""
    video_file = Path(video_path)
    
    if not video_file.exists():
        raise HTTPException(status_code=404, detail=f"影片檔案不存在: {video_path}")
    
    if not video_file.is_file():
        raise HTTPException(status_code=400, detail=f"路徑不是檔案: {video_path}")
    
    return video_file


# === 攝影機分析 ===
@router.post("/camera/{camera_id}")
async def analyze_camera(
    camera_id: int = 0,
    duration: int = Form(60, description="分析持續時間(秒)")
):
    """
    啟動攝影機即時分析
    - camera_id: 攝影機ID (通常0是預設攝影機)
    - duration: 分析持續時間(秒)
    """
    try:
        logger.info(f"開始攝影機分析: Camera {camera_id}, 持續時間: {duration}秒")
        
        def run_analysis():
            return video_analysis_service.analyze_camera(camera_id, duration)
        
        future = executor.submit(run_analysis)
        result = future.result(timeout=duration + 30)
        
        logger.info("攝影機分析完成")
        return {
            "status": "success",
            "message": "攝影機分析完成",
            "camera_id": camera_id,
            "duration": duration,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"攝影機分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"攝影機分析失敗: {str(e)}")


# === 整合影片分析端點 ===
@router.post("/video/analyze")
async def analyze_video(
    file: Optional[UploadFile] = File(None, description="上傳的影片檔案"),
    local_path: Optional[str] = Form(None, description="本地影片檔案路徑"),
    analysis_type: str = Form("detection", description="分析類型: detection(檢測), annotation(標註)")
):
    """
    統一影片分析端點
    - 支援上傳檔案或指定本地路徑
    - 支援檢測分析或標註生成
    """
    try:
        # 參數驗證
        if not file and not local_path:
            raise HTTPException(status_code=400, detail="必須提供上傳檔案或本地檔案路徑")
        
        if file and local_path:
            raise HTTPException(status_code=400, detail="只能選擇上傳檔案或本地檔案路徑其中一種")
        
        if analysis_type not in ["detection", "annotation"]:
            raise HTTPException(status_code=400, detail="analysis_type 必須是 'detection' 或 'annotation'")
        
        # 處理上傳檔案
        if file:
            max_size = 200 if analysis_type == "annotation" else 100
            validate_video_file(file, max_size)
            
            # 建立暫存檔案
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = upload_dir / f"{timestamp}_{file.filename}"
            
            with temp_file.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            video_path = str(temp_file)
            source = "uploaded"
            
        # 處理本地檔案
        else:
            video_file = validate_local_video(local_path)
            video_path = str(video_file)
            source = "local"
        
        logger.info(f"開始{analysis_type}分析: {video_path} (來源: {source})")
        
        # 執行分析
        def run_analysis():
            if analysis_type == "detection":
                return video_analysis_service.analyze_video_file(video_path)
            else:  # annotation
                return video_annotation_service.generate_annotated_video(video_path)
        
        timeout = 600 if analysis_type == "annotation" else 300
        future = executor.submit(run_analysis)
        result = future.result(timeout=timeout)
        
        # 清理上傳的暫存檔案
        if file and Path(video_path).exists():
            try:
                Path(video_path).unlink()
            except Exception as e:
                logger.warning(f"清理暫存檔案失敗: {e}")
        
        logger.info(f"{analysis_type}分析完成: {video_path}")
        
        return {
            "status": "success",
            "analysis_type": analysis_type,
            "source": source,
            "message": f"{analysis_type}分析完成",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"影片分析失敗: {e}")
        # 清理失敗時的暫存檔案
        if file and 'video_path' in locals() and Path(video_path).exists():
            try:
                Path(video_path).unlink()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"影片分析失敗: {str(e)}")


# === 分析狀態與結果 ===
@router.get("/status")
async def get_analysis_status():
    """獲取當前分析狀態"""
    try:
        # 這裡可以實作狀態追蹤邏輯
        return {
            "status": "ready",
            "message": "分析服務正常運行",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法獲取狀態: {str(e)}")


@router.get("/results/latest")
async def get_latest_results():
    """獲取最新分析結果"""
    try:
        # 檢查最新的分析結果檔案
        results_dir = Path("analysis_results")
        
        if not results_dir.exists():
            return {"status": "no_results", "message": "尚無分析結果"}
        
        # 找到最新的結果檔案
        csv_files = list(results_dir.glob("*.csv"))
        
        if not csv_files:
            return {"status": "no_results", "message": "尚無分析結果"}
        
        latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
        
        return {
            "status": "success",
            "latest_file": str(latest_file.name),
            "file_path": str(latest_file),
            "modified_time": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
            "file_size": latest_file.stat().st_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法獲取結果: {str(e)}")


@router.get("/annotated-videos")
async def list_annotated_videos():
    """列出所有標註影片"""
    try:
        videos_dir = Path("annotated_videos")
        
        if not videos_dir.exists():
            return {"status": "no_videos", "videos": [], "message": "尚無標註影片"}
        
        video_files = []
        for ext in [".mp4", ".avi", ".mov"]:
            video_files.extend(videos_dir.glob(f"*{ext}"))
        
        videos = []
        for video in video_files:
            stat = video.stat()
            videos.append({
                "filename": video.name,
                "path": str(video),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        # 按修改時間排序（最新的在前面）
        videos.sort(key=lambda x: x["modified_time"], reverse=True)
        
        return {
            "status": "success", 
            "count": len(videos),
            "videos": videos
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法列出影片: {str(e)}")


# === 系統控制 ===
@router.post("/stop")
async def stop_analysis():
    """停止當前分析"""
    try:
        # 這裡可以實作停止邏輯
        return {
            "status": "stopped",
            "message": "分析已停止",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法停止分析: {str(e)}")


# === 測試與工具 ===
@router.get("/supported-formats")
async def get_supported_formats():
    """獲取支援的影片格式"""
    return {
        "supported_formats": list(SUPPORTED_VIDEO_FORMATS),
        "max_upload_size_mb": 200,
        "description": "支援的影片格式和檔案大小限制"
    }
