#!/usr/bin/env python3
"""
測試來源解析度追蹤功能
"""

import sys
import os
import asyncio
import cv2
from pathlib import Path

# 添加後端路徑
sys.path.append(str(Path(__file__).parent / "yolo_backend"))

from app.services.new_database_service import DatabaseService
from app.models.database import AnalysisTask
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

def test_camera_resolution():
    """測試攝影機解析度獲取"""
    print("=== 測試攝影機解析度獲取 ===")
    
    try:
        # 嘗試開啟攝影機 0
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30.0
            cap.release()
            
            print(f"攝影機 0 解析度: {width}x{height} @ {fps}fps")
            return width, height, fps
        else:
            print("無法開啟攝影機 0")
            return 640, 480, 30.0
    except Exception as e:
        print(f"攝影機解析度測試失敗: {e}")
        return 640, 480, 30.0

def test_video_resolution(video_path):
    """測試影片解析度獲取"""
    print(f"=== 測試影片解析度獲取: {video_path} ===")
    
    if not os.path.exists(video_path):
        print(f"影片檔案不存在: {video_path}")
        return None
        
    try:
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 25.0
            cap.release()
            
            print(f"影片解析度: {width}x{height} @ {fps}fps")
            return width, height, fps
        else:
            print(f"無法開啟影片檔案: {video_path}")
            return None
    except Exception as e:
        print(f"影片解析度測試失敗: {e}")
        return None

async def test_database_task_creation():
    """測試資料庫任務創建"""
    print("=== 測試資料庫任務創建 ===")
    
    try:
        # 設置資料庫連接
        database_url = "sqlite:///./analysis_database.db"
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        db_service = DatabaseService()
        
        # 測試攝影機任務
        camera_width, camera_height, camera_fps = test_camera_resolution()
        camera_task_data = {
            "task_type": "realtime_camera",
            "status": "pending",
            "source_info": {
                "camera_index": 0,
                "camera_type": "USB",
                "backend": "CAP_DSHOW"
            },
            "source_width": camera_width,
            "source_height": camera_height,
            "source_fps": camera_fps
        }
        
        camera_task = await db_service.create_analysis_task(db, camera_task_data)
        print(f"攝影機任務創建成功: ID={camera_task.id}")
        print(f"解析度: {camera_task.source_width}x{camera_task.source_height} @ {camera_task.source_fps}fps")
        
        # 測試影片任務（如果有測試影片的話）
        test_video_paths = [
            "./test_video.mp4",
            "../test_video.mp4",
            "d:/project/system/test_video.mp4"
        ]
        
        for video_path in test_video_paths:
            if os.path.exists(video_path):
                video_resolution = test_video_resolution(video_path)
                if video_resolution:
                    width, height, fps = video_resolution
                    video_task_data = {
                        "task_type": "video_file",
                        "status": "pending",
                        "source_info": {
                            "file_path": video_path,
                            "original_filename": os.path.basename(video_path)
                        },
                        "source_width": width,
                        "source_height": height,
                        "source_fps": fps
                    }
                    
                    video_task = await db_service.create_analysis_task(db, video_task_data)
                    print(f"影片任務創建成功: ID={video_task.id}")
                    print(f"解析度: {video_task.source_width}x{video_task.source_height} @ {video_task.source_fps}fps")
                break
        else:
            print("沒有找到測試影片檔案")
        
        db.close()
        print("資料庫測試完成")
        
    except Exception as e:
        print(f"資料庫測試失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函數"""
    print("開始解析度追蹤功能測試")
    print("=" * 50)
    
    # 測試攝影機解析度
    test_camera_resolution()
    
    # 測試影片解析度
    test_video_resolution("./test_video.mp4")  # 如果有的話
    
    # 測試資料庫任務創建
    asyncio.run(test_database_task_creation())
    
    print("=" * 50)
    print("測試完成")

if __name__ == "__main__":
    main()
