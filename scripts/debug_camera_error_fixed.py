#!/usr/bin/env python3
"""攝影機 API 錯誤診斷腳本 - 修復路徑版本"""

import requests
import json

API_BASE = "http://localhost:8001/api/v1"

def test_basic_cameras():
    """測試基本攝影機列表"""
    try:
        response = requests.get(f"{API_BASE}/frontend/cameras")
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"攝影機數量: {len(data)}")
            for camera in data:
                print(f"  - ID: {camera['id']}, 名稱: {camera['name']}, 狀態: {camera['status']}")
        else:
            print(f"❌ 錯誤回應: {response.text}")
    except Exception as e:
        print(f"❌ 請求失敗: {e}")

def test_realtime_check():
    """測試即時狀態檢測"""
    try:
        response = requests.get(f"{API_BASE}/frontend/cameras?real_time_check=true")
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 即時檢測成功，攝影機數量: {len(data)}")
            for camera in data:
                print(f"  - ID: {camera['id']}, 名稱: {camera['name']}, 狀態: {camera['status']}")
        else:
            print(f"❌ 錯誤回應: {response.text}")
            if response.status_code == 500:
                try:
                    error_data = response.json()
                    print(f"錯誤詳情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    pass
    except Exception as e:
        print(f"❌ 請求失敗: {e}")

if __name__ == "__main__":
    print("🔍 測試攝影機 API (修復路徑版本)...")
    
    print("\n1️⃣ 測試基本攝影機列表...")
    test_basic_cameras()
    
    print("\n2️⃣ 測試即時狀態檢測...")
    test_realtime_check()