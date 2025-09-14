#!/usr/bin/env python3
"""
測試暫停->停止流程的外鍵約束錯誤修復
"""

import asyncio
import time
import requests
from datetime import datetime


BASE_URL = "http://localhost:8001/api/v1"


def start_realtime_detection():
    """啟動即時檢測任務"""
    print("🚀 啟動即時檢測任務...")
    
    url = f"{BASE_URL}/frontend/analysis/start-realtime"
    payload = {
        "task_name": "暫停停止測試任務",
        "camera_id": "79",  # 使用測試攝影機
        "model_id": "yolo11n",
        "confidence": 0.5,
        "iou_threshold": 0.45,
        "description": "測試暫停->停止流程是否會產生外鍵約束錯誤"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ 即時檢測已啟動，任務ID: {task_id}")
            return task_id
        else:
            print(f"❌ 啟動失敗: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 啟動即時檢測失敗: {e}")
        return None


def get_task_info(task_id):
    """獲取任務資訊"""
    try:
        response = requests.get(f"{BASE_URL}/database/analysis_tasks?limit=10")
        if response.status_code == 200:
            tasks = response.json().get('data', [])
            for task in tasks:
                if task.get('id') == int(task_id):
                    return task
        return None
    except Exception as e:
        print(f"❌ 獲取任務資訊失敗: {e}")
        return None


def get_detection_results_count(task_id):
    """獲取檢測結果數量"""
    try:
        response = requests.get(f"{BASE_URL}/database/detection_results?task_id={task_id}&limit=1")
        if response.status_code == 200:
            return response.json().get('total', 0)
        return 0
    except Exception as e:
        print(f"❌ 獲取檢測結果失敗: {e}")
        return 0


def pause_task(task_id):
    """暫停任務"""
    print(f"⏸️ 暫停任務 {task_id}...")
    try:
        response = requests.put(f"{BASE_URL}/frontend/tasks/{task_id}/toggle")
        if response.status_code == 200:
            print("✅ 任務暫停請求成功")
            return True
        else:
            print(f"❌ 暫停失敗: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 暫停任務失敗: {e}")
        return False


def stop_task(task_id):
    """停止任務"""
    print(f"⏹️ 停止任務 {task_id}...")
    try:
        response = requests.put(f"{BASE_URL}/frontend/tasks/{task_id}/stop")
        if response.status_code == 200:
            print("✅ 任務停止請求成功")
            return True
        else:
            print(f"❌ 停止失敗: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 停止任務失敗: {e}")
        return False


def main():
    """主測試流程"""
    print("🧪 測試暫停->停止流程的外鍵約束錯誤修復")
    print("=" * 60)
    
    # 1. 啟動即時檢測
    task_id = start_realtime_detection()
    if not task_id:
        print("❌ 無法啟動測試，結束測試")
        return
    
    print(f"\n⏰ 等待 10 秒讓檢測運行並產生一些結果...")
    time.sleep(10)
    
    # 2. 檢查初始檢測結果數量
    initial_count = get_detection_results_count(task_id)
    print(f"📊 初始檢測結果數量: {initial_count}")
    
    # 3. 暫停任務
    if not pause_task(task_id):
        print("❌ 暫停失敗，跳過後續測試")
        return
    
    # 驗證任務狀態
    task_info = get_task_info(task_id)
    if task_info:
        print(f"📊 暫停後任務狀態: {task_info['status']}")
        if task_info['status'] == 'paused':
            print("✅ 資料庫狀態已更新為 paused")
        else:
            print(f"⚠️ 資料庫狀態異常: {task_info['status']}")
    
    print(f"\n⏰ 等待 5 秒，檢查暫停期間檢測是否停止...")
    time.sleep(5)
    
    paused_count = get_detection_results_count(task_id)
    print(f"📊 暫停期間檢測結果數量: {paused_count}")
    
    # 4. 停止任務（關鍵測試點）
    print(f"\n🔥 關鍵測試：停止已暫停的任務...")
    if not stop_task(task_id):
        print("❌ 停止失敗")
        return
    
    # 驗證任務狀態
    task_info = get_task_info(task_id)
    if task_info:
        print(f"📊 停止後任務狀態: {task_info['status']}")
        if task_info['status'] in ['completed', 'stopped']:
            print("✅ 任務狀態已正確更新")
        else:
            print(f"⚠️ 任務狀態異常: {task_info['status']}")
    else:
        print("⚠️ 無法獲取任務資訊（可能已被刪除）")
    
    # 5. 關鍵測試：等待觀察是否還有外鍵約束錯誤
    print(f"\n🔍 關鍵測試：等待 15 秒觀察是否還有外鍵約束錯誤...")
    print("請觀察後端日誌，看是否出現 ForeignKeyViolation 錯誤")
    
    for i in range(15):
        time.sleep(1)
        current_count = get_detection_results_count(task_id)
        if i % 5 == 0:
            print(f"  {15-i} 秒後結束，當前檢測結果: {current_count}")
    
    final_count = get_detection_results_count(task_id)
    print(f"\n📊 最終檢測結果統計:")
    print(f"  初始結果數量: {initial_count}")
    print(f"  暫停時結果數量: {paused_count}")
    print(f"  最終結果數量: {final_count}")
    
    if final_count == paused_count:
        print("✅ 完美！停止後沒有新增檢測結果，說明檢測已正確停止")
    elif final_count > paused_count:
        print("⚠️ 停止後仍有新的檢測結果，可能存在停滯問題")
    
    print(f"\n🏁 測試完成！")
    print("如果後端日誌中沒有出現 'ForeignKeyViolation' 錯誤，")
    print("說明外鍵約束錯誤修復成功！")


if __name__ == "__main__":
    main()