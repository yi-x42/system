#!/usr/bin/env python3
"""
測試檢測結果儲存修復
"""

import sys
import os
from datetime import datetime

# 將 yolo_backend 加入路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

from app.services.new_database_service import DatabaseService

def test_detection_result_save():
    """測試檢測結果儲存功能"""
    
    print("🧪 測試檢測結果儲存修復")
    print("=" * 50)
    
    # 首先創建一個測試任務來避免外鍵約束錯誤
    import asyncpg
    import asyncio
    from app.core.config import settings
    
    async def ensure_test_task():
        """確保測試任務存在"""
        db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        
        # 檢查是否有任務
        existing_task = await conn.fetchrow("SELECT id FROM analysis_tasks ORDER BY id DESC LIMIT 1")
        
        if existing_task:
            task_id = existing_task['id']
            print(f"使用現有任務 ID: {task_id}")
        else:
            # 創建一個測試任務
            task_id = await conn.fetchval("""
                INSERT INTO analysis_tasks 
                (task_type, status, source_info, source_width, source_height, source_fps, created_at, task_name, model_id, confidence_threshold)
                VALUES 
                ('realtime_camera', 'completed', '{}', 640, 480, 30.0, NOW(), 'Test Task', 'yolo11n', 0.5)
                RETURNING id
            """)
            print(f"創建測試任務 ID: {task_id}")
        
        await conn.close()
        return task_id
    
    # 確保有測試任務
    task_id = asyncio.run(ensure_test_task())
    
    # 測試資料（基於用戶提供的錯誤資料）
    test_detection_data = {
        'task_id': str(task_id), 
        'frame_number': 159, 
        'timestamp': datetime(2025, 9, 14, 13, 45, 14, 926160), 
        'object_type': 'tv', 
        'confidence': 0.6770927906036377, 
        'bbox_x1': 59.167259216308594, 
        'bbox_y1': 287.46026611328125, 
        'bbox_x2': 250.08078002929688, 
        'bbox_y2': 479.98333740234375, 
        'center_x': 154.62401962280273, 
        'center_y': 383.7218017578125
    }
    
    print("📋 測試資料:")
    for key, value in test_detection_data.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    print(f"\n💾 嘗試儲存檢測結果...")
    
    try:
        # 創建資料庫服務實例
        db_service = DatabaseService()
        
        # 嘗試儲存檢測結果
        success = db_service.create_detection_result_sync(test_detection_data)
        
        if success:
            print("✅ 檢測結果儲存成功！")
            return True
        else:
            print("❌ 檢測結果儲存失敗！")
            return False
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

if __name__ == '__main__':
    try:
        success = test_detection_result_save()
        
        if success:
            print(f"\n🎉 檢測結果儲存修復測試成功！")
            print("✅ 同步儲存檢測結果功能正常")
        else:
            print(f"\n❌ 檢測結果儲存修復測試失敗")
            print("需要進一步檢查資料庫連接和表格結構")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 執行測試時發生錯誤: {e}")
        sys.exit(1)