#!/usr/bin/env python3
"""
測試攝影機串流衝突
在實時檢測運行時嘗試訪問攝影機串流
"""

import requests
import time

def test_camera_stream_conflict():
    """測試攝影機串流衝突"""
    print("🧪 測試攝影機串流衝突")
    
    base_url = "http://localhost:8001/api/v1"
    
    try:
        # 1. 啟動實時檢測
        print("🚀 啟動實時檢測...")
        response = requests.post(f"{base_url}/realtime/start/0", timeout=10)
        if response.status_code == 200:
            print("✅ 實時檢測啟動成功")
            result = response.json()
            task_id = result.get('task_id')
            print(f"   任務 ID: {task_id}")
        else:
            print(f"❌ 實時檢測啟動失敗: {response.status_code}")
            print(f"   錯誤: {response.text}")
            return
        
        # 2. 等待一秒讓實時檢測穩定
        print("⏳ 等待實時檢測穩定...")
        time.sleep(2)
        
        # 3. 嘗試訪問攝影機串流
        print("📹 嘗試訪問攝影機串流...")
        try:
            stream_response = requests.get(f"{base_url}/frontend/cameras/0/stream", 
                                         timeout=5, stream=True)
            print(f"📊 串流回應狀態: {stream_response.status_code}")
            
            if stream_response.status_code == 200:
                print("✅ 攝影機串流可以正常訪問（使用共享流）")
                # 讀取一些數據來確認串流工作
                chunk_count = 0
                for chunk in stream_response.iter_content(chunk_size=1024):
                    chunk_count += 1
                    if chunk_count >= 3:  # 讀取3個塊就停止
                        break
                print(f"   成功讀取 {chunk_count} 個數據塊")
            else:
                print(f"❌ 攝影機串流失敗: {stream_response.status_code}")
                print(f"   錯誤: {stream_response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 攝影機串流請求異常: {e}")
        
        # 4. 嘗試停止實時檢測（雖然可能失敗）
        print("⏹️ 嘗試停止實時檢測...")
        try:
            stop_response = requests.post(f"{base_url}/realtime/stop/0", timeout=5)
            if stop_response.status_code == 200:
                print("✅ 實時檢測停止成功")
            else:
                print(f"⚠️ 實時檢測停止失敗: {stop_response.status_code}")
                print(f"   這是已知問題，不影響主要功能")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ 停止請求異常: {e}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 網絡請求錯誤: {e}")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
    
    print("🎉 測試完成")

if __name__ == "__main__":
    test_camera_stream_conflict()