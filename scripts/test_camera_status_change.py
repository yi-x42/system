#!/usr/bin/env python3
"""
攝影機狀態變更測試腳本
用來模擬攝影機狀態變化，測試前端是否能即時更新
"""

import requests
import json
import time
from datetime import datetime

def change_camera_status():
    """模擬攝影機狀態變化"""
    base_url = "http://localhost:8001/api/v1/frontend"
    
    # 定義攝影機資料（移到函式開頭）
    add_camera_data = {
        "name": "測試攝影機",
        "ip": "127.0.0.1",
        "camera_type": "USB",
        "index": 0
    }
    
    print(f"🔄 開始攝影機狀態變更測試 - {datetime.now()}")
    print("=" * 60)
    
    # 1. 首先取得當前攝影機列表
    try:
        print("📋 1. 取得當前攝影機列表...")
        response = requests.get(f"{base_url}/cameras?real_time_check=true")
        if response.status_code == 200:
            cameras = response.json()
            print(f"✅ 當前攝影機數量: {len(cameras)}")
            if cameras:
                for camera in cameras:
                    print(f"   攝影機 {camera.get('id')}: {camera.get('name')} - 狀態: {camera.get('status')}")
            else:
                print("   ❌ 沒有攝影機")
                return
        else:
            print(f"❌ 取得攝影機列表失敗: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 取得攝影機列表錯誤: {e}")
        return
    
    # 2. 如果沒有攝影機，先添加一個
    if not cameras:
        print("📷 2. 添加測試攝影機...")
        try:
            response = requests.post(f"{base_url}/cameras", json=add_camera_data)
            if response.status_code == 200:
                print("✅ 測試攝影機已添加")
                time.sleep(2)  # 等待系統更新
            else:
                print(f"❌ 添加攝影機失敗: {response.text}")
                return
        except Exception as e:
            print(f"❌ 添加攝影機錯誤: {e}")
            return
    
    # 3. 重新取得攝影機列表
    try:
        print("📋 3. 重新取得攝影機列表...")
        response = requests.get(f"{base_url}/cameras?real_time_check=true")
        if response.status_code == 200:
            cameras = response.json()
            print(f"✅ 更新後攝影機數量: {len(cameras)}")
            if cameras:
                camera_id = cameras[0].get('id')
                print(f"   將使用攝影機 ID: {camera_id}")
            else:
                print("   ❌ 仍然沒有攝影機")
                return
        else:
            print(f"❌ 重新取得攝影機列表失敗: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 重新取得攝影機列表錯誤: {e}")
        return
    
    # 4. 模擬狀態變化（刪除再添加）
    print(f"🔄 4. 開始狀態變化測試（每30秒一次）...")
    print("   👀 請觀察前端頁面的攝影機卡片是否有更新")
    print("   🌐 前端頁面: http://localhost:3000")
    print("   ⏹️  按 Ctrl+C 停止測試")
    
    cycle_count = 0
    try:
        while True:
            cycle_count += 1
            print(f"\n🔄 第 {cycle_count} 輪狀態變化 - {datetime.now().strftime('%H:%M:%S')}")
            
            # 刪除攝影機
            print("   🗑️  刪除攝影機...")
            try:
                delete_response = requests.delete(f"{base_url}/cameras/{camera_id}")
                if delete_response.status_code == 200:
                    print("   ✅ 攝影機已刪除")
                else:
                    print(f"   ❌ 刪除失敗: {delete_response.status_code}")
            except Exception as e:
                print(f"   ❌ 刪除錯誤: {e}")
            
            # 等待5秒
            print("   ⏳ 等待 5 秒...")
            time.sleep(5)
            
            # 重新添加攝影機
            print("   ➕ 重新添加攝影機...")
            try:
                add_response = requests.post(f"{base_url}/cameras", json=add_camera_data)
                if add_response.status_code == 200:
                    print("   ✅ 攝影機已重新添加")
                    # 取得新的camera_id
                    new_cameras_response = requests.get(f"{base_url}/cameras")
                    if new_cameras_response.status_code == 200:
                        new_cameras = new_cameras_response.json()
                        if new_cameras:
                            camera_id = new_cameras[0].get('id')
                else:
                    print(f"   ❌ 重新添加失敗: {add_response.status_code}")
            except Exception as e:
                print(f"   ❌ 重新添加錯誤: {e}")
            
            # 等待25秒再進行下一輪
            print("   ⏳ 等待 25 秒進行下一輪...")
            time.sleep(25)
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 測試已停止 - 總共執行 {cycle_count} 輪")
        print("測試結束！")

if __name__ == "__main__":
    change_camera_status()