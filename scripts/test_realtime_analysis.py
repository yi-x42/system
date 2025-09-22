#!/usr/bin/env python3
"""
即時分析API測試工具
"""

import asyncio
import json
import requests
from datetime import datetime

API_BASE = "http://localhost:8001/api/v1"

def test_cameras():
    """測試攝影機API"""
    print("🔍 測試攝影機列表...")
    try:
        response = requests.get(f"{API_BASE}/frontend/cameras")
        if response.status_code == 200:
            cameras = response.json()
            print(f"✅ 找到 {len(cameras)} 個攝影機:")
            for cam in cameras:
                print(f"  - ID: {cam['id']}, 名稱: {cam['name']}, 狀態: {cam['status']}, 類型: {cam['camera_type']}")
            return cameras
        else:
            print(f"❌ 攝影機API錯誤: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 攝影機API異常: {e}")
        return []

def test_models():
    """測試模型API"""
    print("\n🔍 測試模型列表...")
    try:
        response = requests.get(f"{API_BASE}/frontend/models/list")
        if response.status_code == 200:
            models = response.json()
            print(f"✅ 找到 {len(models)} 個模型:")
            for model in models:
                print(f"  - ID: {model['id']}, 名稱: {model['name']}, 狀態: {model['status']}")
            return models
        else:
            print(f"❌ 模型API錯誤: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 模型API異常: {e}")
        return []

def test_realtime_analysis(camera_id, model_id):
    """測試即時分析API"""
    print(f"\n🚀 測試即時分析API...")
    print(f"攝影機ID: {camera_id}, 模型ID: {model_id}")
    
    payload = {
        "task_name": "測試即時分析任務",
        "camera_id": str(camera_id),
        "model_id": str(model_id),
        "confidence": 0.5,
        "iou_threshold": 0.45,
        "description": "自動化測試的即時分析任務"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/frontend/analysis/start-realtime",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"HTTP狀態碼: {response.status_code}")
        print(f"回應內容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 即時分析任務啟動成功!")
            print(f"任務ID: {result['task_id']}")
            print(f"狀態: {result['status']}")
            print(f"訊息: {result['message']}")
            return result
        else:
            print(f"❌ 即時分析API錯誤: {response.status_code}")
            try:
                error_info = response.json()
                print(f"錯誤詳情: {error_info}")
            except:
                print(f"錯誤內容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 即時分析API異常: {e}")
        return None

def test_task_stats():
    """測試任務統計API"""
    print(f"\n📊 測試任務統計...")
    try:
        response = requests.get(f"{API_BASE}/frontend/tasks/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ 任務統計:")
            print(f"  - 執行中: {stats.get('running', 0)}")
            print(f"  - 等待中: {stats.get('pending', 0)}")
            print(f"  - 已完成: {stats.get('completed', 0)}")
            print(f"  - 失敗: {stats.get('failed', 0)}")
            return stats
        else:
            print(f"❌ 任務統計API錯誤: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 任務統計API異常: {e}")
        return None

def main():
    """主測試函數"""
    print("=" * 60)
    print("🧪 YOLOv11 即時分析API完整測試")
    print("=" * 60)
    
    # 1. 測試攝影機
    cameras = test_cameras()
    if not cameras:
        print("❌ 無法獲取攝影機列表，測試終止")
        return
    
    # 2. 測試模型
    models = test_models()
    if not models:
        print("❌ 無法獲取模型列表，測試終止")
        return
    
    # 3. 選擇攝影機和模型
    camera_id = cameras[0]['id']
    model_id = models[0]['id']
    
    print(f"\n✅ 選擇測試用攝影機: {camera_id}")
    print(f"✅ 選擇測試用模型: {model_id}")
    
    # 4. 測試任務統計（啟動前）
    print(f"\n📈 啟動前任務統計:")
    test_task_stats()
    
    # 5. 測試即時分析
    result = test_realtime_analysis(camera_id, model_id)
    
    # 6. 測試任務統計（啟動後）
    if result:
        print(f"\n📈 啟動後任務統計:")
        test_task_stats()
        
        print(f"\n✅ 測試完成! 任務ID: {result['task_id']}")
        print("ℹ️  您可以檢查任務是否正在執行即時檢測")
    else:
        print(f"\n❌ 測試失敗!")
    
    print("=" * 60)

if __name__ == "__main__":
    main()