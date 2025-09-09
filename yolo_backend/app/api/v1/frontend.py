"""
YOLOv11 前端界面 API
專門為新的前端界面提供數據和功能支持
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, File, UploadFile, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete, select, text
from pydantic import BaseModel, Field

from app.core.database import get_db, AsyncSessionLocal, get_async_db
from app.core.logger import api_logger
# from app.services.yolo_service import get_yolo_service  # 暫時註解
from app.services.camera_service import CameraService
from app.services.task_service import TaskService, get_task_service
from app.services.analytics_service import AnalyticsService
from app.services.new_database_service import DatabaseService
from app.models.database import AnalysisTask, DetectionResult, DataSource

router = APIRouter(prefix="/frontend", tags=["前端界面"])

# ===== 模型清單相關模型 =====

class ModelFileInfo(BaseModel):
    """YOLO 模型檔案資訊"""
    id: str
    name: str
    modelType: str
    parameterCount: str
    fileSize: str
    status: str
    size: int
    created_at: float
    modified_at: float
    path: str

# ===== 數據模型 =====

class SystemStats(BaseModel):
    """系統統計數據模型"""
    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="記憶體使用率")
    gpu_usage: float = Field(..., description="GPU使用率")
    active_tasks: int = Field(..., description="活躍任務數")
    total_detections: int = Field(..., description="總檢測數")
    system_uptime_seconds: int = Field(..., description="系統運行總秒數")
    last_updated: datetime = Field(..., description="最後更新時間")

class TaskCreate(BaseModel):
    """任務創建模型"""
    name: str = Field(..., description="任務名稱")
    task_type: str = Field(..., description="任務類型: realtime/batch/scheduled/event")
    camera_id: Optional[str] = Field(None, description="攝影機ID")
    model_name: str = Field("yolov11s", description="YOLO模型名稱")
    confidence: float = Field(0.5, description="信心度閾值")
    iou_threshold: float = Field(0.45, description="IoU閾值")
    schedule_time: Optional[datetime] = Field(None, description="排程時間")
    description: str = Field("", description="任務描述")

class TaskInfo(BaseModel):
    """任務資訊模型"""
    id: str
    name: str
    task_type: str
    status: str
    progress: float
    camera_id: Optional[str]
    model_name: str
    start_time: datetime
    end_time: Optional[datetime]
    created_at: datetime

class CameraInfo(BaseModel):
    """攝影機資訊模型"""
    id: str
    name: str
    status: str  # online/offline
    camera_type: str  # USB/Network
    resolution: str
    fps: int
    group_id: Optional[str]

class ModelRequest(BaseModel):
    """模型操作請求模型"""
    model_id: Optional[str] = Field(None, description="模型ID")
    model_name: Optional[str] = Field(None, description="模型名稱（向後兼容）")
    
    def get_model_identifier(self) -> str:
        """獲取模型識別符，優先使用 model_id，否則使用 model_name"""
        if self.model_id:
            return self.model_id
        elif self.model_name:
            return self.model_name
        else:
            raise ValueError("必須提供 model_id 或 model_name")

class ModelConfigUpdate(BaseModel):
    """模型配置更新模型"""
    confidence: Optional[float] = Field(None, description="信心度閾值")
    iou_threshold: Optional[float] = Field(None, description="IoU閾值")
    image_size: Optional[int] = Field(None, description="輸入圖像大小")

class AnalyticsData(BaseModel):
    """分析數據模型"""
    detection_counts: Dict[str, int]
    hourly_trend: List[Dict[str, Any]]
    category_distribution: Dict[str, int]
    time_period_analysis: Dict[str, int]

# ===== 資料來源管理模型 =====

class DataSourceCreate(BaseModel):
    """創建資料來源模型"""
    source_type: str = Field(..., description="資料來源類型: camera/video_file/image_folder")
    name: str = Field(..., description="資料來源名稱")
    config: Dict[str, Any] = Field(..., description="配置資訊")
    
class DataSourceUpdate(BaseModel):
    """更新資料來源模型"""
    name: Optional[str] = Field(None, description="資料來源名稱")
    config: Optional[Dict[str, Any]] = Field(None, description="配置資訊")
    status: Optional[str] = Field(None, description="狀態: active/inactive/error")

class DataSourceInfo(BaseModel):
    """資料來源資訊模型"""
    id: int
    source_type: str
    name: str
    config: Dict[str, Any]
    status: str
    last_check: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class CameraConfig(BaseModel):
    """攝影機配置模型"""
    device_id: Optional[int] = Field(None, description="USB攝影機裝置ID")
    url: Optional[str] = Field(None, description="網路攝影機URL")
    resolution: str = Field("1280x720", description="解析度")
    fps: int = Field(30, description="幀率")
    
class VideoFileConfig(BaseModel):
    """影片檔案配置模型"""
    file_path: str = Field(..., description="影片檔案路徑")
    auto_loop: bool = Field(False, description="自動循環播放")
    
class ImageFolderConfig(BaseModel):
    """圖片資料夾配置模型"""
    folder_path: str = Field(..., description="圖片資料夾路徑")
    supported_formats: List[str] = Field(["jpg", "jpeg", "png", "bmp"], description="支援的格式")
    scan_subdirs: bool = Field(False, description="掃描子資料夾")

# ===== YOLO 模型輔助函式 =====

def get_model_info_from_filename(filename: str, file_size: int) -> dict:
    """根據檔案名稱推斷模型資訊"""
    # 模型參數映射表
    model_params = {
        'yolo11n': {'params': '2.6M', 'type': '物體偵測'},
        'yolo11s': {'params': '9.4M', 'type': '物體偵測'},
        'yolo11m': {'params': '20.1M', 'type': '物體偵測'},
        'yolo11l': {'params': '25.3M', 'type': '物體偵測'},
        'yolo11x': {'params': '56.9M', 'type': '物體偵測'},
    }
    
    # 預設值
    model_type = "物體偵測"
    param_count = "未知"
    
    # 解析檔案名稱
    basename = filename.replace('.pt', '').lower()
    model_id = filename.replace('.pt', '')
    
    # 檢查是否為已知模型
    for model_key, info in model_params.items():
        if model_key in basename:
            param_count = info['params']
            model_type = info['type']
            break
    
    # 從快取取得狀態，如果沒有則預設為 inactive，除非是 yolo11n
    if model_id not in model_status_cache:
        if 'yolo11n' in basename:
            model_status_cache[model_id] = "active"
        else:
            model_status_cache[model_id] = "inactive"
    
    status = model_status_cache[model_id]
    
    return {
        'modelType': model_type,
        'parameterCount': param_count,
        'fileSize': f"{file_size / (1024 * 1024):.1f} MB",
        'status': status
    }

# ===== YOLO 模型清單 API =====

@router.get("/models/list", response_model=List[ModelFileInfo])
async def list_yolo_models():
    """列出 yolo_backend/模型 資料夾下所有模型檔案"""
    try:
        # 指定模型資料夾路徑
        model_dir = r"D:\project\system\yolo_backend\模型"
        
        # 檢查資料夾是否存在
        if not os.path.exists(model_dir):
            api_logger.warning(f"模型資料夾不存在: {model_dir}")
            return []
        
        model_files = []
        
        # 掃描 .pt 檔案
        for file in os.listdir(model_dir):
            if file.endswith('.pt'):
                file_path = os.path.join(model_dir, file)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    
                    # 根據檔案名稱推斷模型資訊
                    model_info = get_model_info_from_filename(file, stat.st_size)
                    
                    model_files.append(ModelFileInfo(
                        id=file.replace('.pt', ''),
                        name=file,
                        modelType=model_info['modelType'],
                        parameterCount=model_info['parameterCount'],
                        fileSize=model_info['fileSize'],
                        status=model_info['status'],
                        size=stat.st_size,
                        created_at=stat.st_ctime,
                        modified_at=stat.st_mtime,
                        path=file_path
                    ))
        
        api_logger.info(f"找到 {len(model_files)} 個模型檔案")
        return model_files
        
    except Exception as e:
        api_logger.error(f"列出模型檔案時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"無法取得模型清單: {str(e)}")

# ===== 模型狀態管理 API =====

# 全域變數來儲存模型狀態（實際專案中應該使用資料庫）
model_status_cache = {}

@router.post("/models/{model_id}/toggle")
async def toggle_model_status(model_id: str):
    """切換模型啟用狀態"""
    try:
        # 取得當前狀態
        current_status = model_status_cache.get(model_id, "inactive")
        
        # 切換狀態（允許多個模型同時啟用）
        new_status = "active" if current_status == "inactive" else "inactive"
        
        model_status_cache[model_id] = new_status
        
        api_logger.info(f"模型 {model_id} 狀態切換為: {new_status}")
        
        return {
            "success": True,
            "model_id": model_id,
            "new_status": new_status,
            "message": f"模型已{'啟用' if new_status == 'active' else '停用'}"
        }
        
    except Exception as e:
        api_logger.error(f"切換模型狀態時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"無法切換模型狀態: {str(e)}")

@router.get("/models/active", response_model=List[ModelFileInfo])
async def get_active_models():
    """取得已啟用的模型清單（供其他功能使用）"""
    try:
        # 先獲取所有模型
        all_models = await list_yolo_models()
        
        # 只回傳已啟用的模型
        active_models = [model for model in all_models if model.status == "active"]
        
        api_logger.info(f"找到 {len(active_models)} 個已啟用的模型")
        return active_models
        
    except Exception as e:
        api_logger.error(f"取得已啟用模型時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"無法取得已啟用模型: {str(e)}")

# ===== 系統狀態 API =====

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    """獲取系統統計數據"""
    try:
        import psutil
        
        # 獲取真實的系統監控數據
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # 嘗試獲取 GPU 使用率（如果有 GPU 監控庫）
        gpu_usage = 0.0
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_usage = gpus[0].load * 100
        except ImportError:
            # 如果沒有 GPU 監控庫，使用 nvidia-smi 備用方案
            try:
                import subprocess
                result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    gpu_usage = float(result.stdout.strip())
            except:
                gpu_usage = 0.0
        
        # 從資料庫獲取活躍任務數和總檢測數
        active_tasks = 0
        total_detections = 0
        
        try:
            # 獲取活躍任務數
            from sqlalchemy import select, func
            from app.models.database import AnalysisTask, DetectionResult
            
            # 計算活躍任務
            active_tasks_result = await db.execute(
                select(func.count(AnalysisTask.id)).where(
                    AnalysisTask.status.in_(['running', 'pending'])
                )
            )
            active_tasks = active_tasks_result.scalar() or 0
            
            # 計算總檢測數
            total_detections_result = await db.execute(
                select(func.count(DetectionResult.id))
            )
            total_detections = total_detections_result.scalar() or 0
            
        except Exception as db_error:
            api_logger.warning(f"無法從資料庫獲取統計數據: {db_error}")

        # 獲取系統運行時間
        from app.core.uptime import get_system_uptime
        uptime_seconds = get_system_uptime()
        
        stats = SystemStats(
            cpu_usage=round(cpu_usage, 1),
            memory_usage=round(memory_usage, 1),
            gpu_usage=round(gpu_usage, 1),
            active_tasks=active_tasks,
            total_detections=total_detections,
            system_uptime_seconds=int(uptime_seconds),
            last_updated=datetime.now()
        )
        
        return stats
        
    except Exception as e:
        api_logger.error(f"獲取系統統計數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"系統統計數據獲取失敗: {str(e)}")

@router.get("/detection-summary")
async def get_detection_summary(db: AsyncSession = Depends(get_db)):
    """獲取檢測結果摘要"""
    try:
        # 實際從資料庫查詢最近檢測結果
        from sqlalchemy import func, desc
        from sqlalchemy.future import select
        
        # 查詢最近24小時的檢測結果
        yesterday = datetime.now() - timedelta(days=1)
        
        # 總檢測數
        total_query = select(func.count(DetectionResult.id)).where(
            DetectionResult.created_at >= yesterday
        )
        total_result = await db.execute(total_query)
        total_detections = total_result.scalar() or 0
        
        # 按類別統計
        category_query = select(
            DetectionResult.class_name,
            func.count(DetectionResult.id).label('count')
        ).where(
            DetectionResult.created_at >= yesterday
        ).group_by(DetectionResult.class_name)
        
        category_result = await db.execute(category_query)
        category_counts = {row.class_name: row.count for row in category_result}
        
        # 最近檢測記錄
        recent_query = select(DetectionResult).where(
            DetectionResult.created_at >= yesterday
        ).order_by(desc(DetectionResult.created_at)).limit(10)
        
        recent_result = await db.execute(recent_query)
        recent_detections = recent_result.scalars().all()
        
        return {
            "total_detections": total_detections,
            "category_counts": category_counts,
            "recent_detections": [
                {
                    "id": detection.id,
                    "class_name": detection.class_name,
                    "confidence": detection.confidence,
                    "timestamp": detection.created_at.isoformat(),
                    "bbox": [detection.x_min, detection.y_min, detection.x_max, detection.y_max]
                }
                for detection in recent_detections
            ]
        }
        
    except Exception as e:
        api_logger.error(f"獲取檢測摘要失敗: {e}")
        raise HTTPException(status_code=500, detail=f"檢測摘要獲取失敗: {str(e)}")

# ===== 任務管理 API =====

@router.post("/tasks", response_model=Dict[str, Any])
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    task_service: TaskService = Depends(get_task_service)
):
    """創建新任務"""
    try:
        print(f"🔧 API 端點接收到的數據: {task_data}")
        print(f"🔧 task_service 實例: {task_service}")
        print(f"🔧 task_service 類型: {type(task_service)}")
        print(f"🔧 task_service create_task 方法: {task_service.create_task}")
        
        # 檢查方法源碼
        import inspect
        try:
            source_lines = inspect.getsource(task_service.create_task).split('\n')[:5]
            print("🔧 create_task 方法源碼前5行:")
            for i, line in enumerate(source_lines):
                print(f"  {i+1}: {line}")
        except Exception as e:
            print(f"🔧 無法獲取源碼: {e}")
        
        # 創建任務配置
        config = {
            'camera_id': task_data.camera_id,
            'model_name': task_data.model_name,
            'confidence': task_data.confidence,
            'iou_threshold': task_data.iou_threshold,
            'description': task_data.description,
            'schedule_time': task_data.schedule_time
        }
        print(f"🔧 任務配置: {config}")
        
        # 映射前端任務類型到資料庫任務類型
        task_type_mapping = {
            "realtime": "realtime_camera",
            "batch": "video_file",
            "scheduled": "video_file",
            "event": "realtime_camera"
        }
        
        db_task_type = task_type_mapping.get(task_data.task_type, "video_file")
        print(f"🔧 映射後的任務類型: {task_data.task_type} -> {db_task_type}")
        
        print("🔧 即將調用 task_service.create_task")
        # 創建任務
        task_id = await task_service.create_task(
            task_name=task_data.name,
            task_type=db_task_type,  # 使用映射後的類型
            config=config,
            db=db
        )
        print(f"🔧 task_service.create_task 返回: {task_id}")
        
        # 如果是即時任務，立即開始執行
        if task_data.task_type == "realtime":
            background_tasks.add_task(task_service.start_realtime_task, task_id, db)
        
        api_logger.info(f"任務創建成功: {task_id}")
        
        return {
            "task_id": task_id,
            "message": "任務創建成功",
            "status": "created"
        }
        
    except Exception as e:
        print(f"🔧 API 端點捕獲到異常: {e}")
        import traceback
        traceback.print_exc()
        api_logger.error(f"任務創建失敗: {e}")
        raise HTTPException(status_code=500, detail=f"任務創建失敗: {str(e)}")

@router.get("/tasks", response_model=List[TaskInfo])
async def get_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    task_service: TaskService = Depends(get_task_service)
):
    """獲取任務列表"""
    try:
        tasks = await task_service.get_all_tasks(db=db)
        
        return [
            TaskInfo(
                id=task["id"],
                name=task["name"],
                task_type=task["type"],
                status=task["status"],
                progress=task["progress"],
                camera_id=task.camera_id,
                model_name=task.model_name,
                start_time=task.start_time,
                end_time=task.end_time,
                created_at=task.created_at
            )
            for task in tasks
        ]
        
    except Exception as e:
        api_logger.error(f"獲取任務列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"任務列表獲取失敗: {str(e)}")

@router.put("/tasks/{task_id}/stop")
async def stop_task(task_id: str, db: AsyncSession = Depends(get_db), task_service: TaskService = Depends(get_task_service)):
    """停止任務"""
    try:
        await task_service.stop_task(task_id, db)
        
        return {"message": "任務已停止", "task_id": task_id}
        
    except Exception as e:
        api_logger.error(f"停止任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止任務失敗: {str(e)}")

@router.get("/tasks/stats")
async def get_task_stats(db: AsyncSession = Depends(get_db), task_service: TaskService = Depends(get_task_service)):
    """獲取任務統計"""
    try:
        stats = await task_service.get_task_statistics(db)
        
        return stats
        
    except Exception as e:
        api_logger.error(f"獲取任務統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"任務統計獲取失敗: {str(e)}")

# ===== 攝影機管理 API =====

@router.get("/cameras", response_model=List[CameraInfo])
async def get_cameras():
    """獲取攝影機列表"""
    try:
        camera_service = CameraService()
        cameras = await camera_service.get_cameras()
        
        return [
            CameraInfo(
                id=camera.id,
                name=camera.name,
                status=camera.status,
                camera_type=camera.camera_type,
                resolution=camera.resolution,
                fps=camera.fps,
                group_id=camera.group_id
            )
            for camera in cameras
        ]
        
    except Exception as e:
        api_logger.error(f"獲取攝影機列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"攝影機列表獲取失敗: {str(e)}")

@router.put("/cameras/{camera_id}/toggle")
async def toggle_camera(camera_id: str):
    """切換攝影機狀態"""
    try:
        camera_service = CameraService()
        new_status = await camera_service.toggle_camera(camera_id)
        
        return {
            "camera_id": camera_id,
            "status": new_status,
            "message": f"攝影機已{'啟動' if new_status == 'online' else '停止'}"
        }
        
    except Exception as e:
        api_logger.error(f"切換攝影機狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"攝影機狀態切換失敗: {str(e)}")

@router.post("/cameras/scan")
async def scan_cameras():
    """超快速掃描可用攝影機"""
    try:
        camera_service = CameraService()
        cameras = await camera_service.scan_cameras()
        
        return {
            "message": f"掃描完成，發現 {len(cameras)} 個攝影機",
            "cameras": cameras
        }
        
    except Exception as e:
        api_logger.error(f"掃描攝影機失敗: {e}")
        raise HTTPException(status_code=500, detail=f"攝影機掃描失敗: {str(e)}")

@router.delete("/cameras/{camera_id}")
async def remove_camera(camera_id: str):
    """刪除攝影機配置"""
    try:
        camera_service = CameraService()
        await camera_service.remove_camera(camera_id)
        
        return {
            "message": f"攝影機 {camera_id} 已成功刪除",
            "camera_id": camera_id
        }
        
    except Exception as e:
        api_logger.error(f"刪除攝影機失敗: {e}")
        raise HTTPException(status_code=500, detail=f"攝影機刪除失敗: {str(e)}")

@router.get("/cameras/{camera_index}/preview")
async def get_camera_preview(camera_index: int):
    """獲取攝影機即時預覽影像（JPEG格式）"""
    try:
        from fastapi.responses import Response
        import io
        import cv2
        
        # 直接創建攝影機連接進行即時預覽
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            raise HTTPException(status_code=404, detail=f"攝影機 {camera_index} 無法開啟")
        
        try:
            # 讀取當前影格
            ret, frame = cap.read()
            if not ret or frame is None:
                raise HTTPException(status_code=500, detail=f"攝影機 {camera_index} 無法讀取影格")
            
            # 轉換為JPEG
            _, jpeg_buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            return Response(
                content=jpeg_buffer.tobytes(),
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
            
        finally:
            cap.release()
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"獲取攝影機預覽失敗: {e}")
        raise HTTPException(status_code=500, detail=f"預覽獲取失敗: {str(e)}")

@router.get("/cameras/{camera_index}/stream")
async def camera_stream(camera_index: int):
    """攝影機即時串流（MJPEG格式）"""
    try:
        from fastapi.responses import StreamingResponse
        import cv2
        import time
        
        def generate_frames():
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                return
            
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 編碼為JPEG
                    _, jpeg_buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    # MJPEG串流格式
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' +
                           jpeg_buffer.tobytes() + b'\r\n')
                    
                    # 控制幀率（約30fps）
                    time.sleep(0.033)
                    
            finally:
                cap.release()
        
        return StreamingResponse(
            generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        api_logger.error(f"掃描攝影機失敗: {e}")
        raise HTTPException(status_code=500, detail=f"攝影機掃描失敗: {str(e)}")

# ===== 分析統計 API =====

@router.get("/analytics", response_model=AnalyticsData)
async def get_analytics(
    period: str = "24h",
    db: AsyncSession = Depends(get_db)
):
    """獲取分析統計數據"""
    try:
        analytics_service = AnalyticsService()
        data = await analytics_service.get_analytics_data(period=period, db=db)
        
        return AnalyticsData(
            detection_counts=data["detection_counts"],
            hourly_trend=data["hourly_trend"],
            category_distribution=data["category_distribution"],
            time_period_analysis=data["time_period_analysis"]
        )
        
    except Exception as e:
        api_logger.error(f"獲取分析數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分析數據獲取失敗: {str(e)}")

@router.get("/analytics/heatmap")
async def get_heatmap_data(db: AsyncSession = Depends(get_db)):
    """獲取熱點圖數據"""
    try:
        analytics_service = AnalyticsService()
        heatmap_data = await analytics_service.get_heatmap_data(db=db)
        
        return heatmap_data
        
    except Exception as e:
        api_logger.error(f"獲取熱點圖數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"熱點圖數據獲取失敗: {str(e)}")

@router.get("/detection-results")
async def get_detection_results(
    page: int = 1,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """獲取檢測結果列表"""
    try:
        from app.models.database import DetectionResult
        from sqlalchemy import desc, select
        
        # 計算 offset
        offset = (page - 1) * limit
        
        # 查詢檢測結果
        stmt = (
            select(DetectionResult)
            .order_by(desc(DetectionResult.timestamp))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(stmt)
        detection_results = result.scalars().all()
        
        # 查詢總數
        from sqlalchemy import func
        count_stmt = select(func.count(DetectionResult.id))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # 轉換為響應格式
        results = []
        for detection in detection_results:
            # 計算邊界框的寬度和高度
            width = detection.bbox_x2 - detection.bbox_x1
            height = detection.bbox_y2 - detection.bbox_y1
            area = width * height
            
            results.append({
                "id": detection.id,
                "timestamp": detection.timestamp.isoformat(),
                "task_id": detection.task_id,  # 使用 task_id 而不是 camera_id
                "object_type": detection.object_type,
                "object_chinese": detection.object_type,  # 暫時相同
                "object_id": f"obj_{detection.id}",
                "confidence": detection.confidence,
                "bbox_x1": detection.bbox_x1,
                "bbox_y1": detection.bbox_y1,
                "bbox_x2": detection.bbox_x2,
                "bbox_y2": detection.bbox_y2,
                "center_x": detection.center_x,
                "center_y": detection.center_y,
                "width": width,
                "height": height,
                "area": area,
                "zone": f"zone_{detection.task_id}",
                "zone_chinese": f"區域{detection.task_id}",
                "status": "completed"
            })
        
        return {
            "results": results,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        api_logger.error(f"獲取檢測結果失敗: {e}")
        raise HTTPException(status_code=500, detail=f"檢測結果獲取失敗: {str(e)}")

@router.get("/detection-results/{detection_id}")
async def get_detection_detail(
    detection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """獲取特定檢測結果的詳細信息"""
    try:
        from app.models.database import DetectionResult
        from sqlalchemy import select
        from uuid import UUID
        
        # 查詢特定檢測結果
        stmt = select(DetectionResult).where(DetectionResult.id == UUID(detection_id))
        result = await db.execute(stmt)
        detection = result.scalar_one_or_none()
        
        if not detection:
            raise HTTPException(status_code=404, detail="檢測結果不存在")
        
        return {
            "id": str(detection.id),
            "timestamp": detection.timestamp.isoformat(),
            "camera_id": detection.camera_id,
            "object_type": detection.object_type,
            "confidence": detection.confidence,
            "bbox": detection.bbox,
            "status": "completed",
            "processing_time": getattr(detection, 'processing_time', None),
            "image_url": getattr(detection, 'image_url', None)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="無效的檢測結果ID")
    except Exception as e:
        api_logger.error(f"獲取檢測詳情失敗: {e}")
        raise HTTPException(status_code=500, detail=f"檢測詳情獲取失敗: {str(e)}")

# ===== YOLO 模型管理 API =====

@router.get("/models")
async def get_available_models():
    """獲取可用的YOLO模型"""
    try:
        import os
        from pathlib import Path
        
        # 檢查當前目錄和常見模型目錄中的 .pt 文件
        model_dirs = [
            ".",  # 當前目錄
            "models",  # models 目錄
            "weights",  # weights 目錄
            "../",  # 上級目錄
            "../../",  # 根目錄
        ]
        
        found_models = []
        
        # 預定義的模型信息
        model_info = {
            "yolo11n.pt": {
                "id": "yolov11n",
                "name": "YOLOv11n",
                "params": "2.6M",
                "speed": "Fast",
                "accuracy": "Good",
                "size_mb": 5.2
            },
            "yolo11s.pt": {
                "id": "yolov11s", 
                "name": "YOLOv11s",
                "params": "9.4M",
                "speed": "Fast",
                "accuracy": "Good",
                "size_mb": 18.8
            },
            "yolo11m.pt": {
                "id": "yolov11m",
                "name": "YOLOv11m", 
                "params": "20.1M",
                "speed": "Medium",
                "accuracy": "Better",
                "size_mb": 40.2
            },
            "yolo11l.pt": {
                "id": "yolov11l",
                "name": "YOLOv11l",
                "params": "25.3M", 
                "speed": "Medium",
                "accuracy": "Better",
                "size_mb": 50.6
            },
            "yolo11x.pt": {
                "id": "yolov11x",
                "name": "YOLOv11x",
                "params": "56.9M",
                "speed": "Slow", 
                "accuracy": "Best",
                "size_mb": 113.8
            }
        }
        
        # 掃描模型文件
        for model_dir in model_dirs:
            model_path = Path(model_dir)
            if model_path.exists():
                for pt_file in model_path.glob("*.pt"):
                    filename = pt_file.name
                    if filename in model_info:
                        file_size = pt_file.stat().st_size / (1024 * 1024)  # MB
                        model_data = model_info[filename].copy()
                        model_data.update({
                            "file": filename,
                            "status": "unloaded",  # 預設為未載入
                            "available": True,
                            "file_path": str(pt_file.absolute()),
                            "actual_size_mb": round(file_size, 1)
                        })
                        found_models.append(model_data)
        
        # 如果沒找到任何模型，返回預設的模型列表（但標記為不可用）
        if not found_models:
            for filename, info in model_info.items():
                model_data = info.copy()
                model_data.update({
                    "file": filename,
                    "status": "unavailable",
                    "available": False,
                    "file_path": None,
                    "actual_size_mb": 0
                })
                found_models.append(model_data)
        
        # 假設第一個可用的模型是當前載入的模型
        current_model = None
        available_models = [m for m in found_models if m["available"]]
        if available_models:
            available_models[0]["status"] = "loaded"
            current_model = available_models[0]["id"]
        
        return {
            "models": found_models,
            "current_model": current_model,
            "total_models": len(found_models),
            "available_models": len(available_models)
        }
        
    except Exception as e:
        api_logger.error(f"獲取模型列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模型列表獲取失敗: {str(e)}")

@router.get("/models/current")
async def get_current_model():
    """獲取當前載入的模型"""
    try:
        return {
            "model_id": "yolov11s",
            "model_name": "YOLOv11s",
            "status": "loaded",
            "loaded_at": "2024-01-01T10:00:00Z"
        }
    except Exception as e:
        api_logger.error(f"獲取當前模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"當前模型獲取失敗: {str(e)}")

@router.post("/models/load")
async def load_model(request: ModelRequest):
    """載入指定的YOLO模型"""
    try:
        model_identifier = request.get_model_identifier()
        
        # 模擬載入延遲
        import asyncio
        await asyncio.sleep(1)
        
        return {
            "message": f"模型 {model_identifier} 載入成功",
            "model_id": model_identifier,
            "status": "loaded"
        }
        
    except ValueError as e:
        api_logger.error(f"模型識別符錯誤: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        api_logger.error(f"載入模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模型載入失敗: {str(e)}")

@router.post("/models/unload")
async def unload_model(request: ModelRequest):
    """卸載指定的YOLO模型"""
    try:
        model_identifier = request.get_model_identifier()
        
        # 模擬卸載延遲
        import asyncio
        await asyncio.sleep(0.5)
        
        return {
            "message": f"模型 {model_identifier} 卸載成功",
            "model_id": model_identifier,
            "status": "unloaded"
        }
        
    except ValueError as e:
        api_logger.error(f"模型識別符錯誤: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        api_logger.error(f"卸載模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模型卸載失敗: {str(e)}")

@router.get("/models/config")
async def get_model_config():
    """獲取模型配置"""
    try:
        return {
            "confidence": 0.5,
            "iou": 0.45,
            "image_size": 640,
            "max_detections": 1000,
            "classes": None  # None 表示檢測所有類別
        }
    except Exception as e:
        api_logger.error(f"獲取模型配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模型配置獲取失敗: {str(e)}")

@router.put("/models/config")
async def update_model_config(config: ModelConfigUpdate):
    """更新模型配置"""
    try:
        # 驗證配置參數
        confidence = config.confidence if config.confidence is not None else 0.5
        iou = config.iou_threshold if config.iou_threshold is not None else 0.45
        image_size = config.image_size if config.image_size is not None else 640
        
        if not (0.0 <= confidence <= 1.0):
            raise HTTPException(status_code=400, detail="confidence 必須在 0.0 到 1.0 之間")
        if not (0.0 <= iou <= 1.0):
            raise HTTPException(status_code=400, detail="iou 必須在 0.0 到 1.0 之間")
        if image_size not in [320, 480, 640, 800, 1024]:
            raise HTTPException(status_code=400, detail="image_size 必須是 320, 480, 640, 800, 1024 中的一個")
        
        # 模擬保存配置
        return {
            "message": "模型配置更新成功",
            "config": {
                "confidence": confidence,
                "iou": iou,
                "image_size": image_size
            }
        }
    except Exception as e:
        api_logger.error(f"更新模型配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模型配置更新失敗: {str(e)}")

@router.put("/models/{model_name}/load")
async def load_model_legacy(model_name: str):
    """載入指定的YOLO模型（舊版API，向後兼容）"""
    try:
        # 模擬載入延遲
        import asyncio
        await asyncio.sleep(1)
        
        return {
            "message": f"模型 {model_name} 載入成功",
            "model_name": model_name
        }
        
    except Exception as e:
        api_logger.error(f"載入模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模型載入失敗: {str(e)}")

@router.post("/models/upload")
async def upload_model(file: UploadFile = File(...)):
    """上傳自定義模型"""
    try:
        if not file.filename.endswith('.pt'):
            raise HTTPException(status_code=400, detail="只支援 .pt 格式的模型文件")
        
        # 保存上傳的模型文件
        model_dir = "models"
        os.makedirs(model_dir, exist_ok=True)
        file_path = os.path.join(model_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "message": f"模型 {file.filename} 上傳成功",
            "file_path": file_path
        }
        
    except Exception as e:
        api_logger.error(f"上傳模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模型上傳失敗: {str(e)}")

# ===== 即時檢測 API =====

@router.get("/detection/stream/{camera_id}")
async def get_detection_stream(camera_id: str):
    """獲取攝影機檢測串流（WebSocket將在另一個文件實現）"""
    try:
        # 這裡返回串流端點信息
        return {
            "camera_id": camera_id,
            "stream_url": f"/ws/detection/{camera_id}",
            "message": "請使用WebSocket連接獲取即時檢測串流"
        }
        
    except Exception as e:
        api_logger.error(f"獲取檢測串流失敗: {e}")
        raise HTTPException(status_code=500, detail=f"檢測串流獲取失敗: {str(e)}")

# ===== 資料來源管理 API =====

@router.get("/data-sources", response_model=List[DataSourceInfo])
async def get_data_sources(
    source_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """獲取資料來源列表"""
    try:
        db_service = DatabaseService()
        sources = await db_service.get_data_sources(db, source_type=source_type, status=status)
        
        return [
            DataSourceInfo(
                id=source.id,
                source_type=source.source_type,
                name=source.name,
                config=source.config or {},
                status=source.status,
                last_check=source.last_check,
                created_at=source.created_at
            )
            for source in sources
        ]
        
    except Exception as e:
        api_logger.error(f"獲取資料來源列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取資料來源列表失敗: {str(e)}")

@router.post("/data-sources", response_model=DataSourceInfo)
async def create_data_source(
    source_data: DataSourceCreate,
    db: AsyncSession = Depends(get_db)
):
    """創建新的資料來源"""
    try:
        api_logger.info(f"📥 收到創建資料來源請求: {source_data.dict()}")
        
        db_service = DatabaseService()
        
        # 驗證配置格式
        if source_data.source_type == "camera":
            api_logger.info(f"🔍 驗證攝影機配置: {source_data.config}")
            # 驗證攝影機配置
            if "device_id" not in source_data.config and "url" not in source_data.config:
                api_logger.error(f"❌ 攝影機配置驗證失敗: 缺少 device_id 或 url")
                raise HTTPException(status_code=400, detail="攝影機來源必須提供 device_id 或 url")
        elif source_data.source_type == "video_file":
            # 驗證影片檔案配置
            if "file_path" not in source_data.config:
                raise HTTPException(status_code=400, detail="影片檔案來源必須提供 file_path")
        elif source_data.source_type == "image_folder":
            # 驗證圖片資料夾配置
            if "folder_path" not in source_data.config:
                raise HTTPException(status_code=400, detail="圖片資料夾來源必須提供 folder_path")
        
        source = await db_service.create_data_source(db, {
            "source_type": source_data.source_type,
            "name": source_data.name,
            "config": source_data.config,
            "status": "active"
        })
        
        return DataSourceInfo(
            id=source.id,
            source_type=source.source_type,
            name=source.name,
            config=source.config or {},
            status=source.status,
            last_check=source.last_check,
            created_at=source.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"創建資料來源失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建資料來源失敗: {str(e)}")

@router.get("/data-sources/{source_id}", response_model=DataSourceInfo)
async def get_data_source(
    source_id: int,
    db: AsyncSession = Depends(get_db)
):
    """獲取特定資料來源詳情"""
    try:
        db_service = DatabaseService()
        source = await db_service.get_data_source(db, source_id)
        
        if not source:
            raise HTTPException(status_code=404, detail="資料來源不存在")
        
        return DataSourceInfo(
            id=source.id,
            source_type=source.source_type,
            name=source.name,
            config=source.config or {},
            status=source.status,
            last_check=source.last_check,
            created_at=source.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"獲取資料來源詳情失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取資料來源詳情失敗: {str(e)}")

@router.put("/data-sources/{source_id}", response_model=DataSourceInfo)
async def update_data_source(
    source_id: int,
    update_data: DataSourceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新資料來源"""
    try:
        db_service = DatabaseService()
        
        # 檢查資料來源是否存在
        source = await db_service.get_data_source(db, source_id)
        if not source:
            raise HTTPException(status_code=404, detail="資料來源不存在")
        
        # 準備更新數據
        update_dict = {}
        if update_data.name is not None:
            update_dict["name"] = update_data.name
        if update_data.config is not None:
            update_dict["config"] = update_data.config
        if update_data.status is not None:
            update_dict["status"] = update_data.status
            update_dict["last_check"] = datetime.utcnow()
        
        # 執行更新
        from sqlalchemy import update
        await db.execute(
            update(DataSource)
            .where(DataSource.id == source_id)
            .values(**update_dict)
        )
        await db.commit()
        
        # 返回更新後的資料
        updated_source = await db_service.get_data_source(db, source_id)
        
        return DataSourceInfo(
            id=updated_source.id,
            source_type=updated_source.source_type,
            name=updated_source.name,
            config=updated_source.config or {},
            status=updated_source.status,
            last_check=updated_source.last_check,
            created_at=updated_source.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"更新資料來源失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新資料來源失敗: {str(e)}")

