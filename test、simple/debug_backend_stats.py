#!/usr/bin/env python3
"""
後端統計API詳細調試測試
檢查為什麼系統統計API沒有返回攝影機相關資料
"""

import requests
import json
from datetime import datetime

def debug_backend_stats():
    """詳細調試後端統計API"""
    print("🔍 後端統計API調試測試")
    print("=" * 60)
    
    try:
        # 1. 測試系統統計API並查看完整響應
        print("📊 1. 系統統計API完整響應...")
        response = requests.get("http://localhost:8001/api/v1/frontend/stats", timeout=10)
        
        print(f"狀態碼: {response.status_code}")
        print(f"響應標頭: {dict(response.headers)}")
        print(f"響應內容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n解析後的JSON:")
            for key, value in data.items():
                print(f"  {key}: {value}")
        
        # 2. 測試資料來源API
        print("\n📂 2. 資料來源API測試...")
        try:
            sources_response = requests.get("http://localhost:8001/api/v1/data-sources", timeout=10)
            print(f"資料來源API狀態碼: {sources_response.status_code}")
            
            if sources_response.status_code == 200:
                sources_data = sources_response.json()
                camera_sources = [s for s in sources_data if s.get('source_type') == 'camera']
                print(f"資料庫中攝影機類型來源數量: {len(camera_sources)}")
            else:
                print(f"資料來源API失敗: {sources_response.text}")
        except Exception as e:
            print(f"資料來源API錯誤: {e}")
        
        # 3. 測試攝影機API
        print("\n🎥 3. 攝影機API測試...")
        try:
            cameras_response = requests.get("http://localhost:8001/api/v1/frontend/cameras?real_time_check=true", timeout=15)
            print(f"攝影機API狀態碼: {cameras_response.status_code}")
            
            if cameras_response.status_code == 200:
                cameras_data = cameras_response.json()
                online_count = len([c for c in cameras_data if c.get('status') == 'online'])
                print(f"攝影機API檢測數量: {len(cameras_data)}")
                print(f"攝影機API線上數量: {online_count}")
            else:
                print(f"攝影機API失敗: {cameras_response.text}")
        except Exception as e:
            print(f"攝影機API錯誤: {e}")
        
        # 4. 測試後端日誌端點（如果有的話）
        print("\n📝 4. 嘗試獲取後端日誌...")
        try:
            log_response = requests.get("http://localhost:8001/api/v1/debug/logs", timeout=5)
            if log_response.status_code == 200:
                print("後端日誌:")
                print(log_response.text[-1000:])  # 最後1000字符
            else:
                print(f"無法獲取日誌: {log_response.status_code}")
        except:
            print("無後端日誌端點")
            
    except Exception as e:
        print(f"❌ 測試錯誤: {e}")

def test_camera_service_directly():
    """直接測試攝影機服務邏輯"""
    print("\n🔧 攝影機服務直接測試...")
    try:
        # 測試攝影機服務是否可以正常初始化
        service_test_response = requests.get("http://localhost:8001/api/v1/frontend/cameras", timeout=10)
        print(f"攝影機服務基礎測試: {service_test_response.status_code}")
        
        if service_test_response.status_code == 200:
            cameras = service_test_response.json()
            print(f"基礎攝影機數量: {len(cameras)}")
        else:
            print(f"攝影機服務錯誤: {service_test_response.text}")
            
    except Exception as e:
        print(f"攝影機服務測試錯誤: {e}")

if __name__ == "__main__":
    print("🚀 開始後端統計API調試...")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    debug_backend_stats()
    test_camera_service_directly()
    
    print("\n✅ 調試測試完成！")