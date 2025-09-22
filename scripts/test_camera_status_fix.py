"""
攝影機狀態檢測修復驗證腳本
檢查修復後的狀態是否符合資料庫約束
"""

import asyncio
import aiohttp
import json
import sys
import os

# 添加路徑以便導入模組
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = "http://localhost:8001/api/v1/frontend"

async def test_camera_status_fix():
    """測試攝影機狀態檢測修復"""
    print("🔧 測試攝影機狀態檢測修復")
    print("=" * 50)
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            # 1. 測試基本攝影機列表
            print("📋 1. 測試基本攝影機列表...")
            try:
                async with session.get(f"{BASE_URL}/cameras") as response:
                    if response.status == 200:
                        cameras = await response.json()
                        print(f"✅ 成功獲取 {len(cameras)} 個攝影機")
                        
                        # 檢查狀態值是否合法
                        valid_statuses = {'active', 'inactive', 'error'}
                        for camera in cameras:
                            status = camera.get('status', 'unknown')
                            if status not in valid_statuses:
                                print(f"⚠️ 攝影機 {camera.get('name')} 狀態異常: {status}")
                            else:
                                print(f"✅ 攝影機 {camera.get('name')}: {status}")
                    else:
                        print(f"❌ HTTP錯誤: {response.status}")
                        
            except Exception as e:
                print(f"❌ 基本列表測試失敗: {e}")
            
            # 2. 測試即時檢測（重點測試）
            print("\n🔍 2. 測試即時狀態檢測...")
            try:
                async with session.get(f"{BASE_URL}/cameras?real_time_check=true") as response:
                    if response.status == 200:
                        cameras = await response.json()
                        print(f"✅ 成功執行即時檢測 {len(cameras)} 個攝影機")
                        
                        # 統計狀態分佈
                        status_count = {}
                        invalid_statuses = []
                        valid_statuses = {'active', 'inactive', 'error'}
                        
                        for camera in cameras:
                            status = camera.get('status', 'unknown')
                            status_count[status] = status_count.get(status, 0) + 1
                            
                            if status not in valid_statuses:
                                invalid_statuses.append({
                                    'name': camera.get('name'),
                                    'id': camera.get('id'),
                                    'status': status
                                })
                        
                        print("狀態統計:")
                        for status, count in status_count.items():
                            icon = "✅" if status in valid_statuses else "❌"
                            print(f"  {icon} {status}: {count} 個")
                        
                        if invalid_statuses:
                            print("\n❌ 發現無效狀態:")
                            for item in invalid_statuses:
                                print(f"  - {item['name']} (ID: {item['id']}): {item['status']}")
                        else:
                            print("\n✅ 所有狀態都符合資料庫約束")
                            
                    else:
                        print(f"❌ HTTP錯誤: {response.status}")
                        error_text = await response.text()
                        print(f"錯誤詳情: {error_text}")
                        
            except Exception as e:
                print(f"❌ 即時檢測測試失敗: {e}")
            
            # 3. 測試批量檢測
            print("\n📊 3. 測試批量狀態檢測...")
            try:
                async with session.post(f"{BASE_URL}/cameras/status/check-all") as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', {})
                        print(f"✅ 成功執行批量檢測 {len(results)} 個攝影機")
                        
                        # 檢查批量檢測的狀態值
                        valid_statuses = {'active', 'inactive', 'error'}
                        invalid_count = 0
                        
                        for camera_id, status in results.items():
                            if status not in valid_statuses:
                                print(f"❌ 攝影機 {camera_id}: 無效狀態 {status}")
                                invalid_count += 1
                            else:
                                print(f"✅ 攝影機 {camera_id}: {status}")
                        
                        if invalid_count == 0:
                            print("✅ 批量檢測所有狀態都有效")
                        else:
                            print(f"❌ 發現 {invalid_count} 個無效狀態")
                            
                    else:
                        print(f"❌ HTTP錯誤: {response.status}")
                        error_text = await response.text()
                        print(f"錯誤詳情: {error_text}")
                        
            except Exception as e:
                print(f"❌ 批量檢測測試失敗: {e}")
                
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 修復驗證完成")

if __name__ == "__main__":
    asyncio.run(test_camera_status_fix())