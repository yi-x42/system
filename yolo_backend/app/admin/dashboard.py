"""
YOLOv11 後台管理系統 - 主儀表板
包含系統監控、YOLO 配置、檔案管理等功能
"""

import os
import psutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# 創建路由器
admin_router = APIRouter(prefix="/admin", tags=["admin"])

# 設置模板目錄
templates = Jinja2Templates(directory="app/admin/templates")

@admin_router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """後台管理主頁面"""
    return templates.TemplateResponse("dashboard_fixed.html", {
        "request": request,
        "title": "YOLOv11 後台管理系統",
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@admin_router.get("/test", response_class=HTMLResponse)
async def admin_test(request: Request):
    """後台管理 API 測試頁面"""
    return templates.TemplateResponse("test.html", {
        "request": request,
        "title": "API 測試"
    })

@admin_router.get("/api/test")
async def test_api():
    """測試 API 端點"""
    return {"message": "後台管理 API 正常工作", "timestamp": datetime.now().isoformat()}

# 兼容性路由 - 處理舊版本的 API 請求
@admin_router.get("/api/system-status")
async def get_system_status_legacy():
    """舊版本系統狀態 API（兼容性）"""
    return await get_system_status()

@admin_router.get("/api/yolo-status")
async def get_yolo_status_legacy():
    """舊版本 YOLO 狀態 API（兼容性）"""
    return await get_yolo_config()

@admin_router.get("/api/service-status")
async def get_service_status_legacy():
    """舊版本服務狀態 API（兼容性）"""
    return {"status": "running", "message": "服務正常運行", "timestamp": datetime.now().isoformat()}

@admin_router.get("/api/recent-logs")
async def get_recent_logs_legacy(lines: int = 5):
    """舊版本日誌 API（兼容性）"""
    return await get_logs(lines=lines)

@admin_router.get("/api/system/status")
async def get_system_status():
    """獲取系統狀態資訊"""
    try:
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 記憶體使用情況
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = round(memory.used / (1024**3), 2)  # GB
        memory_total = round(memory.total / (1024**3), 2)  # GB
        
        # 磁碟使用情況
        disk = psutil.disk_usage('/')
        disk_percent = round((disk.used / disk.total) * 100, 2)
        disk_used = round(disk.used / (1024**3), 2)  # GB
        disk_total = round(disk.total / (1024**3), 2)  # GB
        
        # GPU 資訊（如果可用）
        gpu_info = get_gpu_info()
        
        # 網絡統計
        net_io = psutil.net_io_counters()
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "percent": memory_percent,
                "used": memory_used,
                "total": memory_total
            },
            "disk": {
                "percent": disk_percent,
                "used": disk_used,
                "total": disk_total
            },
            "gpu": gpu_info,
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取系統狀態失敗: {str(e)}")

def get_gpu_info():
    """獲取 GPU 資訊"""
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]  # 使用第一個 GPU
            return {
                "name": gpu.name,
                "memory_used": round(gpu.memoryUsed / 1024, 2),  # GB
                "memory_total": round(gpu.memoryTotal / 1024, 2),  # GB
                "memory_percent": round((gpu.memoryUsed / gpu.memoryTotal) * 100, 2),
                "temperature": gpu.temperature,
                "load": round(gpu.load * 100, 2)
            }
    except (ImportError, Exception):
        # GPUtil 未安裝或發生錯誤，返回預設值
        pass
    
    # 如果無法獲取 GPU 資訊，返回預設值
    return {
        "name": "未檢測到 GPU",
        "memory_used": 0,
        "memory_total": 0,
        "memory_percent": 0,
        "temperature": 0,
        "load": 0
    }

