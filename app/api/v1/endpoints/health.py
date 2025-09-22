"""
YOLOv11 數位雙生分析系統 - 整合健康檢查 API 端點
"""

import time
import psutil
import platform
import torch
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.services.yolo_service import get_yolo_service
from app.core.logger import api_logger

router = APIRouter()

# 系統啟動時間
_start_time = time.time()


@router.get("/")
async def comprehensive_health_check():
    """
    整合健康檢查端點 - 提供完整系統資訊
    
    包含：
    - 基本狀態與運行時間
    - 系統資源使用情況 (CPU, 記憶體, 磁碟)
    - YOLOv11 模型狀態
    - 系統環境資訊
    - 服務狀態檢查
    """
    try:
        settings = get_settings()
        yolo_service = get_yolo_service()
        current_time = datetime.utcnow()
        uptime_seconds = time.time() - _start_time
        
        # === 基本資訊 ===
        basic_info = {
            "status": "healthy",
            "timestamp": current_time.isoformat(),
            "uptime_seconds": round(uptime_seconds, 2),
            "uptime_readable": format_uptime(uptime_seconds),
            "version": "1.0.0",
            "api_port": 8001
        }
        
        # === 系統資源 ===
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_resources = {
                "cpu_percent": cpu_percent,
                "cpu_count": psutil.cpu_count(),
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                    "free_percent": round(100 - memory.percent, 1)
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 1)
                }
            }
        except Exception as e:
            system_resources = {"error": f"無法獲取系統資源資訊: {str(e)}"}
        
        # === YOLO 模型狀態 ===
        try:
            model_loaded = yolo_service._model is not None
            model_info = {
                "loaded": model_loaded,
                "model_path": getattr(yolo_service, '_model_path', settings.model_path),
                "device": settings.device,
                "confidence_threshold": settings.confidence_threshold,
                "iou_threshold": settings.iou_threshold,
                "model_file_exists": Path(settings.model_path).exists()
            }
            
            # 如果模型已載入，添加更多詳細資訊
            if model_loaded:
                try:
                    model = yolo_service._model
                    model_info.update({
                        "model_type": str(type(model).__name__),
                        "task": getattr(model, 'task', 'detection'),
                        "input_size": getattr(model, 'imgsz', 'unknown'),
                        "class_count": len(getattr(model, 'names', {}))
                    })
                except Exception:
                    pass
                    
        except Exception as e:
            model_info = {"error": f"無法獲取模型資訊: {str(e)}"}
        
        # === 系統環境資訊 ===
        try:
            system_info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "processor": platform.processor()[:50],  # 限制長度
                "architecture": platform.architecture()[0],
                "hostname": platform.node(),
                "torch_version": torch.__version__ if 'torch' in globals() else "未安裝",
                "cuda_available": torch.cuda.is_available() if 'torch' in globals() else False
            }
            
            if 'torch' in globals() and torch.cuda.is_available():
                system_info["cuda_device_count"] = torch.cuda.device_count()
                system_info["cuda_current_device"] = torch.cuda.current_device()
                
        except Exception as e:
            system_info = {"error": f"無法獲取系統環境資訊: {str(e)}"}
        
        # === 應用程序狀態 ===
        try:
            current_process = psutil.Process()
            app_status = {
                "pid": current_process.pid,
                "memory_usage_mb": round(current_process.memory_info().rss / (1024*1024), 2),
                "cpu_percent": current_process.cpu_percent(),
                "threads": current_process.num_threads(),
                "started_at": datetime.fromtimestamp(current_process.create_time()).isoformat()
            }
        except Exception as e:
            app_status = {"error": f"無法獲取應用程序狀態: {str(e)}"}
        
        # === 服務檢查 ===
        services_status = {
            "yolo_service": "healthy" if model_loaded else "model_not_loaded",
            "api_server": "healthy",
            "logging": "healthy"
        }
        
        # 判斷整體健康狀態
        overall_status = "healthy"
        issues = []
        
        if not model_loaded:
            issues.append("YOLO模型未載入")
            
        if isinstance(system_resources, dict) and "error" in system_resources:
            issues.append("系統資源監控異常")
        else:
            if system_resources.get("cpu_percent", 0) > 90:
                issues.append("CPU使用率過高")
                overall_status = "warning"
                
            if system_resources.get("memory", {}).get("used_percent", 0) > 90:
                issues.append("記憶體使用率過高")  
                overall_status = "warning"
        
        if issues and overall_status == "healthy":
            overall_status = "warning"
        
        return {
            "status": overall_status,
            "issues": issues,
            "basic_info": basic_info,
            "system_resources": system_resources,
            "yolo_model": model_info,
            "system_environment": system_info,
            "application": app_status,
            "services": services_status
        }
        
    except Exception as e:
        api_logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "message": "健康檢查執行失敗"
        }


def format_uptime(seconds):
    """格式化運行時間為可讀格式"""
    try:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}天 {hours}小時 {minutes}分鐘"
        elif hours > 0:
            return f"{hours}小時 {minutes}分鐘"
        elif minutes > 0:
            return f"{minutes}分鐘 {secs}秒"
        else:
            return f"{secs}秒"
    except:
        return f"{seconds:.1f}秒"


@router.get("/videos")
async def get_videos_list():
    """
    獲取影片列表 - 讀取實際目錄內容
    """
    import os
    from datetime import datetime
    
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
                        "duration": "unknown",  
                        "resolution": "unknown",  
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
        return {"error": str(e), "videos": [], "total": 0}
