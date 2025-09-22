#!/usr/bin/env python3
"""
建立有檢測結果的測試任務，用於測試級聯刪除功能
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

from yolo_backend.app.models.database import AnalysisTask, DetectionResult
from yolo_backend.app.core.database import AsyncSessionLocal
from yolo_backend.app.services.new_database_service import DatabaseService

async def create_task_with_detections():
    """建立一個有檢測結果的測試任務"""
    
    db_service = DatabaseService()
    
    # 測試任務資料
    task_data = {
        "task_type": "video_file",
        "status": "completed",
        "source_info": {"file_path": "/test/completed_video.mp4"},
        "source_width": 1280,
        "source_height": 720,
        "source_fps": 25.0,
        "start_time": datetime.now() - timedelta(minutes=30),
        "end_time": datetime.now() - timedelta(minutes=25),
        "task_name": "測試級聯刪除的任務",
        "model_id": "yolo11n.pt",
        "confidence_threshold": 0.7
    }
    
    try:
        async with AsyncSessionLocal() as session:
            # 建立任務
            print("建立測試任務...")
            task = await db_service.create_analysis_task(session, task_data)
            await session.commit()
            
            task_id = task.id
            print(f"任務已建立，ID: {task_id}")
            
            # 新增一些測試檢測結果
            print("新增檢測結果...")
            detection_results = []
            
            for i in range(10):  # 建立10筆檢測結果
                detection_data = {
                    "task_id": task_id,
                    "frame_number": i + 1,
                    "timestamp": datetime.now() - timedelta(minutes=25) + timedelta(seconds=i*2),
                    "object_type": "person" if i % 2 == 0 else "car",
                    "confidence": 0.8 + (i * 0.01),
                    "bbox_x1": float(100 + i * 10),
                    "bbox_y1": float(200 + i * 5),
                    "bbox_x2": float(150 + i * 10),
                    "bbox_y2": float(250 + i * 5),
                    "center_x": float(125 + i * 10),
                    "center_y": float(225 + i * 5)
                }
                
                detection = await db_service.save_detection_result(session, detection_data)
                detection_results.append(detection)
            
            await session.commit()
            
            print(f"✅ 成功建立任務 {task_id} 並新增 {len(detection_results)} 筆檢測結果")
            return task_id
            
    except Exception as e:
        print(f"❌ 建立測試任務失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 建立有檢測結果的測試任務...")
    task_id = asyncio.run(create_task_with_detections())
    if task_id:
        print(f"\n📝 可以使用以下命令測試刪除:")
        print(f"   Invoke-RestMethod -Uri \"http://localhost:8001/api/v1/analysis/tasks/{task_id}\" -Method DELETE")
        print(f"\n🌐 或在前端任務管理頁面點擊刪除按鈕測試")