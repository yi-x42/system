#!/usr/bin/env python3
"""
測試前端模型選擇修復是否生效
"""

import requests
import json
import time

def test_frontend_model_apis():
    """測試前端模型相關API"""
    base_url = "http://localhost:8001/api/v1"
    
    print("=" * 60)
    print("🧪 前端模型API測試")
    print("=" * 60)
    
    # 1. 測試模型列表API
    print("1️⃣ 測試模型列表API...")
    try:
        response = requests.get(f"{base_url}/frontend/models/list")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 模型列表API成功")
            print(f"   📊 格式: {type(data)}")
            if isinstance(data, dict) and 'value' in data:
                print(f"   📝 包含字段: {list(data.keys())}")
                print(f"   📈 模型數量: {data.get('Count', len(data.get('value', [])))}")
                if data.get('value'):
                    print(f"   🎯 第一個模型: {data['value'][0].get('name', 'Unknown')}")
            else:
                print(f"   ⚠️ 數據格式: {data}")
        else:
            print(f"   ❌ 模型列表API失敗: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 模型列表API錯誤: {e}")
    
    # 2. 測試活動模型API
    print(f"\n2️⃣ 測試活動模型API...")
    try:
        response = requests.get(f"{base_url}/frontend/models/active")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 活動模型API成功")
            print(f"   📊 格式: {type(data)}")
            if isinstance(data, dict) and 'value' in data:
                print(f"   📝 包含字段: {list(data.keys())}")
                print(f"   📈 活動模型數量: {data.get('Count', len(data.get('value', [])))}")
                if data.get('value'):
                    for model in data['value']:
                        print(f"      🟢 {model.get('name', 'Unknown')} ({model.get('id', 'Unknown')})")
            else:
                print(f"   ⚠️ 數據格式: {data}")
        else:
            print(f"   ❌ 活動模型API失敗: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 活動模型API錯誤: {e}")
    
    # 3. 模擬前端數據處理
    print(f"\n3️⃣ 模擬前端數據處理...")
    try:
        # 獲取原始數據
        models_response = requests.get(f"{base_url}/frontend/models/list")
        active_response = requests.get(f"{base_url}/frontend/models/active")
        
        if models_response.status_code == 200 and active_response.status_code == 200:
            models_data = models_response.json()
            active_data = active_response.json()
            
            # 模擬前端處理邏輯
            models_list = models_data.get('value', models_data) if isinstance(models_data, dict) else models_data
            active_list = active_data.get('value', active_data) if isinstance(active_data, dict) else active_data
            
            print(f"   📝 處理後的模型列表: {len(models_list)} 個模型")
            print(f"   📝 處理後的活動模型: {len(active_list)} 個模型")
            
            if active_list and len(active_list) > 0:
                print(f"   ✅ 有活動模型可選擇，按鈕應該可以點擊")
                print(f"   🎯 可選模型:")
                for model in active_list:
                    print(f"      - {model.get('id', 'Unknown')}: {model.get('name', 'Unknown')}")
            else:
                print(f"   ❌ 沒有活動模型，按鈕會被禁用")
        else:
            print(f"   ❌ API調用失敗")
    except Exception as e:
        print(f"   ❌ 前端處理模擬錯誤: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 前端模型API測試完成")
    print("=" * 60)

if __name__ == "__main__":
    test_frontend_model_apis()
