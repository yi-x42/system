#!/usr/bin/env python3
"""
快速啟動一個即時分析任務用於測試
"""

import requests
import json
import time

# API 基礎地址
BASE_URL = "http://localhost:8001/api/v1"

def start_realtime_analysis():
    """啟動即時分析任務"""
    print("🚀 啟動即時分析任務...")
    
    # 準備請求數據
    realtime_data = {
        "task_name": "測試暫停恢復功能",
        "camera_id": "79",
        "model_id": "yolov11l",
        "confidence": 0.5,
        "iou_threshold": 0.45,
        "description": "用於測試暫停恢復功能的即時分析任務"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/frontend/analysis/start-realtime",
            json=realtime_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 即時分析啟動成功！")
            print(f"   任務 ID: {result.get('task_id', 'N/A')}")
            print(f"   狀態: {result.get('status', 'N/A')}")
            return result.get('task_id')
        else:
            print(f"❌ 即時分析啟動失敗: {response.status_code}")
            print(f"   錯誤內容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 啟動即時分析時發生錯誤: {e}")
        return None

if __name__ == "__main__":
    task_id = start_realtime_analysis()
    if task_id:
        print(f"\n🎯 可以使用任務 ID {task_id} 進行測試")
    else:
        print("\n❌ 無法啟動即時分析任務")