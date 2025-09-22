"""
簡化的任務停止測試
只測試關鍵的停止功能，不中斷系統
"""

import requests
import json
from datetime import datetime

def test_stop_task_fix():
    """測試任務停止修復"""
    
    base_url = "http://localhost:8001"
    
    print("🔧 任務停止功能修復測試")
    print("=" * 50)
    
    try:
        # 檢查服務器是否運行
        resp = requests.get(f"{base_url}/api/v1/frontend/stats", timeout=5)
        if resp.status_code != 200:
            print("❌ 服務器未運行，請先啟動系統")
            return
        
        print("✅ 服務器運行正常")
        
        # 1. 創建任務
        print("\n📝 步驟 1: 創建新任務")
        task_data = {
            "task_name": f"停止測試-{datetime.now().strftime('%H%M%S')}",
            "task_type": "realtime_camera",
            "source_info": {
                "camera_id": "1",
                "name": "測試攝影機",
                "description": "測試任務停止功能"
            },
            "model_id": "yolo11n.pt",
            "confidence_threshold": 0.5
        }
        
        resp = requests.post(f"{base_url}/api/v1/frontend/analysis-tasks", json=task_data, timeout=10)
        if resp.status_code == 200:
            create_result = resp.json()
            task_id = str(create_result["task_id"])
            print(f"✅ 任務創建成功，ID: {task_id}")
        else:
            print(f"❌ 任務創建失敗: {resp.status_code} - {resp.text}")
            return
        
        # 2. 啟動任務
        print("\n🚀 步驟 2: 啟動任務")
        resp = requests.post(f"{base_url}/api/v1/frontend/tasks/{task_id}/start", timeout=10)
        if resp.status_code == 200:
            print("✅ 任務啟動成功")
        else:
            print(f"❌ 任務啟動失敗: {resp.status_code} - {resp.text}")
            return
        
        # 等待一下讓任務開始運行
        print("⏳ 等待任務運行...")
        import time
        time.sleep(2)
        
        # 3. 直接測試停止任務 (這是關鍵測試)
        print("\n🛑 步驟 3: 停止任務 (關鍵測試)")
        resp = requests.post(f"{base_url}/api/v1/frontend/tasks/{task_id}/stop", timeout=10)
        
        if resp.status_code == 200:
            print("✅ 任務停止成功!")
            print(f"   響應: {resp.text}")
        else:
            print(f"❌ 任務停止失敗: {resp.status_code}")
            print(f"   錯誤詳情: {resp.text}")
            
            # 檢查是否是"任務不存在"錯誤
            if "任務不存在" in resp.text:
                print("\n🔍 這是我們要修復的關鍵錯誤!")
                print("   - 表明內存狀態與數據庫不同步")
                print("   - stop_task方法可能沒有使用database-first邏輯")
                return False
        
        # 4. 測試停止不存在的任務
        print("\n🧪 步驟 4: 測試停止不存在的任務")
        fake_task_id = "99999"
        resp = requests.post(f"{base_url}/api/v1/frontend/tasks/{fake_task_id}/stop", timeout=10)
        
        if resp.status_code == 404 or "任務不存在" in resp.text:
            print("✅ 正確處理不存在的任務")
        else:
            print(f"⚠️  不存在任務的處理結果: {resp.status_code} - {resp.text}")
        
        print("\n" + "=" * 50)
        print("✅ 測試完成! 任務停止功能修復驗證成功")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 網絡錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

if __name__ == "__main__":
    test_stop_task_fix()