@router.delete("/data-sources/{source_id}")
async def delete_data_source(
    source_id: int,
    db: AsyncSession = Depends(get_db)
):
    """刪除資料來源"""
    try:
        # 檢查資料來源是否存在
        from sqlalchemy import select, delete
        
        result = await db.execute(
            select(DataSource).where(DataSource.id == source_id)
        )
        source = result.scalar_one_or_none()
        
        if not source:
            raise HTTPException(status_code=404, detail="資料來源不存在")
        
        source_name = source.name
        
        # 執行刪除 (簡化版本，跳過複雜的關聯檢查)
        await db.execute(
            delete(DataSource).where(DataSource.id == source_id)
        )
        await db.commit()
        
        api_logger.info(f"資料來源 {source_name} (ID: {source_id}) 已被刪除")
        return {"message": f"資料來源 {source_name} 已成功刪除"}
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"刪除資料來源失敗 (ID: {source_id}): {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"刪除資料來源失敗: {str(e)}")

@router.post("/data-sources/{source_id}/test")
async def test_data_source(
    source_id: int,
    db: AsyncSession = Depends(get_db)
):
    """測試資料來源連接"""
    try:
        db_service = DatabaseService()
        source = await db_service.get_data_source(db, source_id)
        
        if not source:
            raise HTTPException(status_code=404, detail="資料來源不存在")
        
        test_result = {"source_id": source_id, "status": "success", "message": ""}
        
        if source.source_type == "camera":
            # 測試攝影機連接
            config = source.config or {}
            if "device_id" in config:
                # USB 攝影機測試
                import cv2
                try:
                    cap = cv2.VideoCapture(config["device_id"])
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            test_result["message"] = f"USB攝影機 {config['device_id']} 連接正常"
                        else:
                            test_result["status"] = "error"
                            test_result["message"] = f"USB攝影機 {config['device_id']} 無法讀取幀"
                    else:
                        test_result["status"] = "error"
                        test_result["message"] = f"無法開啟USB攝影機 {config['device_id']}"
                    cap.release()
                except Exception as e:
                    test_result["status"] = "error"
                    test_result["message"] = f"USB攝影機測試失敗: {str(e)}"
            
            elif "url" in config:
                # 網路攝影機測試
                import cv2
                try:
                    cap = cv2.VideoCapture(config["url"])
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            test_result["message"] = f"網路攝影機 {config['url']} 連接正常"
                        else:
                            test_result["status"] = "error"
                            test_result["message"] = f"網路攝影機 {config['url']} 無法讀取幀"
                    else:
                        test_result["status"] = "error"
                        test_result["message"] = f"無法連接網路攝影機 {config['url']}"
                    cap.release()
                except Exception as e:
                    test_result["status"] = "error"
                    test_result["message"] = f"網路攝影機測試失敗: {str(e)}"
        
        elif source.source_type == "video_file":
            # 測試影片檔案
            config = source.config or {}
            file_path = config.get("file_path")
            if file_path and os.path.exists(file_path):
                import cv2
                try:
                    cap = cv2.VideoCapture(file_path)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            duration = frame_count / fps if fps > 0 else 0
                            test_result["message"] = f"影片檔案 {file_path} 可正常讀取，總幀數: {frame_count}，時長: {duration:.2f}秒"
                        else:
                            test_result["status"] = "error"
                            test_result["message"] = f"影片檔案 {file_path} 無法讀取幀"
                    else:
                        test_result["status"] = "error"
                        test_result["message"] = f"無法開啟影片檔案 {file_path}"
                    cap.release()
                except Exception as e:
                    test_result["status"] = "error"
                    test_result["message"] = f"影片檔案測試失敗: {str(e)}"
            else:
                test_result["status"] = "error"
                test_result["message"] = f"影片檔案 {file_path} 不存在"
        
        elif source.source_type == "image_folder":
            # 測試圖片資料夾
            config = source.config or {}
            folder_path = config.get("folder_path")
            if folder_path and os.path.exists(folder_path):
                supported_formats = config.get("supported_formats", ["jpg", "jpeg", "png", "bmp"])
                scan_subdirs = config.get("scan_subdirs", False)
                
                image_count = 0
                if scan_subdirs:
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            if any(file.lower().endswith(f".{fmt}") for fmt in supported_formats):
                                image_count += 1
                else:
                    for file in os.listdir(folder_path):
                        if any(file.lower().endswith(f".{fmt}") for fmt in supported_formats):
                            image_count += 1
                
                test_result["message"] = f"圖片資料夾 {folder_path} 找到 {image_count} 張圖片"
                if image_count == 0:
                    test_result["status"] = "warning"
                    test_result["message"] += "（未找到支援格式的圖片）"
            else:
                test_result["status"] = "error"
                test_result["message"] = f"圖片資料夾 {folder_path} 不存在"
        
        # 更新測試狀態到資料庫
        await db_service.update_data_source_status(
            db, source_id, 
            "active" if test_result["status"] == "success" else "error"
        )
        
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"測試資料來源失敗: {e}")
        raise HTTPException(status_code=500, detail=f"測試資料來源失敗: {str(e)}")

