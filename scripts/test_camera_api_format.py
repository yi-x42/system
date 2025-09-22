#!/usr/bin/env python3
"""
測試攝影機 API 的回傳格式
用來了解為什麼前端卡片沒有更新
"""

import requests
import json
from datetime import datetime

def test_camera_api():
    print(f"🔍 測試時間: {datetime.now()}")
    print("=" * 50)
    
    # 測試一般攝影機 API
    try:
        print("📷 測試一般攝影機 API:")
        response = requests.get('http://localhost:8001/api/v1/frontend/cameras')
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("回傳資料:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"錯誤: {response.text}")
    except Exception as e:
        print(f"❌ 一般攝影機 API 錯誤: {e}")
    
    print("\n" + "-" * 50)
    
    # 測試即時檢測攝影機 API
    try:
        print("⚡ 測試即時檢測攝影機 API:")
        response = requests.get('http://localhost:8001/api/v1/frontend/cameras?real_time_check=true')
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("回傳資料:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 分析狀態欄位
            print("\n📊 狀態分析:")
            for camera in data:
                print(f"  攝影機 {camera.get('id', 'unknown')}: {camera.get('name', 'unknown')}")
                print(f"    狀態: {camera.get('status', 'unknown')}")
                print(f"    類型: {camera.get('camera_type', 'unknown')}")
                print(f"    IP: {camera.get('ip', 'unknown')}")
        else:
            print(f"錯誤: {response.text}")
    except Exception as e:
        print(f"❌ 即時檢測攝影機 API 錯誤: {e}")

if __name__ == "__main__":
    test_camera_api()