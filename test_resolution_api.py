#!/usr/bin/env python3
"""
測試解析度追蹤 API 功能
"""

import requests
import json
import time

def test_realtime_detection_resolution():
    """測試實時檢測解析度追蹤"""
    print("=== 測試實時檢測解析度追蹤 ===")
    
    base_url = "http://localhost:8001/api/v1"
    
    try:
        # 啟動實時檢測
        start_data = {
            "camera_index": 0,
            "camera_type": "USB"
        }
        
        print("啟動實時檢測...")
        response = requests.post(f"{base_url}/realtime/start", json=start_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 實時檢測啟動成功")
            print(f"任務 ID: {result.get('task_id')}")
            task_id = result.get('task_id')
            
            # 等待一會兒讓系統處理
            time.sleep(2)
            
            # 查詢任務詳細信息
            print("\n查詢任務詳細信息...")
            response = requests.get(f"{base_url}/database/tasks/{task_id}")
            
            if response.status_code == 200:
                task_info = response.json()
                print(f"✅ 任務信息獲取成功")
                print(f"任務類型: {task_info.get('task_type')}")
                print(f"來源寬度: {task_info.get('source_width')}")
                print(f"來源高度: {task_info.get('source_height')}")
                print(f"來源FPS: {task_info.get('source_fps')}")
                print(f"來源資訊: {json.dumps(task_info.get('source_info', {}), indent=2, ensure_ascii=False)}")
                
                # 驗證解析度是否正確
                if task_info.get('source_width') and task_info.get('source_height'):
                    print(f"✅ 解析度追蹤成功: {task_info.get('source_width')}x{task_info.get('source_height')}")
                else:
                    print("❌ 解析度追蹤失敗")
                    
            else:
                print(f"❌ 無法獲取任務信息: {response.status_code}")
                print(response.text)
                
            # 停止實時檢測
            print("\n停止實時檢測...")
            response = requests.post(f"{base_url}/realtime/stop")
            if response.status_code == 200:
                print("✅ 實時檢測已停止")
            else:
                print(f"❌ 停止失敗: {response.status_code}")
                
        else:
            print(f"❌ 實時檢測啟動失敗: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def test_database_query_api():
    """測試資料庫查詢 API"""
    print("\n=== 測試資料庫查詢 API ===")
    
    base_url = "http://localhost:8001/api/v1"
    
    try:
        # 查詢所有任務
        print("查詢所有分析任務...")
        response = requests.get(f"{base_url}/database/tasks")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 任務查詢成功")
            print(f"總任務數: {result.get('total', 0)}")
            
            tasks = result.get('data', [])
            if tasks:
                print("\n最新任務:")
                for task in tasks[:3]:  # 只顯示前3個
                    print(f"  ID: {task.get('id')}")
                    print(f"  類型: {task.get('task_type')}")
                    print(f"  解析度: {task.get('source_width')}x{task.get('source_height')}")
                    print(f"  FPS: {task.get('source_fps')}")
                    print(f"  狀態: {task.get('status')}")
                    print("  ---")
            else:
                print("沒有找到任務")
                
        else:
            print(f"❌ 任務查詢失敗: {response.status_code}")
            print(response.text)
            
        # 查詢統計資訊
        print("\n查詢系統統計...")
        response = requests.get(f"{base_url}/database/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 統計查詢成功")
            print(f"總任務數: {stats.get('total_tasks', 0)}")
            print(f"攝影機任務: {stats.get('realtime_tasks', 0)}")
            print(f"影片任務: {stats.get('video_tasks', 0)}")
            
            # 顯示解析度統計
            resolution_stats = stats.get('resolution_stats', {})
            if resolution_stats:
                print("\n解析度統計:")
                for resolution, count in resolution_stats.items():
                    print(f"  {resolution}: {count} 個任務")
                    
        else:
            print(f"❌ 統計查詢失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 資料庫測試失敗: {e}")

def main():
    """主函數"""
    print("開始解析度追蹤 API 測試")
    print("=" * 60)
    
    # 測試實時檢測解析度追蹤
    test_realtime_detection_resolution()
    
    # 測試資料庫查詢 API
    test_database_query_api()
    
    print("=" * 60)
    print("API 測試完成")

if __name__ == "__main__":
    main()
