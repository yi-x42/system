#!/usr/bin/env python3
"""
檢查當前攝影機流狀態
找出為什麼會有攝影機 76 的連接嘗試
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "yolo_backend"))

from app.services.camera_stream_manager import camera_stream_manager

def check_camera_streams():
    """檢查當前的攝影機流狀態"""
    print("🔍 檢查當前攝影機流狀態...")
    
    try:
        # 檢查所有活動的流
        active_streams = camera_stream_manager.streams
        
        print(f"📊 發現 {len(active_streams)} 個活動流:")
        
        for camera_id, stream in active_streams.items():
            stats = stream.get_stats()
            print(f"  - {camera_id}:")
            print(f"    狀態: {stream.status}")
            print(f"    設備索引: {stream.device_index}")
            print(f"    幀數: {stats.get('frame_count', 0) if stats else 0}")
            print(f"    消費者: {len(stream.consumers)}")
            
            # 列出消費者
            for consumer_id in stream.consumers:
                print(f"      * {consumer_id}")
        
        if not active_streams:
            print("  ℹ️  目前沒有活動的攝影機流")
        
        # 檢查是否有攝影機 76
        camera_76_id = "camera_76"
        if camera_76_id in active_streams:
            print(f"\n⚠️  發現攝影機 76 流:")
            stream = active_streams[camera_76_id]
            print(f"    狀態: {stream.status}")
            print(f"    設備索引: {stream.device_index}")
            print(f"    消費者: {list(stream.consumers.keys())}")
        else:
            print(f"\n✅ 沒有發現攝影機 76 的活動流")
        
        return True
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        import traceback
        print(f"錯誤詳情:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    check_camera_streams()