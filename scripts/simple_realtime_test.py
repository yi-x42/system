import requests
import time

print("🧪 簡單測試開始")

try:
    # 健康檢查
    resp = requests.get("http://localhost:8001/api/v1/health/", timeout=5)
    print(f"健康檢查結果: {resp.status_code}")
    if resp.status_code == 200:
        print(f"✅ 系統健康: {resp.json()}")
    
    # 啟動實時檢測
    print("\n🚀 啟動實時檢測...")
    resp = requests.post("http://localhost:8001/api/v1/realtime/start/0", timeout=10)
    print(f"啟動結果: {resp.status_code}")
    if resp.status_code == 200:
        result = resp.json()
        print(f"✅ 啟動成功: {result}")
        
        # 等待 3 秒
        print("⏳ 等待 3 秒...")
        time.sleep(3)
        
        # 停止檢測
        print("⏹️ 停止檢測...")
        resp = requests.post("http://localhost:8001/api/v1/realtime/stop/0", timeout=10)
        print(f"停止結果: {resp.status_code}")
        if resp.status_code == 200:
            print(f"✅ 停止成功: {resp.json()}")
    else:
        print(f"❌ 啟動失敗: {resp.status_code} - {resp.text}")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")

print("🎉 測試完成")
