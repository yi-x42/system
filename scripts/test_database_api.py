#!/usr/bin/env python3
"""
測試新的資料庫查詢 API
"""

import requests
import json
import time

def test_database_apis():
    """測試資料庫查詢 API"""
    base_url = "http://localhost:8001"
    
    print("🔍 測試資料庫查詢 API...")
    
    # 測試 1: 統計資訊
    print("\n1. 測試統計資訊 API")
    try:
        response = requests.get(f"{base_url}/api/v1/database/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 統計資訊獲取成功")
            print(f"   📊 總任務數: {data['data']['summary']['total_tasks']}")
            print(f"   📊 總檢測數: {data['data']['summary']['total_detections']}")
        else:
            print(f"   ❌ 統計資訊失敗: {response.status_code}")
            print(f"   詳情: {response.text}")
    except Exception as e:
        print(f"   ❌ 統計資訊錯誤: {e}")
    
    # 測試 2: 分析任務表
    print("\n2. 測試分析任務表查詢")
    try:
        response = requests.get(f"{base_url}/api/v1/database/tasks?limit=10", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 任務表查詢成功")
            print(f"   📋 返回任務數: {len(data['data'])}")
            print(f"   📋 總任務數: {data['pagination']['total']}")
            if data['data']:
                print(f"   📋 最新任務: {data['data'][0]['task_type']} - {data['data'][0]['status']}")
        else:
            print(f"   ❌ 任務表查詢失敗: {response.status_code}")
            print(f"   詳情: {response.text}")
    except Exception as e:
        print(f"   ❌ 任務表查詢錯誤: {e}")
    
    # 測試 3: 檢測結果表
    print("\n3. 測試檢測結果表查詢")
    try:
        response = requests.get(f"{base_url}/api/v1/database/detection-results?limit=20", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 檢測結果查詢成功")
            print(f"   🎯 返回檢測數: {len(data['data'])}")
            print(f"   🎯 總檢測數: {data['pagination']['total']}")
            if data['data']:
                print(f"   🎯 最新檢測: {data['data'][0]['object_type']} (信心度: {data['data'][0]['confidence']:.3f})")
        else:
            print(f"   ❌ 檢測結果查詢失敗: {response.status_code}")
            print(f"   詳情: {response.text}")
    except Exception as e:
        print(f"   ❌ 檢測結果查詢錯誤: {e}")
    
    # 測試 4: 過濾功能
    print("\n4. 測試過濾功能")
    try:
        # 測試按物件類型過濾
        response = requests.get(f"{base_url}/api/v1/database/detection-results?object_type=person&limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 按物件類型過濾成功")
            print(f"   👤 Person檢測數: {len(data['data'])}")
        
        # 測試按信心度過濾
        response = requests.get(f"{base_url}/api/v1/database/detection-results?min_confidence=0.5&limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 按信心度過濾成功")
            print(f"   📈 高信心度檢測數: {len(data['data'])}")
        
    except Exception as e:
        print(f"   ❌ 過濾功能錯誤: {e}")
    
    print("\n📋 API 端點列表:")
    print("   📊 統計資訊: GET /api/v1/database/stats")
    print("   📋 分析任務: GET /api/v1/database/tasks")
    print("   🎯 檢測結果: GET /api/v1/database/detection-results")
    print("   🔍 任務詳情: GET /api/v1/database/tasks/{task_id}")
    print("   📚 API 文檔: http://localhost:8001/docs")
    
    return True

if __name__ == "__main__":
    print("🧪 資料庫查詢 API 測試")
    print("=" * 50)
    
    # 等待系統啟動
    print("⏳ 等待系統就緒...")
    time.sleep(2)
    
    try:
        success = test_database_apis()
        if success:
            print("\n✅ 資料庫查詢 API 測試完成！")
            print("🔗 請訪問 http://localhost:8001/docs 查看完整 API 文檔")
        else:
            print("\n⚠️ 部分測試失敗，請檢查系統狀態")
    except KeyboardInterrupt:
        print("\n⏹️ 測試中斷")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
