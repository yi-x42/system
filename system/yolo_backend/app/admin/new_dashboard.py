"""
YOLOv11 後台管理系統 - 新版本
整合新的資料庫架構，支援雙模式分析
"""

import os
import psutil
import json
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.new_database_service import DatabaseService
from app.models.database import AnalysisTask, DetectionResult, DataSource, SystemConfig

# 創建路由器
new_admin_router = APIRouter(prefix="/admin/v2", tags=["新版後台管理"])

# 設置模板目錄
templates = Jinja2Templates(directory="app/admin/templates")

# 創建資料庫服務實例
db_service = DatabaseService()

# ============================================================================
# 主要頁面路由
# ============================================================================

@new_admin_router.get("/", response_class=HTMLResponse)
@new_admin_router.get("/dashboard", response_class=HTMLResponse)
async def new_admin_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """新版後台管理主頁面"""
    try:
        # 獲取系統統計
        stats = await db_service.get_system_statistics(db)
        
        # 獲取系統資源使用情況
        system_info = get_system_resource_info()
        
        # 獲取最近的任務
        recent_tasks = await db_service.get_analysis_tasks(db, limit=10)
        
        # 獲取正在運行的任務
        running_tasks = await db_service.get_running_tasks(db)
        
        return templates.TemplateResponse("new_dashboard.html", {
            "request": request,
            "title": "YOLOv11 數位雙生分析系統 v2.0",
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stats": stats,
            "system_info": system_info,
            "recent_tasks": [task.to_dict() for task in recent_tasks],
            "running_tasks": [task.to_dict() for task in running_tasks],
            "running_count": len(running_tasks)
        })
        
    except Exception as e:
        # 如果出錯，顯示基本頁面
        return templates.TemplateResponse("new_dashboard.html", {
            "request": request,
            "title": "YOLOv11 數位雙生分析系統 v2.0",
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e),
            "stats": {
                "total_analyses": 0,
                "total_detections": 0,
                "total_events": 0,
                "active_cameras": 0
            },
            "system_info": {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "gpu_status": "N/A"
            },
            "recent_tasks": [],
            "running_tasks": [],
            "running_count": 0
        })

@new_admin_router.get("/tasks", response_class=HTMLResponse)
async def task_management(request: Request, db: AsyncSession = Depends(get_db)):
    """任務管理頁面"""
    try:
        # 獲取所有任務
        all_tasks = await db_service.get_analysis_tasks(db, limit=100)
        
        # 獲取資料來源列表
        data_sources = await db_service.get_data_sources(db)
        
        # 按狀態分類任務
        tasks_by_status = {}
        for task in all_tasks:
            status = task.status
            if status not in tasks_by_status:
                tasks_by_status[status] = []
            tasks_by_status[status].append(task.to_dict())
        
        return templates.TemplateResponse("task_management.html", {
            "request": request,
            "title": "任務管理",
            "tasks": [task.to_dict() for task in all_tasks],
            "tasks_by_status": tasks_by_status,
            "data_sources": [source.to_dict() for source in data_sources],
            "task_types": ["realtime_camera", "video_file"],
            "task_statuses": ["pending", "running", "completed", "failed"]
        })
        
    except Exception as e:
        return templates.TemplateResponse("task_management.html", {
            "request": request,
            "title": "任務管理",
            "tasks": [],
            "tasks_by_status": {},
            "data_sources": [],
            "task_types": ["realtime_camera", "video_file"],
            "task_statuses": ["pending", "running", "completed", "failed"],
            "error": str(e)
        })

@new_admin_router.get("/sources", response_class=HTMLResponse)
async def source_management(request: Request, db: AsyncSession = Depends(get_db)):
    """資料來源管理頁面"""
    try:
        # 獲取所有資料來源
        sources = await db_service.get_data_sources(db)
        
        # 按類型分類
        sources_by_type = {}
        for source in sources:
            source_type = source.source_type
            if source_type not in sources_by_type:
                sources_by_type[source_type] = []
            sources_by_type[source_type].append(source.to_dict())
        
        return templates.TemplateResponse("source_management.html", {
            "request": request,
            "title": "資料來源管理",
            "sources": [source.to_dict() for source in sources],
            "sources_by_type": sources_by_type,
            "source_types": ["camera", "video_file"],
            "source_statuses": ["active", "inactive", "error"]
        })
        
    except Exception as e:
        return templates.TemplateResponse("source_management.html", {
            "request": request,
            "title": "資料來源管理",
            "sources": [],
            "sources_by_type": {},
            "source_types": ["camera", "video_file"],
            "source_statuses": ["active", "inactive", "error"],
            "error": str(e)
        })