@router.get("/data-sources/types/camera/devices")
async def get_available_cameras():
    """獲取可用的攝影機設備"""
    try:
        import cv2
        available_cameras = []
        
        # 檢測USB攝影機
        for i in range(10):  # 檢查前10個設備
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    available_cameras.append({
                        "device_id": i,
                        "name": f"USB Camera {i}",
                        "type": "usb"
                    })
                cap.release()
        
        return {
            "cameras": available_cameras,
            "message": f"找到 {len(available_cameras)} 個可用的攝影機"
        }
        
    except Exception as e:
        api_logger.error(f"獲取可用攝影機失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取可用攝影機失敗: {str(e)}")

@router.get("/data-sources/types/video/files")
async def get_video_files(directory: str = "."):
    """獲取指定目錄下的影片檔案"""
    try:
        if not os.path.exists(directory):
            raise HTTPException(status_code=404, detail="目錄不存在")
        
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        video_files = []
        
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file)
                if ext.lower() in video_extensions:
                    stat = os.stat(file_path)
                    video_files.append({
                        "filename": file,
                        "path": file_path,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return {
            "directory": directory,
            "files": video_files,
            "count": len(video_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"獲取影片檔案失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取影片檔案失敗: {str(e)}")

@router.post("/data-sources/upload/video")
async def upload_video_file(file: UploadFile = File(...)):
    """上傳影片檔案"""
    try:
        # 檢查檔案類型
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支援的檔案格式。支援的格式: {', '.join(allowed_extensions)}"
            )
        
        # 檢查檔案大小 (限制為 500MB)
        max_size = 500 * 1024 * 1024  # 500MB
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"檔案太大。最大支援 500MB，您的檔案為 {file.size / 1024 / 1024:.1f}MB"
            )
        
        # 創建上傳目錄
        upload_dir = "uploads/videos"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成唯一檔案名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # 保存檔案
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 驗證影片檔案
        try:
            import cv2
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                os.remove(file_path)  # 刪除無效檔案
                raise HTTPException(status_code=400, detail="無效的影片檔案")
            
            # 獲取影片資訊
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"影片檔案驗證失敗: {str(e)}")
        
        # 創建資料來源記錄
        async with AsyncSessionLocal() as db:
            db_service = DatabaseService()
            
            # 創建資料來源配置
            video_config = {
                "path": file_path,  # 使用 "path" 符合模型期望
                "file_path": file_path,  # 保留向後相容性
                "original_name": file.filename,
                "file_size": os.path.getsize(file_path),
                "duration": round(duration, 2),
                "fps": round(fps, 2),
                "resolution": f"{width}x{height}",
                "frame_count": frame_count,
                "upload_time": datetime.now().isoformat()
            }
            
            # 創建資料來源記錄
            source_data = {
                "source_type": "video_file",  # 使用 "video_file" 符合資料庫約束
                "name": file.filename,
                "config": video_config,
                "status": "active"
            }
            
            created_source = await db_service.create_data_source(db, source_data)
            
            return {
                "message": f"影片檔案 {file.filename} 上傳成功",
                "source_id": created_source.id,
                "file_path": file_path,
                "original_name": file.filename,
                "size": os.path.getsize(file_path),
                "video_info": {
                    "duration": round(duration, 2),
                    "fps": round(fps, 2),
                    "resolution": f"{width}x{height}",
                    "frame_count": frame_count
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"上傳影片檔案失敗: {e}")
        raise HTTPException(status_code=500, detail=f"上傳影片檔案失敗: {str(e)}")

@router.get("/data-sources/upload/video/progress/{task_id}")
async def get_upload_progress(task_id: str):
    """獲取上傳進度（未來功能）"""
    return {
        "task_id": task_id,
        "progress": 100,
        "status": "completed",
        "message": "上傳完成"
    }

# ===== 數據管理 API =====

@router.get("/storage-analysis")
async def get_storage_analysis():
    """獲取儲存空間分析"""
    try:
        import os
        import psutil
        from pathlib import Path
        
        # 計算不同類型文件的大小
        detection_size = 0
        video_size = 0
        log_size = 0
        
        # 檢測結果數據庫大小（估算）
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("SELECT COUNT(*) FROM detection_results"))
                count = result.scalar()
                detection_size = count * 500  # 估算每筆記錄約500字節
        except:
            detection_size = 0
        
        # 檢查影片文件夾大小
        video_dirs = ["uploads", "videos", "media"]
        for dir_name in video_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        video_size += file_path.stat().st_size
        
        # 檢查日誌文件夾大小
        log_dirs = ["logs", "log"]
        for dir_name in log_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        log_size += file_path.stat().st_size
        
        total_size = detection_size + video_size + log_size
        
        return {
            "detection_size": detection_size,
            "video_size": video_size,
            "log_size": log_size,
            "total_size": total_size,
            "free_space": psutil.disk_usage('.').free
        }
    except Exception as e:
        api_logger.error(f"獲取儲存分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取儲存分析失敗: {str(e)}")

