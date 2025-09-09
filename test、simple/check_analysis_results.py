#!/usr/bin/env python3
"""
檢查分析結果 - 查看任務狀態和檢測結果
"""

import requests
import time
import json

def check_task_status(task_id):
    """檢查任務狀態"""
    try:
        response = requests.get(f"http://localhost:8001/api/v1/tasks/{task_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 任務 {task_id} 狀態:")
            print(f"   狀態: {data.get('status', 'unknown')}")
            print(f"   任務類型: {data.get('task_type', 'unknown')}")
            print(f"   開始時間: {data.get('start_time', 'N/A')}")
            print(f"   結束時間: {data.get('end_time', 'N/A')}")
            return data.get('status')
        else:
            print(f"❌ 無法獲取任務狀態: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return None

def check_detection_results(task_id):
    """檢查檢測結果"""
    try:
        response = requests.get(f"http://localhost:8001/api/v1/tasks/{task_id}/results")
        if response.status_code == 200:
            data = response.json()
            detections = data.get('detections', [])
            statistics = data.get('statistics', {})
            
            print(f"🔍 檢測結果:")
            print(f"   總檢測數: {len(detections)}")
            print(f"   統計資料: {json.dumps(statistics, indent=2, ensure_ascii=False)}")
            
            # 顯示前5個檢測結果
            if detections:
                print(f"   前5個檢測結果:")
                for i, detection in enumerate(detections[:5]):
                    print(f"     {i+1}. 幀 {detection.get('frame_number', 'N/A')}: "
                          f"{detection.get('object_type', 'unknown')} "
                          f"(信心度: {detection.get('confidence', 0):.2f})")
            
            return len(detections)
        else:
            print(f"❌ 無法獲取檢測結果: {response.status_code}")
            return 0
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return 0

def main():
    print("=" * 50)
    print("🔍 檢查分析結果")
    print("=" * 50)
    
    # 檢查最新的任務 (ID 74)
    task_id = 74
    
    print(f"🕐 檢查任務 {task_id} 的執行狀態...")
    status = check_task_status(task_id)
    
    if status:
        print(f"\n⏱️ 等待任務完成...")
        
        # 等待任務完成，最多等待30秒
        max_wait = 30
        wait_time = 0
        
        while wait_time < max_wait and status in ['scheduled', 'running', 'pending']:
            time.sleep(2)
            wait_time += 2
            status = check_task_status(task_id)
            print(f"   等待中... ({wait_time}s) 狀態: {status}")
        
        print(f"\n📋 最終狀態: {status}")
        
        # 檢查檢測結果
        print(f"\n" + "-" * 30)
        detection_count = check_detection_results(task_id)
        
        if detection_count > 0:
            print(f"✅ 分析完成！找到 {detection_count} 個檢測結果")
        elif status == 'completed':
            print(f"⚠️ 任務完成但沒有檢測結果")
        else:
            print(f"❌ 任務未完成或發生錯誤")
    
    print("=" * 50)
    print("✅ 檢查完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
