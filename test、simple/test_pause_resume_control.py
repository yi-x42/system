#!/usr/bin/env python3
"""
測試暫停/恢復和停止功能是否真正控制檢測服務
"""

import requests
import json
import time
from datetime import datetime

# API 基礎地址
BASE_URL = "http://localhost:8001/api/v1"

def print_separator(title=""):
    print("\n" + "="*60)
    if title:
        print(f"  {title}")
        print("="*60)

def get_task_info(task_id):
    """獲取任務詳細資訊"""
    try:
        response = requests.get(f"{BASE_URL}/frontend/tasks")
        response.raise_for_status()
        tasks = response.json()
        
        for task in tasks:
            if str(task['id']) == str(task_id):
                return task
        return None
    except Exception as e:
        print(f"❌ 獲取任務資訊失敗: {e}")
        return None

def get_detection_results_count(task_id):
    """獲取檢測結果數量"""
    try:
        response = requests.get(f"{BASE_URL}/realtime/detection-results/{task_id}")
        if response.status_code == 200:
            results = response.json()
            return len(results.get('results', []))
        return 0
    except Exception as e:
        print(f"⚠️  獲取檢測結果失敗: {e}")
        return 0

def test_pause_resume_functionality():
    """測試暫停/恢復功能是否真正停止檢測"""
    print_separator("測試暫停/恢復功能")
    
    try:
        # 1. 獲取運行中的任務
        print("📋 尋找運行中的任務...")
        response = requests.get(f"{BASE_URL}/frontend/tasks")
        response.raise_for_status()
        tasks = response.json()
        
        running_task = None
        for task in tasks:
            if task['status'] == 'running':
                running_task = task
                break
        
        if not running_task:
            print("❌ 沒有找到運行中的任務，請先啟動一個即時分析任務")
            return
        
        task_id = running_task['id']
        print(f"🎯 找到運行中的任務: ID = {task_id}")
        
        # 2. 獲取當前檢測結果數量
        initial_count = get_detection_results_count(task_id)
        print(f"📊 當前檢測結果數量: {initial_count}")
        
        # 3. 等待幾秒，讓檢測持續運行
        print("⏰ 等待5秒讓檢測持續運行...")
        time.sleep(5)
        
        # 4. 再次檢查檢測結果數量
        after_wait_count = get_detection_results_count(task_id)
        print(f"📊 5秒後檢測結果數量: {after_wait_count}")
        
        if after_wait_count > initial_count:
            print("✅ 檢測正在持續進行")
        else:
            print("⚠️  檢測似乎沒有產生新結果")
        
        # 5. 暫停任務
        print(f"\n⏸️  暫停任務 {task_id}...")
        toggle_response = requests.put(f"{BASE_URL}/frontend/tasks/{task_id}/toggle")
        toggle_response.raise_for_status()
        toggle_data = toggle_response.json()
        
        print(f"✅ 暫停回應: {toggle_data['old_status']} → {toggle_data['new_status']}")
        
        # 6. 驗證任務狀態已變更
        task_info = get_task_info(task_id)
        if task_info and task_info['status'] == 'paused':
            print("✅ 資料庫狀態已更新為 paused")
        else:
            print(f"❌ 資料庫狀態更新失敗，當前狀態: {task_info['status'] if task_info else 'unknown'}")
        
        # 7. 等待一段時間，檢查檢測是否真的停止了
        paused_count = get_detection_results_count(task_id)
        print(f"📊 暫停時檢測結果數量: {paused_count}")
        
        print("⏰ 等待10秒檢查檢測是否真的停止...")
        time.sleep(10)
        
        # 8. 檢查暫停期間是否有新的檢測結果
        after_pause_count = get_detection_results_count(task_id)
        print(f"📊 暫停10秒後檢測結果數量: {after_pause_count}")
        
        if after_pause_count == paused_count:
            print("✅ 暫停期間沒有新的檢測結果，暫停功能正常！")
        else:
            print(f"❌ 暫停期間仍有新檢測結果 (+{after_pause_count - paused_count})，暫停功能異常！")
        
        # 9. 恢復任務
        print(f"\n▶️  恢復任務 {task_id}...")
        resume_response = requests.put(f"{BASE_URL}/frontend/tasks/{task_id}/toggle")
        resume_response.raise_for_status()
        resume_data = resume_response.json()
        
        print(f"✅ 恢復回應: {resume_data['old_status']} → {resume_data['new_status']}")
        
        # 10. 等待一段時間，檢查檢測是否恢復
        print("⏰ 等待5秒檢查檢測是否恢復...")
        time.sleep(5)
        
        after_resume_count = get_detection_results_count(task_id)
        print(f"📊 恢復5秒後檢測結果數量: {after_resume_count}")
        
        if after_resume_count > after_pause_count:
            print("✅ 恢復後檢測繼續進行，恢復功能正常！")
        else:
            print("❌ 恢復後檢測沒有繼續，恢復功能異常！")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

def test_stop_functionality():
    """測試停止功能是否真正停止檢測"""
    print_separator("測試停止功能")
    
    try:
        # 1. 獲取運行中的任務
        print("📋 尋找運行中的任務...")
        response = requests.get(f"{BASE_URL}/frontend/tasks")
        response.raise_for_status()
        tasks = response.json()
        
        running_task = None
        for task in tasks:
            if task['status'] in ['running', 'paused']:
                running_task = task
                break
        
        if not running_task:
            print("❌ 沒有找到可停止的任務")
            return
        
        task_id = running_task['id']
        print(f"🎯 找到任務: ID = {task_id}, 狀態 = {running_task['status']}")
        
        # 2. 獲取當前檢測結果數量
        before_stop_count = get_detection_results_count(task_id)
        print(f"📊 停止前檢測結果數量: {before_stop_count}")
        
        # 3. 停止任務
        print(f"\n🛑 停止任務 {task_id}...")
        stop_response = requests.put(f"{BASE_URL}/frontend/tasks/{task_id}/stop")
        stop_response.raise_for_status()
        stop_data = stop_response.json()
        
        print(f"✅ 停止回應: {stop_data}")
        
        # 4. 驗證任務狀態已變更
        time.sleep(2)  # 等待狀態更新
        task_info = get_task_info(task_id)
        if task_info:
            print(f"📊 停止後任務狀態: {task_info['status']}")
            if task_info['status'] in ['completed', 'stopped']:
                print("✅ 任務狀態已正確更新")
            else:
                print(f"❌ 任務狀態更新異常: {task_info['status']}")
        
        # 5. 等待一段時間，檢查是否真的停止檢測
        print("⏰ 等待10秒檢查檢測是否真的停止...")
        time.sleep(10)
        
        after_stop_count = get_detection_results_count(task_id)
        print(f"📊 停止10秒後檢測結果數量: {after_stop_count}")
        
        if after_stop_count == before_stop_count:
            print("✅ 停止後沒有新的檢測結果，停止功能正常！")
        else:
            print(f"❌ 停止後仍有新檢測結果 (+{after_stop_count - before_stop_count})，停止功能異常！")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

def main():
    """主測試函式"""
    print("🧪 測試暫停/恢復和停止功能的實際控制效果")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試暫停/恢復功能
    test_pause_resume_functionality()
    
    # 測試停止功能
    test_stop_functionality()
    
    print_separator("測試完成")
    print("✅ 暫停/恢復和停止功能測試完成！")

if __name__ == "__main__":
    main()