@router.get("/quick-stats")
async def get_quick_stats():
    """獲取快速統計數據"""
    try:
        async with AsyncSessionLocal() as db:
            # 今日檢測數
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            result = await db.execute(text("""
                SELECT COUNT(*) FROM detection_results 
                WHERE timestamp >= :today_start
            """), {"today_start": today_start})
            today_detections = result.scalar() or 0
            
            # 平均信心度
            result = await db.execute(text("SELECT AVG(confidence) FROM detection_results"))
            avg_confidence = result.scalar() or 0
            
            # 最常見物件
            result = await db.execute(text("""
                SELECT object_type, COUNT(*) as count 
                FROM detection_results 
                GROUP BY object_type 
                ORDER BY count DESC 
                LIMIT 1
            """))
            most_common = result.fetchone()
            most_common_object = most_common[0] if most_common else "N/A"
            
            # 活躍時段
            result = await db.execute(text("""
                SELECT EXTRACT(hour FROM timestamp) as hour, COUNT(*) as count
                FROM detection_results 
                GROUP BY hour 
                ORDER BY count DESC 
                LIMIT 1
            """))
            peak_hour = result.fetchone()
            peak_hours = f"{int(peak_hour[0]):02d}:00-{int(peak_hour[0])+1:02d}:00" if peak_hour else "N/A"
            
            # 高信心度檢測百分比
            result = await db.execute(text("""
                SELECT 
                    CASE 
                        WHEN COUNT(*) > 0 THEN
                            COUNT(CASE WHEN confidence >= 0.8 THEN 1 END) * 100.0 / COUNT(*)
                        ELSE 0 
                    END as high_confidence_percentage
                FROM detection_results
            """))
            high_confidence_percentage = result.scalar() or 0
            
            # 追蹤連續性（簡化計算）
            tracking_continuity = 85.0  # 假設值，實際應該根據object_id連續性計算
            
            return {
                "today_detections": int(today_detections),
                "avg_confidence": float(avg_confidence),
                "most_common_object": most_common_object,
                "peak_hours": peak_hours,
                "high_confidence_percentage": float(high_confidence_percentage),
                "tracking_continuity": tracking_continuity
            }
    except Exception as e:
        api_logger.error(f"獲取快速統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取快速統計失敗: {str(e)}")

