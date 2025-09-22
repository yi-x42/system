#!/usr/bin/env python3
"""
實時檢測API測試腳本
用於測試新實現的實時檢測功能
"""

import requests
import json
import time
import sys

# API基礎URL
BASE_URL = "http://26.86.64.166:8001/api/v1"

def test_api_connection():
    """測試API連接"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API連接正常")
            return True
        else:
            print(f"❌ API連接失敗，狀態碼: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API連接錯誤: {e}")
        return False

def start_realtime_detection(camera_index=0):
    """啟動實時檢測"""
    try:
        print(f"📹 啟動攝影機 {camera_index} 的實時檢測...")
        response = requests.post(f"{BASE_URL}/realtime/start/{camera_index}", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 實時檢測啟動成功")
            print(f"   - 任務ID: {result['task_id']}")
            print(f"   - 攝影機: {result['camera_index']}")
            print(f"   - 狀態: {result['status']}")
            return result['task_id']
        else:
            print(f"❌ 啟動失敗，狀態碼: {response.status_code}")
            print(f"   錯誤詳情: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 啟動實時檢測錯誤: {e}")
        return None

def check_realtime_status(camera_index=0):
    """檢查實時檢測狀態"""
    try:
        print(f"🔍 檢查攝影機 {camera_index} 的檢測狀態...")
        response = requests.get(f"{BASE_URL}/realtime/status/{camera_index}", timeout=5)
        
        if response.status_code == 200:
            status = response.json()
            print(f"📊 檢測狀態:")
            print(f"   - 運行中: {status['running']}")
            if status['running']:
                print(f"   - 任務ID: {status['task_id']}")
                print(f"   - 攝影機: {status['camera_index']}")
                print(f"   - 開始時間: {status['start_time']}")
                print(f"   - 檢測數量: {status['detection_count']}")
            return status
        else:
            print(f"❌ 狀態檢查失敗，狀態碼: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 狀態檢查錯誤: {e}")
        return None

def stop_realtime_detection(camera_index=0):
    """停止實時檢測"""
    try:
        print(f"🛑 停止攝影機 {camera_index} 的實時檢測...")
        response = requests.post(f"{BASE_URL}/realtime/stop/{camera_index}", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 實時檢測已停止")
            print(f"   - 狀態: {result['status']}")
            print(f"   - 總檢測數量: {result['total_detections']}")
            return True
        else:
            print(f"❌ 停止失敗，狀態碼: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 停止實時檢測錯誤: {e}")
        return False

def main():
    """主要測試流程"""
    print("🧪 開始測試實時檢測API")
    print("=" * 50)
    
    # 1. 測試API連接
    if not test_api_connection():
        print("❌ API連接失敗，無法繼續測試")
        return
    
    # 2. 檢查初始狀態
    initial_status = check_realtime_status(0)
    if initial_status and initial_status['running']:
        print("⚠️  檢測到現有的實時檢測任務，先停止...")
        stop_realtime_detection(0)
        time.sleep(2)
    
    # 3. 啟動實時檢測
    task_id = start_realtime_detection(0)
    if not task_id:
        print("❌ 無法啟動實時檢測")
        return
    
    # 4. 等待幾秒讓檢測運行
    print("\n⏳ 讓實時檢測運行10秒...")
    for i in range(10):
        time.sleep(1)
        print(f"   等待中... {i+1}/10秒")
    
    # 5. 檢查運行狀態
    print("\n📊 檢查運行狀態:")
    status = check_realtime_status(0)
    
    # 6. 停止檢測
    print("\n🛑 停止檢測:")
    stop_realtime_detection(0)
    
    # 7. 最終狀態檢查
    print("\n📋 最終狀態檢查:")
    final_status = check_realtime_status(0)
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    main()
