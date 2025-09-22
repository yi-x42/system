#!/usr/bin/env python3
"""
完整測試：模擬清空資料庫後重啟系統的行為
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "yolo_backend"))

import asyncio
import requests
from app.services.camera_service import CameraService

def test_frontend_api():
    """測試前端API是否會返回虛擬攝影機"""
    try:
        print("🌐 測試前端API...")
        
        # 假設後端正在運行在 8001 埠
        try:
            response = requests.get("http://localhost:8001/api/v1/frontend/cameras", timeout=5)
            if response.status_code == 200:
                cameras = response.json()
                print(f"   前端API返回 {len(cameras)} 個攝影機:")
                for camera in cameras:
                    print(f"      - {camera.get('name', 'Unknown')} ({camera.get('camera_type', 'Unknown')})")
                return len(cameras)
            else:
                print(f"   API請求失敗: {response.status_code}")
                return -1
        except requests.exceptions.RequestException:
            print("   ⚠️  後端服務未運行，跳過API測試")
            return -1
            
    except Exception as e:
        print(f"   ❌ API測試失敗: {e}")
        return -1

async def test_service_layer():
    """測試服務層是否會創建虛擬攝影機"""
    print("🔧 測試服務層...")
    
    try:
        # 創建新的攝影機服務實例（模擬重啟）
        camera_service = CameraService()
        
        # 檢查內存中的攝影機
        cameras = await camera_service.get_cameras()
        print(f"   服務層中有 {len(cameras)} 個攝影機:")
        
        for camera in cameras:
            print(f"      - {camera.name} ({camera.camera_type})")
            
        return len(cameras)
        
    except Exception as e:
        print(f"   ❌ 服務層測試失敗: {e}")
        return -1

async def main():
    """主測試函數"""
    print("🧪 完整測試：清空資料庫後的系統行為")
    print("=" * 50)
    
    # 測試服務層
    service_camera_count = await test_service_layer()
    
    # 測試前端API
    api_camera_count = test_frontend_api()
    
    print("\n📊 測試結果總結:")
    print(f"   服務層攝影機數量: {service_camera_count}")
    if api_camera_count >= 0:
        print(f"   API返回攝影機數量: {api_camera_count}")
    else:
        print(f"   API測試: 跳過（後端未運行）")
    
    print("\n🎯 期望結果:")
    print("   - 服務層攝影機數量應該為 0")
    print("   - API返回攝影機數量也應該為 0")
    print("   - 用戶需要手動添加真實攝影機")
    
    # 判斷測試是否通過
    success = (service_camera_count == 0)
    if api_camera_count >= 0:
        success = success and (api_camera_count == 0)
    
    if success:
        print("\n✅ 測試通過: 系統不會自動創建虛擬攝影機！")
    else:
        print("\n❌ 測試失敗: 系統仍在創建虛擬攝影機")
        print("   建議檢查 _initialize_default_cameras() 方法是否被正確註釋")

if __name__ == "__main__":
    asyncio.run(main())