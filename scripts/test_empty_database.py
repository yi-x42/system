#!/usr/bin/env python3
"""
測試清空資料庫後的攝影機初始化行為
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "yolo_backend"))

import asyncio
from app.services.camera_service import CameraService

async def test_empty_database_behavior():
    """測試資料庫沒有攝影機資料時的行為"""
    print("🧪 測試清空資料庫後的攝影機初始化行為...")
    
    try:
        # 創建攝影機服務實例
        camera_service = CameraService()
        
        print("1️⃣ 檢查初始化時的攝影機數量...")
        camera_count = len(camera_service.cameras)
        print(f"   攝影機服務中的攝影機數量: {camera_count}")
        
        if camera_count == 0:
            print("   ✅ 沒有自動創建虛擬攝影機")
        else:
            print("   ⚠️  仍然創建了攝影機:")
            for camera_id, camera in camera_service.cameras.items():
                print(f"      - {camera_id}: {camera.name} ({camera.camera_type})")
        
        print("\n2️⃣ 測試攝影機掃描功能...")
        scanned_cameras = await camera_service.scan_cameras()
        print(f"   掃描到的攝影機數量: {len(scanned_cameras)}")
        
        for camera in scanned_cameras:
            print(f"   - {camera.get('name', 'Unknown')} ({camera.get('type', 'Unknown')})")
        
        print("\n3️⃣ 檢查資料庫狀態...")
        # 這裡我們不直接操作資料庫，只是說明期望的行為
        print("   期望: 資料庫中沒有自動創建的虛擬攝影機記錄")
        print("   用戶需要手動添加真實的攝影機設備")
        
        print("\n🎉 測試完成!")
        return camera_count == 0  # 如果沒有攝影機，則測試通過
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        print(f"錯誤詳情:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_empty_database_behavior())
    if success:
        print("\n✅ 測試通過: 系統不會自動創建虛擬攝影機")
    else:
        print("\n❌ 測試失敗: 系統仍在創建虛擬攝影機")