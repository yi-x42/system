#!/usr/bin/env python3
"""
測試刪除攝影機API
"""

import requests
import json

BASE_URL = "http://localhost:8001/api/v1/frontend"

def test_delete_camera():
    """測試刪除攝影機功能"""
    
    print("=== 測試刪除攝影機API ===")
    
    # 1. 先獲取攝影機列表
    print("\n1. 獲取攝影機列表...")
    try:
        response = requests.get(f"{BASE_URL}/cameras")
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            cameras = response.json()
            print(f"攝影機數量: {len(cameras)}")
            
            if cameras:
                print("攝影機列表:")
                for camera in cameras:
                    print(f"  - ID: {camera.get('id')}, 名稱: {camera.get('name')}, 狀態: {camera.get('status')}")
                
                # 2. 測試刪除第一個攝影機
                camera_to_delete = cameras[0]
                camera_id = camera_to_delete.get('id')
                
                print(f"\n2. 測試刪除攝影機: {camera_id}")
                delete_response = requests.delete(f"{BASE_URL}/cameras/{camera_id}")
                print(f"刪除狀態碼: {delete_response.status_code}")
                
                if delete_response.status_code == 200:
                    result = delete_response.json()
                    print("刪除成功:")
                    print(f"  訊息: {result.get('message')}")
                    print(f"  攝影機ID: {result.get('camera_id')}")
                    
                    # 3. 驗證攝影機是否已刪除
                    print(f"\n3. 驗證攝影機 {camera_id} 是否已刪除...")
                    verify_response = requests.get(f"{BASE_URL}/cameras")
                    if verify_response.status_code == 200:
                        remaining_cameras = verify_response.json()
                        print(f"剩餘攝影機數量: {len(remaining_cameras)}")
                        
                        deleted_camera_found = any(cam.get('id') == camera_id for cam in remaining_cameras)
                        if not deleted_camera_found:
                            print("✅ 攝影機已成功刪除")
                        else:
                            print("❌ 攝影機仍然存在")
                    else:
                        print(f"❌ 無法驗證刪除結果: {verify_response.status_code}")
                        
                else:
                    print(f"❌ 刪除失敗: {delete_response.text}")
            else:
                print("沒有攝影機可以測試刪除")
        else:
            print(f"❌ 獲取攝影機列表失敗: {response.text}")
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

    # 4. 測試刪除不存在的攝影機
    print(f"\n4. 測試刪除不存在的攝影機...")
    fake_id = "fake-camera-id-123"
    fake_response = requests.delete(f"{BASE_URL}/cameras/{fake_id}")
    print(f"刪除不存在攝影機的狀態碼: {fake_response.status_code}")
    
    if fake_response.status_code != 200:
        print("✅ 正確處理了不存在的攝影機ID")
    else:
        print("❌ 應該返回錯誤狀態")

if __name__ == "__main__":
    test_delete_camera()
