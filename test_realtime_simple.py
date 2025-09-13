#!/usr/bin/env python3
"""簡單測試即時分析修復"""

import requests
import json

def test_realtime_analysis_fix():
    """測試即時分析修復"""
    print("🧪 測試即時分析修復...")
    
    try:
        # 正確的端點
        url = "http://localhost:8001/api/v1/frontend/analysis/start-realtime"
        print(f"🚀 測試端點: {url}")
        
        # 準備請求數據
        data = {
            "task_name": "測試即時分析",
            "camera_id": "0",
            "model_id": "yolo11n.pt",
            "confidence": 0.5,
            "iou_threshold": 0.45,
            "description": "測試修復"
        }
        
        print(f"📤 發送請求數據: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"📥 回應狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 即時分析啟動成功!")
            print(f"📊 回應數據: {json.dumps(result, indent=2)}")
            
            if 'task_id' in result:
                print(f"🎯 任務ID: {result['task_id']}")
                print("✅ 'no running event loop' 錯誤已修復!")
            
        else:
            print(f"❌ 請求失敗: {response.status_code}")
            try:
                error_data = response.json()
                print(f"❌ 錯誤詳細: {json.dumps(error_data, indent=2)}")
            except:
                print(f"❌ 錯誤文本: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 請求超時")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 連接錯誤: {e}")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 即時分析修復測試")
    print("=" * 40)
    test_realtime_analysis_fix()
    print("\n💡 如果沒有 'no running event loop' 錯誤，表示修復成功")