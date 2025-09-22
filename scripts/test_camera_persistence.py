#!/usr/bin/env python3
"""
測試攝影機配置持久化功能
測試攝影機在重啟後是否能持久保存
"""

import requests
import json
import time
import sys
import os

# 設置 API 基礎 URL
API_BASE = "http://localhost:8001"

def test_camera_persistence():
    """測試攝影機持久化功能"""
    print("🔄 測試攝影機配置持久化功能...")
    
    try:
        # 1. 獲取當前攝影機列表
        print("\n📋 步驟1: 獲取當前攝影機列表")
        response = requests.get(f"{API_BASE}/api/v1/frontend/cameras")
        
        if response.status_code != 200:
            print(f"❌ 無法獲取攝影機列表: {response.status_code}")
            print(f"響應內容: {response.text}")
            return False
        
        cameras_before = response.json()
        print(f"✅ 當前有 {len(cameras_before)} 個攝影機")
        for camera in cameras_before:
            print(f"   - {camera['name']} (ID: {camera['id']})")
        
        # 2. 添加新攝影機
        print("\n➕ 步驟2: 添加新測試攝影機")
        new_camera_data = {
            "name": "持久化測試攝影機",
            "camera_type": "USB",
            "resolution": "1280x720",
            "fps": 25,
            "device_index": 99
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/frontend/cameras",
            json=new_camera_data
        )
        
        if response.status_code != 200:
            print(f"❌ 添加攝影機失敗: {response.status_code}")
            print(f"響應內容: {response.text}")
            return False
        
        new_camera_id = response.json().get("camera_id")
        print(f"✅ 成功添加攝影機，ID: {new_camera_id}")
        
        # 3. 確認攝影機已添加
        print(f"\n🔍 步驟3: 確認攝影機已添加")
        response = requests.get(f"{API_BASE}/api/v1/frontend/cameras")
        cameras_after_add = response.json()
        
        found_camera = None
        for camera in cameras_after_add:
            if camera['id'] == new_camera_id:
                found_camera = camera
                break
        
        if not found_camera:
            print(f"❌ 新添加的攝影機未在列表中找到")
            return False
        
        print(f"✅ 確認攝影機已添加: {found_camera['name']}")
        
        # 4. 重啟服務測試持久化
        print("\n🔄 步驟4: 請手動重啟系統來測試持久化...")
        print("   請在另一個終端執行: python start.py")
        print("   然後按 Enter 繼續測試...")
        input("   等待重啟完成後按 Enter...")
        
        # 5. 等待服務重啟
        print("\n⏳ 步驟5: 等待服務重啟...")
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{API_BASE}/api/v1/frontend/cameras", timeout=2)
                if response.status_code == 200:
                    print(f"✅ 服務已重啟 (嘗試 {i+1}/{max_retries})")
                    break
            except requests.exceptions.RequestException:
                print(f"⏳ 等待服務重啟... ({i+1}/{max_retries})")
                time.sleep(2)
        else:
            print("❌ 服務重啟超時")
            return False
        
        # 6. 檢查攝影機是否持久保存
        print(f"\n🔍 步驟6: 檢查攝影機持久化")
        response = requests.get(f"{API_BASE}/api/v1/frontend/cameras")
        cameras_after_restart = response.json()
        
        found_after_restart = None
        for camera in cameras_after_restart:
            if camera['id'] == new_camera_id:
                found_after_restart = camera
                break
        
        if not found_after_restart:
            print(f"❌ 攝影機在重啟後遺失，持久化失敗")
            print(f"   重啟前攝影機數量: {len(cameras_after_add)}")
            print(f"   重啟後攝影機數量: {len(cameras_after_restart)}")
            return False
        
        print(f"✅ 攝影機持久化成功！")
        print(f"   名稱: {found_after_restart['name']}")
        print(f"   類型: {found_after_restart['camera_type']}")
        print(f"   解析度: {found_after_restart['resolution']}")
        
        # 7. 測試刪除功能
        print(f"\n🗑️ 步驟7: 測試刪除功能")
        response = requests.delete(f"{API_BASE}/api/v1/frontend/cameras/{new_camera_id}")
        
        if response.status_code != 200:
            print(f"❌ 刪除攝影機失敗: {response.status_code}")
            print(f"響應內容: {response.text}")
            return False
        
        print(f"✅ 成功刪除攝影機")
        
        # 8. 確認已刪除
        print(f"\n🔍 步驟8: 確認攝影機已刪除")
        response = requests.get(f"{API_BASE}/api/v1/frontend/cameras")
        cameras_final = response.json()
        
        for camera in cameras_final:
            if camera['id'] == new_camera_id:
                print(f"❌ 攝影機仍在列表中，刪除失敗")
                return False
        
        print(f"✅ 攝影機已成功刪除")
        print(f"   最終攝影機數量: {len(cameras_final)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🎯 攝影機配置持久化測試")
    print("=" * 50)
    
    success = test_camera_persistence()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 所有測試通過！攝影機持久化功能正常")
    else:
        print("❌ 測試失敗！請檢查系統配置")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
