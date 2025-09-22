"""
YOLOv11 物件檢測 API 端點 - 整合簡化版本
"""

import asyncio
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator

from app.services.yolo_service import YOLOService, get_yolo_service
from app.core.config import get_settings, YOLO_CLASSES
from app.core.logger import api_logger
from app.models.schemas import DetectionRequest, DetectionResponse, TrackingResponse

router = APIRouter()


# === 主要檢測端點 ===
@router.post("/detect", response_model=DetectionResponse)
async def detect_objects(
    file: UploadFile = File(..., description="要進行檢測的圖片檔案"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="信心值閾值"),
    iou_threshold: float = Form(0.45, ge=0.0, le=1.0, description="IOU閾值"),
    max_detections: int = Form(300, ge=1, le=1000, description="最大檢測數量"),
    save_results: bool = Form(False, description="是否儲存檢測結果"),
    yolo_service: YOLOService = Depends(get_yolo_service)
):
    """
    統一物件檢測端點
    - 支援圖片上傳檢測
    - 可調整檢測參數
    - 可選擇儲存結果
    """
    start_time = time.time()
    
    try:
        # 檔案驗證
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            raise HTTPException(
                status_code=400,
                detail="不支援的檔案格式。支援: PNG, JPG, JPEG, BMP, TIFF"
            )
        
        # 檔案大小檢查 (10MB限制)
        max_size = 10 * 1024 * 1024
        if file.size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"檔案過大: {file.size / 1024 / 1024:.1f}MB，限制: 10MB"
            )
        
        # 建立暫存檔案
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 執行檢測
            result = await yolo_service.detect_objects(
                tmp_file_path,
                confidence_threshold=confidence,
                iou_threshold=iou_threshold,
                max_detections=max_detections,
                save_results=save_results
            )
            
            processing_time = time.time() - start_time
            
            # 加入處理時間資訊
            if isinstance(result, dict):
                result['processing_time'] = round(processing_time, 3)
                result['parameters'] = {
                    'confidence': confidence,
                    'iou_threshold': iou_threshold,
                    'max_detections': max_detections
                }
            
            api_logger.info(f"檢測完成: {file.filename}, 耗時: {processing_time:.3f}秒")
            return result
            
        finally:
            # 清理暫存檔案
            try:
                Path(tmp_file_path).unlink()
            except Exception as e:
                api_logger.warning(f"清理暫存檔案失敗: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"檢測失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"檢測失敗: {str(e)}")


# === 物件追蹤端點 ===
@router.post("/track", response_model=TrackingResponse)
async def track_objects(
    file: UploadFile = File(..., description="要進行追蹤的圖片檔案"),
    confidence: float = Form(0.5, ge=0.0, le=1.0),
    iou_threshold: float = Form(0.45, ge=0.0, le=1.0),
    tracker_config: str = Form("bytetrack.yaml", description="追蹤器配置"),
    yolo_service: YOLOService = Depends(get_yolo_service)
):
    """物件追蹤端點 - 為影片分析提供追蹤功能"""
    try:
        # 檔案驗證 (與detect_objects相同)
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            raise HTTPException(
                status_code=400,
                detail="不支援的檔案格式。支援: PNG, JPG, JPEG, BMP, TIFF"
            )
        
        # 建立暫存檔案
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 執行追蹤
            result = await yolo_service.track_objects(
                tmp_file_path,
                confidence_threshold=confidence,
                iou_threshold=iou_threshold,
                tracker_config=tracker_config
            )
            
            return result
            
        finally:
            # 清理暫存檔案
            try:
                Path(tmp_file_path).unlink()
            except:
                pass
        
    except Exception as e:
        api_logger.error(f"追蹤失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"追蹤失敗: {str(e)}")


# === 模型管理 ===
@router.get("/model/status")
async def get_model_status(yolo_service: YOLOService = Depends(get_yolo_service)):
    """獲取模型狀態"""
    try:
        settings = get_settings()
        
        return {
            "model_loaded": yolo_service._model is not None,
            "model_path": getattr(yolo_service, '_model_path', settings.model_path),
            "device": settings.device,
            "confidence_threshold": settings.confidence_threshold,
            "iou_threshold": settings.iou_threshold,
            "model_file_exists": Path(settings.model_path).exists()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法獲取模型狀態: {str(e)}")


@router.post("/model/load")
async def load_model(
    model_path: str = Form(..., description="模型檔案路徑"),
    yolo_service: YOLOService = Depends(get_yolo_service)
):
    """載入指定的YOLO模型"""
    try:
        if not Path(model_path).exists():
            raise HTTPException(status_code=404, detail=f"模型檔案不存在: {model_path}")
        
        success = await yolo_service.load_model(model_path)
        
        if success:
            return {
                "status": "success",
                "message": f"模型載入成功: {model_path}",
                "model_path": model_path
            }
        else:
            raise HTTPException(status_code=500, detail="模型載入失敗")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"載入模型失敗: {str(e)}")


# === 系統資訊 ===
@router.get("/classes")
async def get_detection_classes():
    """獲取支援的檢測類別"""
    try:
        return {
            "classes": YOLO_CLASSES,
            "total_classes": len(YOLO_CLASSES),
            "description": "YOLOv11支援的物件類別"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法取得類別清單: {str(e)}")


# === 相容性別名端點 ===
@router.post("/objects", response_model=DetectionResponse)
async def detect_objects_alias(
    file: UploadFile = File(...),
    confidence_threshold: Optional[float] = Form(None),
    iou_threshold: Optional[float] = Form(None),
    max_detections: Optional[int] = Form(None)
):
    """物件檢測別名端點 - 為了向後相容性"""
    return await detect_objects(
        file=file,
        confidence=confidence_threshold or 0.5,
        iou_threshold=iou_threshold or 0.45,
        max_detections=max_detections or 300,
        save_results=False
    )
