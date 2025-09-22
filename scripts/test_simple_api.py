"""
簡化的API測試 - 只測試創建任務
"""

import requests
import json

# API 基礎 URL
BASE_URL = "http://localhost:8001/api/v1"

def test_simple_task_creation():
    """簡單測試任務創建API"""
    
    print("🧪 測試 create-and-execute API...")
    
    # 準備任務資料
    task_data = {
        "task_type": "video_file",
        "source_info": {
            "file_path": "D:/project/system/yolo_backend/uploads/videos/20250909_231421_3687560-uhd_2160_3840_30fps.mp4",
            "original_filename": "test_video.mp4",
            "confidence_threshold": 0.5
        },
        "source_width": 2160,
        "source_height": 3840,
        "source_fps": 30.0
    }
    
    try:
        print("📝 發送 create-and-execute 請求...")
        
        response = requests.post(
            f"{BASE_URL}/tasks/create-and-execute",
            json=task_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"🔍 回應狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 任務創建成功!")
            print(f"   任務 ID: {result.get('task_id', 'N/A')}")
            print(f"   狀態: {result.get('status', 'N/A')}")
            print(f"   訊息: {result.get('message', 'N/A')}")
        else:
            print(f"❌ API 錯誤: {response.status_code}")
            print(f"錯誤內容: {response.text}")
        
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")


def test_health():
    """測試健康狀況"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 系統健康正常")
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 無法連接系統: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 簡化 API 測試")
    print("=" * 50)
    
    test_health()
    print("-" * 30)
    test_simple_task_creation()
    
    print("=" * 50)
    print("✅ 測試完成")
    print("=" * 50)
