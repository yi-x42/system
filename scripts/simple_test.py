import requests
import json

try:
    # 測試基本連接
    print("測試API連接...")
    response = requests.get("http://26.86.64.166:8001/docs", timeout=5)
    print(f"API文檔訪問: {response.status_code}")
    
    # 測試實時檢測API
    print("\n測試實時檢測API...")
    response = requests.post("http://26.86.64.166:8001/api/v1/realtime/start/0", timeout=10)
    print(f"啟動實時檢測: {response.status_code}")
    print(f"回應內容: {response.text}")
    
except Exception as e:
    print(f"錯誤: {e}")
