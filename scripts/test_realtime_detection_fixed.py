#!/usr/bin/env python3
"""
測試修復後的實時檢測功能
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8001"

async def test_realtime_detection():
    """測試實時檢測功能"""
    async with aiohttp.ClientSession() as session:
        print("🧪 開始測試修復後的實時檢測功能")
        print("=" * 60)
        
        # 1. 測試健康檢查
        try:
            async with session.get(f"{API_BASE}/api/v1/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ 健康檢查: {data.get('status', 'unknown')}")
                else:
                    print(f"❌ 健康檢查失敗: {resp.status}")
                    return
        except Exception as e:
            print(f"❌ 健康檢查錯誤: {e}")
            return
        
        # 2. 測試攝影機列表
        try:
            async with session.get(f"{API_BASE}/api/v1/camera/list") as resp:
                if resp.status == 200:
                    cameras = await resp.json()
                    print(f"✅ 可用攝影機: {len(cameras.get('cameras', []))} 台")
                    if not cameras.get('cameras'):
                        print("⚠️  沒有可用的攝影機，測試將使用攝影機 0")
                else:
                    print(f"❌ 攝影機列表獲取失敗: {resp.status}")
        except Exception as e:
            print(f"❌ 攝影機列表錯誤: {e}")
        
        # 3. 測試啟動實時檢測
        camera_id = 0
        task_id = f"test_realtime_{int(time.time())}"
        
        print(f"\n🚀 啟動實時檢測...")
        print(f"   攝影機 ID: {camera_id}")
        print(f"   任務 ID: {task_id}")
        
        try:
            async with session.post(f"{API_BASE}/api/v1/realtime/start/{camera_id}") as resp:
                response_text = await resp.text()
                print(f"📄 啟動回應: {response_text}")
                
                if resp.status == 200:
                    result = await resp.json()
                    if result.get('success'):
                        print(f"✅ 實時檢測啟動成功")
                        print(f"   任務 ID: {result.get('task_id', 'N/A')}")
                        actual_task_id = result.get('task_id', task_id)
                        
                        # 等待檢測運行
                        print(f"\n⏱️  等待檢測運行 10 秒...")
                        await asyncio.sleep(10)
                        
                        # 4. 檢查檢測狀態
                        try:
                            async with session.get(f"{API_BASE}/api/v1/realtime/status/{actual_task_id}") as status_resp:
                                if status_resp.status == 200:
                                    status_data = await status_resp.json()
                                    print(f"✅ 檢測狀態:")
                                    print(f"   運行中: {status_data.get('running', False)}")
                                    print(f"   處理幀數: {status_data.get('frame_count', 0)}")
                                    print(f"   檢測次數: {status_data.get('detection_count', 0)}")
                                    print(f"   FPS: {status_data.get('fps', 0):.2f}")
                                else:
                                    print(f"❌ 狀態檢查失敗: {status_resp.status}")
                        except Exception as e:
                            print(f"❌ 狀態檢查錯誤: {e}")
                        
                        # 5. 停止實時檢測
                        print(f"\n🛑 停止實時檢測...")
                        try:
                            async with session.post(f"{API_BASE}/api/v1/realtime/stop/{actual_task_id}") as stop_resp:
                                if stop_resp.status == 200:
                                    stop_result = await stop_resp.json()
                                    if stop_result.get('success'):
                                        print(f"✅ 實時檢測停止成功")
                                    else:
                                        print(f"❌ 停止失敗: {stop_result.get('error', 'unknown')}")
                                else:
                                    print(f"❌ 停止請求失敗: {stop_resp.status}")
                        except Exception as e:
                            print(f"❌ 停止錯誤: {e}")
                            
                    else:
                        print(f"❌ 實時檢測啟動失敗: {result.get('error', 'unknown')}")
                else:
                    print(f"❌ 啟動請求失敗: {resp.status}")
                    print(f"   錯誤內容: {response_text}")
                    
        except Exception as e:
            print(f"❌ 啟動錯誤: {e}")
        
        print("\n" + "=" * 60)
        print("🧪 測試完成")

if __name__ == "__main__":
    asyncio.run(test_realtime_detection())
