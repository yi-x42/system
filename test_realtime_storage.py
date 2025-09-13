#!/usr/bin/env python3
"""
即時檢測結果儲存測試
測試完整的即時檢測與資料庫儲存流程
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "yolo_backend"))

import asyncio
import time
from datetime import datetime
from app.services.realtime_detection_service import RealtimeDetectionService
from app.services.new_database_service import DatabaseService

async def test_realtime_detection_storage():
    """測試即時檢測與資料庫儲存"""
    print("🔧 測試即時檢測結果儲存...")
    
    try:
        # 初始化服務
        detection_service = RealtimeDetectionService()
        db_service = DatabaseService()
        
        # 先創建一個分析任務
        print("📝 創建測試分析任務...")
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            task_data = {
                'task_type': 'realtime_camera',
                'status': 'running',
                'source_info': {'camera_id': 0, 'name': '測試攝影機'},
                'source_width': 640,
                'source_height': 480,
                'source_fps': 30.0,
                'start_time': datetime.now()
            }
            
            task = await db_service.create_analysis_task(session, task_data)
            await session.commit()
            task_id = task.id
            print(f"✅ 創建任務成功，ID: {task_id}")
        
        # 測試即時檢測功能
        print("🎥 開始測試即時檢測...")
        
        # 模擬檢測結果（這裡我們不需要真正的攝影機）
        test_detections = [
            {
                'task_id': str(task_id),
                'frame_number': 1,
                'timestamp': datetime.now(),
                'object_type': 'person',
                'confidence': 0.95,
                'bbox_x1': 100.0,
                'bbox_y1': 150.0,
                'bbox_x2': 300.0,
                'bbox_y2': 400.0,
                'center_x': 200.0,
                'center_y': 275.0
            },
            {
                'task_id': str(task_id),
                'frame_number': 2,
                'timestamp': datetime.now(),
                'object_type': 'tv',
                'confidence': 0.88,
                'bbox_x1': 50.0,
                'bbox_y1': 80.0,
                'bbox_x2': 250.0,
                'bbox_y2': 200.0,
                'center_x': 150.0,
                'center_y': 140.0
            }
        ]
        
        # 測試檢測結果儲存
        for i, detection in enumerate(test_detections):
            print(f"💾 儲存第 {i+1} 個檢測結果...")
            
            success = db_service.create_detection_result_sync(detection)
            
            if success:
                print(f"✅ 檢測結果 {i+1} 儲存成功")
            else:
                print(f"❌ 檢測結果 {i+1} 儲存失敗")
                return False
            
            # 稍微等待一下
            time.sleep(0.1)
        
        # 驗證資料是否真的儲存到資料庫
        print("🔍 驗證資料庫中的檢測結果...")
        async with AsyncSessionLocal() as session:
            results = await db_service.get_detection_results(session, task_id=task_id)
            print(f"📊 找到 {len(results)} 筆檢測結果")
            
            for result in results:
                print(f"   - 幀 {result.frame_number}: {result.object_type} (信心度: {result.confidence:.2f})")
        
        print("🎉 即時檢測結果儲存測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        print(f"錯誤詳情:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    asyncio.run(test_realtime_detection_storage())