"""
簡化版影片分析 API 端點 - 只包含資料庫整合功能
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.new_database_service import DatabaseService
from app.core.database import get_async_db
from app.core.config import Settings
from app.core.logger import main_logger as logger

settings = Settings()
router = APIRouter(prefix="/analysis", tags=["影片分析 - 資料庫版"])

# 支援的影片格式
SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}

def validate_video_file(file: UploadFile, max_size_mb: int = 100) -> None:
    """驗證上傳的影片檔案"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="檔案名稱不能為空")
    
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in SUPPORTED_VIDEO_FORMATS:
        raise HTTPException(
            status_code=400, 
            detail=f"不支援的檔案格式: {file_extension}. 支援的格式: {', '.join(SUPPORTED_VIDEO_FORMATS)}"
        )
    
    # 注意：file.size 在某些情況下可能為 None
    if hasattr(file, 'size') and file.size:
        max_size = max_size_mb * 1024 * 1024
        if file.size > max_size:
            raise HTTPException(
                status_code=413, 
                detail=f"檔案過大: {file.size / 1024 / 1024:.1f}MB, 最大限制: {max_size_mb}MB"
            )

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
        logger.info("✅ Enhanced video analysis service initialized")
    return _enhanced_analysis_service

async def get_enhanced_analysis_service(db: AsyncSession = Depends(get_async_db)):
    """獲取增強分析服務（帶資料庫）"""
    service = get_global_enhanced_service()
    db_service = DatabaseService()
    service.set_database_service(db_service)
    return service

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

# === 測試與工具 ===
@router.get("/supported-formats")
async def get_supported_formats():
    """獲取支援的影片格式"""
    return {
        "supported_formats": list(SUPPORTED_VIDEO_FORMATS),
        "max_upload_size_mb": 200,
        "description": "支援的影片格式和檔案大小限制"
    }

@router.get("/test-db")
async def test_database_connection():
    """測試資料庫連接"""
    try:
        from app.core.database import check_database_connection
        db_ok = await check_database_connection()
        
        if db_ok:
            return {
                "status": "success",
                "message": "資料庫連接正常",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error", 
                "message": "資料庫連接失敗",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ 資料庫測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"資料庫測試失敗: {str(e)}")
