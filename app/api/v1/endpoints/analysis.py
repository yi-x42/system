"""
YOLOv11 影片分析 API 端點 - 整合版本
將所有分析功能整合到統一的端點中，減少重複代碼，並支援資料庫整合
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from typing import Optional, Dict, Any, List
import shutil
import tempfile
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.video_analysis_service import get_video_analysis_service
from app.services.video_annotation_service import get_video_annotation_service
# 延遲導入 EnhancedVideoAnalysisService，避免在模組級別初始化
# from app.services.enhanced_video_analysis_service import EnhancedVideoAnalysisService
from app.services.new_database_service import DatabaseService
from app.core.database import get_async_db
from app.core.config import Settings
from app.core.logger import main_logger as logger

settings = Settings()
router = APIRouter(prefix="/analysis", tags=["影片分析"])

# 執行緒池用於後台處理
executor = ThreadPoolExecutor(max_workers=2)

# 支援的影片格式
SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}

# 延遲初始化的全域變數
_enhanced_analysis_service = None

def get_global_enhanced_service():
    """獲取全域的增強分析服務實例"""
    global _enhanced_analysis_service
    if _enhanced_analysis_service is None:
        # 在這裡才導入，避免模組級別初始化
        from app.services.enhanced_video_analysis_service import EnhancedVideoAnalysisService
        _enhanced_analysis_service = EnhancedVideoAnalysisService(
            model_path=settings.YOLO_MODEL_PATH,
            device=settings.DEVICE
        )
    return _enhanced_analysis_service

async def get_enhanced_analysis_service(db: AsyncSession = Depends(get_async_db)):
    """獲取增強分析服務（帶資料庫）"""
    service = get_global_enhanced_service()
    db_service = DatabaseService()
    service.set_database_service(db_service)
    return service


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
            return get_video_analysis_service().analyze_camera(camera_id, duration)
        
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
@router.post("/video/upload")
async def analyze_uploaded_video(
    file: UploadFile = File(..., description="上傳的影片檔案"),
    analysis_type: str = Form("detection", description="分析類型: detection(檢測), annotation(標註)"),
    model_id: Optional[int] = Form(None, description="指定使用的模型 ID")
):
    """
    上傳影片分析端點
    - 專門處理上傳的影片檔案
    - 支援檢測分析或標註生成
    """
    try:
        if analysis_type not in ["detection", "annotation"]:
            raise HTTPException(status_code=400, detail="analysis_type 必須是 'detection' 或 'annotation'")
        
        # 驗證上傳檔案
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
        
        # 執行分析
        # 解析模型路徑（若有指定）
        model_path = None
        if model_id is not None:
            try:
                # 使用現有 get_async_db 產生 session
                async for db in get_async_db():  # get_async_db 是 async generator
                    from sqlalchemy import select
                    from app.models.database import Model
                    q = select(Model).where(Model.id == model_id)
                    res = await db.execute(q)
                    m = res.scalar_one_or_none()
                    if not m:
                        raise HTTPException(status_code=404, detail=f"模型 {model_id} 不存在")
                    model_path = m.path
                    break
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"查詢模型失敗: {e}")
                raise HTTPException(status_code=500, detail="查詢模型失敗")

        if analysis_type == "detection":
            result = get_video_analysis_service().analyze_video_file(video_path, model_path=model_path)
        else:  # annotation
            result = get_video_annotation_service().generate_annotated_video(video_path)
        
        timeout = 600 if analysis_type == "annotation" else 300
        
        return {
            "success": True,
            "message": f"影片{analysis_type}完成",
            "source": source,
            "video_path": video_path,
            "analysis_type": analysis_type,
            "result": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上傳影片分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"上傳影片分析失敗: {str(e)}")


@router.post("/video/local")
async def analyze_local_video(
    local_path: str = Form(..., description="本地影片檔案路徑"),
    analysis_type: str = Form("detection", description="分析類型: detection(檢測), annotation(標註)"),
    model_id: Optional[int] = Form(None, description="指定使用的模型 ID")
):
    """
    本地影片分析端點
    - 專門處理本地影片檔案
    - 支援檢測分析或標註生成
    """
    try:
        if analysis_type not in ["detection", "annotation"]:
            raise HTTPException(status_code=400, detail="analysis_type 必須是 'detection' 或 'annotation'")
        
        # 驗證本地檔案
        video_path = validate_local_video(local_path)
        source = "local"
        
        # 執行分析
        model_path = None
        if model_id is not None:
            try:
                async for db in get_async_db():
                    from sqlalchemy import select
                    from app.models.database import Model
                    q = select(Model).where(Model.id == model_id)
                    res = await db.execute(q)
                    m = res.scalar_one_or_none()
                    if not m:
                        raise HTTPException(status_code=404, detail=f"模型 {model_id} 不存在")
                    model_path = m.path
                    break
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"查詢模型失敗: {e}")
                raise HTTPException(status_code=500, detail="查詢模型失敗")

        if analysis_type == "detection":
            result = get_video_analysis_service().analyze_video_file(str(video_path), model_path=model_path)
        else:  # annotation  
            result = get_video_annotation_service().generate_annotated_video(str(video_path))
        
        return {
            "success": True,
            "message": f"本地影片{analysis_type}完成",
            "source": source,
            "video_path": str(video_path),
            "analysis_type": analysis_type,
            "result": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"本地影片分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"本地影片分析失敗: {str(e)}")


# === 快速測試端點 ===
@router.get("/test")
async def test_analysis_service():
    """
    測試分析服務狀態
    """
    try:
        # 檢查測試影片
        test_video = Path("test_videos/basic_movement_test.mp4")
        
        return {
            "success": True,
            "message": "影片分析服務正常運作",
            "available_endpoints": [
                "/api/v1/analysis/video/upload - 上傳影片分析",
                "/api/v1/analysis/video/local - 本地影片分析",
                "/api/v1/analysis/video/analyze - 統一分析端點"
            ],
            "test_video_available": test_video.exists(),
            "test_video_path": str(test_video) if test_video.exists() else None,
            "supported_formats": list(SUPPORTED_VIDEO_FORMATS),
            "analysis_types": ["detection", "annotation"]
        }
    
    except Exception as e:
        logger.error(f"測試端點失敗: {e}")
        return {
            "success": False,
            "message": f"測試失敗: {str(e)}"
        }


# 保留原來的統一端點作為備用
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
        # 參數驗證 - 更加嚴格的空值檢查
        has_file = False
        has_local_path = False
        
        # 檢查檔案上傳
        if file is not None:
            # 檢查是否有實際的檔案名稱和內容
            if hasattr(file, 'filename') and file.filename and file.filename.strip():
                has_file = True
        
        # 檢查本地路徑
        if local_path is not None:
            # 檢查是否為非空字串
            if isinstance(local_path, str) and local_path.strip():
                has_local_path = True
        
        # 調試資訊
        logger.info(f"調試: file={file}, filename={getattr(file, 'filename', None) if file else None}")
        logger.info(f"調試: local_path='{local_path}', has_file={has_file}, has_local_path={has_local_path}")
        
        if not has_file and not has_local_path:
            raise HTTPException(status_code=400, detail="必須提供上傳檔案或本地檔案路徑")
        
        if has_file and has_local_path:
            raise HTTPException(status_code=400, detail="只能選擇上傳檔案或本地檔案路徑其中一種")
        
        if analysis_type not in ["detection", "annotation"]:
            raise HTTPException(status_code=400, detail="analysis_type 必須是 'detection' 或 'annotation'")
        
        # 處理上傳檔案
        if has_file:
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
                return get_video_analysis_service().analyze_video_file(video_path)
            else:  # annotation
                return get_video_annotation_service().generate_annotated_video(video_path)
        
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


# =========================================
# 資料庫整合端點
# =========================================

@router.post("/upload-with-database")
async def analyze_uploaded_video_with_database(
    file: UploadFile = File(...),
    confidence_threshold: float = Form(0.5),
    track_objects: bool = Form(True),
    detect_behaviors: bool = Form(True),
    annotate_video: bool = Form(False),
    enhanced_service = Depends(get_enhanced_analysis_service)
):
    """
    上傳影片並使用資料庫進行分析
    """
    validate_video_file(file)
    
    # 保存上傳的檔案
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = f"{timestamp}_{file.filename}"
    video_path = Path("uploads") / video_filename
    
    try:
        # 確保目錄存在
        video_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存檔案
        with video_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"📤 檔案已保存: {video_path}")
        
        # 使用資料庫進行分析
        results = await enhanced_service.analyze_video_with_database(
            video_path=str(video_path),
            output_dir="analysis_results",
            confidence_threshold=confidence_threshold,
            track_objects=track_objects,
            detect_behaviors=detect_behaviors,
            annotate_video=annotate_video
        )
        
        return {
            "status": "success",
            "message": "影片分析完成並已保存到資料庫",
            "analysis_record_id": results.get("analysis_record_id"),
            "video_info": results.get("video_info", {}),
            "analysis_summary": {
                "total_detections": results.get("total_detections", 0),
                "unique_objects": len(results.get("detection_summary", {})),
                "behavior_events": len(results.get("behavior_events", [])),
                "processing_time": results.get("processing_time", 0)
            },
            "files": {
                "csv_file": results.get("csv_file"),
                "annotated_video": results.get("annotated_video_path") if annotate_video else None
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 資料庫分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}")
    finally:
        # 清理上傳的檔案（可選）
        if video_path.exists():
            try:
                # 這裡可以選擇是否刪除原檔案
                # video_path.unlink()
                pass
            except:
                pass


@router.post("/local-with-database")
async def analyze_local_video_with_database(
    video_path: str = Form(...),
    confidence_threshold: float = Form(0.5),
    track_objects: bool = Form(True),
    detect_behaviors: bool = Form(True),
    annotate_video: bool = Form(False),
    enhanced_service = Depends(get_enhanced_analysis_service)
):
    """
    分析本地影片檔案並保存到資料庫
    """
    if not Path(video_path).exists():
        raise HTTPException(status_code=404, detail=f"找不到影片檔案: {video_path}")
    
    try:
        # 使用資料庫進行分析
        results = await enhanced_service.analyze_video_with_database(
            video_path=video_path,
            output_dir="analysis_results",
            confidence_threshold=confidence_threshold,
            track_objects=track_objects,
            detect_behaviors=detect_behaviors,
            annotate_video=annotate_video
        )
        
        return {
            "status": "success",
            "message": "本地影片分析完成並已保存到資料庫",
            "analysis_record_id": results.get("analysis_record_id"),
            "video_info": results.get("video_info", {}),
            "analysis_summary": {
                "total_detections": results.get("total_detections", 0),
                "unique_objects": len(results.get("detection_summary", {})),
                "behavior_events": len(results.get("behavior_events", [])),
                "processing_time": results.get("processing_time", 0)
            },
            "files": {
                "csv_file": results.get("csv_file"),
                "annotated_video": results.get("annotated_video_path") if annotate_video else None
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 本地影片資料庫分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}")


@router.get("/history")
async def get_analysis_history(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    enhanced_service = Depends(get_enhanced_analysis_service)
):
    """
    獲取分析歷史記錄
    """
    try:
        records = await enhanced_service.get_analysis_history(skip, limit, status)
        
        return {
            "status": "success",
            "count": len(records),
            "records": [
                {
                    "id": record.id,
                    "video_name": record.video_name,
                    "analysis_type": record.analysis_type,
                    "status": record.status,
                    "total_detections": record.total_detections,
                    "unique_objects": record.unique_objects,
                    "analysis_duration": record.analysis_duration,
                    "created_at": record.created_at.isoformat(),
                    "updated_at": record.updated_at.isoformat() if record.updated_at else None
                }
                for record in records
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取歷史記錄失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取歷史記錄失敗: {str(e)}")


@router.get("/details/{analysis_id}")
async def get_analysis_details(
    analysis_id: int,
    enhanced_service = Depends(get_enhanced_analysis_service)
):
    """
    獲取特定分析的詳細資訊
    """
    try:
        details = await enhanced_service.get_analysis_details(analysis_id)
        
        if not details:
            raise HTTPException(status_code=404, detail=f"找不到分析記錄: {analysis_id}")
        
        analysis_record = details["analysis_record"]
        
        return {
            "status": "success",
            "analysis_record": {
                "id": analysis_record.id,
                "video_name": analysis_record.video_name,
                "video_path": analysis_record.video_path,
                "analysis_type": analysis_record.analysis_type,
                "status": analysis_record.status,
                "duration": analysis_record.duration,
                "fps": analysis_record.fps,
                "total_frames": analysis_record.total_frames,
                "resolution": analysis_record.resolution,
                "total_detections": analysis_record.total_detections,
                "unique_objects": analysis_record.unique_objects,
                "analysis_duration": analysis_record.analysis_duration,
                "csv_file_path": analysis_record.csv_file_path,
                "annotated_video_path": analysis_record.annotated_video_path,
                "created_at": analysis_record.created_at.isoformat(),
                "updated_at": analysis_record.updated_at.isoformat() if analysis_record.updated_at else None,
                "error_message": analysis_record.error_message
            },
            "detection_count": details["detection_count"],
            "behavior_events_count": len(details["behavior_events"]),
            "has_more_detections": details["has_more_detections"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 獲取分析詳情失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取分析詳情失敗: {str(e)}")


@router.get("/statistics")
async def get_analysis_statistics(
    enhanced_service = Depends(get_enhanced_analysis_service)
):
    """
    獲取分析統計資訊
    """
    try:
        stats = await enhanced_service.get_analysis_statistics()
        
        return {
            "status": "success",
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取統計資訊失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計資訊失敗: {str(e)}")


@router.get("/detections/{analysis_id}")
async def get_detection_results(
    analysis_id: int,
    skip: int = 0,
    limit: int = 100,
    enhanced_service = Depends(get_enhanced_analysis_service)
):
    """
    獲取特定分析的檢測結果
    """
    try:
        if not enhanced_service.db_service:
            raise HTTPException(status_code=503, detail="資料庫服務不可用")
        
        # 檢查分析記錄是否存在
        analysis_record = await enhanced_service.db_service.get_analysis_record(analysis_id)
        if not analysis_record:
            raise HTTPException(status_code=404, detail=f"找不到分析記錄: {analysis_id}")
        
        # 獲取檢測結果
        detections = await enhanced_service.db_service.get_detection_results(
            analysis_id, skip, limit
        )
        
        return {
            "status": "success",
            "analysis_id": analysis_id,
            "count": len(detections),
            "detections": [
                {
                    "id": det.id,
                    "frame_number": det.frame_number,
                    "frame_time": det.frame_time,
                    "object_id": det.object_id,
                    "object_type": det.object_type,
                    "object_chinese": det.object_chinese,
                    "confidence": det.confidence,
                    "bbox": {
                        "x1": det.bbox_x1,
                        "y1": det.bbox_y1,
                        "x2": det.bbox_x2,
                        "y2": det.bbox_y2
                    },
                    "center": {"x": det.center_x, "y": det.center_y},
                    "dimensions": {"width": det.width, "height": det.height},
                    "area": det.area,
                    "zone": det.zone,
                    "zone_chinese": det.zone_chinese,
                    "speed": det.speed,
                    "direction": det.direction,
                    "direction_chinese": det.direction_chinese,
                    "detection_quality": det.detection_quality,
                    "timestamp": det.created_at.isoformat()
                }
                for det in detections
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "has_more": len(detections) == limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 獲取檢測結果失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取檢測結果失敗: {str(e)}")

