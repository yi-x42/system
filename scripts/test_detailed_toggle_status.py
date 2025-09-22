#!/usr/bin/env python3
"""
詳細測試任務狀態切換功能
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

def get_task_status(task_id):
    """獲取指定任務的狀態"""
    try:
        response = requests.get(f"{BASE_URL}/frontend/tasks")
        response.raise_for_status()
        tasks = response.json()
        
        for task in tasks:
            if task['id'] == task_id:
                return task['status']
        return None
    except Exception as e:
        print(f"❌ 獲取任務狀態失敗: {e}")
        return None

def detailed_status_test():
    """詳細的狀態切換測試"""
    print_separator("詳細任務狀態切換測試")
    
    try:
        # 1. 獲取現有任務列表
        print("📋 獲取現有任務列表...")
        response = requests.get(f"{BASE_URL}/frontend/tasks")
        response.raise_for_status()
        tasks = response.json()
        
        print(f"找到 {len(tasks)} 個任務:")
        for task in tasks:
            print(f"  - 任務 {task['id']}: {task['status']} ({task.get('name', 'No Name')})")
        
        if not tasks:
            print("❌ 沒有找到任何任務")
            return
        
        # 選擇第一個任務進行測試
        task_id = tasks[0]['id']
        print(f"\n🎯 選擇任務進行測試: ID = {task_id}")
        
        # 2. 獲取初始狀態
        initial_status = get_task_status(task_id)
        print(f"📊 初始狀態: {initial_status}")
        
        # 3. 第一次切換
        print(f"\n🔄 執行第一次狀態切換...")
        toggle_response = requests.put(f"{BASE_URL}/frontend/tasks/{task_id}/toggle")
        
        if toggle_response.status_code != 200:
            print(f"❌ 切換失敗，狀態碼: {toggle_response.status_code}")
            print(f"響應內容: {toggle_response.text}")
            return
        
        toggle_data = toggle_response.json()
        print(f"API 回應:")
        print(f"  old_status: {toggle_data['old_status']}")
        print(f"  new_status: {toggle_data['new_status']}")
        print(f"  message: {toggle_data['message']}")
        
        # 4. 驗證第一次切換
        time.sleep(0.5)  # 等待資料庫更新
        after_first_status = get_task_status(task_id)
        print(f"✅ 第一次切換後的實際狀態: {after_first_status}")
        
        if after_first_status == toggle_data['new_status']:
            print("✅ 第一次切換驗證成功！")
        else:
            print(f"❌ 第一次切換驗證失敗！預期: {toggle_data['new_status']}, 實際: {after_first_status}")
        
        # 5. 第二次切換
        print(f"\n🔄 執行第二次狀態切換...")
        toggle2_response = requests.put(f"{BASE_URL}/frontend/tasks/{task_id}/toggle")
        toggle2_response.raise_for_status()
        toggle2_data = toggle2_response.json()
        
        print(f"API 回應:")
        print(f"  old_status: {toggle2_data['old_status']}")
        print(f"  new_status: {toggle2_data['new_status']}")
        print(f"  message: {toggle2_data['message']}")
        
        # 6. 驗證第二次切換
        time.sleep(0.5)  # 等待資料庫更新
        after_second_status = get_task_status(task_id)
        print(f"✅ 第二次切換後的實際狀態: {after_second_status}")
        
        if after_second_status == toggle2_data['new_status']:
            print("✅ 第二次切換驗證成功！")
        else:
            print(f"❌ 第二次切換驗證失敗！預期: {toggle2_data['new_status']}, 實際: {after_second_status}")
        
        # 7. 總結
        print(f"\n📊 狀態變化總結:")
        print(f"  初始狀態: {initial_status}")
        print(f"  第一次切換: {initial_status} → {after_first_status}")
        print(f"  第二次切換: {after_first_status} → {after_second_status}")
        
        # 檢查是否回到原始狀態
        if after_second_status == initial_status:
            print("✅ 成功回到原始狀態！雙向切換正常工作")
        else:
            print(f"⚠️  最終狀態 ({after_second_status}) 與初始狀態 ({initial_status}) 不同")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API 請求錯誤: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"錯誤詳情: {error_data}")
            except:
                print(f"響應內容: {e.response.text}")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

def test_all_task_types():
    """測試不同狀態的任務"""
    print_separator("測試不同狀態任務的切換")
    
    try:
        response = requests.get(f"{BASE_URL}/frontend/tasks")
        response.raise_for_status()
        tasks = response.json()
        
        status_groups = {}
        for task in tasks:
            status = task['status']
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(task)
        
        print("按狀態分組的任務:")
        for status, task_list in status_groups.items():
            print(f"  {status}: {len(task_list)} 個任務")
        
        # 測試每種狀態
        for status in ['running', 'paused']:
            if status in status_groups:
                task = status_groups[status][0]
                task_id = task['id']
                print(f"\n🧪 測試 {status} 狀態的任務 (ID: {task_id})")
                
                toggle_response = requests.put(f"{BASE_URL}/frontend/tasks/{task_id}/toggle")
                if toggle_response.status_code == 200:
                    data = toggle_response.json()
                    print(f"  ✅ 切換成功: {data['old_status']} → {data['new_status']}")
                else:
                    print(f"  ❌ 切換失敗: {toggle_response.status_code}")
                    error_data = toggle_response.json()
                    print(f"  錯誤: {error_data.get('detail', '未知錯誤')}")
            else:
                print(f"\n⚠️  沒有找到狀態為 {status} 的任務")
        
        # 測試無法切換的狀態
        for status in ['completed', 'failed', 'pending']:
            if status in status_groups:
                task = status_groups[status][0]
                task_id = task['id']
                print(f"\n🧪 測試 {status} 狀態的任務 (ID: {task_id}) - 預期失敗")
                
                toggle_response = requests.put(f"{BASE_URL}/frontend/tasks/{task_id}/toggle")
                if toggle_response.status_code == 400:
                    error_data = toggle_response.json()
                    print(f"  ✅ 正確拒絕切換: {error_data.get('detail', '未知錯誤')}")
                else:
                    print(f"  ❌ 預期錯誤但成功: {toggle_response.status_code}")
    
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def main():
    """主測試函式"""
    print("🧪 任務狀態切換詳細測試")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 詳細測試
    detailed_status_test()
    
    # 測試不同類型任務
    test_all_task_types()
    
    print_separator("測試完成")
    print("✅ 詳細任務狀態切換測試完成！")

if __name__ == "__main__":
    main()