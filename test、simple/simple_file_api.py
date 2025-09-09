"""
簡單的檔案系統 API - 用於影片列表
當主 API 無法正常工作時的備用方案
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from datetime import datetime

app = FastAPI(title="檔案系統 API")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/videos")
def get_videos():
    """獲取影片列表"""
    videos_dir = "D:/project/system/yolo_backend/uploads/videos"
    
    if not os.path.exists(videos_dir):
        return {"videos": [], "total": 0}
    
    video_list = []
    supported_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    
    try:
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
        return {"error": str(e), "videos": [], "total": 0}

if __name__ == "__main__":
    import uvicorn
    print("🚀 啟動檔案系統 API (Port 8002)")
    print("📁 影片目錄 API: http://localhost:8002/videos")
    uvicorn.run(app, host="0.0.0.0", port=8002)
