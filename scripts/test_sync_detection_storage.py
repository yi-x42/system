#!/usr/bin/env python3
"""
同步檢測結果儲存測試
測試完全同步的檢測結果儲存方法
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "yolo_backend"))

from datetime import datetime
from app.services.new_database_service import DatabaseService

def test_sync_storage():
    """測試同步檢測結果儲存"""
    print("🔧 測試同步檢測結果儲存方法...")
    
    try:
        # 初始化資料庫服務
        db_service = DatabaseService()
        
        # 準備測試檢測結果數據
        test_detection = {
            'task_id': '114',  # 使用字串形式的ID
            'frame_number': 100,
            'timestamp': datetime.now(),
            'object_type': 'person',
            'confidence': 0.95,
            'bbox_x1': 100.0,
            'bbox_y1': 150.0,
            'bbox_x2': 300.0,
            'bbox_y2': 400.0,
            'center_x': 200.0,
            'center_y': 275.0
        }
        
        print(f"📊 準備儲存檢測結果: {test_detection}")
        
        # 測試同步儲存
        result = db_service.create_detection_result_sync(test_detection)
        
        if result:
            print("✅ 同步檢測結果儲存成功！")
        else:
            print("❌ 同步檢測結果儲存失敗")
            return False
            
        # 再測試一個不同的檢測結果
        test_detection2 = {
            'task_id': '114',
            'frame_number': 101,
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
        
        print(f"📊 準備儲存第二個檢測結果: {test_detection2}")
        
        result2 = db_service.create_detection_result_sync(test_detection2)
        
        if result2:
            print("✅ 第二個同步檢測結果儲存成功！")
        else:
            print("❌ 第二個同步檢測結果儲存失敗")
            return False
            
        print("🎉 所有測試通過！同步檢測結果儲存功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        print(f"錯誤詳情:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_sync_storage()