#!/usr/bin/env python3
"""
快速實時檢測測試
"""

import requests
import json
import time

API_BASE = "http://localhost:8001"

def test_realtime_fixed():
    """測試修復後的實時檢測"""
    print("🧪 快速實時檢測測試")
    print("=" * 40)
    
    # 1. 健康檢查
    try:
        resp = requests.get(f"{API_BASE}/api/v1/health", timeout=5)
        if resp.status_code == 200:
            print(f"✅ 系統健康: {resp.json().get('status', 'unknown')}")
        else:
            print(f"❌ 健康檢查失敗: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康檢查錯誤: {e}")
        return False
    
    # 2. 啟動實時檢測
    camera_index = 0
    
    try:
        print(f"\n🚀 啟動實時檢測 (攝影機: {camera_index})...")
        resp = requests.post(
            f"{API_BASE}/api/v1/realtime/start/{camera_index}",
            timeout=10
        )
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"✅ 啟動成功: {result}")
            task_id = result.get('task_id', 'unknown')
        else:
            print(f"❌ 啟動失敗: {resp.status_code} - {resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ 啟動錯誤: {e}")
        return False
    
    # 3. 等待檢測運行
    print("\n⏳ 等待檢測運行 3 秒...")
    time.sleep(3)
    
    # 4. 檢查狀態
    try:
        resp = requests.get(f"{API_BASE}/api/v1/realtime/sessions", timeout=5)
        if resp.status_code == 200:
            sessions = resp.json()
            print(f"📊 活躍會話: {sessions}")
        else:
            print(f"⚠️ 狀態查詢失敗: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ 狀態查詢錯誤: {e}")
    
    # 5. 停止檢測
    try:
        print(f"\n⏹️ 停止實時檢測 (攝影機: {camera_index})...")
        resp = requests.post(f"{API_BASE}/api/v1/realtime/stop/{camera_index}", timeout=10)
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"✅ 停止成功: {result}")
        else:
            print(f"❌ 停止失敗: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"❌ 停止錯誤: {e}")
    
    print("\n🎉 測試完成！")
    return True

if __name__ == "__main__":
    test_realtime_fixed()
