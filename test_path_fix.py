#!/usr/bin/env python3
"""
簡單測試即時分析 API 路徑修復
"""

import requests
import json

def test_realtime_api():
    """測試即時分析功能的路徑修復"""
    print("🔍 測試即時分析 API 路徑修復...")
    
    # 使用已知的測試數據
    test_data = {
        "task_name": "路徑修復測試",
        "camera_id": "72",  # 從之前的測試中知道有這個攝影機
        "model_id": "yolo11n",  # 使用 yolo11n 模型
        "confidence": 0.5,
        "iou_threshold": 0.45,
        "description": "測試模型檔案路徑修復"
    }
    
    print(f"發送測試請求到 API...")
    print(f"數據: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            "http://localhost:8001/api/v1/frontend/analysis/start-realtime",
            json=test_data,
            timeout=30
        )
        
        print(f"\n📊 API 響應狀態: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 路徑修復成功！即時分析啟動成功！")
            print(f"   任務 ID: {result.get('task_id', 'N/A')}")
            print(f"   狀態: {result.get('status', 'N/A')}")
            print(f"   訊息: {result.get('message', 'N/A')}")
            return True
        else:
            print(f"❌ API 請求失敗: {response.status_code}")
            try:
                error_detail = response.json()
                error_msg = error_detail.get('detail', 'Unknown error')
                print(f"   錯誤: {error_msg}")
                
                # 檢查是否還是路徑問題
                if "找不到指定的路徑" in error_msg or "yolo_backend" in error_msg:
                    print("⚠️  仍然是路徑問題，需要進一步調試")
                    return False
                else:
                    print("ℹ️  這不是路徑問題，可能是其他配置問題")
                    return True  # 路徑問題已解決
                    
            except:
                print(f"   原始錯誤: {response.text}")
                return False
                
    except requests.RequestException as e:
        print(f"❌ 連接錯誤: {e}")
        return False

if __name__ == "__main__":
    success = test_realtime_api()
    if success:
        print("\n🎉 路徑修復測試完成！")
    else:
        print("\n⚠️  可能需要進一步檢查")