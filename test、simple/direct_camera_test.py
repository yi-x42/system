#!/usr/bin/env python3
"""
簡化測試：直接檢查攝影機數據獲取功能
"""

import asyncio
import requests
import sys
import os

# 將後端路徑添加到 sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'yolo_backend'))

async def test_camera_data_directly():
    """直接測試攝影機數據獲取"""
    print("🔍 直接測試攝影機數據獲取...")
    
    try:
        # 導入必要的模組
        from app.core.database import get_async_db, AsyncSessionLocal
        from app.services.camera_service import CameraService
        from sqlalchemy import select, func
        from app.models.database import DataSource
        
        # 建立資料庫連接
        async with AsyncSessionLocal() as db:
            print("✅ 資料庫連接成功")
            
            # 1. 測試資料庫中的攝影機數量
            total_cameras_result = await db.execute(
                select(func.count(DataSource.id)).where(
                    DataSource.source_type == 'camera'
                )
            )
            total_cameras = total_cameras_result.scalar() or 0
            print(f"📊 資料庫中攝影機總數: {total_cameras}")
            
            # 2. 測試攝影機服務
            camera_service = CameraService(db)
            print("✅ 攝影機服務初始化成功")
            
            # 3. 測試即時狀態檢測
            cameras_with_status = await camera_service.get_cameras_with_realtime_status()
            online_cameras = len([camera for camera in cameras_with_status if camera.status == "online"])
            
            print(f"🎥 即時檢測攝影機數: {len(cameras_with_status)}")
            print(f"🟢 線上攝影機數量: {online_cameras}")
            
            # 顯示每個攝影機的狀態
            for i, camera in enumerate(cameras_with_status):
                print(f"   攝影機 {i+1}: {camera.name} - {camera.status}")
            
            return total_cameras, online_cameras
            
    except Exception as e:
        print(f"❌ 直接測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0

def test_api_stats():
    """測試系統統計API"""
    print("\n📊 測試系統統計API...")
    try:
        response = requests.get("http://localhost:8001/api/v1/frontend/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("API回應:")
            for key, value in data.items():
                print(f"  {key}: {value}")
            return data
        else:
            print(f"API失敗: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"API測試錯誤: {e}")
        return None

async def main():
    print("🚀 開始簡化攝影機數據測試...")
    
    # 1. 直接測試數據獲取
    total_cameras, online_cameras = await test_camera_data_directly()
    
    # 2. 測試API
    api_data = test_api_stats()
    
    # 3. 比較結果
    print("\n🔍 結果比較:")
    print(f"直接查詢 - 總數: {total_cameras}, 線上: {online_cameras}")
    if api_data:
        api_total = api_data.get('total_cameras', '缺少')
        api_online = api_data.get('online_cameras', '缺少')
        print(f"API查詢 - 總數: {api_total}, 線上: {api_online}")
    else:
        print("API查詢 - 失敗")

if __name__ == "__main__":
    asyncio.run(main())