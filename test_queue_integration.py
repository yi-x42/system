#!/usr/bin/env python3
"""
測試隊列管理器集成
"""

import requests
import time
import json

def test_realtime_detection():
    """測試實時檢測功能"""
    base_url = "http://127.0.0.1:8002"
    
    print("🔍 測試隊列管理器集成...")
    
    # 1. 檢查健康狀態
    try:
        health_response = requests.get(f"{base_url}/")
        print(f"✅ 健康檢查: {health_response.status_code}")
    except Exception as e:
        print(f"❌ 健康檢查失敗: {e}")
        return
    
    # 2. 嘗試啟動實時檢測
    try:
        start_response = requests.post(f"{base_url}/api/v1/realtime/start/0")
        print(f"📊 啟動實時檢測: {start_response.status_code}")
        
        if start_response.status_code == 200:
            data = start_response.json()
            print(f"✅ 實時檢測已啟動:")
            print(f"   任務ID: {data.get('task_id')}")
            print(f"   攝影機: {data.get('camera_index')}")
            print(f"   WebSocket: {data.get('websocket_endpoint')}")
            
            # 等待一段時間讓檢測運行
            print("⏳ 等待 10 秒讓檢測運行...")
            time.sleep(10)
            
            # 檢查狀態
            status_response = requests.get(f"{base_url}/api/v1/realtime/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"📈 檢測狀態: {json.dumps(status_data, indent=2, ensure_ascii=False)}")
            
            # 停止檢測
            stop_response = requests.post(f"{base_url}/api/v1/realtime/stop/0")
            print(f"⏹️ 停止實時檢測: {stop_response.status_code}")
            
        else:
            print(f"❌ 啟動失敗: {start_response.text}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    test_realtime_detection()
