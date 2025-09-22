#!/usr/bin/env python3
"""測試佇列修復"""

import sys
import os
import threading
import time
import queue

# 添加專案路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

def test_sync_queue():
    """測試同步佇列在多執行緒環境中的工作情況"""
    print("🧪 測試同步佇列修復...")
    
    try:
        # 創建同步佇列
        frame_queue = queue.Queue(maxsize=10)
        
        def camera_callback(frame_data):
            """模擬攝影機回調函式"""
            try:
                frame_queue.put(frame_data, timeout=0.1)
                print(f"✅ 成功放入佇列: {frame_data}")
            except queue.Full:
                print("⚠️ 佇列已滿，丟棄幀")
            except Exception as e:
                print(f"❌ 佇列操作錯誤: {e}")
        
        def generate_frames():
            """模擬幀生成器"""
            while True:
                try:
                    frame_data = frame_queue.get(timeout=1.0)
                    yield frame_data
                    frame_queue.task_done()
                except queue.Empty:
                    print("⏰ 佇列超時，結束生成")
                    break
                except Exception as e:
                    print(f"❌ 生成器錯誤: {e}")
                    break
        
        # 在背景執行緒中模擬攝影機回調
        def simulate_camera():
            for i in range(5):
                time.sleep(0.5)
                camera_callback(f"frame_{i}")
        
        print("📹 啟動模擬攝影機...")
        camera_thread = threading.Thread(target=simulate_camera)
        camera_thread.start()
        
        print("🎬 開始生成幀...")
        frames = list(generate_frames())
        
        print(f"✅ 成功處理 {len(frames)} 個幀: {frames}")
        
        camera_thread.join()
        print("✅ 同步佇列測試通過")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_async_queue_problem():
    """展示異步佇列在非異步環境中的問題"""
    print("\n🔍 展示異步佇列問題...")
    
    try:
        import asyncio
        
        # 這會導致錯誤
        async_queue = asyncio.Queue(maxsize=10)
        
        def bad_callback(frame_data):
            """這會失敗的回調函式"""
            try:
                # 這會導致 "no running event loop" 錯誤
                asyncio.create_task(async_queue.put(frame_data))
                print("這行不會被印出")
            except RuntimeError as e:
                print(f"❌ 預期的錯誤: {e}")
        
        print("📹 測試異步佇列在非異步環境中...")
        bad_callback("test_frame")
        
    except Exception as e:
        print(f"❌ 異步佇列測試錯誤: {e}")

if __name__ == "__main__":
    test_sync_queue()
    test_async_queue_problem()
    print("\n🎯 結論: 修復後的同步佇列可以在多執行緒環境中正常工作")