@router.get("/export-data")
async def export_data(
    format: str = Query(..., description="匯出格式: csv, json, excel"),
    ids: Optional[str] = Query(None, description="要匯出的記錄ID，用逗號分隔"),
    object_type: Optional[str] = Query(None, description="物件類型篩選"),
    confidence_min: Optional[float] = Query(None, description="最小信心度"),
    confidence_max: Optional[float] = Query(None, description="最大信心度"),
    start_date: Optional[str] = Query(None, description="開始日期"),
    end_date: Optional[str] = Query(None, description="結束日期")
):
    """匯出檢測數據"""
    try:
        from fastapi.responses import StreamingResponse
        import csv
        import json
        import io
        
        async with AsyncSessionLocal() as db:
            # 構建查詢
            query = "SELECT * FROM detection_results WHERE 1=1"
            params = {}
            
            if ids:
                id_list = [int(id.strip()) for id in ids.split(',')]
                query += " AND id = ANY(:ids)"
                params["ids"] = id_list
            
            if object_type:
                query += " AND object_type = :object_type"
                params["object_type"] = object_type
            
            if confidence_min is not None:
                query += " AND confidence >= :confidence_min"
                params["confidence_min"] = confidence_min
                
            if confidence_max is not None:
                query += " AND confidence <= :confidence_max"
                params["confidence_max"] = confidence_max
            
            if start_date:
                query += " AND timestamp >= :start_date"
                params["start_date"] = start_date
                
            if end_date:
                query += " AND timestamp <= :end_date"
                params["end_date"] = end_date
            
            query += " ORDER BY timestamp DESC"
            
            result = await db.execute(text(query), params)
            records = result.fetchall()
            
            if format.lower() == 'csv':
                output = io.StringIO()
                writer = csv.writer(output)
                
                # 寫入標題
                if records:
                    writer.writerow(records[0]._fields)
                    
                # 寫入數據
                for record in records:
                    writer.writerow(record)
                
                output.seek(0)
                return StreamingResponse(
                    io.BytesIO(output.getvalue().encode('utf-8')),
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=detection_results_{datetime.now().strftime('%Y%m%d')}.csv"}
                )
            
            elif format.lower() == 'json':
                data = []
                for record in records:
                    record_dict = {}
                    for i, field in enumerate(record._fields):
                        value = record[i]
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        record_dict[field] = value
                    data.append(record_dict)
                
                json_str = json.dumps(data, ensure_ascii=False, indent=2)
                return StreamingResponse(
                    io.BytesIO(json_str.encode('utf-8')),
                    media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename=detection_results_{datetime.now().strftime('%Y%m%d')}.json"}
                )
            
            else:
                raise HTTPException(status_code=400, detail="不支援的匯出格式")
                
    except Exception as e:
        api_logger.error(f"匯出數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"匯出數據失敗: {str(e)}")

@router.delete("/detection-results/{detection_id}")
async def delete_detection_result(detection_id: int):
    """刪除檢測結果"""
    try:
        async with AsyncSessionLocal() as db:
            # 檢查記錄是否存在
            result = await db.execute(
                text("SELECT id FROM detection_results WHERE id = :id"),
                {"id": detection_id}
            )
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="記錄不存在")
            
            # 刪除記錄
            await db.execute(
                text("DELETE FROM detection_results WHERE id = :id"),
                {"id": detection_id}
            )
            await db.commit()
            
            return {"message": "記錄已刪除", "id": detection_id}
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"刪除檢測結果失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除檢測結果失敗: {str(e)}")

