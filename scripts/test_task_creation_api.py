#!/usr/bin/env python3
"""
測試分析任務創建 API
"""

import requests
import json
from datetime import datetime

# API 基礎 URL
BASE_URL = "http://localhost:8001/api/v1"

def test_create_analysis_task():
    """測試分析任務創建功能"""
    print("📋 測試分析任務創建 API")
    print("=" * 50)
    
    # 準備測試資料
    task_data = {
        "title": "測試分析任務",
        "description": "這是一個測試分析任務",
        "video_file_path": "uploads/videos/20250909_221552_test_video.mp4",
        "model_name": "yolo11n",
        "analysis_type": "object_detection",
        "parameters": {
            "confidence_threshold": 0.5,
            "iou_threshold": 0.4,
            "max_detections": 100
        }
    }
    
    try:
        print(f"📤 發送請求到: {BASE_URL}/tasks/create")
        print(f"📋 請求資料: {json.dumps(task_data, ensure_ascii=False, indent=2)}")
        
        # 發送任務創建請求
        response = requests.post(
            f"{BASE_URL}/tasks/create",
            json=task_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"🌐 HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 任務創建成功!")
            print(f"📋 回應資料:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif response.status_code == 404:
            print(f"❌ 404 錯誤: API 端點未找到")
            print(f"錯誤詳情: {response.text}")
            
            # 列出可用的端點
            print(f"\n🔍 檢查可用端點:")
            try:
                docs_response = requests.get(f"http://localhost:8001/docs")
                if docs_response.status_code == 200:
                    print("✅ API 文檔可訪問: http://localhost:8001/docs")
                else:
                    print("❌ API 文檔無法訪問")
            except:
                print("❌ 無法訪問 API 文檔")
                
        else:
            print(f"❌ 請求失敗: {response.status_code}")
            print(f"錯誤詳情: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API 服務器，請確認後端服務是否啟動")
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")

def test_alternative_endpoints():
    """測試其他可能的端點路徑"""
    print(f"\n🔍 測試其他可能的端點")
    print("=" * 50)
    
    alternative_paths = [
        "/analysis/create-task",
        "/analysis/tasks/create", 
        "/tasks",
        "/new-analysis/tasks/create"
    ]
    
    for path in alternative_paths:
        try:
            url = f"{BASE_URL}{path}"
            response = requests.get(url, timeout=5)
            print(f"✅ {path}: {response.status_code}")
        except:
            print(f"❌ {path}: 無法訪問")

if __name__ == "__main__":
    print("🚀 開始測試分析任務創建功能")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 測試主要的任務創建端點
    test_create_analysis_task()
    
    # 2. 測試其他可能的端點
    test_alternative_endpoints()
    
    print("\n🏁 測試完成")
