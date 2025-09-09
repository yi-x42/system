#!/usr/bin/env python3
"""
測試創建分析任務 API
驗證分析任務是否能正確保存到 analysis_tasks 表
"""

import requests
import json
import os
from datetime import datetime

# API 基礎 URL
BASE_URL = "http://localhost:8001/api/v1"

def test_create_analysis_task():
    """測試創建分析任務"""
    print("🧪 測試創建分析任務 API")
    print("=" * 50)
    
    # 準備測試資料
    task_data = {
        "task_type": "video_file",
        "source_info": {
            "file_path": "D:/project/system/yolo_backend/uploads/test_video.mp4",
            "original_filename": "test_video.mp4",
            "confidence_threshold": 0.8
        },
        "source_width": 1920,
        "source_height": 1080,
        "source_fps": 30.0
    }
    
    print(f"📤 請求資料:")
    print(json.dumps(task_data, indent=2, ensure_ascii=False))
    print()
    
    try:
        # 發送創建任務請求
        response = requests.post(
            f"{BASE_URL}/tasks/create",
            json=task_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"🌐 HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 創建成功!")
            print(f"📋 回應資料:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            task_id = result.get('task_id')
            if task_id:
                print(f"\n🎯 任務 ID: {task_id}")
                
                # 驗證任務是否真的保存到資料庫
                verify_task_in_database(task_id)
            
        else:
            print(f"❌ 創建失敗: {response.status_code}")
            print(f"錯誤詳情: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API 服務器，請確認後端服務是否啟動")
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")

def verify_task_in_database(task_id):
    """驗證任務是否保存到資料庫"""
    print(f"\n🔍 驗證任務 {task_id} 是否保存到資料庫...")
    
    try:
        # 查詢分析任務表
        response = requests.get(f"{BASE_URL}/database/analysis_tasks?limit=5")
        
        if response.status_code == 200:
            result = response.json()
            tasks = result.get('data', [])
            
            # 尋找我們剛創建的任務
            found_task = None
            for task in tasks:
                if task.get('id') == task_id:
                    found_task = task
                    break
            
            if found_task:
                print(f"✅ 任務已成功保存到 analysis_tasks 表")
                print(f"📊 任務詳情:")
                print(f"   - ID: {found_task['id']}")
                print(f"   - 類型: {found_task['task_type']}")
                print(f"   - 狀態: {found_task['status']}")
                print(f"   - 來源資訊: {found_task['source_info']}")
                print(f"   - 創建時間: {found_task['created_at']}")
            else:
                print(f"❌ 在資料庫中找不到任務 {task_id}")
                
        else:
            print(f"❌ 查詢資料庫失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 資料庫驗證失敗: {str(e)}")

def test_database_view():
    """測試查看資料庫內容"""
    print(f"\n🗄️ 查看 analysis_tasks 資料庫內容")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/database/analysis_tasks?limit=10")
        
        if response.status_code == 200:
            result = response.json()
            tasks = result.get('data', [])
            total_count = result.get('total_count', 0)
            
            print(f"📊 analysis_tasks 表統計:")
            print(f"   - 總記錄數: {total_count}")
            print(f"   - 當前顯示: {len(tasks)}")
            print()
            
            if tasks:
                print(f"📋 最近的任務:")
                for i, task in enumerate(tasks[:3]):  # 只顯示前3個
                    print(f"   {i+1}. ID: {task['id']} | 類型: {task['task_type']} | 狀態: {task['status']}")
                    print(f"      來源: {task.get('source_info', {}).get('original_filename', 'N/A')}")
                    print(f"      時間: {task['created_at']}")
                    print()
            else:
                print("📭 資料庫中沒有任務記錄")
                
        else:
            print(f"❌ 查詢失敗: {response.status_code}")
            print(f"錯誤: {response.text}")
            
    except Exception as e:
        print(f"❌ 查看資料庫失敗: {str(e)}")

if __name__ == "__main__":
    print("🚀 開始測試創建分析任務功能")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 先查看當前資料庫狀態
    test_database_view()
    
    # 2. 測試創建分析任務
    test_create_analysis_task()
    
    print("\n🏁 測試完成")
