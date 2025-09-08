#!/usr/bin/env python3
"""
簡單測試解析度追蹤功能
"""

import requests
import json
import time

def simple_test():
    """簡單測試"""
    base_url = "http://localhost:8001/api/v1"
    
    print("=== 測試健康檢查 ===")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"健康檢查: {response.status_code}")
        if response.status_code == 200:
            print("✅ API 服務正常")
        else:
            print("❌ API 服務異常")
            return
    except Exception as e:
        print(f"❌ 無法連接到 API: {e}")
        return
    
    print("\n=== 測試資料庫統計 ===")
    try:
        response = requests.get(f"{base_url}/database/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("✅ 資料庫統計查詢成功")
            print(f"總任務數: {stats.get('total_tasks', 0)}")
            print(f"攝影機任務: {stats.get('realtime_tasks', 0)}")
            print(f"影片任務: {stats.get('video_tasks', 0)}")
        else:
            print(f"❌ 統計查詢失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 統計查詢錯誤: {e}")
    
    print("\n=== 測試任務列表 ===")
    try:
        response = requests.get(f"{base_url}/database/tasks?limit=5", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ 任務列表查詢成功")
            print(f"總任務數: {result.get('total', 0)}")
            
            tasks = result.get('data', [])
            if tasks:
                print("\n最新任務:")
                for i, task in enumerate(tasks[:3], 1):
                    print(f"  任務 {i}:")
                    print(f"    ID: {task.get('id')}")
                    print(f"    類型: {task.get('task_type')}")
                    print(f"    解析度: {task.get('source_width', '?')}x{task.get('source_height', '?')}")
                    print(f"    FPS: {task.get('source_fps', '?')}")
                    print(f"    狀態: {task.get('status')}")
            else:
                print("沒有找到任務記錄")
        else:
            print(f"❌ 任務查詢失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 任務查詢錯誤: {e}")

if __name__ == "__main__":
    print("開始簡單測試")
    print("=" * 50)
    simple_test()
    print("=" * 50)
    print("測試完成")
