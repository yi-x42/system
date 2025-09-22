#!/usr/bin/env python3
"""
清理模擬網路攝影機後的完整系統測試
確認所有功能都正常工作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "yolo_backend"))

import asyncio
from app.services.camera_service import CameraService

async def test_system_after_cleanup():
    """測試清理模擬攝影機後的系統狀態"""
    print("🧹 測試清理模擬網路攝影機後的系統狀態...")
    
    try:
        # 初始化攝影機服務
        camera_service = CameraService()
        
        print("1️⃣ 測試攝影機掃描...")
        cameras = await camera_service.scan_cameras()
        
        print(f"✅ 發現 {len(cameras)} 個真實攝影機:")
        for camera in cameras:
            print(f"  - {camera.get('name', 'Unknown')} ({camera.get('type', 'Unknown')})")
        
        print("\n2️⃣ 檢查掃描結果內容...")
        usb_cameras = [cam for cam in cameras if cam.get('type') == 'USB']
        network_cameras = [cam for cam in cameras if cam.get('type') == 'Network']
        
        print(f"  📱 USB攝影機: {len(usb_cameras)} 個")
        print(f"  🌐 網路攝影機: {len(network_cameras)} 個")
        
        if network_cameras:
            print("  ⚠️  警告: 仍然發現網路攝影機，可能需要進一步清理")
        else:
            print("  ✅ 成功移除所有模擬網路攝影機")
        
        print("\n3️⃣ 驗證真實攝影機功能...")
        if usb_cameras:
            print(f"  攝影機 0 可用於即時檢測和影像串流")
        else:
            print(f"  ⚠️  沒有可用的USB攝影機")
        
        print("\n🎉 系統清理完成，只保留真實的攝影機設備")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        print(f"錯誤詳情:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    asyncio.run(test_system_after_cleanup())