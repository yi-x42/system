#!/usr/bin/env python3
"""
調試攝影機狀態錯誤的測試腳本
"""
import asyncio
import requests
import json

async def test_camera_api():
    """測試攝影機 API"""
    print("🔍 測試攝影機 API...")
    
    # 測試1: 基本攝影機列表 (不進行即時檢測)
    print("\n1️⃣ 測試基本攝影機列表...")
    try:
        response = requests.get("http://localhost:8001/api/v1/frontend/cameras")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            cameras = response.json()
            print(f"攝影機數量: {len(cameras)}")
            for camera in cameras:
                print(f"  - ID: {camera['id']}, 名稱: {camera['name']}, 狀態: {camera['status']}")
        else:
            print(f"錯誤: {response.text}")
    except Exception as e:
        print(f"❌ 基本攝影機列表測試失敗: {e}")
    
    # 測試2: 攝影機列表 (進行即時檢測)
    print("\n2️⃣ 測試即時狀態檢測...")
    try:
        response = requests.get("http://localhost:8001/api/v1/frontend/cameras?real_time_check=true")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            cameras = response.json()
            print(f"攝影機數量: {len(cameras)}")
            for camera in cameras:
                print(f"  - ID: {camera['id']}, 名稱: {camera['name']}, 狀態: {camera['status']}")
        else:
            print(f"❌ 錯誤回應: {response.text}")
            try:
                error_data = response.json()
                print(f"錯誤詳情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print("無法解析錯誤回應為 JSON")
    except Exception as e:
        print(f"❌ 即時狀態檢測測試失敗: {e}")

if __name__ == "__main__":
    asyncio.run(test_camera_api())