#!/usr/bin/env python3
"""
測試攝影機服務的資料庫載入功能
檢查持久化是否正常工作
"""

import sys
import os
sys.path.append('d:/project/system/yolo_backend')

from app.services.camera_service import CameraService
from app.core.database import SyncSessionLocal
from app.models.database import DataSource

def test_camera_service():
    """測試攝影機服務"""
    print("🧪 測試攝影機服務持久化功能...")
    
    # 1. 檢查資料庫中的攝影機配置
    print("\n📋 檢查資料庫中的攝影機配置...")
    try:
        with SyncSessionLocal() as db:
            camera_sources = db.query(DataSource).filter(
                DataSource.source_type == 'camera'
            ).all()
            
            print(f"資料庫中找到 {len(camera_sources)} 個攝影機配置:")
            for source in camera_sources:
                print(f"  - ID: {source.id}, 名稱: {source.name}, 狀態: {source.status}")
                print(f"    配置: {source.config}")
    
    except Exception as e:
        print(f"❌ 資料庫查詢失敗: {e}")
        return False
    
    # 2. 測試 CameraService Singleton 行為
    print("\n🔄 測試 CameraService Singleton 行為...")
    service1 = CameraService()
    service2 = CameraService()
    
    print(f"Service1 ID: {id(service1)}")
    print(f"Service2 ID: {id(service2)}")
    print(f"是否為同一實例: {service1 is service2}")
    
    # 3. 檢查載入的攝影機
    print(f"\n📱 CameraService 中載入的攝影機數量: {len(service1.cameras)}")
    for camera_id, camera in service1.cameras.items():
        print(f"  - ID: {camera_id}, 名稱: {camera.name}, 類型: {camera.camera_type}")
    
    # 4. 測試添加攝影機
    print("\n➕ 測試添加新攝影機...")
    try:
        import asyncio
        
        async def test_add():
            camera_id = await service1.add_camera(
                name="測試攝影機_持久化",
                camera_type="USB",
                resolution="1280x720",
                fps=25,
                device_index=99
            )
            print(f"✅ 成功添加攝影機，ID: {camera_id}")
            return camera_id
        
        camera_id = asyncio.run(test_add())
        
        # 檢查是否真的添加到內存中
        print(f"內存中攝影機數量: {len(service1.cameras)}")
        
        # 檢查是否保存到資料庫
        with SyncSessionLocal() as db:
            saved_source = db.query(DataSource).filter(
                DataSource.id == int(camera_id)
            ).first()
            if saved_source:
                print(f"✅ 攝影機已保存到資料庫: {saved_source.name}")
            else:
                print(f"❌ 攝影機未保存到資料庫")
        
    except Exception as e:
        print(f"❌ 添加攝影機失敗: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 測試重新創建服務實例
    print("\n🔄 測試重新創建服務實例...")
    service3 = CameraService()
    print(f"Service3 ID: {id(service3)}")
    print(f"Service3 攝影機數量: {len(service3.cameras)}")
    print(f"是否為同一實例: {service1 is service3}")
    
    return True

if __name__ == "__main__":
    test_camera_service()
