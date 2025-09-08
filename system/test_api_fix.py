import requests
import json

print("🔍 測試修復後的隊列管理器...")

try:
    # 測試基本連接
    response = requests.get("http://127.0.0.1:8002/")
    print(f"✅ 基本連接測試: {response.status_code}")
    
    # 測試實時檢測啟動
    start_response = requests.post("http://127.0.0.1:8002/api/v1/realtime/start/0")
    print(f"📊 實時檢測啟動: {start_response.status_code}")
    
    if start_response.status_code == 200:
        data = start_response.json()
        print(f"✅ 成功啟動實時檢測:")
        print(f"   任務ID: {data.get('task_id')}")
        print("✅ 隊列管理器事件循環問題已修復！")
    else:
        print(f"❌ 啟動失敗: {start_response.status_code}")
        print(f"   回應: {start_response.text}")

except Exception as e:
    print(f"❌ 測試失敗: {e}")
