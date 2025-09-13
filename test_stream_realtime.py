#!/usr/bin/env python3
"""測試即時影像串流修復"""

import requests
import time
import threading

def test_camera_stream():
    """測試攝影機串流端點"""
    print("🧪 測試即時影像串流修復...")
    
    try:
        # 測試攝影機串流端點
        url = "http://localhost:8001/api/v1/frontend/cameras/0/stream"
        print(f"📹 測試串流端點: {url}")
        
        response = requests.get(url, stream=True, timeout=10)
        
        if response.status_code == 200:
            print("✅ 串流端點回應正常")
            
            # 讀取前幾個數據塊
            chunk_count = 0
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    print(f"📦 收到數據塊 {chunk_count}: {len(chunk)} bytes")
                    
                    if chunk_count >= 3:  # 只測試前3個塊
                        break
            
            print(f"✅ 成功接收 {chunk_count} 個數據塊")
            
        else:
            print(f"❌ 串流端點回應錯誤: {response.status_code}")
            print(f"   錯誤詳細: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 請求超時 - 這可能是正常的，因為串流是持續的")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 連接錯誤: {e}")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def test_realtime_analysis():
    """測試即時分析功能"""
    print("\n🔄 測試即時分析功能...")
    
    try:
        # 啟動即時分析
        start_url = "http://localhost:8001/api/v1/frontend/cameras/0/realtime-analysis"
        print(f"🚀 啟動即時分析: {start_url}")
        
        response = requests.post(start_url, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 即時分析啟動成功: {result}")
            
            # 等待一下讓分析運行
            time.sleep(3)
            
            # 檢查任務狀態
            if 'task_id' in result:
                task_id = result['task_id']
                status_url = f"http://localhost:8001/api/v1/analysis-tasks/{task_id}"
                print(f"📊 檢查任務狀態: {status_url}")
                
                status_response = requests.get(status_url, timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"✅ 任務狀態: {status_data.get('status', 'unknown')}")
                else:
                    print(f"❌ 無法檢查任務狀態: {status_response.status_code}")
                
        else:
            print(f"❌ 即時分析啟動失敗: {response.status_code}")
            print(f"   錯誤詳細: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 請求超時")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 連接錯誤: {e}")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    print("🧪 開始即時影像串流修復測試...")
    print("=" * 50)
    
    # 測試串流端點
    test_camera_stream()
    
    # 測試即時分析
    test_realtime_analysis()
    
    print("\n✅ 測試完成！")
    print("💡 如果沒有錯誤，表示 'no running event loop' 問題已修復")