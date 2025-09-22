"""
影片列表 API - 專門處理影片檔案列表功能
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.logger import api_logger

# 創建路由器
router = APIRouter(prefix="/video-list", tags=["影片列表"])

class VideoFileInfo(BaseModel):
    """影片檔案資訊模型"""
    id: str
    name: str
    file_path: str
    upload_time: str
    size: str
    duration: str = "unknown"
    resolution: str = "unknown"
    status: str = "ready"

class VideoListResponse(BaseModel):
    """影片列表回應模型"""
    videos: List[VideoFileInfo]
    total: int

@router.get("/", response_model=VideoListResponse)
async def get_video_list():
    """
    獲取影片列表 - 讀取 uploads/videos 目錄內容
    """
    try:
        # 影片目錄路徑
        videos_dir = os.path.join(os.getcwd(), "uploads", "videos")
        api_logger.info(f"正在讀取影片目錄: {videos_dir}")
        
        # 檢查目錄是否存在
        if not os.path.exists(videos_dir):
            api_logger.warning(f"影片目錄不存在: {videos_dir}")
            return VideoListResponse(videos=[], total=0)
        
        video_list = []
        supported_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        
        # 遍歷目錄中的檔案
        for filename in os.listdir(videos_dir):
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                file_path = os.path.join(videos_dir, filename)
                
                if os.path.isfile(file_path):
                    try:
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
                        
                        # 創建影片資訊
                        video_info = VideoFileInfo(
                            id=filename,
                            name=filename,
                            file_path=file_path,
                            upload_time=upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                            size=size_str,
                            duration="unknown",
                            resolution="unknown",
                            status="ready"
                        )
                        
                        video_list.append(video_info)
                        api_logger.info(f"找到影片檔案: {filename}, 大小: {size_str}")
                        
                    except Exception as file_error:
                        api_logger.error(f"處理檔案 {filename} 時發生錯誤: {file_error}")
                        continue
        
        # 按上傳時間降序排列
        video_list.sort(key=lambda x: x.upload_time, reverse=True)
        
        api_logger.info(f"成功獲取 {len(video_list)} 個影片檔案")
        
        return VideoListResponse(
            videos=video_list,
            total=len(video_list)
        )
        
    except Exception as e:
        api_logger.error(f"獲取影片列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取影片列表失敗: {str(e)}")

@router.get("/debug")
async def debug_video_directory():
    """
    除錯端點 - 檢查目錄狀態
    """
    try:
        videos_dir = os.path.join(os.getcwd(), "uploads", "videos")
        
        debug_info = {
            "current_working_directory": os.getcwd(),
            "videos_directory": videos_dir,
            "directory_exists": os.path.exists(videos_dir),
            "files_in_directory": [],
            "all_extensions": []
        }
        
        if os.path.exists(videos_dir):
            all_files = os.listdir(videos_dir)
            debug_info["files_in_directory"] = all_files
            debug_info["all_extensions"] = [os.path.splitext(f)[1].lower() for f in all_files if os.path.isfile(os.path.join(videos_dir, f))]
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/simple")
async def get_simple_video_list():
    """
    簡化版影片列表 - 直接返回 JSON
    """
    try:
        videos_dir = "D:/project/system/yolo_backend/uploads/videos"
        
        if not os.path.exists(videos_dir):
            return {"videos": [], "total": 0, "message": f"目錄不存在: {videos_dir}"}
        
        video_list = []
        supported_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        
        for filename in os.listdir(videos_dir):
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                file_path = os.path.join(videos_dir, filename)
                
                if os.path.isfile(file_path):
                    stat_info = os.stat(file_path)
                    file_size = stat_info.st_size
                    upload_time = datetime.fromtimestamp(stat_info.st_mtime)
                    
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
        
        video_list.sort(key=lambda x: x['upload_time'], reverse=True)
        
        return {
            "videos": video_list,
            "total": len(video_list),
            "directory": videos_dir,
            "message": f"成功讀取 {len(video_list)} 個影片檔案"
        }
        
    except Exception as e:
        return {
            "videos": [], 
            "total": 0, 
            "error": str(e),
            "message": "讀取影片列表時發生錯誤"
        }
