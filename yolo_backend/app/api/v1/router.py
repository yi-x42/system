"""
YOLOv11 數位雙生分析系統 - API 路由器
"""

from fastapi import APIRouter

from app.api.v1.endpoints import detection, health
# 使用簡化版 analysis
from app.api.v1.endpoints import analysis_simple
from app.core.config import get_settings

api_router = APIRouter()

# 包含各個端點路由器
api_router.include_router(
    detection.router,
    prefix="/detection",
    tags=["物件偵測"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["健康檢查"]
)

# 包含影片分析端點 (簡化版)
api_router.include_router(
    analysis_simple.router
)

# 影片列表端點
@api_router.get("/video-files")
async def get_video_files():
    """
    獲取影片列表 - 直接讀取目錄內容，包含完整的影片資訊
    """
    import os
    import cv2
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
                    
                    # 使用 OpenCV 獲取影片詳細資訊
                    duration_str = "unknown"
                    resolution_str = "unknown"
                    
                    try:
                        cap = cv2.VideoCapture(file_path)
                        if cap.isOpened():
                            # 獲取影片幀數和幀率
                            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            
                            # 計算時長
                            if fps > 0 and total_frames > 0:
                                duration_seconds = total_frames / fps
                                minutes = int(duration_seconds // 60)
                                seconds = int(duration_seconds % 60)
                                duration_str = f"{minutes}:{seconds:02d}"
                            
                            # 獲取解析度
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            if width > 0 and height > 0:
                                resolution_str = f"{width}x{height}"
                            
                            cap.release()
                    except Exception as cv_error:
                        # 如果 OpenCV 無法讀取，保持預設值
                        pass
                    
                    video_info = {
                        "id": filename,
                        "name": filename,
                        "file_path": file_path,
                        "upload_time": upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "size": size_str,
                        "duration": duration_str,
                        "resolution": resolution_str,
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
        return {"error": str(e), "videos": [], "total": 0}

# 根路徑端點
@api_router.get("/")
async def root():
    """API 根端點"""
    settings = get_settings()
    return {
        "message": f"歡迎使用 {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": f"{settings.api_v1_str}/health",
        "analysis": f"{settings.api_v1_str}/analysis",
        "video_files": f"{settings.api_v1_str}/video-files"
    }