@new_admin_router.get("/yolo-config", response_class=HTMLResponse)
async def yolo_config_page(request: Request):
    """YOLO 模型配置頁面"""
    return templates.TemplateResponse("yolo_config.html", {
        "request": request,
        "title": "YOLO 模型配置"
    })

@new_admin_router.get("/camera-management", response_class=HTMLResponse)
async def camera_management_page(request: Request):
    """攝影機管理頁面"""
    return templates.TemplateResponse("camera_management.html", {
        "request": request,
        "title": "攝影機管理"
    })

@new_admin_router.get("/config", response_class=HTMLResponse)
async def system_config(request: Request, db: AsyncSession = Depends(get_db)):
    """系統配置頁面"""
    try:
        # 獲取所有配置
        configs = await db_service.get_all_configs(db)
        
        # 按類別分組配置
        grouped_configs = {}
        for config in configs:
            category = config.config_key.split('.')[0] if '.' in config.config_key else 'other'
            if category not in grouped_configs:
                grouped_configs[category] = []
            grouped_configs[category].append(config.to_dict())
        
        return templates.TemplateResponse("system_config.html", {
            "request": request,
            "title": "系統配置",
            "configs": [config.to_dict() for config in configs],
            "grouped_configs": grouped_configs,
            "categories": list(grouped_configs.keys())
        })
        
    except Exception as e:
        return templates.TemplateResponse("system_config.html", {
            "request": request,
            "title": "系統配置",
            "error": str(e),
            "grouped_configs": {},
            "categories": []
        })

@new_admin_router.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """分析統計頁面"""
    try:
        # 獲取系統統計
        system_stats = await db_service.get_system_statistics(db)
        
        # 獲取最近的任務進行詳細分析
        recent_tasks = await db_service.get_analysis_tasks(db, limit=50)
        
        # 計算分析統計
        analytics_data = {
            "total_tasks": len(recent_tasks),
            "completed_tasks": len([t for t in recent_tasks if t.status == 'completed']),
            "running_tasks": len([t for t in recent_tasks if t.status == 'running']),
            "failed_tasks": len([t for t in recent_tasks if t.status == 'failed']),
            "realtime_tasks": len([t for t in recent_tasks if t.task_type == 'realtime_camera']),
            "video_tasks": len([t for t in recent_tasks if t.task_type == 'video_file'])
        }
        
        return templates.TemplateResponse("analytics.html", {
            "request": request,
            "title": "分析統計",
            "system_stats": system_stats,
            "analytics_data": analytics_data,
            "recent_tasks": [task.to_dict() for task in recent_tasks[:10]]
        })
        
    except Exception as e:
        return templates.TemplateResponse("analytics.html", {
            "request": request,
            "title": "分析統計",
            "error": str(e),
            "system_stats": {},
            "analytics_data": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "running_tasks": 0,
                "failed_tasks": 0,
                "realtime_tasks": 0,
                "video_tasks": 0
            },
            "recent_tasks": []
        })

# ============================================================================
# API 端點（用於前端 AJAX 請求）
# ============================================================================