@router.post("/optimize-database")
async def optimize_database():
    """優化資料庫"""
    try:
        async with AsyncSessionLocal() as db:
            # PostgreSQL 優化命令
            await db.execute(text("VACUUM ANALYZE detection_results"))
            await db.execute(text("VACUUM ANALYZE analysis_tasks"))
            await db.execute(text("VACUUM ANALYZE behavior_events"))
            await db.commit()
            
        return {"message": "資料庫優化完成"}
    except Exception as e:
        api_logger.error(f"優化資料庫失敗: {e}")
        raise HTTPException(status_code=500, detail=f"優化資料庫失敗: {str(e)}")

@router.post("/clear-database")
async def clear_database():
    """清空資料庫（危險操作）"""
    try:
        async with AsyncSessionLocal() as db:
            # 按照外鍵依賴順序刪除
            await db.execute(text("DELETE FROM behavior_events"))
            await db.execute(text("DELETE FROM detection_results"))
            await db.execute(text("DELETE FROM analysis_tasks"))
            await db.commit()
            
        return {"message": "資料庫已清空"}
    except Exception as e:
        api_logger.error(f"清空資料庫失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清空資料庫失敗: {str(e)}")

@router.get("/backup-database")
async def backup_database():
    """備份資料庫"""
    try:
        from fastapi.responses import FileResponse
        import subprocess
        import tempfile
        import os
        
        # 創建臨時文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            temp_file = f.name
        
        try:
            # 使用 pg_dump 備份（需要配置）
            # 這裡使用簡化的SQL導出
            async with AsyncSessionLocal() as db:
                backup_sql = "-- Database Backup\n"
                
                # 導出analysis_tasks
                result = await db.execute(text("SELECT * FROM analysis_tasks"))
                records = result.fetchall()
                if records:
                    backup_sql += "\n-- Analysis Tasks\n"
                    for record in records:
                        backup_sql += f"INSERT INTO analysis_tasks VALUES {tuple(record)};\n"
                
                # 寫入文件
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(backup_sql)
            
            return FileResponse(
                temp_file,
                filename=f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                media_type="application/sql"
            )
        finally:
            # 清理臨時文件將在請求完成後進行
            pass
            
    except Exception as e:
        api_logger.error(f"備份資料庫失敗: {e}")
        raise HTTPException(status_code=500, detail=f"備份資料庫失敗: {str(e)}")

