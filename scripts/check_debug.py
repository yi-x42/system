import requests
import time

print("🔍 檢查debug訊息...")

try:
    # 測試啟動實時檢測
    response = requests.post("http://127.0.0.1:8000/api/v1/realtime/start/0")
    print(f"啟動檢測: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"任務ID: {data.get('task_id')}")
        print("等待5秒檢查debug訊息...")
        time.sleep(5)
        
        # 停止檢測
        stop_response = requests.post("http://127.0.0.1:8000/api/v1/realtime/stop/0")
        print(f"停止檢測: {stop_response.status_code}")
    else:
        print(f"錯誤: {response.text}")

except Exception as e:
    print(f"測試失敗: {e}")
