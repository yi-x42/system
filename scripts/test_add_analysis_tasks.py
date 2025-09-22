#!/usr/bin/env python3
"""
建立測試分析任務資料
"""
import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
import sys

# 加入專案路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

from yolo_backend.app.models.database import AnalysisTask
from yolo_backend.app.core.database import AsyncSessionLocal
from yolo_backend.app.services.new_database_service import DatabaseService

async def add_test_analysis_tasks():
    """新增測試分析任務資料"""
    
    db_service = DatabaseService()
    
    # 測試任務資料
    test_tasks = [
        {
            "task_type": "realtime_camera",
            "status": "running",
            "source_info": {"camera_id": 1, "camera_name": "前門攝影機"},
            "source_width": 1920,
            "source_height": 1080,
            "source_fps": 30.0,
            "start_time": datetime.now() - timedelta(hours=2),
            "task_name": "前門即時監控",
            "model_id": "yolo11n.pt",
            "confidence_threshold": 0.8
        },
        {
            "task_type": "video_file",
            "status": "completed",
            "source_info": {"file_path": "/uploads/test_video.mp4"},
            "source_width": 1280,
            "source_height": 720,
            "source_fps": 25.0,
            "start_time": datetime.now() - timedelta(days=1),
            "end_time": datetime.now() - timedelta(days=1) + timedelta(minutes=30),
            "task_name": "測試影片分析",
            "model_id": "yolo11s.pt",
            "confidence_threshold": 0.7
        },
        {
            "task_type": "realtime_camera",
            "status": "paused",
            "source_info": {"camera_id": 2, "camera_name": "後門攝影機"},
            "source_width": 1920,
            "source_height": 1080,
            "source_fps": 30.0,
            "start_time": datetime.now() - timedelta(hours=1),
            "task_name": "後門即時監控",
            "model_id": "yolo11n.pt",
            "confidence_threshold": 0.6
        },
        {
            "task_type": "video_file",
            "status": "pending",
            "source_info": {"file_path": "/uploads/waiting_video.mp4"},
            "source_width": 1920,
            "source_height": 1080,
            "source_fps": 30.0,
            "task_name": "待處理影片分析",
            "model_id": "yolo11m.pt",
            "confidence_threshold": 0.75
        },
        {
            "task_type": "realtime_camera",
            "status": "failed",
            "source_info": {"camera_id": 3, "camera_name": "側門攝影機"},
            "source_width": 1280,
            "source_height": 720,
            "source_fps": 25.0,
            "start_time": datetime.now() - timedelta(minutes=30),
            "end_time": datetime.now() - timedelta(minutes=25),
            "task_name": "側門監控（失敗）",
            "model_id": "yolo11n.pt",
            "confidence_threshold": 0.5
        }
    ]
    
    try:
        async with AsyncSessionLocal() as session:
            for task_data in test_tasks:
                print(f"建立任務: {task_data['task_name']}")
                await db_service.create_analysis_task(session, task_data)
            
            await session.commit()
            print(f"✅ 成功新增 {len(test_tasks)} 個測試任務")
            
    except Exception as e:
        print(f"❌ 新增測試任務失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 新增測試分析任務資料...")
    asyncio.run(add_test_analysis_tasks())