@router.post("/system/shutdown")
async def shutdown_system():
    """停止整個系統"""
    try:
        import os
        import signal
        import asyncio
        import psutil
        import threading
        import time
        
        api_logger.info("收到系統停止請求")
        
        def delayed_shutdown():
            """延遲執行停止，確保回應先發送"""
            time.sleep(1)
            
            try:
                # 獲取當前進程和父進程
                current_process = psutil.Process()
                parent_process = current_process.parent()
                
                api_logger.info("執行系統停止")
                
                # 如果是Windows，發送KeyboardInterrupt到父進程
                if os.name == 'nt':  # Windows
                    # 使用更溫和的方式，發送CTRL+C事件
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    # 發送 CTRL+C 到主控制台
                    kernel32.GenerateConsoleCtrlEvent(0, parent_process.pid)
                    
                    # 如果溫和方式失敗，再使用強制終止
                    time.sleep(3)
                    if parent_process.is_running():
                        os.system(f'taskkill /F /T /PID {parent_process.pid}')
                else:  # Unix/Linux
                    # 發送SIGINT到父進程（相當於Ctrl+C）
                    parent_process.send_signal(signal.SIGINT)
                
            except Exception as e:
                print(f"停止過程中發生錯誤: {e}")
                api_logger.error(f"停止過程中發生錯誤: {e}")
                # 最後的強制退出
                os._exit(0)
        
        # 在背景執行停止
        threading.Thread(target=delayed_shutdown, daemon=True).start()
        
        # 返回確認訊息給前端
        response = {
            "success": True,
            "message": "系統停止指令已發送",
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        api_logger.error(f"停止系統失敗: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"停止系統失敗: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/system/status")
async def get_system_status():
    """獲取系統狀態"""
    try:
        import psutil
        import sys
        
        # 獲取系統資源使用情況
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 獲取Python進程信息
        process = psutil.Process()
        
        status = {
            "running": True,
            "uptime": time.time() - process.create_time(),
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "memory_total": memory.total,
            "memory_used": memory.used,
            "disk_usage": disk.percent,
            "python_version": sys.version,
            "pid": os.getpid(),
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(content=status)
        
    except Exception as e:
        api_logger.error(f"獲取系統狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取系統狀態失敗: {str(e)}")

@router.get("/video-file")
async def get_video_file(path: str):
    """讀取伺服器上的影片檔案"""
    try:
        import os
        from fastapi.responses import FileResponse
        
        # 檢查檔案是否存在
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="影片檔案不存在")
        
        # 檢查是否為影片檔案
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        if not any(path.lower().endswith(ext) for ext in video_extensions):
            raise HTTPException(status_code=400, detail="不是有效的影片檔案")
        
        return FileResponse(
            path=path,
            media_type='video/mp4',
            filename=os.path.basename(path)
        )
        
    except Exception as e:
        api_logger.error(f"讀取影片檔案失敗: {e}")
        raise HTTPException(status_code=500, detail=f"讀取影片檔案失敗: {str(e)}")

# ===== 影片列表相關 =====

class VideoFileInfo(BaseModel):
    """影片檔案資訊"""
    id: str
    name: str
    file_path: str
    upload_time: str
    size: str
    duration: Optional[str] = None
    resolution: Optional[str] = None
    status: str  # 'ready', 'analyzing', 'completed'

@router.get("/video-list")
async def get_video_list():
    """
    獲取上傳影片資料夾中的影片列表
    """
    try:
        videos_dir = "D:/project/system/yolo_backend/uploads/videos"
        
        if not os.path.exists(videos_dir):
            return JSONResponse(content={"videos": []})
        
        video_list = []
        supported_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        
        for filename in os.listdir(videos_dir):
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                file_path = os.path.join(videos_dir, filename)
                
                if os.path.isfile(file_path):
                    # 獲取檔案資訊
                    stat_info = os.stat(file_path)
                    file_size = stat_info.st_size
                    upload_time = datetime.fromtimestamp(stat_info.st_mtime)
                    
                    # 格式化檔案大小
                    if file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.1f}KB"
                    elif file_size < 1024 * 1024 * 1024:
                        size_str = f"{file_size / (1024 * 1024):.1f}MB"
                    else:
                        size_str = f"{file_size / (1024 * 1024 * 1024):.1f}GB"
                    
                    # 嘗試獲取影片資訊
                    duration = None
                    resolution = None
                    try:
                        import cv2
                        cap = cv2.VideoCapture(file_path)
                        if cap.isOpened():
                            # 獲取影片時長
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                            if fps > 0:
                                duration_seconds = frame_count / fps
                                minutes = int(duration_seconds // 60)
                                seconds = int(duration_seconds % 60)
                                duration = f"{minutes}:{seconds:02d}"
                            
                            # 獲取解析度
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            if width > 0 and height > 0:
                                resolution = f"{width}x{height}"
                        
                        cap.release()
                    except:
                        # 如果無法讀取影片資訊，使用預設值
                        duration = "未知"
                        resolution = "未知"
                    
                    # 預設狀態為 ready
                    status = "ready"
                    
                    video_info = VideoFileInfo(
                        id=filename,  # 使用檔名作為 ID
                        name=filename,
                        file_path=file_path,
                        upload_time=upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                        size=size_str,
                        duration=duration,
                        resolution=resolution,
                        status=status
                    )
                    
                    video_list.append(video_info.dict())
        
        # 按上傳時間降序排列
        video_list.sort(key=lambda x: x['upload_time'], reverse=True)
        
        return JSONResponse(content={
            "videos": video_list,
            "total": len(video_list)
        })
        
    except Exception as e:
        api_logger.error(f"獲取影片列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取影片列表失敗: {str(e)}")


@router.get("/videos")
async def get_videos_simple():
    """
    簡化版獲取影片列表 - 用於測試
    """
    try:
        videos_dir = "D:/project/system/yolo_backend/uploads/videos"
        
        if not os.path.exists(videos_dir):
            return {"videos": [], "total": 0}
        
        video_list = []
        supported_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        
        for filename in os.listdir(videos_dir):
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                file_path = os.path.join(videos_dir, filename)
                
                if os.path.isfile(file_path):
                    # 獲取檔案基本資訊
                    stat_info = os.stat(file_path)
                    file_size = stat_info.st_size
                    upload_time = datetime.fromtimestamp(stat_info.st_mtime)
                    
                    # 格式化檔案大小
                    if file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.1f}KB"
                    elif file_size < 1024 * 1024 * 1024:
                        size_str = f"{file_size / (1024 * 1024):.1f}MB"
                    else:
                        size_str = f"{file_size / (1024 * 1024 * 1024):.1f}GB"
                    
                    video_info = {
                        "id": filename,
                        "name": filename,
                        "file_path": file_path,
                        "upload_time": upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "size": size_str,
                        "duration": "2:30",  # 預設值
                        "resolution": "1920x1080",  # 預設值  
                        "status": "ready"
                    }
                    
                    video_list.append(video_info)
        
        # 按上傳時間降序排列
        video_list.sort(key=lambda x: x['upload_time'], reverse=True)
        
        return {
            "videos": video_list,
            "total": len(video_list)
        }
        
    except Exception as e:
        api_logger.error(f"獲取影片列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取影片列表失敗: {str(e)}")


@router.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    """
    刪除影片檔案
    """
    try:
        videos_dir = "D:/project/system/yolo_backend/uploads/videos"
        video_path = os.path.join(videos_dir, video_id)
        
        # 檢查檔案是否存在
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="影片檔案不存在")
        
        # 檢查是否為檔案
        if not os.path.isfile(video_path):
            raise HTTPException(status_code=400, detail="指定的路徑不是檔案")
        
        # 檢查檔案副檔名是否為支援的影片格式
        supported_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        if not any(video_id.lower().endswith(ext) for ext in supported_extensions):
            raise HTTPException(status_code=400, detail="不是有效的影片檔案")
        
        # 刪除檔案
        os.remove(video_path)
        
        api_logger.info(f"成功刪除影片檔案: {video_id}")
        
        return {
            "success": True,
            "message": f"成功刪除影片: {video_id}",
            "deleted_file": video_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"刪除影片失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除影片失敗: {str(e)}")
