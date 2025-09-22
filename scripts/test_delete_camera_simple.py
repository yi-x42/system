#!/usr/bin/env python3
"""
簡化的攝影機刪除功能測試
驗證前端刪除按鈕是否正常工作
"""

import requests
import json
import time

# 設置 API 基礎 URL
API_BASE = "http://localhost:8001"

def test_camera_delete_api():
    """測試攝影機刪除API"""
    print("🧪 測試攝影機刪除功能...")
    
    try:
        # 1. 檢查API是否可用
        print("🔍 檢查API服務狀態...")
        response = requests.get(f"{API_BASE}/api/v1/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API服務不可用: {response.status_code}")
            return False
        print("✅ API服務正常")
        
        # 2. 獲取攝影機列表
        print("\n📋 獲取攝影機列表...")
        response = requests.get(f"{API_BASE}/api/v1/frontend/cameras", timeout=10)
        if response.status_code != 200:
            print(f"❌ 無法獲取攝影機列表: {response.status_code}")
            print(f"響應: {response.text}")
            return False
        
        cameras = response.json()
        print(f"✅ 找到 {len(cameras)} 個攝影機")
        for camera in cameras:
            print(f"   - {camera['name']} (ID: {camera['id']})")
        
        if not cameras:
            print("⚠️ 沒有攝影機可以測試刪除功能")
            return True
        
        # 3. 測試刪除第一個攝影機 (如果有的話)
        first_camera = cameras[0]
        camera_id = first_camera['id']
        camera_name = first_camera['name']
        
        print(f"\n🗑️ 測試刪除攝影機: {camera_name} (ID: {camera_id})")
        
        # 注意：這會真的刪除攝影機，請謹慎使用
        confirm = input("⚠️ 這會真的刪除攝影機，繼續嗎？(y/N): ")
        if confirm.lower() != 'y':
            print("🛑 已取消測試")
            return True
        
        response = requests.delete(f"{API_BASE}/api/v1/frontend/cameras/{camera_id}", timeout=10)
        if response.status_code != 200:
            print(f"❌ 刪除攝影機失敗: {response.status_code}")
            print(f"響應: {response.text}")
            return False
        
        result = response.json()
        print(f"✅ 刪除攝影機成功: {result.get('message', '已刪除')}")
        
        # 4. 確認攝影機已刪除
        print("\n🔍 確認攝影機已刪除...")
        response = requests.get(f"{API_BASE}/api/v1/frontend/cameras", timeout=10)
        cameras_after = response.json()
        
        found = any(cam['id'] == camera_id for cam in cameras_after)
        if found:
            print(f"❌ 攝影機仍在列表中，刪除失敗")
            return False
        
        print(f"✅ 攝影機已成功從列表中移除")
        print(f"   刪除前: {len(cameras)} 個攝影機")
        print(f"   刪除後: {len(cameras_after)} 個攝影機")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到API服務，請確保系統已啟動")
        return False
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

def main():
    print("🎯 攝影機刪除功能測試")
    print("=" * 40)
    
    success = test_camera_delete_api()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ 測試完成！")
    else:
        print("❌ 測試失敗！")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
