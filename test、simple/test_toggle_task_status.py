#!/usr/bin/env python3
"""
測試任務狀態切換（暫停/恢復）功能
"""

import requests
import json
import time
from datetime import datetime

# API 基礎地址
BASE_URL = "http://localhost:8001/api/v1"

def print_separator(title=""):
    print("\n" + "="*50)
    if title:
        print(f"  {title}")
        print("="*50)

def test_toggle_task_status():
    """測試任務狀態切換功能"""
    print_separator("測試任務狀態切換功能")
    
    try:
        # 1. 獲取現有任務列表
        print("📋 獲取現有任務列表...")
        response = requests.get(f"{BASE_URL}/frontend/tasks")
        response.raise_for_status()
        tasks_data = response.json()
        
        print(f"✅ 找到 {len(tasks_data)} 個任務")
        
        if not tasks_data:
            print("❌ 沒有找到任何任務，請先創建一個任務")
            return
        
        # 尋找一個運行中或暫停的任務
        suitable_task = None
        for task in tasks_data:
            if task['status'] in ['running', 'paused']:
                suitable_task = task
                break
        
        if not suitable_task:
            print("❌ 沒有找到運行中或暫停的任務")
            print("可用任務狀態:", [task['status'] for task in tasks_data])
            return
        
        task_id = suitable_task['id']
        original_status = suitable_task['status']
        
        print(f"🎯 選擇任務 ID: {task_id}")
        print(f"📊 原始狀態: {original_status}")
        
        # 2. 切換任務狀態
        print(f"\n🔄 切換任務狀態...")
        toggle_response = requests.put(f"{BASE_URL}/frontend/tasks/{task_id}/toggle")
        toggle_response.raise_for_status()
        toggle_data = toggle_response.json()
        
        print(f"✅ 狀態切換成功!")
        print(f"📈 狀態變化: {toggle_data['old_status']} → {toggle_data['new_status']}")
        print(f"📝 回應訊息: {toggle_data['message']}")
        
        # 3. 驗證狀態變更
        print(f"\n🔍 驗證狀態變更...")
        time.sleep(1)  # 等待一秒確保資料庫更新
        
        verify_response = requests.get(f"{BASE_URL}/frontend/tasks")
        verify_response.raise_for_status()
        verify_data = verify_response.json()
        
        updated_task = None
        for task in verify_data:
            if task['id'] == task_id:
                updated_task = task
                break
        
        if updated_task:
            print(f"✅ 任務狀態已更新: {updated_task['status']}")
            if updated_task['status'] == toggle_data['new_status']:
                print("✅ 狀態驗證成功！")
            else:
                print(f"❌ 狀態驗證失敗！預期: {toggle_data['new_status']}, 實際: {updated_task['status']}")
        else:
            print("❌ 找不到更新後的任務")
        
        # 4. 再次切換回原狀態（可選）
        print(f"\n🔄 再次切換任務狀態（測試雙向切換）...")
        toggle_back_response = requests.put(f"{BASE_URL}/frontend/tasks/{task_id}/toggle")
        toggle_back_response.raise_for_status()
        toggle_back_data = toggle_back_response.json()
        
        print(f"✅ 第二次切換成功!")
        print(f"📈 狀態變化: {toggle_back_data['old_status']} → {toggle_back_data['new_status']}")
        
        if toggle_back_data['new_status'] == original_status:
            print("✅ 成功切換回原始狀態！")
        else:
            print(f"⚠️  狀態不同於原始狀態 (原始: {original_status}, 當前: {toggle_back_data['new_status']})")
        
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

def test_invalid_task_toggle():
    """測試無效任務 ID 的狀態切換"""
    print_separator("測試無效任務 ID")
    
    try:
        # 使用不存在的任務 ID
        invalid_task_id = 99999
        response = requests.put(f"{BASE_URL}/frontend/tasks/{invalid_task_id}/toggle")
        
        if response.status_code == 404:
            print("✅ 正確處理了無效任務 ID (返回 404)")
            error_data = response.json()
            print(f"錯誤訊息: {error_data.get('detail', '無訊息')}")
        else:
            print(f"❌ 預期 404 錯誤，但收到 {response.status_code}")
            
    except Exception as e:
        print(f"❌ 測試無效任務 ID 時發生錯誤: {e}")

def main():
    """主測試函式"""
    print("🧪 任務狀態切換功能測試")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試正常功能
    test_toggle_task_status()
    
    # 測試錯誤處理
    test_invalid_task_toggle()
    
    print_separator("測試完成")
    print("✅ 任務狀態切換功能測試完成！")

if __name__ == "__main__":
    main()