@admin_router.get("/api/yolo/config")
async def get_yolo_config():
    """獲取 YOLO 配置"""
    try:
        config_file = Path(".env")
        config = {}
        
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key] = value
        
        return {
            "model_path": config.get("MODEL_PATH", "yolo11n.pt"),
            "device": config.get("DEVICE", "auto"),
            "confidence_threshold": float(config.get("CONFIDENCE_THRESHOLD", "0.25")),
            "iou_threshold": float(config.get("IOU_THRESHOLD", "0.7")),
            "max_file_size": config.get("MAX_FILE_SIZE", "50MB"),
            "allowed_extensions": config.get("ALLOWED_EXTENSIONS", "jpg,jpeg,png,bmp,mp4,avi,mov,mkv").split(",")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取配置失敗: {str(e)}")

@admin_router.get("/api/yolo/models")
async def get_available_models():
    """獲取可用的 YOLO 模型列表"""
    try:
        models = []
        
        # 預定義的官方模型
        official_models = [
            {"name": "YOLOv11n", "file": "yolo11n.pt", "size": "~6MB", "description": "輕量級，適合快速檢測"},
            {"name": "YOLOv11s", "file": "yolo11s.pt", "size": "~22MB", "description": "小型模型，平衡速度和精度"},
            {"name": "YOLOv11m", "file": "yolo11m.pt", "size": "~50MB", "description": "中型模型，較好精度"},
            {"name": "YOLOv11l", "file": "yolo11l.pt", "size": "~87MB", "description": "大型模型，高精度"},
            {"name": "YOLOv11x", "file": "yolo11x.pt", "size": "~137MB", "description": "超大模型，最高精度"},
        ]
        
        # 檢查當前目錄中的模型檔案
        current_dir = Path(".")
        existing_models = []
        
        for model in official_models:
            model_path = current_dir / model["file"]
            if model_path.exists():
                file_size = model_path.stat().st_size / (1024 * 1024)  # MB
                existing_models.append({
                    **model,
                    "exists": True,
                    "actual_size": f"{file_size:.1f}MB",
                    "path": str(model_path)
                })
            else:
                existing_models.append({
                    **model,
                    "exists": False,
                    "actual_size": model["size"],
                    "path": model["file"]
                })
        
        # 搜尋其他 .pt 檔案
        custom_models = []
        for pt_file in current_dir.glob("*.pt"):
            if pt_file.name not in [m["file"] for m in official_models]:
                file_size = pt_file.stat().st_size / (1024 * 1024)
                custom_models.append({
                    "name": pt_file.stem,
                    "file": pt_file.name,
                    "size": f"{file_size:.1f}MB",
                    "description": "自定義模型",
                    "exists": True,
                    "actual_size": f"{file_size:.1f}MB",
                    "path": str(pt_file),
                    "custom": True
                })
        
        return {
            "official_models": existing_models,
            "custom_models": custom_models,
            "total_count": len(existing_models) + len(custom_models)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取模型列表失敗: {str(e)}")

@admin_router.post("/api/yolo/download-model")
async def download_model(model_file: str = Form(...)):
    """下載官方 YOLO 模型"""
    try:
        import subprocess
        import sys
        
        # 使用 ultralytics 下載模型
        cmd = [sys.executable, "-c", f"from ultralytics import YOLO; YOLO('{model_file}')"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            return {"success": True, "message": f"模型 {model_file} 下載成功"}
        else:
            return {"success": False, "message": f"下載失敗: {result.stderr}"}
            
    except Exception as e:
        return {"success": False, "message": f"下載過程發生錯誤: {str(e)}"}

@admin_router.post("/api/yolo/download/{model_name}")
async def download_model_by_name(model_name: str):
    """根據模型名稱下載官方 YOLO 模型 - 前端兼容端點"""
    try:
        import subprocess
        import sys
        
        # 使用 ultralytics 下載模型
        cmd = [sys.executable, "-c", f"from ultralytics import YOLO; YOLO('{model_name}')"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            return {"success": True, "message": f"模型 {model_name} 下載成功"}
        else:
            return {"success": False, "message": f"下載失敗: {result.stderr}"}
            
    except Exception as e:
        return {"success": False, "message": f"下載過程發生錯誤: {str(e)}"}

@admin_router.get("/api/yolo/config")
async def get_yolo_config():
    """獲取 YOLO 配置"""
    try:
        config_file = Path(".env")
        config = {}
        
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key] = value
        
        return {
            "model_path": config.get("MODEL_PATH", "yolo11n.pt"),
            "device": config.get("DEVICE", "auto"),
            "confidence_threshold": float(config.get("CONFIDENCE_THRESHOLD", "0.25")),
            "iou_threshold": float(config.get("IOU_THRESHOLD", "0.7")),
            "max_file_size": config.get("MAX_FILE_SIZE", "50MB"),
            "allowed_extensions": config.get("ALLOWED_EXTENSIONS", "jpg,jpeg,png,bmp,mp4,avi,mov,mkv").split(",")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取配置失敗: {str(e)}")

@admin_router.post("/api/yolo/config")
async def update_yolo_config(
    model_path: str = Form(...),
    device: str = Form(...),
    confidence_threshold: float = Form(...),
    iou_threshold: float = Form(...),
    max_file_size: str = Form(...),
    allowed_extensions: str = Form(...)
):
    """更新 YOLO 配置"""
    try:
        config_content = f"""# YOLOv11 數位雙生分析系統配置

# API 設定
HOST=0.0.0.0
PORT=8001
DEBUG=true

# YOLO 模型設定
MODEL_PATH={model_path}
DEVICE={device}
CONFIDENCE_THRESHOLD={confidence_threshold}
IOU_THRESHOLD={iou_threshold}

# 檔案上傳設定
MAX_FILE_SIZE={max_file_size}
ALLOWED_EXTENSIONS={allowed_extensions}

# 日誌設定
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 資料庫設定 (可選)
# DATABASE_URL=postgresql://user:password@localhost:5432/yolo_db
# REDIS_URL=redis://localhost:6379/0

# 安全設定
# SECRET_KEY=your-secret-key-here
# CORS_ORIGINS=["http://localhost:3000"]
"""
        
        with open(".env", "w", encoding="utf-8") as f:
            f.write(config_content)
        
        return {"message": "配置更新成功", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失敗: {str(e)}")

@admin_router.get("/api/logs/list")
async def get_logs(lines: int = 100):
    """獲取系統日誌"""
    try:
        log_file = Path("logs/app.log")
        if not log_file.exists():
            return {"logs": [], "message": "日誌檔案不存在"}
        
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
            "showing_lines": len(recent_lines)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取日誌失敗: {str(e)}")

@admin_router.get("/api/radmin/status")
async def get_radmin_status():
    """獲取 Radmin 網絡狀態"""
    try:
        # 檢查 Radmin IP 連接狀態
        import subprocess
        
        result = subprocess.run(
            ["ping", "-n", "1", "26.86.64.166"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        is_connected = result.returncode == 0
        
        # 獲取網絡介面資訊
        network_interfaces = []
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == 2:  # IPv4
                    network_interfaces.append({
                        "interface": interface,
                        "ip": addr.address,
                        "netmask": addr.netmask
                    })
        
        return {
            "radmin_connected": is_connected,
            "radmin_ip": "26.86.64.166",
            "network_interfaces": network_interfaces,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "radmin_connected": False,
            "radmin_ip": "26.86.64.166",
            "network_interfaces": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@admin_router.get("/api/network/status")
async def get_network_status():
    """獲取網絡狀態 - 前端兼容端點"""
    try:
        # 檢查 Radmin IP 連接狀態
        import subprocess
        
        result = subprocess.run(
            ["ping", "-n", "1", "26.86.64.166"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        is_connected = result.returncode == 0
        
        # 獲取網絡統計資訊
        net_io = psutil.net_io_counters()
        
        # 獲取網絡介面資訊
        network_interfaces = []
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == 2:  # IPv4
                    network_interfaces.append({
                        "interface": interface,
                        "ip": addr.address,
                        "netmask": addr.netmask
                    })
        
        return {
            "radmin_connected": is_connected,
            "radmin_ip": "26.86.64.166",
            "network_interfaces": network_interfaces,
            "net_io": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "radmin_connected": False,
            "radmin_ip": "26.86.64.166",
            "network_interfaces": [],
            "net_io": {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0
            },
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ===================== 檔案管理 API =====================

@admin_router.get("/api/files")
async def get_file_list(path: str = ""):
    """獲取檔案列表"""
    try:
        import os
        from pathlib import Path
        
        # 安全路徑處理 - 只允許在專案目錄內瀏覽
        base_path = Path(".").resolve()
        
        # 處理路徑參數
        if not path or path in [".", ""]:
            current_path = base_path
        else:
            current_path = (base_path / path).resolve()
            
        # 確保路徑在安全範圍內
        try:
            current_path.relative_to(base_path)
        except ValueError:
            raise HTTPException(status_code=403, detail="路徑存取被拒絕")
        
        if not current_path.exists():
            raise HTTPException(status_code=404, detail="路徑不存在")
        
        files = []
        directories = []
        
        # 添加上一級目錄（如果不是根目錄）
        if current_path != base_path:
            parent_path = current_path.parent
            relative_parent = parent_path.relative_to(base_path)
            directories.append({
                "name": "..",
                "path": str(relative_parent) if str(relative_parent) != "." else "",
                "type": "directory",
                "size": 0,
                "modified": "",
                "is_parent": True
            })
        
        # 遍歷目錄內容
        for item in sorted(current_path.iterdir()):
            try:
                if item.name.startswith('.'):
                    continue  # 跳過隱藏檔案
                    
                relative_path = item.relative_to(base_path)
                stat = item.stat()
                
                item_info = {
                    "name": item.name,
                    "path": str(relative_path),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "is_parent": False
                }
                
                if item.is_dir():
                    item_info["type"] = "directory"
                    directories.append(item_info)
                else:
                    item_info["type"] = "file"
                    item_info["extension"] = item.suffix.lower()
                    files.append(item_info)
                    
            except (OSError, ValueError):
                continue  # 跳過無法讀取的檔案
        
        return {
            "current_path": str(current_path.relative_to(base_path)) if current_path != base_path else "",
            "directories": directories,
            "files": files,
            "total_items": len(directories) + len(files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取檔案列表失敗: {str(e)}")

@admin_router.get("/api/files/download")
async def download_file(path: str):
    """下載檔案"""
    try:
        from fastapi.responses import FileResponse
        from pathlib import Path
        
        # 安全路徑處理
        base_path = Path(".").resolve()
        file_path = (base_path / path).resolve()
        
        # 確保檔案在安全範圍內
        file_path.relative_to(base_path)
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="檔案不存在")
        
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type='application/octet-stream'
        )
        
    except ValueError:
        raise HTTPException(status_code=403, detail="檔案存取被拒絕")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下載檔案失敗: {str(e)}")

@admin_router.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...), path: str = Form("")):
    """上傳檔案"""
    try:
        from pathlib import Path
        import shutil
        
        # 安全路徑處理
        base_path = Path(".").resolve()
        if path:
            upload_path = (base_path / path).resolve()
        else:
            upload_path = base_path / "uploads"
            
        # 確保路徑在安全範圍內
        upload_path.relative_to(base_path)
        
        # 確保目錄存在
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # 檔案路徑
        file_path = upload_path / file.filename
        
        # 檢查檔案大小（限制 100MB）
        max_size = 100 * 1024 * 1024  # 100MB
        if file.size and file.size > max_size:
            raise HTTPException(status_code=413, detail="檔案太大，最大限制 100MB")
        
        # 儲存檔案
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "success": True,
            "message": f"檔案 {file.filename} 上傳成功",
            "path": str(file_path.relative_to(base_path)),
            "size": file_path.stat().st_size
        }
        
    except ValueError:
        raise HTTPException(status_code=403, detail="路徑存取被拒絕")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上傳檔案失敗: {str(e)}")

@admin_router.delete("/api/files/delete")
async def delete_file(path: str):
    """刪除檔案或目錄"""
    try:
        from pathlib import Path
        import shutil
        
        # 安全路徑處理
        base_path = Path(".").resolve()
        target_path = (base_path / path).resolve()
        
        # 確保路徑在安全範圍內
        target_path.relative_to(base_path)
        
        # 防止刪除重要系統檔案
        protected_paths = ["app", "requirements.txt", "start.py", ".env"]
        relative_path = str(target_path.relative_to(base_path))
        
        if any(relative_path.startswith(p) for p in protected_paths):
            raise HTTPException(status_code=403, detail="無法刪除系統重要檔案")
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="檔案或目錄不存在")
        
        # 刪除檔案或目錄
        if target_path.is_file():
            target_path.unlink()
            message = f"檔案 {target_path.name} 已刪除"
        else:
            shutil.rmtree(target_path)
            message = f"目錄 {target_path.name} 已刪除"
        
        return {"success": True, "message": message}
        
    except ValueError:
        raise HTTPException(status_code=403, detail="路徑存取被拒絕")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除失敗: {str(e)}")

@admin_router.post("/api/files/create-folder")
async def create_folder(name: str = Form(...), path: str = Form("")):
    """建立新資料夾"""
    try:
        from pathlib import Path
        
        # 安全路徑處理
        base_path = Path(".").resolve()
        if path:
            parent_path = (base_path / path).resolve()
        else:
            parent_path = base_path
            
        # 確保路徑在安全範圍內
        parent_path.relative_to(base_path)
        
        # 新資料夾路徑
        new_folder = parent_path / name
        
        if new_folder.exists():
            raise HTTPException(status_code=409, detail="資料夾已存在")
        
        new_folder.mkdir(parents=True)
        
        return {
            "success": True,
            "message": f"資料夾 {name} 建立成功",
            "path": str(new_folder.relative_to(base_path))
        }
        
    except ValueError:
        raise HTTPException(status_code=403, detail="路徑存取被拒絕")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立資料夾失敗: {str(e)}")


# ==================== 攝影機管理 API ====================

import cv2
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

# 攝影機配置存儲
CAMERA_CONFIGS_FILE = Path("camera_configs.json")
active_cameras = {}

def load_camera_configs() -> Dict[str, Any]:
    """載入攝影機配置"""
    try:
        if CAMERA_CONFIGS_FILE.exists():
            with open(CAMERA_CONFIGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"載入攝影機配置失敗: {e}")
        return {}

def save_camera_configs(configs: Dict[str, Any]):
    """保存攝影機配置"""
    try:
        with open(CAMERA_CONFIGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存攝影機配置失敗: {e}")

@admin_router.get("/api/cameras/scan")
async def scan_cameras():
    """掃描可用的攝影機設備 - 改進版本"""
    try:
        cameras = []
        
        print("🔍 開始掃描攝影機設備...")
        
        # 擴展掃描範圍到 0-10，並使用不同的 DirectShow 後端
        for i in range(11):
            try:
                print(f"   檢查攝影機索引 {i}...")
                
                # 嘗試不同的後端
                backends_to_try = [
                    cv2.CAP_DSHOW,  # DirectShow (Windows 推薦)
                    cv2.CAP_MSMF,   # Microsoft Media Foundation
                    cv2.CAP_ANY     # 任何可用的後端
                ]
                
                cap = None
                backend_used = None
                
                for backend in backends_to_try:
                    try:
                        cap = cv2.VideoCapture(i, backend)
                        if cap.isOpened():
                            # 設置較低的超時時間
                            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                            
                            # 嘗試讀取一幀來確認攝影機可用
                            ret, frame = cap.read()
                            if ret and frame is not None:
                                backend_used = backend
                                print(f"   ✅ 攝影機 {i} 可用 (後端: {backend})")
                                break
                            else:
                                cap.release()
                                cap = None
                        else:
                            if cap is not None:
                                cap.release()
                            cap = None
                    except Exception as e:
                        if cap is not None:
                            cap.release()
                        cap = None
                        continue
                
                if cap is not None and cap.isOpened():
                    try:
                        # 獲取攝影機屬性
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = int(cap.get(cv2.CAP_PROP_FPS))
                        
                        # 如果無法獲取正確的 FPS，設置默認值
                        if fps <= 0:
                            fps = 30
                        
                        # 如果無法獲取正確的解析度，設置默認值
                        if width <= 0 or height <= 0:
                            width, height = 640, 480
                        
                        # 檢測攝影機類型
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
                            "type": "usb",
                            "width": width,
                            "height": height,
                            "fps": fps,
                            "available": True,
                            "backend": backend_used,
                            "backend_name": {
                                cv2.CAP_DSHOW: "DirectShow",
                                cv2.CAP_MSMF: "Media Foundation",
                                cv2.CAP_ANY: "Default"
                            }.get(backend_used, "Unknown")
                        }
                        
                        cameras.append(camera_info)
                        print(f"   📹 找到: {camera_name} ({width}x{height}@{fps}fps)")
                        
                    except Exception as e:
                        print(f"   ⚠️ 攝影機 {i} 屬性讀取失敗: {e}")
                    finally:
                        cap.release()
                
            except Exception as e:
                print(f"   ❌ 攝影機 {i} 檢查失敗: {e}")
                continue
        
        # 額外嘗試：使用 DirectShow 列舉設備
        try:
            print("🔍 使用 DirectShow 額外掃描...")
            import subprocess
            import re
            
            # 嘗試使用 ffmpeg 列舉設備（如果可用）
            try:
                result = subprocess.run(['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'], 
                                      capture_output=True, text=True, timeout=10)
                if 'video=' in result.stderr:
                    print("   💡 找到額外的 DirectShow 設備信息")
            except:
                pass
                
        except Exception as e:
            print(f"   ⚠️ DirectShow 掃描失敗: {e}")
        
        print(f"🎯 掃描完成，找到 {len(cameras)} 個可用攝影機")
        
        return {
            "success": True,
            "cameras": cameras,
            "total": len(cameras),
            "message": f"找到 {len(cameras)} 個可用攝影機" + (
                "\n💡 提示：如果沒有找到內建攝影機，請檢查:\n" +
                "1. 攝影機是否被其他程序占用\n" +
                "2. 攝影機驅動是否正常\n" +
                "3. 攝影機隱私設定是否允許應用程式訪問"
                if len(cameras) == 0 else ""
            )
        }
        
    except Exception as e:
        print(f"❌ 掃描攝影機失敗: {e}")
        raise HTTPException(status_code=500, detail=f"掃描攝影機失敗: {str(e)}")

@admin_router.get("/api/cameras")
async def get_cameras():
    """獲取攝影機列表"""
    try:
        configs = load_camera_configs()
        cameras = []
        
        for camera_id, config in configs.items():
            # 檢查攝影機狀態
            status = "inactive"
            if camera_id in active_cameras:
                status = "active"
            
            camera_info = {
                "id": camera_id,
                "name": config.get("name", "未命名攝影機"),
                "type": config.get("type", "unknown"),
                "source": config.get("source", ""),
                "width": config.get("width", 640),
                "height": config.get("height", 480),
                "fps": config.get("fps", 30),
                "auto_start": config.get("auto_start", False),
                "status": status,
                "created_at": config.get("created_at", ""),
                "last_used": config.get("last_used", "")
            }
            
            # 添加認證資訊（如果有）
            if config.get("username"):
                camera_info["username"] = config.get("username")
            if config.get("password"):
                camera_info["password"] = "***"  # 隱藏密碼
                
            cameras.append(camera_info)
        
        return {
            "success": True,
            "cameras": cameras,
            "total": len(cameras)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取攝影機列表失敗: {str(e)}")

@admin_router.post("/api/cameras")
async def create_camera(camera_data: dict):
    """新增攝影機配置"""
    try:
        # 生成唯一 ID
        camera_id = str(uuid.uuid4())
        
        # 驗證必要欄位
        required_fields = ["name", "type", "source"]
        for field in required_fields:
            if field not in camera_data:
                raise HTTPException(status_code=400, detail=f"缺少必要欄位: {field}")
        
        # 載入現有配置
        configs = load_camera_configs()
        
        # 建立攝影機配置
        config = {
            "name": camera_data["name"],
            "type": camera_data["type"],
            "source": camera_data["source"],
            "width": camera_data.get("width", 640),
            "height": camera_data.get("height", 480),
            "fps": camera_data.get("fps", 30),
            "auto_start": camera_data.get("auto_start", False),
            "created_at": datetime.now().isoformat(),
            "last_used": ""
        }
        
        # 添加認證資訊（如果有）
        if camera_data.get("username"):
            config["username"] = camera_data["username"]
        if camera_data.get("password"):
            config["password"] = camera_data["password"]
        
        # 保存配置
        configs[camera_id] = config
        save_camera_configs(configs)
        
        return {
            "success": True,
            "camera_id": camera_id,
            "message": f"攝影機 '{camera_data['name']}' 配置已保存"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"新增攝影機失敗: {str(e)}")

@admin_router.post("/api/cameras/test")
async def test_camera(camera_data: dict):
    """測試攝影機連接 - 改進版本"""
    try:
        camera_type = camera_data.get("type")
        source = camera_data.get("source")
        
        print(f"🧪 測試攝影機連接: {camera_type} - {source}")
        
        if camera_type == "usb":
            # 測試 USB 攝影機 - 使用多種後端
            camera_index = int(source)
            
            backends_to_try = [
                (cv2.CAP_DSHOW, "DirectShow"),
                (cv2.CAP_MSMF, "Media Foundation"),
                (cv2.CAP_ANY, "Default")
            ]
            
            cap = None
            backend_used = None
            
            for backend, backend_name in backends_to_try:
                try:
                    print(f"   嘗試後端: {backend_name}")
                    cap = cv2.VideoCapture(camera_index, backend)
                    
                    if cap.isOpened():
                        # 設置緩衝區大小
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        # 嘗試讀取一幀
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            backend_used = backend_name
                            print(f"   ✅ 成功使用 {backend_name}")
                            break
                        else:
                            cap.release()
                            cap = None
                    else:
                        if cap is not None:
                            cap.release()
                        cap = None
                        
                except Exception as e:
                    print(f"   ❌ {backend_name} 失敗: {e}")
                    if cap is not None:
                        cap.release()
                    cap = None
                    continue
            
            if cap is None:
                return {
                    "success": False,
                    "message": f"無法連接到 USB 攝影機 {camera_index}。請檢查:\n" +
                             "1. 攝影機是否被其他程序占用\n" +
                             "2. 攝影機驅動是否正常\n" +
                             "3. Windows 攝影機隱私設定"
                }
            
        elif camera_type in ["rtsp", "ip"]:
            # 測試網絡攝影機
            username = camera_data.get("username", "")
            password = camera_data.get("password", "")
            
            if username and password:
                # 構建帶認證的 URL
                if "://" in source:
                    protocol, url_part = source.split("://", 1)
                    source = f"{protocol}://{username}:{password}@{url_part}"
            
            cap = cv2.VideoCapture(source)
            backend_used = "Network Stream"
            
        elif camera_type == "file":
            # 測試影片檔案
            if not Path(source).exists():
                return {
                    "success": False,
                    "message": f"影片檔案不存在: {source}"
                }
            cap = cv2.VideoCapture(source)
            backend_used = "File Stream"
            
        else:
            return {
                "success": False,
                "message": f"不支援的攝影機類型: {camera_type}"
            }
        
        # 測試是否能打開
        if not cap.isOpened():
            cap.release()
            return {
                "success": False,
                "message": "無法連接到攝影機，請檢查設備狀態"
            }
        
        # 嘗試讀取一幀
        ret, frame = cap.read()
        
        if not ret or frame is None:
            cap.release()
            return {
                "success": False,
                "message": "攝影機已連接但無法讀取畫面，可能是格式不支援或設備故障"
            }
        
        # 獲取攝影機資訊
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        cap.release()
        
        return {
            "success": True,
            "message": f"攝影機連接測試成功！\n後端: {backend_used}\n解析度: {width}x{height}\n幀率: {fps}fps",
            "details": {
                "backend": backend_used,
                "frame_size": [width, height],
                "fps": fps if fps > 0 else "Unknown"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 攝影機連接測試失敗: {e}")
        return {
            "success": False,
            "message": f"連接測試失敗: {str(e)}\n\n💡 常見解決方案:\n" +
                      "1. 確保攝影機未被其他程序使用\n" +
                      "2. 檢查 Windows 隱私設定 → 攝影機\n" +
                      "3. 更新攝影機驅動程序\n" +
                      "4. 重新插拔 USB 攝影機"
        }

@admin_router.post("/api/cameras/{camera_id}/start")
async def start_camera(camera_id: str):
    """啟動攝影機 - 改進版本"""
    try:
        configs = load_camera_configs()
        
        if camera_id not in configs:
            raise HTTPException(status_code=404, detail="攝影機配置不存在")
        
        config = configs[camera_id]
        
        print(f"🚀 啟動攝影機: {config['name']} ({config['type']})")
        
        # 如果攝影機已經啟動，先停止
        if camera_id in active_cameras:
            active_cameras[camera_id].release()
            del active_cameras[camera_id]
        
        cap = None
        backend_used = None
        
        # 根據類型建立攝影機連接
        if config["type"] == "usb":
            # USB 攝影機 - 使用多後端嘗試
            camera_index = int(config["source"])
            
            backends_to_try = [
                (cv2.CAP_DSHOW, "DirectShow"),
                (cv2.CAP_MSMF, "Media Foundation"),
                (cv2.CAP_ANY, "Default")
            ]
            
            for backend, backend_name in backends_to_try:
                try:
                    print(f"   嘗試後端: {backend_name}")
                    cap = cv2.VideoCapture(camera_index, backend)
                    
                    if cap.isOpened():
                        # 設置緩衝區大小
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        # 嘗試讀取一幀來驗證
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            backend_used = backend_name
                            print(f"   ✅ 成功使用 {backend_name}")
                            break
                        else:
                            cap.release()
                            cap = None
                    else:
                        if cap is not None:
                            cap.release()
                        cap = None
                        
                except Exception as e:
                    print(f"   ❌ {backend_name} 失敗: {e}")
                    if cap is not None:
                        cap.release()
                    cap = None
                    continue
                    
        elif config["type"] in ["rtsp", "ip"]:
            source = config["source"]
            if config.get("username") and config.get("password"):
                # 構建帶認證的 URL
                username = config["username"]
                password = config["password"]
                if "://" in source:
                    protocol, url_part = source.split("://", 1)
                    source = f"{protocol}://{username}:{password}@{url_part}"
            cap = cv2.VideoCapture(source)
            backend_used = "Network Stream"
            
        elif config["type"] == "file":
            cap = cv2.VideoCapture(config["source"])
            backend_used = "File Stream"
            
        else:
            raise HTTPException(status_code=400, detail="不支援的攝影機類型")
        
        if cap is None or not cap.isOpened():
            error_msg = f"無法啟動攝影機 '{config['name']}'"
            if config["type"] == "usb":
                error_msg += "\n\n💡 解決建議:\n" + \
                           "1. 確保攝影機未被其他程序占用\n" + \
                           "2. 檢查 Windows 隱私設定 → 攝影機\n" + \
                           "3. 嘗試重新插拔 USB 攝影機\n" + \
                           "4. 更新攝影機驅動程序"
            raise HTTPException(status_code=500, detail=error_msg)
        
        # 設定攝影機參數
        try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.get("width", 640))
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.get("height", 480))
            cap.set(cv2.CAP_PROP_FPS, config.get("fps", 30))
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 減少延遲
        except Exception as e:
            print(f"   ⚠️ 設定攝影機參數時出現警告: {e}")
        
        # 儲存到活動攝影機列表
        active_cameras[camera_id] = cap
        
        # 更新最後使用時間
        config["last_used"] = datetime.now().isoformat()
        configs[camera_id] = config
        save_camera_configs(configs)
        
        print(f"   ✅ 攝影機 '{config['name']}' 啟動成功")
        
        return {
            "success": True,
            "message": f"攝影機 '{config['name']}' 已啟動\n使用後端: {backend_used}",
            "backend": backend_used
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 啟動攝影機失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動攝影機失敗: {str(e)}")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.get("width", 640))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.get("height", 480))
        cap.set(cv2.CAP_PROP_FPS, config.get("fps", 30))
        
        # 儲存到活動攝影機列表
        active_cameras[camera_id] = cap
        
        # 更新最後使用時間
        config["last_used"] = datetime.now().isoformat()
        configs[camera_id] = config
        save_camera_configs(configs)
        
        return {
            "success": True,
            "message": f"攝影機 '{config['name']}' 已啟動"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"啟動攝影機失敗: {str(e)}")

@admin_router.post("/api/cameras/{camera_id}/stop")
async def stop_camera(camera_id: str):
    """停止攝影機"""
    try:
        if camera_id not in active_cameras:
            raise HTTPException(status_code=404, detail="攝影機未啟動")
        
        # 釋放攝影機資源
        active_cameras[camera_id].release()
        del active_cameras[camera_id]
        
        return {
            "success": True,
            "message": "攝影機已停止"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止攝影機失敗: {str(e)}")

@admin_router.get("/api/cameras/{camera_id}/frame")
async def get_camera_frame(camera_id: str):
    """獲取攝影機當前畫面"""
    try:
        if camera_id not in active_cameras:
            raise HTTPException(status_code=404, detail="攝影機未啟動")
        
        cap = active_cameras[camera_id]
        ret, frame = cap.read()
        
        if not ret:
            raise HTTPException(status_code=500, detail="無法讀取攝影機畫面")
        
        # 將畫面編碼為 JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        
        from fastapi.responses import Response
        return Response(content=buffer.tobytes(), media_type="image/jpeg")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取畫面失敗: {str(e)}")

@admin_router.post("/api/cameras/{camera_id}/capture")
async def capture_frame(camera_id: str):
    """截圖保存"""
    try:
        if camera_id not in active_cameras:
            raise HTTPException(status_code=404, detail="攝影機未啟動")
        
        cap = active_cameras[camera_id]
        ret, frame = cap.read()
        
        if not ret:
            raise HTTPException(status_code=500, detail="無法讀取攝影機畫面")
        
        # 建立截圖目錄
        capture_dir = Path("captures")
        capture_dir.mkdir(exist_ok=True)
        
        # 生成檔案名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{camera_id[:8]}_{timestamp}.jpg"
        filepath = capture_dir / filename
        
        # 保存截圖
        cv2.imwrite(str(filepath), frame)
        
        return {
            "success": True,
            "filename": filename,
            "filepath": str(filepath),
            "message": "截圖已保存"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"截圖失敗: {str(e)}")

@admin_router.delete("/api/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    """刪除攝影機配置"""
    try:
        configs = load_camera_configs()
        
        if camera_id not in configs:
            raise HTTPException(status_code=404, detail="攝影機配置不存在")
        
        # 如果攝影機正在運行，先停止
        if camera_id in active_cameras:
            active_cameras[camera_id].release()
            del active_cameras[camera_id]
        
        # 刪除配置
        camera_name = configs[camera_id]["name"]
        del configs[camera_id]
        save_camera_configs(configs)
        
        return {
            "success": True,
            "message": f"攝影機 '{camera_name}' 配置已刪除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除攝影機失敗: {str(e)}")

# ==================== 攝影機管理 API ====================

import cv2
import uuid
from pydantic import BaseModel
from typing import Optional
import threading
import time

# 攝影機配置模型
class CameraConfig(BaseModel):
    name: str
    type: str  # usb, rtsp, ip, file
    source: str  # 設備索引、URL 或檔案路徑
    width: int = 640
    height: int = 480
    fps: int = 30
    username: Optional[str] = None
    password: Optional[str] = None
    auto_start: bool = False

# 全域攝影機管理
camera_manager = {}
camera_configs = {}

class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.active_cameras = {}
        
    def get_camera_source(self, config: CameraConfig):
        """根據配置獲取攝影機來源"""
        if config.type == 'usb':
            return int(config.source)
        elif config.type in ['rtsp', 'ip']:
            if config.username and config.password:
                # 構建帶認證的 RTSP URL
                url_parts = config.source.split('://')
                if len(url_parts) == 2:
                    protocol, rest = url_parts
                    return f"{protocol}://{config.username}:{config.password}@{rest}"
            return config.source
        elif config.type == 'file':
            return config.source
        else:
            raise ValueError(f"不支持的攝影機類型: {config.type}")
    
    def test_camera(self, config: CameraConfig):
        """測試攝影機連接"""
        try:
            source = self.get_camera_source(config)
            cap = cv2.VideoCapture(source)
            
            if not cap.isOpened():
                return False, "無法開啟攝影機"
            
            # 設置解析度
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)
            cap.set(cv2.CAP_PROP_FPS, config.fps)
            
            # 讀取一幀來測試
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                return True, "攝影機連接成功"
            else:
                return False, "無法讀取攝影機畫面"
                
        except Exception as e:
            return False, f"測試失敗: {str(e)}"
    
    def start_camera(self, camera_id: str, config: CameraConfig):
        """啟動攝影機"""
        try:
            if camera_id in self.active_cameras:
                return False, "攝影機已在運行"
            
            source = self.get_camera_source(config)
            cap = cv2.VideoCapture(source)
            
            if not cap.isOpened():
                return False, "無法開啟攝影機"
            
            # 設置參數
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)
            cap.set(cv2.CAP_PROP_FPS, config.fps)
            
            self.active_cameras[camera_id] = {
                'capture': cap,
                'config': config,
                'last_frame': None,
                'running': True
            }
            
            return True, "攝影機已啟動"
            
        except Exception as e:
            return False, f"啟動失敗: {str(e)}"
    
    def stop_camera(self, camera_id: str):
        """停止攝影機"""
        if camera_id in self.active_cameras:
            camera_info = self.active_cameras[camera_id]
            camera_info['running'] = False
            camera_info['capture'].release()
            del self.active_cameras[camera_id]
            return True, "攝影機已停止"
        return False, "攝影機未在運行"
    
    def get_frame(self, camera_id: str):
        """獲取攝影機畫面"""
        if camera_id not in self.active_cameras:
            return None, "攝影機未啟動"
        
        camera_info = self.active_cameras[camera_id]
        cap = camera_info['capture']
        
        ret, frame = cap.read()
        if ret:
            camera_info['last_frame'] = frame
            return frame, "成功"
        else:
            return None, "無法讀取畫面"
    
    def capture_frame(self, camera_id: str, save_path: str = "captures"):
        """截圖保存"""
        frame, message = self.get_frame(camera_id)
        if frame is not None:
            os.makedirs(save_path, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{camera_id}_{timestamp}.jpg"
            filepath = os.path.join(save_path, filename)
            cv2.imwrite(filepath, frame)
            return True, filename
        return False, message

# 創建全域攝影機管理器
camera_mgr = CameraManager()

@admin_router.get("/api/cameras/scan")
async def scan_cameras():
    """掃描可用的攝影機設備"""
    try:
        available_cameras = []
        
        # 掃描 USB 攝影機（索引 0-5）
        for i in range(6):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    available_cameras.append({
                        "index": i,
                        "name": f"USB 攝影機 {i}",
                        "type": "usb"
                    })
                cap.release()
        
        return {
            "success": True,
            "cameras": available_cameras,
            "count": len(available_cameras)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"掃描攝影機失敗: {str(e)}")

@admin_router.get("/api/cameras")
async def get_cameras():
    """獲取所有攝影機配置"""
    cameras = []
    for camera_id, config in camera_configs.items():
        status = "active" if camera_id in camera_mgr.active_cameras else "inactive"
        cameras.append({
            "id": camera_id,
            "name": config.name,
            "type": config.type,
            "source": config.source,
            "width": config.width,
            "height": config.height,
            "fps": config.fps,
            "auto_start": config.auto_start,
            "status": status
        })
    
    return {"cameras": cameras}

@admin_router.post("/api/cameras")
async def add_camera(config: CameraConfig):
    """新增攝影機配置"""
    try:
        camera_id = str(uuid.uuid4())
        camera_configs[camera_id] = config
        
        return {
            "success": True,
            "camera_id": camera_id,
            "message": f"攝影機 {config.name} 配置已保存"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存攝影機配置失敗: {str(e)}")

@admin_router.post("/api/cameras/test")
async def test_camera_connection(config: CameraConfig):
    """測試攝影機連接"""
    try:
        success, message = camera_mgr.test_camera(config)
        return {
            "success": success,
            "message": message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"測試攝影機失敗: {str(e)}")

@admin_router.post("/api/cameras/{camera_id}/start")
async def start_camera(camera_id: str):
    """啟動攝影機"""
    try:
        if camera_id not in camera_configs:
            raise HTTPException(status_code=404, detail="攝影機配置不存在")
        
        config = camera_configs[camera_id]
        success, message = camera_mgr.start_camera(camera_id, config)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"啟動攝影機失敗: {str(e)}")

@admin_router.post("/api/cameras/{camera_id}/stop")
async def stop_camera(camera_id: str):
    """停止攝影機"""
    try:
        success, message = camera_mgr.stop_camera(camera_id)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止攝影機失敗: {str(e)}")

from fastapi.responses import StreamingResponse
import io

@admin_router.get("/api/cameras/{camera_id}/frame")
async def get_camera_frame(camera_id: str):
    """獲取攝影機當前畫面"""
    try:
        frame, message = camera_mgr.get_frame(camera_id)
        
        if frame is not None:
            # 將畫面編碼為 JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                return StreamingResponse(
                    io.BytesIO(buffer.tobytes()),
                    media_type="image/jpeg"
                )
            else:
                raise HTTPException(status_code=500, detail="畫面編碼失敗")
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取畫面失敗: {str(e)}")

@admin_router.post("/api/cameras/{camera_id}/capture")
async def capture_camera_frame(camera_id: str):
    """截圖並保存"""
    try:
        success, filename = camera_mgr.capture_frame(camera_id)
        
        if success:
            return {
                "success": True,
                "filename": filename,
                "message": "截圖已保存"
            }
        else:
            raise HTTPException(status_code=400, detail=filename)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"截圖失敗: {str(e)}")

@admin_router.delete("/api/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    """刪除攝影機配置"""
    try:
        if camera_id not in camera_configs:
            raise HTTPException(status_code=404, detail="攝影機配置不存在")
        
        # 如果攝影機正在運行，先停止它
        if camera_id in camera_mgr.active_cameras:
            camera_mgr.stop_camera(camera_id)
        
        # 刪除配置
        del camera_configs[camera_id]
        
        return {
            "success": True,
            "message": "攝影機配置已刪除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除攝影機配置失敗: {str(e)}")

@admin_router.get("/api/cameras/{camera_id}")
async def get_camera_info(camera_id: str):
    """獲取特定攝影機資訊"""
    try:
        if camera_id not in camera_configs:
            raise HTTPException(status_code=404, detail="攝影機配置不存在")
        
        config = camera_configs[camera_id]
        status = "active" if camera_id in camera_mgr.active_cameras else "inactive"
        
        return {
            "id": camera_id,
            "name": config.name,
            "type": config.type,
            "source": config.source,
            "width": config.width,
            "height": config.height,
            "fps": config.fps,
            "auto_start": config.auto_start,
            "status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取攝影機資訊失敗: {str(e)}")


# =============================================================================
# 資料庫管理 API
# =============================================================================

@admin_router.get("/api/database/stats")
async def get_database_stats():
    """獲取資料庫統計資訊"""
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.analysis import AnalysisRecord, DetectionResult, BehaviorEvent
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # 獲取各表的記錄數量
            analysis_count = await session.execute(
                text("SELECT COUNT(*) FROM analysis_records")
            )
            detection_count = await session.execute(
                text("SELECT COUNT(*) FROM detection_results")
            )
            behavior_count = await session.execute(
                text("SELECT COUNT(*) FROM behavior_events")
            )
            
            # 獲取資料庫大小（PostgreSQL）
            try:
                db_size = await session.execute(
                    text("SELECT pg_size_pretty(pg_database_size(current_database()))")
                )
                database_size = db_size.scalar()
            except:
                database_size = "N/A"
            
            return {
                "analysis_records": analysis_count.scalar(),
                "detection_results": detection_count.scalar(),
                "behavior_events": behavior_count.scalar(),
                "database_size": database_size,
                "last_updated": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取資料庫統計失敗: {str(e)}")


@admin_router.get("/api/database/query/{table_name}")
async def query_table_data(
    table_name: str,
    limit: int = 25,
    offset: int = 0,
    order_by: str = "created_at",
    order_direction: str = "DESC",
    search: str = None
):
    """查詢指定資料表的資料"""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        
        # 驗證表名
        allowed_tables = ["analysis_records", "detection_results", "behavior_events"]
        if table_name not in allowed_tables:
            raise HTTPException(status_code=400, detail="不支援的資料表")
        
        # 驗證排序欄位
        allowed_columns = {
            "analysis_records": ["id", "created_at", "updated_at", "video_name", "status"],
            "detection_results": ["id", "created_at", "timestamp", "object_type", "confidence"],
            "behavior_events": ["id", "created_at", "event_type", "object_id"]
        }
        
        if order_by not in allowed_columns.get(table_name, []):
            order_by = "created_at"
        
        # 驗證排序方向
        if order_direction.upper() not in ["ASC", "DESC"]:
            order_direction = "DESC"
        
        async with AsyncSessionLocal() as session:
            # 構建基本查詢
            base_query = f"SELECT * FROM {table_name}"
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            
            # 添加搜尋條件
            where_conditions = []
            if search:
                if table_name == "analysis_records":
                    where_conditions.append(f"(video_name ILIKE '%{search}%' OR status ILIKE '%{search}%')")
                elif table_name == "detection_results":
                    where_conditions.append(f"(object_type ILIKE '%{search}%' OR object_chinese ILIKE '%{search}%')")
                elif table_name == "behavior_events":
                    where_conditions.append(f"(event_type ILIKE '%{search}%' OR description ILIKE '%{search}%')")
            
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                base_query += where_clause
                count_query += where_clause
            
            # 添加排序和分頁
            query = f"{base_query} ORDER BY {order_by} {order_direction} LIMIT {limit} OFFSET {offset}"
            
            # 執行查詢
            result = await session.execute(text(query))
            rows = result.fetchall()
            
            # 獲取總數
            total_result = await session.execute(text(count_query))
            total_count = total_result.scalar()
            
            # 轉換為字典格式
            columns = result.keys()
            data = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # 處理特殊類型
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    elif value is None:
                        value = ""
                    row_dict[column] = value
                data.append(row_dict)
            
            return {
                "data": data,
                "total_count": total_count,
                "page_size": limit,
                "current_page": offset // limit + 1,
                "columns": list(columns),
                "table_name": table_name,
                "search": search,
                "order_by": order_by,
                "order_direction": order_direction
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢資料表失敗: {str(e)}")


@admin_router.post("/api/database/export/{table_name}")
async def export_table_data(table_name: str, limit: int = 1000):
    """匯出資料表資料為 CSV"""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        import csv
        import io
        from fastapi.responses import StreamingResponse
        
        # 驗證表名
        allowed_tables = ["analysis_records", "detection_results", "behavior_events"]
        if table_name not in allowed_tables:
            raise HTTPException(status_code=400, detail="不支援的資料表")
        
        async with AsyncSessionLocal() as session:
            # 查詢資料
            query = f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT {limit}"
            result = await session.execute(text(query))
            rows = result.fetchall()
            columns = result.keys()
            
            # 創建 CSV 內容
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 寫入標題行
            writer.writerow(columns)
            
            # 寫入資料行
            for row in rows:
                processed_row = []
                for value in row:
                    if isinstance(value, datetime):
                        processed_row.append(value.isoformat())
                    elif value is None:
                        processed_row.append("")
                    else:
                        processed_row.append(str(value))
                writer.writerow(processed_row)
            
            output.seek(0)
            
            # 返回 CSV 檔案
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出資料失敗: {str(e)}")


@admin_router.post("/api/database/cleanup")
async def cleanup_old_data(days: int = 30):
    """清理指定天數前的舊資料"""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with AsyncSessionLocal() as session:
            # 刪除舊的檢測結果
            delete_detection = await session.execute(
                text("DELETE FROM detection_results WHERE created_at < :cutoff_date"),
                {"cutoff_date": cutoff_date}
            )
            
            # 刪除舊的行為事件
            delete_behavior = await session.execute(
                text("DELETE FROM behavior_events WHERE created_at < :cutoff_date"),
                {"cutoff_date": cutoff_date}
            )
            
            # 刪除舊的分析記錄（沒有相關檢測結果的）
            delete_analysis = await session.execute(
                text("""
                    DELETE FROM analysis_records 
                    WHERE created_at < :cutoff_date 
                    AND id NOT IN (SELECT DISTINCT analysis_id FROM detection_results WHERE analysis_id IS NOT NULL)
                """),
                {"cutoff_date": cutoff_date}
            )
            
            await session.commit()
            
            return {
                "success": True,
                "deleted_detections": delete_detection.rowcount,
                "deleted_behaviors": delete_behavior.rowcount,
                "deleted_analysis": delete_analysis.rowcount,
                "cutoff_date": cutoff_date.isoformat(),
                "days": days
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理資料失敗: {str(e)}")


@admin_router.post("/api/database/clear-all")
async def clear_all_database():
    """刪除所有資料"""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # 刪除所有表格中的資料（保持資料表結構）
            await session.execute(text("TRUNCATE TABLE behavior_events CASCADE"))
            await session.execute(text("TRUNCATE TABLE detection_results CASCADE"))
            await session.execute(text("TRUNCATE TABLE analysis_records CASCADE"))
            
            # 重置自增序列
            await session.execute(text("ALTER SEQUENCE analysis_records_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE detection_results_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE behavior_events_id_seq RESTART WITH 1"))
            
            await session.commit()
            
            return {
                "success": True,
                "message": "所有資料已成功刪除",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"資料庫最佳化失敗: {str(e)}")


@admin_router.get("/api/database/item-info/{table_name}/{item_id}")
async def get_item_detailed_info(table_name: str, item_id: int):
    """獲取指定項目的詳細資訊及其用途說明"""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        
        # 驗證表名
        allowed_tables = ["analysis_records", "detection_results", "behavior_events"]
        if table_name not in allowed_tables:
            raise HTTPException(status_code=400, detail="不支援的資料表")
        
        async with AsyncSessionLocal() as session:
            # 獲取基本項目資訊
            item_query = f"SELECT * FROM {table_name} WHERE id = :item_id"
            result = await session.execute(text(item_query), {"item_id": item_id})
            item_data = result.fetchone()
            
            if not item_data:
                raise HTTPException(status_code=404, detail="找不到指定的項目")
            
            # 轉換為字典格式
            columns = result.keys()
            item_dict = {}
            for i, column in enumerate(columns):
                value = item_data[i]
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif value is None:
                    value = ""
                item_dict[column] = value
            
            # 根據不同表格提供詳細說明和用途
            if table_name == "analysis_records":
                info = await get_analysis_record_info(session, item_dict)
            elif table_name == "detection_results":
                info = await get_detection_result_info(session, item_dict)
            elif table_name == "behavior_events":
                info = await get_behavior_event_info(session, item_dict)
            
            return {
                "item_data": item_dict,
                "detailed_info": info,
                "table_name": table_name,
                "item_id": item_id,
                "timestamp": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取項目詳細資訊失敗: {str(e)}")

async def get_analysis_record_info(session, item_dict):
    """獲取分析記錄的詳細資訊和用途說明"""
    from sqlalchemy import text
    
    analysis_id = item_dict.get("id")
    
    # 獲取相關的檢測結果數量
    detection_count_result = await session.execute(
        text("SELECT COUNT(*) FROM detection_results WHERE analysis_id = :analysis_id"),
        {"analysis_id": analysis_id}
    )
    detection_count = detection_count_result.scalar()
    
    # 獲取相關的行為事件數量
    behavior_count_result = await session.execute(
        text("SELECT COUNT(*) FROM behavior_events WHERE analysis_id = :analysis_id"),
        {"analysis_id": analysis_id}
    )
    behavior_count = behavior_count_result.scalar()
    
    # 獲取檢測到的物件類型統計
    object_types_result = await session.execute(
        text("""
            SELECT object_type, object_chinese, COUNT(*) as count 
            FROM detection_results 
            WHERE analysis_id = :analysis_id 
            GROUP BY object_type, object_chinese 
            ORDER BY count DESC
        """),
        {"analysis_id": analysis_id}
    )
    object_types = [dict(row._mapping) for row in object_types_result.fetchall()]
    
    return {
        "purpose": "影片分析記錄",
        "description": "這個項目是一個完整的影片分析任務記錄，包含了從影片檔案到檢測結果的完整處理流程。",
        "functionality": [
            "記錄影片檔案的基本資訊（路徑、名稱、時長等）",
            "追蹤分析處理的狀態（處理中、完成、失敗等）",
            "統計分析結果（檢測數量、物件類型等）",
            "保存結果檔案路徑（CSV、標註影片等）"
        ],
        "usage_scenarios": [
            "數位雙生系統中的影片監控分析",
            "YOLO 模型的批次檢測任務",
            "安全監控系統的影片處理",
            "物件識別與追蹤的歷史記錄"
        ],
        "related_data": {
            "detection_results_count": detection_count,
            "behavior_events_count": behavior_count,
            "detected_object_types": object_types
        },
        "field_explanations": {
            "video_path": "影片檔案的完整路徑，用於重新處理或查看原始檔案",
            "video_name": "影片檔案名稱，方便識別和管理",
            "analysis_type": "分析類型，detection=物件檢測，annotation=標註生成",
            "status": "處理狀態，processing=處理中，completed=完成，failed=失敗",
            "total_detections": "在整個影片中檢測到的物件總數",
            "unique_objects": "檢測到的不同物件類型數量",
            "analysis_duration": "完成整個分析任務所花費的時間",
            "csv_file_path": "生成的 CSV 結果檔案路徑，包含詳細檢測資料",
            "annotated_video_path": "標註後的影片檔案路徑，視覺化檢測結果"
        }
    }

async def get_detection_result_info(session, item_dict):
    """獲取檢測結果的詳細資訊和用途說明"""
    from sqlalchemy import text
    
    analysis_id = item_dict.get("analysis_id")
    
    # 獲取關聯的分析記錄資訊
    analysis_result = await session.execute(
        text("SELECT video_name, analysis_type FROM analysis_records WHERE id = :analysis_id"),
        {"analysis_id": analysis_id}
    )
    analysis_info = analysis_result.fetchone()
    
    # 獲取同一物件的其他檢測記錄數量
    object_id = item_dict.get("object_id")
    same_object_count = 0
    if object_id:
        same_object_result = await session.execute(
            text("SELECT COUNT(*) FROM detection_results WHERE object_id = :object_id AND analysis_id = :analysis_id"),
            {"object_id": object_id, "analysis_id": analysis_id}
        )
        same_object_count = same_object_result.scalar()
    
    return {
        "purpose": "物件檢測結果",
        "description": "這個項目記錄了 YOLO 模型在特定影片幀中檢測到的一個物件的詳細資訊，包括位置、信心度和運動資料。",
        "functionality": [
            "記錄檢測到的物件類型和信心度",
            "保存物件在畫面中的精確位置（邊界框座標）",
            "計算物件的運動資訊（速度、方向等）",
            "提供 Unity 座標系統的座標轉換"
        ],
        "usage_scenarios": [
            "即時物件追蹤和監控",
            "數位雙生系統中的物件狀態同步",
            "安全監控中的物件行為分析",
            "Unity 遊戲引擎中的物件定位"
        ],
        "related_data": {
            "source_video": analysis_info._mapping["video_name"] if analysis_info else "未知",
            "analysis_type": analysis_info._mapping["analysis_type"] if analysis_info else "未知",
            "same_object_detections": same_object_count
        },
        "field_explanations": {
            "timestamp": "檢測發生的精確時間戳",
            "frame_number": "在影片中的幀編號，用於定位具體畫面",
            "frame_time": "影片中的時間點（秒），方便跳轉到特定時刻",
            "object_type": "YOLO 檢測到的物件類型（英文）",
            "object_chinese": "物件類型的中文翻譯，便於理解",
            "confidence": "檢測信心度（0-1），越高表示檢測越準確",
            "bbox_x1, bbox_y1, bbox_x2, bbox_y2": "邊界框座標，使用 Unity 座標系統",
            "center_x, center_y": "物件中心點座標，Y軸向上為正",
            "velocity_x, velocity_y": "物件在 X 和 Y 方向的移動速度",
            "speed": "物件的移動速度大小",
            "direction": "物件移動方向（如：north, south, east, west）",
            "zone": "物件所在的預定義區域（如果有設定區域劃分）"
        }
    }

async def get_behavior_event_info(session, item_dict):
    """獲取行為事件的詳細資訊和用途說明"""
    from sqlalchemy import text
    
    analysis_id = item_dict.get("analysis_id")
    
    # 獲取關聯的分析記錄資訊
    analysis_result = await session.execute(
        text("SELECT video_name FROM analysis_records WHERE id = :analysis_id"),
        {"analysis_id": analysis_id}
    )
    analysis_info = analysis_result.fetchone()
    
    # 獲取相同事件類型的發生次數
    event_type = item_dict.get("event_type")
    same_event_result = await session.execute(
        text("SELECT COUNT(*) FROM behavior_events WHERE event_type = :event_type AND analysis_id = :analysis_id"),
        {"event_type": event_type, "analysis_id": analysis_id}
    )
    same_event_count = same_event_result.scalar()
    
    return {
        "purpose": "行為事件記錄",
        "description": "這個項目記錄了系統檢測到的特定行為事件，用於監控和分析物件的異常或重要行為模式。",
        "functionality": [
            "記錄特定行為事件的發生時間和位置",
            "追蹤行為的持續時間和嚴重程度",
            "關聯相關的物件和檢測結果",
            "提供事件的描述和觸發條件"
        ],
        "usage_scenarios": [
            "安全監控中的異常行為檢測",
            "自動化系統中的事件觸發",
            "行為模式分析和統計",
            "警報系統的事件記錄"
        ],
        "related_data": {
            "source_video": analysis_info._mapping["video_name"] if analysis_info else "未知",
            "same_event_occurrences": same_event_count
        },
        "field_explanations": {
            "timestamp": "事件發生的精確時間",
            "event_type": "事件類型，如進入區域、離開區域、停留過久等",
            "event_chinese": "事件類型的中文描述",
            "object_id": "觸發事件的物件追蹤 ID",
            "object_type": "觸發事件的物件類型",
            "zone": "事件發生的區域",
            "position_x, position_y": "事件發生的座標位置",
            "duration": "事件持續的時間（秒）",
            "severity": "事件的嚴重程度（low, medium, high）",
            "description": "事件的詳細描述",
            "trigger_condition": "觸發此事件的具體條件",
            "occurrence_count": "此事件在當前分析中的發生次數",
            "confidence_level": "事件檢測的信心度"
        }
    }

@admin_router.get("/api/database/search-suggestions/{table_name}")
async def get_search_suggestions(table_name: str):
    """獲取指定資料表的搜尋建議"""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        
        # 驗證表名
        allowed_tables = ["analysis_records", "detection_results", "behavior_events"]
        if table_name not in allowed_tables:
            raise HTTPException(status_code=400, detail="不支援的資料表")
        
        async with AsyncSessionLocal() as session:
            suggestions = {
                "common_values": [],
                "status_options": [],
                "type_options": [],
                "recent_searches": []
            }
            
            if table_name == "analysis_records":
                # 獲取常見的狀態值
                status_result = await session.execute(
                    text("SELECT DISTINCT status FROM analysis_records WHERE status IS NOT NULL ORDER BY status")
                )
                suggestions["status_options"] = [row[0] for row in status_result.fetchall()]
                
                # 獲取常見的分析類型
                type_result = await session.execute(
                    text("SELECT DISTINCT analysis_type FROM analysis_records WHERE analysis_type IS NOT NULL ORDER BY analysis_type")
                )
                suggestions["type_options"] = [row[0] for row in type_result.fetchall()]
                
                # 獲取常見的影片名稱關鍵字（取前10個）
                video_result = await session.execute(
                    text("""
                        SELECT DISTINCT video_name 
                        FROM analysis_records 
                        WHERE video_name IS NOT NULL 
                        ORDER BY created_at DESC 
                        LIMIT 10
                    """)
                )
                suggestions["common_values"] = [row[0] for row in video_result.fetchall()]
                
            elif table_name == "detection_results":
                # 獲取常見的物件類型
                object_result = await session.execute(
                    text("SELECT DISTINCT object_type FROM detection_results WHERE object_type IS NOT NULL ORDER BY object_type")
                )
                suggestions["type_options"] = [row[0] for row in object_result.fetchall()]
                
                # 獲取常見的物件中文名稱
                chinese_result = await session.execute(
                    text("SELECT DISTINCT object_chinese FROM detection_results WHERE object_chinese IS NOT NULL ORDER BY object_chinese")
                )
                suggestions["common_values"] = [row[0] for row in chinese_result.fetchall()]
                
                # 獲取常見的區域
                zone_result = await session.execute(
                    text("SELECT DISTINCT zone FROM detection_results WHERE zone IS NOT NULL ORDER BY zone")
                )
                suggestions["status_options"] = [row[0] for row in zone_result.fetchall()]
                
            elif table_name == "behavior_events":
                # 獲取常見的事件類型
                event_result = await session.execute(
                    text("SELECT DISTINCT event_type FROM behavior_events WHERE event_type IS NOT NULL ORDER BY event_type")
                )
                suggestions["type_options"] = [row[0] for row in event_result.fetchall()]
                
                # 獲取常見的事件中文名稱
                chinese_result = await session.execute(
                    text("SELECT DISTINCT event_chinese FROM behavior_events WHERE event_chinese IS NOT NULL ORDER BY event_chinese")
                )
                suggestions["common_values"] = [row[0] for row in chinese_result.fetchall()]
                
                # 獲取嚴重程度選項
                severity_result = await session.execute(
                    text("SELECT DISTINCT severity FROM behavior_events WHERE severity IS NOT NULL ORDER BY severity")
                )
                suggestions["status_options"] = [row[0] for row in severity_result.fetchall()]
            
            return {
                "table_name": table_name,
                "suggestions": suggestions,
                "timestamp": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取搜尋建議失敗: {str(e)}")

@admin_router.get("/api/database/backup")
async def backup_database():
    """建立資料庫備份"""
    try:
        import subprocess
        from app.core.config import settings
        
        backup_filename = f"yolo_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        backup_path = Path("backups") / backup_filename
        backup_path.parent.mkdir(exist_ok=True)
        
        # 使用 pg_dump 建立備份（需要 PostgreSQL 客戶端工具）
        try:
            cmd = [
                "pg_dump",
                settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
                "-f", str(backup_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "backup_file": backup_filename,
                "backup_path": str(backup_path),
                "size": backup_path.stat().st_size if backup_path.exists() else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"備份執行失敗: {e.stderr}")
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="找不到 pg_dump 工具，請安裝 PostgreSQL 客戶端")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立備份失敗: {str(e)}")
