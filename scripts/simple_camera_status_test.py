"""
攝影機狀態監控 - 簡單手動測試
測試基本的API端點功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001/api/v1/frontend"

def test_basic_cameras_list():
    """測試基本攝影機列表"""
    print("📋 測試基本攝影機列表...")
    try:
        response = requests.get(f"{BASE_URL}/cameras", timeout=10)
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            cameras = response.json()
            print(f"✅ 成功獲取 {len(cameras)} 個攝影機")
            
            for i, camera in enumerate(cameras[:3]):  # 只顯示前3個
                print(f"  {i+1}. {camera.get('name', 'Unknown')} - 狀態: {camera.get('status', 'Unknown')}")
            
            return cameras
        else:
            print(f"❌ 請求失敗: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ 請求錯誤: {e}")
        return []

def test_realtime_cameras_list():
    """測試即時檢測攝影機列表"""
    print("\n🔍 測試即時檢測攝影機列表...")
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/cameras?real_time_check=true", timeout=30)
        elapsed_time = time.time() - start_time
        
        print(f"狀態碼: {response.status_code}")
        print(f"耗時: {elapsed_time:.2f} 秒")
        
        if response.status_code == 200:
            cameras = response.json()
            print(f"✅ 成功檢測 {len(cameras)} 個攝影機狀態")
            
            status_count = {}
            for camera in cameras:
                status = camera.get('status', 'unknown')
                status_count[status] = status_count.get(status, 0) + 1
                
            print("狀態統計:")
            for status, count in status_count.items():
                print(f"  {status}: {count} 個")
            
            return cameras
        else:
            print(f"❌ 請求失敗: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ 請求錯誤: {e}")
        return []

def test_single_camera_status(camera_id):
    """測試單個攝影機狀態檢測"""
    print(f"\n📷 測試攝影機 {camera_id} 狀態檢測...")
    try:
        response = requests.get(f"{BASE_URL}/cameras/{camera_id}/status", timeout=15)
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            timestamp = data.get('timestamp')
            print(f"✅ 攝影機 {camera_id} 狀態: {status}")
            print(f"   檢測時間: {timestamp}")
            return status
        elif response.status_code == 404:
            print(f"⚠️ 攝影機 {camera_id} 不存在")
            return None
        else:
            print(f"❌ 請求失敗: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 請求錯誤: {e}")
        return None

def test_check_all_cameras():
    """測試檢查所有攝影機狀態"""
    print("\n📊 測試批量檢查所有攝影機狀態...")
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/cameras/status/check-all", timeout=60)
        elapsed_time = time.time() - start_time
        
        print(f"狀態碼: {response.status_code}")
        print(f"耗時: {elapsed_time:.2f} 秒")
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            results = data.get('results', {})
            
            print(f"✅ {message}")
            print("詳細結果:")
            
            for camera_id, status in results.items():
                print(f"  攝影機 {camera_id}: {status}")
            
            return results
        else:
            print(f"❌ 請求失敗: {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ 請求錯誤: {e}")
        return {}

def main():
    """主測試函數"""
    print("🚀 攝影機狀態監控功能 - 手動測試")
    print("=" * 50)
    
    # 1. 測試基本攝影機列表
    cameras = test_basic_cameras_list()
    
    # 2. 測試即時檢測
    realtime_cameras = test_realtime_cameras_list()
    
    # 3. 測試單個攝影機狀態
    if cameras and len(cameras) > 0:
        first_camera_id = cameras[0].get('id')
        if first_camera_id:
            test_single_camera_status(first_camera_id)
    
    # 測試不存在的攝影機
    test_single_camera_status(99999)
    
    # 4. 測試批量檢查
    test_check_all_cameras()
    
    print("\n✅ 手動測試完成!")
    print("\n💡 提示:")
    print("- 如果有錯誤，請檢查後端服務是否正在運行")
    print("- 確保資料庫中有攝影機記錄")
    print("- 檢查網路連接和攝影機配置")

if __name__ == "__main__":
    main()