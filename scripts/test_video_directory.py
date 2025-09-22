"""
測試讀取影片目錄內容
"""
import os
import json
from datetime import datetime

def get_video_files():
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

if __name__ == "__main__":
    result = get_video_files()
    print("影片目錄內容:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
