#!/usr/bin/env python3
"""
測試攝影機掃描功能
確認改善後的日誌輸出
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "yolo_backend"))

import asyncio
from app.services.camera_service import CameraService

async def test_camera_scan():
    """測試攝影機掃描功能"""
    print("🔧 測試攝影機掃描功能...")
    
    try:
        # 初始化攝影機服務
        camera_service = CameraService()
        
        print("📡 開始掃描可用攝影機...")
        cameras = await camera_service.scan_cameras()
        
        print(f"✅ 掃描完成，發現 {len(cameras)} 個攝影機:")
        
        for camera in cameras:
            print(f"  - {camera.get('name', 'Unknown')}")
            print(f"    類型: {camera.get('type', 'Unknown')}")
            print(f"    索引: {camera.get('device_index', 'Unknown')}")
            print(f"    解析度: {camera.get('resolution', 'Unknown')}")
            print(f"    狀態: {camera.get('status', 'Unknown')}")
            print()
        
        if not cameras:
            print("  ℹ️  沒有發現可用的攝影機")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        print(f"錯誤詳情:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    asyncio.run(test_camera_scan())