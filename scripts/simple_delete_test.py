#!/usr/bin/env python3
"""
簡單的攝影機狀態測試
僅測試刪除功能來觀察前端更新
"""

import requests
import time
from datetime import datetime

def simple_delete_test():
    """簡單的刪除測試"""
    base_url = "http://localhost:8001/api/v1/frontend"
    
    print(f"🔄 攝影機刪除測試 - {datetime.now()}")
    print("=" * 50)
    
    # 取得當前攝影機
    response = requests.get(f"{base_url}/cameras")
    if response.status_code == 200:
        cameras = response.json()
        print(f"📋 當前攝影機數量: {len(cameras)}")
        
        if cameras:
            camera_id = cameras[0]['id']
            print(f"🎯 將刪除攝影機 ID: {camera_id}")
            print("👀 請觀察前端頁面 http://localhost:3000")
            print("⏳ 5 秒後開始刪除...")
            time.sleep(5)
            
            # 刪除攝影機
            delete_response = requests.delete(f"{base_url}/cameras/{camera_id}")
            if delete_response.status_code == 200:
                print("✅ 攝影機已成功刪除！")
                print("📺 請檢查前端頁面是否顯示「尚未配置攝影機」")
            else:
                print(f"❌ 刪除失敗: {delete_response.status_code}")
        else:
            print("❌ 沒有攝影機可刪除")
    else:
        print(f"❌ 無法取得攝影機列表: {response.status_code}")

if __name__ == "__main__":
    simple_delete_test()