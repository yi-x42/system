#!/usr/bin/env python3
"""
測試攝影機資源衝突修復
測試同時啟動即時辨識和攝影機串流是否還會發生 MSMF 錯誤
"""

import requests
import time
import json
import sys

# API 基礎 URL
BASE_URL = "http://localhost:8001/api/v1"

def test_camera_detection():
    """測試可用攝影機檢測"""
    try:
        print("🔍 測試可用攝影機檢測...")
        response = requests.get(f"{BASE_URL}/frontend/data-sources/types/camera/devices")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功檢測到 {len(result.get('cameras', []))} 個攝影機")
            for camera in result.get('cameras', []):
                print(f"   📹 攝影機 {camera['device_id']}: {camera['name']}")
                if 'resolution' in camera:
                    print(f"      解析度: {camera['resolution']}, FPS: {camera['fps']}")
            return True
        else:
            print(f"❌ 攝影機檢測失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 攝影機檢測異常: {e}")
        return False

def test_realtime_detection():
    """測試即時辨識啟動"""
    try:
        print("\n🚀 測試即時辨識啟動...")
        
        # 啟動即時辨識 (使用realtime_routes的API)
        camera_index = 0
        
        response = requests.post(f"{BASE_URL}/realtime/start/{camera_index}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 即時辨識啟動成功，任務 ID: {result.get('task_id')}")
            return result.get('task_id')
        else:
            print(f"❌ 即時辨識啟動失敗: {response.status_code}")
            print(f"   錯誤訊息: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 即時辨識啟動異常: {e}")
        return None

def check_realtime_status():
    """檢查即時辨識狀態"""
    try:
        print("\n📊 檢查即時辨識狀態...")
        camera_index = 0
        response = requests.get(f"{BASE_URL}/realtime/status/{camera_index}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 即時辨識狀態: {result.get('status')}")
            if result.get('is_running'):
                print(f"   📈 已處理幀數: {result.get('processed_frames', 0)}")
                print(f"   🎯 檢測到物件數: {result.get('detection_count', 0)}")
            return True
        else:
            print(f"❌ 狀態檢查失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 狀態檢查異常: {e}")
        return False

def test_camera_stream_conflict():
    """測試攝影機串流與即時辨識的衝突"""
    try:
        print("\n🔄 測試攝影機串流與即時辨識衝突...")
        
        # 在即時辨識運行時，嘗試訪問攝影機串流
        camera_index = 0
        response = requests.get(f"{BASE_URL}/frontend/cameras/{camera_index}/stream", 
                               stream=True, timeout=5)
        
        if response.status_code == 200:
            print("✅ 攝影機串流可以正常訪問 (未發生資源衝突)")
            return True
        else:
            print(f"❌ 攝影機串流訪問失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 攝影機串流測試異常: {e}")
        return False

def stop_realtime_detection():
    """停止即時辨識"""
    try:
        print("\n🛑 停止即時辨識...")
        camera_index = 0
        response = requests.post(f"{BASE_URL}/realtime/stop/{camera_index}")
        
        if response.status_code == 200:
            print("✅ 即時辨識已停止")
            return True
        else:
            print(f"❌ 停止即時辨識失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 停止即時辨識異常: {e}")
        return False

def main():
    """主測試流程"""
    print("🧪 攝影機資源衝突修復測試")
    print("=" * 50)
    
    # 1. 測試攝影機檢測
    if not test_camera_detection():
        print("❌ 攝影機檢測失敗，終止測試")
        return False
    
    # 2. 啟動即時辨識
    task_id = test_realtime_detection()
    if not task_id:
        print("❌ 即時辨識啟動失敗，終止測試")
        return False
    
    # 3. 等待系統穩定
    print("\n⏱️  等待系統穩定 (5秒)...")
    time.sleep(5)
    
    # 4. 檢查即時辨識狀態
    if not check_realtime_status():
        print("❌ 即時辨識狀態檢查失敗")
    
    # 5. 測試攝影機串流衝突
    if test_camera_stream_conflict():
        print("✅ 攝影機資源衝突問題已修復!")
    else:
        print("❌ 攝影機資源衝突問題仍然存在")
    
    # 6. 清理 - 停止即時辨識
    stop_realtime_detection()
    
    print("\n" + "=" * 50)
    print("🎯 測試完成")

if __name__ == "__main__":
    main()