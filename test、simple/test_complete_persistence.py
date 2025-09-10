#!/usr/bin/env python3
"""
完整的攝影機持久化測試
測試添加、刪除、重新載入功能
"""

import requests
import json
import time

API_BASE = "http://localhost:8001"

def test_complete_persistence():
    """完整的持久化測試"""
    print("🎯 完整攝影機持久化測試")
    print("=" * 50)
    
    try:
        # 1. 獲取初始狀態
        print("📋 步驟1: 獲取初始攝影機列表")
        response = requests.get(f"{API_BASE}/api/v1/frontend/cameras", timeout=10)
        if response.status_code != 200:
            print(f"❌ 無法獲取攝影機列表: {response.status_code}")
            return False
        
        initial_cameras = response.json()
        print(f"✅ 初始攝影機數量: {len(initial_cameras)}")
        
        # 2. 添加新攝影機
        print("\n➕ 步驟2: 添加新攝影機")
        new_camera = {
            "name": "持久化測試攝影機",
            "camera_type": "USB",
            "resolution": "1280x720",
            "fps": 25,
            "device_index": 88
        }
        
        response = requests.post(f"{API_BASE}/api/v1/frontend/cameras", json=new_camera, timeout=10)
        if response.status_code != 200:
            print(f"❌ 添加攝影機失敗: {response.status_code}")
            print(f"響應: {response.text}")
            return False
        
        add_result = response.json()
        camera_id = add_result.get("camera_id")
        print(f"✅ 成功添加攝影機，ID: {camera_id}")
        
        # 3. 確認添加成功
        print("\n🔍 步驟3: 確認攝影機已添加")
        response = requests.get(f"{API_BASE}/api/v1/frontend/cameras", timeout=10)
        cameras_after_add = response.json()
        
        added_camera = None
        for cam in cameras_after_add:
            if cam['id'] == camera_id:
                added_camera = cam
                break
        
        if not added_camera:
            print("❌ 新添加的攝影機未在列表中")
            return False
        
        print(f"✅ 攝影機已成功添加")
        print(f"   名稱: {added_camera['name']}")
        print(f"   類型: {added_camera['camera_type']}")
        print(f"   解析度: {added_camera['resolution']}")
        
        # 4. 模擬頁面刷新 (重新獲取攝影機列表)
        print(f"\n🔄 步驟4: 模擬頁面刷新")
        time.sleep(1)  # 等待一秒
        
        response = requests.get(f"{API_BASE}/api/v1/frontend/cameras", timeout=10)
        cameras_after_refresh = response.json()
        
        refreshed_camera = None
        for cam in cameras_after_refresh:
            if cam['id'] == camera_id:
                refreshed_camera = cam
                break
        
        if not refreshed_camera:
            print("❌ 頁面刷新後攝影機消失！持久化失敗！")
            return False
        
        print("✅ 頁面刷新後攝影機仍然存在！持久化成功！")
        
        # 5. 測試刪除功能
        print(f"\n🗑️ 步驟5: 測試刪除攝影機")
        response = requests.delete(f"{API_BASE}/api/v1/frontend/cameras/{camera_id}", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ 刪除攝影機失敗: {response.status_code}")
            print(f"響應: {response.text}")
            return False
        
        print("✅ 刪除請求成功")
        
        # 6. 確認刪除成功
        print(f"\n🔍 步驟6: 確認攝影機已刪除")
        response = requests.get(f"{API_BASE}/api/v1/frontend/cameras", timeout=10)
        final_cameras = response.json()
        
        for cam in final_cameras:
            if cam['id'] == camera_id:
                print("❌ 攝影機仍在列表中，刪除失敗")
                return False
        
        print("✅ 攝影機已成功刪除")
        print(f"   最終攝影機數量: {len(final_cameras)}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到API服務，請確保系統已啟動")
        return False
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_complete_persistence()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有持久化測試通過！")
        print("✅ 攝影機配置可以正常添加、保存和刪除")
        print("✅ 頁面刷新後配置不會丟失")
    else:
        print("❌ 持久化測試失敗！")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
