#!/usr/bin/env python3
"""
測試即時分析 API 修復
"""

import requests
import json

def test_realtime_analysis():
    """測試即時分析功能"""
    print("🔍 測試即時分析 API 修復...")
    
    base_url = "http://localhost:8001/api/v1"
    
    # 1. 首先獲取可用的攝影機列表
    print("\n1. 獲取攝影機列表...")
    try:
        cameras_response = requests.get(f"{base_url}/frontend/cameras")
        if cameras_response.status_code == 200:
            cameras = cameras_response.json()
            print(f"✅ 找到 {len(cameras)} 個攝影機")
            if cameras:
                camera_id = str(cameras[0]['id'])
                print(f"   選擇攝影機: {cameras[0]['name']} (ID: {camera_id})")
            else:
                print("❌ 沒有可用的攝影機")
                return
        else:
            print(f"❌ 獲取攝影機失敗: {cameras_response.status_code}")
            return
    except Exception as e:
        print(f"❌ 攝影機 API 錯誤: {e}")
        return
    
    # 2. 獲取可用的模型列表
    print("\n2. 獲取 YOLO 模型列表...")
    try:
        models_response = requests.get(f"{base_url}/frontend/models")
        if models_response.status_code == 200:
            models_data = models_response.json()
            # 處理可能的嵌套結構
            models = models_data.get('value', models_data) if isinstance(models_data, dict) else models_data
            print(f"✅ 找到 {len(models)} 個模型")
            if models:
                model_id = models[0]['id']
                print(f"   選擇模型: {models[0]['name']} (ID: {model_id})")
            else:
                print("❌ 沒有可用的模型")
                return
        else:
            print(f"❌ 獲取模型失敗: {models_response.status_code}")
            return
    except Exception as e:
        print(f"❌ 模型 API 錯誤: {e}")
        return
    
    # 3. 測試即時分析 API
    print("\n3. 測試即時分析 API...")
    realtime_data = {
        "task_name": "測試即時分析_API修復驗證",
        "camera_id": camera_id,
        "model_id": model_id,
        "confidence": 0.5,
        "iou_threshold": 0.45,
        "description": "測試路徑修復後的即時分析功能"
    }
    
    print(f"   請求數據: {json.dumps(realtime_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{base_url}/frontend/analysis/start-realtime",
            json=realtime_data,
            timeout=30
        )
        
        print(f"\n📊 API 響應狀態: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 即時分析啟動成功！")
            print(f"   任務 ID: {result.get('task_id', 'N/A')}")
            print(f"   狀態: {result.get('status', 'N/A')}")
            print(f"   訊息: {result.get('message', 'N/A')}")
            print(f"   攝影機資訊: {result.get('camera_info', {}).get('name', 'N/A')}")
            print(f"   模型資訊: {result.get('model_info', {}).get('filename', 'N/A')}")
        else:
            print(f"❌ 即時分析啟動失敗: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   錯誤詳情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"   錯誤內容: {response.text}")
                
    except requests.RequestException as e:
        print(f"❌ API 請求錯誤: {e}")
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")

if __name__ == "__main__":
    test_realtime_analysis()