@new_admin_router.get("/api/system-status")
async def get_system_status():
    """獲取系統狀態 API"""
    try:
        system_info = get_system_resource_info()
        return {
            "success": True,
            "data": system_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@new_admin_router.get("/api/tasks/recent")
async def get_recent_tasks(db: AsyncSession = Depends(get_db)):
    """獲取最近任務 API"""
    try:
        tasks = await db_service.get_analysis_tasks(db, limit=20)
        return {
            "success": True,
            "data": [task.to_dict() for task in tasks],
            "count": len(tasks)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@new_admin_router.get("/api/statistics")
async def get_system_statistics_api(db: AsyncSession = Depends(get_db)):
    """獲取系統統計 API"""
    try:
        stats = await db_service.get_system_statistics(db)
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@new_admin_router.post("/api/tasks/{task_id}/stop")
async def stop_task_api(task_id: int, db: AsyncSession = Depends(get_db)):
    """停止任務 API"""
    try:
        success = await db_service.complete_analysis_task(db, task_id, 'completed')
        if success:
            return {
                "success": True,
                "message": "任務已停止",
                "task_id": task_id
            }
        else:
            return {
                "success": False,
                "error": "停止任務失敗"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@new_admin_router.post("/api/sources")
async def create_source_api(source_data: dict, db: AsyncSession = Depends(get_db)):
    """建立資料來源 API"""
    try:
        source = await db_service.create_data_source(db, source_data)
        return {
            "success": True,
            "data": source.to_dict(),
            "message": "資料來源建立成功"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@new_admin_router.post("/api/config/{key}")
async def update_config_api(key: str, config_data: dict, db: AsyncSession = Depends(get_db)):
    """更新配置 API"""
    try:
        value = config_data.get('value')
        description = config_data.get('description')
        
        success = await db_service.set_config(db, key, value, description)
        if success:
            return {
                "success": True,
                "message": "配置更新成功",
                "key": key,
                "value": value
            }
        else:
            return {
                "success": False,
                "error": "配置更新失敗"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ============================================================================
# 輔助函數
# ============================================================================

def get_system_resource_info() -> Dict[str, Any]:
    """獲取系統資源使用情況"""
    try:
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 記憶體使用情況
        memory = psutil.virtual_memory()
        
        # 磁碟使用情況
        disk = psutil.disk_usage('/')
        
        # 網絡狀態
        network = psutil.net_io_counters()
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100 if disk.total > 0 else 0
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "cpu": {"percent": 0},
            "memory": {"percent": 0},
            "disk": {"percent": 0}
        }


# ============================================================================
# YOLO 模型配置 API
# ============================================================================

@new_admin_router.get("/api/config/current")
async def get_current_config(db: AsyncSession = Depends(get_db)):
    """獲取當前 YOLO 模型配置"""
    try:
        # 定義默認配置
        default_config = {
            "model_path": "",
            "device": "auto",
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "max_det": 1000
        }
        
        # 嘗試從資料庫載入配置
        config_keys = [
            "yolo.model_path",
            "yolo.device", 
            "yolo.confidence_threshold",
            "yolo.iou_threshold",
            "yolo.max_det"
        ]
        
        current_config = default_config.copy()
        
        for key in config_keys:
            config_value = await db_service.get_config(db, key)
            if config_value:
                config_name = key.split('.')[1]  # 移除 "yolo." 前綴
                try:
                    # 嘗試轉換為適當的類型
                    if config_name in ["confidence_threshold", "iou_threshold"]:
                        current_config[config_name] = float(config_value)
                    elif config_name == "max_det":
                        current_config[config_name] = int(config_value)
                    else:
                        current_config[config_name] = config_value
                except (ValueError, TypeError):
                    # 如果轉換失敗，使用默認值
                    pass
        
        return JSONResponse({
            "success": True,
            "config": current_config
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@new_admin_router.post("/api/config/save")
async def save_config(request: Request, db: AsyncSession = Depends(get_db)):
    """保存 YOLO 模型配置"""
    try:
        data = await request.json()
        
        # 驗證配置參數
        required_fields = ["device", "confidence", "iou_threshold", "max_det"]
        for field in required_fields:
            if field not in data:
                return JSONResponse({
                    "success": False,
                    "error": f"缺少必要參數: {field}"
                }, status_code=400)
        
        # 驗證參數範圍
        if not (0.0 <= data["confidence"] <= 1.0):
            return JSONResponse({
                "success": False,
                "error": "信心度閾值必須在 0.0 到 1.0 之間"
            }, status_code=400)
            
        if not (0.0 <= data["iou_threshold"] <= 1.0):
            return JSONResponse({
                "success": False,
                "error": "IoU 閾值必須在 0.0 到 1.0 之間"
            }, status_code=400)
            
        if not (1 <= data["max_det"] <= 10000):
            return JSONResponse({
                "success": False,
                "error": "最大檢測數必須在 1 到 10000 之間"
            }, status_code=400)
        
        # 保存配置到資料庫
        config_mappings = {
            "yolo.model_path": data.get("model_path", ""),
            "yolo.device": data["device"],
            "yolo.confidence_threshold": str(data["confidence"]),
            "yolo.iou_threshold": str(data["iou_threshold"]),
            "yolo.max_det": str(data["max_det"])
        }
        
        for key, value in config_mappings.items():
            await db_service.set_config(db, key, value, f"YOLO 模型配置 - {key}")
        
        return JSONResponse({
            "success": True,
            "message": "配置已成功保存"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"保存配置失敗: {str(e)}"
        }, status_code=500)


@new_admin_router.get("/api/models")
async def get_available_models():
    """獲取可用的 YOLO 模型列表"""
    try:
        # 官方預訓練模型
        official_models = [
            {
                "name": "yolo11n.pt",
                "display_name": "YOLOv11 Nano",
                "size": "最小",
                "description": "超輕量級模型，適用於資源受限的環境",
                "official": True
            },
            {
                "name": "yolo11s.pt", 
                "display_name": "YOLOv11 Small",
                "size": "小型",
                "description": "小型模型，平衡速度與精確度",
                "official": True
            },
            {
                "name": "yolo11m.pt",
                "display_name": "YOLOv11 Medium", 
                "size": "中型",
                "description": "中型模型，良好的精確度與速度平衡",
                "official": True
            },
            {
                "name": "yolo11l.pt",
                "display_name": "YOLOv11 Large",
                "size": "大型", 
                "description": "大型模型，高精確度",
                "official": True
            },
            {
                "name": "yolo11x.pt",
                "display_name": "YOLOv11 Extra Large",
                "size": "超大型",
                "description": "最大模型，最高精確度",
                "official": True
            }
        ]
        
        # 檢查自定義模型目錄
        custom_models = []
        models_dir = Path("models")
        if models_dir.exists():
            for model_file in models_dir.glob("*.pt"):
                # 排除官方模型
                if model_file.name not in [m["name"] for m in official_models]:
                    custom_models.append({
                        "name": model_file.name,
                        "display_name": model_file.stem,
                        "size": "自定義",
                        "description": "用戶上傳的自定義模型",
                        "official": False,
                        "path": str(model_file)
                    })
        
        return JSONResponse({
            "success": True,
            "data": {
                "official_models": official_models,
                "custom_models": custom_models
            }
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"獲取模型列表失敗: {str(e)}"
        }, status_code=500)

# ============================================================================
# 攝影機管理 API 端點
# ============================================================================

@new_admin_router.get("/api/cameras/scan")
async def scan_cameras_v2():
    """掃描可用的攝影機設備"""
    try:
        import cv2
        cameras = []
        
        print("🔍 開始掃描攝影機設備...")
        
        # 掃描 0-10 個可能的攝影機索引
        for i in range(11):
            try:
                # 嘗試打開攝影機
                cap = cv2.VideoCapture(i)
                
                if cap.isOpened():
                    # 獲取攝影機資訊
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    backend_name = cap.getBackendName()
                    
                    # 嘗試讀取一幀來確認攝影機真的可用
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # 生成攝影機名稱
                        camera_name = f"攝影機 {i}"
                        if i == 0:
                            camera_name = "內建攝影機 (主要)"
                        elif i == 1:
                            camera_name = "外接攝影機 (次要)"
                        else:
                            camera_name = f"USB 攝影機 {i}"
                        
                        camera_info = {
                            "index": i,
                            "name": camera_name,
                            "width": width,
                            "height": height,
                            "fps": fps if fps > 0 else 30,
                            "backend_name": backend_name,
                            "status": "available",
                            "description": f"解析度: {width}x{height}, 幀率: {fps}fps",
                            "device_path": f"/dev/video{i}" if platform.system() == "Linux" else f"攝影機索引 {i}"
                        }
                        
                        cameras.append(camera_info)
                        print(f"   📹 找到: {camera_name} ({width}x{height}@{fps}fps)")
                
                cap.release()
                
            except Exception as e:
                # 忽略無法訪問的攝影機
                continue
        
        # 添加網路攝影機配置選項
        network_cameras = [
            {
                "index": "rtsp_1",
                "name": "網路攝影機 (RTSP)",
                "width": 1920,
                "height": 1080,
                "fps": 25,
                "backend_name": "RTSP",
                "status": "configurable",
                "description": "需要配置 RTSP 地址",
                "device_path": "rtsp://example.com/stream",
                "type": "network"
            },
            {
                "index": "http_1",
                "name": "HTTP 攝影機串流",
                "width": 1280,
                "height": 720,
                "fps": 30,
                "backend_name": "HTTP",
                "status": "configurable", 
                "description": "需要配置 HTTP 串流地址",
                "device_path": "http://example.com/stream.mjpg",
                "type": "network"
            }
        ]
        
        cameras.extend(network_cameras)
        
        print(f"🎯 掃描完成，找到 {len(cameras)} 個攝影機選項")
        
        return JSONResponse({
            "success": True,
            "data": {
                "cameras": cameras,
                "total": len(cameras),
                "scan_time": datetime.now().isoformat()
            }
        })
        
    except ImportError:
        return JSONResponse({
            "success": False,
            "error": "OpenCV 未安裝，無法掃描攝影機"
        }, status_code=500)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"掃描攝影機失敗: {str(e)}"
        }, status_code=500)

@new_admin_router.get("/api/cameras")
async def get_camera_configs_v2():
    """獲取攝影機配置列表"""
    try:
        from pathlib import Path
        import json
        
        configs_file = Path("camera_configs.json")
        
        if configs_file.exists():
            with open(configs_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
        else:
            configs = {}
        
        return JSONResponse({
            "success": True,
            "data": {
                "cameras": configs,
                "total": len(configs)
            }
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"獲取攝影機配置失敗: {str(e)}"
        }, status_code=500)

@new_admin_router.post("/api/cameras")
async def save_camera_config_v2(request: Request):
    """保存攝影機配置"""
    try:
        from pathlib import Path
        import json
        
        data = await request.json()
        camera_id = data.get("id")
        
        if not camera_id:
            return JSONResponse({
                "success": False,
                "error": "攝影機 ID 不能為空"
            }, status_code=400)
        
        configs_file = Path("camera_configs.json")
        
        # 載入現有配置
        if configs_file.exists():
            with open(configs_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
        else:
            configs = {}
        
        # 更新配置
        configs[camera_id] = {
            "name": data.get("name", f"攝影機 {camera_id}"),
            "index": data.get("index", camera_id),
            "resolution": data.get("resolution", "1280x720"),
            "fps": data.get("fps", 30),
            "enabled": data.get("enabled", True),
            "device_path": data.get("device_path", ""),
            "type": data.get("type", "usb"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # 保存配置
        with open(configs_file, 'w', encoding='utf-8') as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
        
        return JSONResponse({
            "success": True,
            "message": "攝影機配置已保存",
            "data": configs[camera_id]
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"保存攝影機配置失敗: {str(e)}"
        }, status_code=500)

@new_admin_router.delete("/api/cameras/{camera_id}")
async def delete_camera_config_v2(camera_id: str):
    """刪除攝影機配置"""
    try:
        from pathlib import Path
        import json
        
        configs_file = Path("camera_configs.json")
        
        if not configs_file.exists():
            return JSONResponse({
                "success": False,
                "error": "配置檔案不存在"
            }, status_code=404)
        
        with open(configs_file, 'r', encoding='utf-8') as f:
            configs = json.load(f)
        
        if camera_id not in configs:
            return JSONResponse({
                "success": False,
                "error": "攝影機配置不存在"
            }, status_code=404)
        
        # 刪除配置
        del configs[camera_id]
        
        # 保存更新後的配置
        with open(configs_file, 'w', encoding='utf-8') as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
        
        return JSONResponse({
            "success": True,
            "message": "攝影機配置已刪除"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"刪除攝影機配置失敗: {str(e)}"
        }, status_code=500)
