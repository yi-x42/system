"""
測試任務停止修復效果的腳本
驗證database-first stop_task方法是否能解決"任務不存在"錯誤
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_task_lifecycle():
    """測試完整的任務生命週期：創建 -> 啟動 -> 暫停 -> 停止"""
    
    base_url = "http://localhost:8001"
    
    print("🚀 開始測試任務生命週期...")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. 創建任務
        print("📝 步驟 1: 創建新任務")
        task_data = {
            "task_name": f"測試任務-{datetime.now().strftime('%H%M%S')}",
            "task_type": "realtime_camera",
            "source_info": {
                "camera_id": "1",
                "name": "測試攝影機",
                "description": "測試任務停止功能"
            },
            "model_id": "yolo11n.pt",
            "confidence_threshold": 0.5
        }
        
        async with session.post(f"{base_url}/api/v1/frontend/analysis-tasks", json=task_data) as resp:
            if resp.status == 200:
                create_result = await resp.json()
                task_id = str(create_result["task_id"])
                print(f"✅ 任務創建成功，ID: {task_id}")
            else:
                print(f"❌ 任務創建失敗: {resp.status}")
                return
        
        await asyncio.sleep(1)
        
        # 2. 啟動任務
        print("\n🚀 步驟 2: 啟動任務")
        async with session.post(f"{base_url}/api/v1/frontend/tasks/{task_id}/start") as resp:
            if resp.status == 200:
                print("✅ 任務啟動成功")
            else:
                error_text = await resp.text()
                print(f"❌ 任務啟動失敗: {resp.status} - {error_text}")
                return
        
        await asyncio.sleep(3)
        
        # 3. 檢查任務狀態
        print("\n📊 步驟 3: 檢查任務狀態")
        async with session.get(f"{base_url}/api/v1/frontend/tasks") as resp:
            if resp.status == 200:
                tasks = await resp.json()
                current_task = None
                for task in tasks:
                    if str(task["id"]) == task_id:
                        current_task = task
                        break
                
                if current_task:
                    print(f"✅ 找到任務: ID={task_id}, 狀態={current_task['status']}")
                else:
                    print(f"❌ 任務列表中找不到任務 {task_id}")
                    return
            else:
                print(f"❌ 獲取任務列表失敗: {resp.status}")
                return
        
        # 4. 暫停任務
        print("\n⏸️  步驟 4: 暫停任務")
        async with session.post(f"{base_url}/api/v1/frontend/tasks/{task_id}/pause") as resp:
            if resp.status == 200:
                print("✅ 任務暫停成功")
            else:
                error_text = await resp.text()
                print(f"❌ 任務暫停失敗: {resp.status} - {error_text}")
        
        await asyncio.sleep(2)
        
        # 5. 停止任務 (這裡是我們要測試的關鍵步驟)
        print("\n🛑 步驟 5: 停止任務 (關鍵測試)")
        async with session.post(f"{base_url}/api/v1/frontend/tasks/{task_id}/stop") as resp:
            response_text = await resp.text()
            if resp.status == 200:
                print("✅ 任務停止成功!")
                print(f"   響應: {response_text}")
            else:
                print(f"❌ 任務停止失敗: {resp.status}")
                print(f"   錯誤詳情: {response_text}")
                
                # 如果仍然失敗，打印更多診斷信息
                if "任務不存在" in response_text:
                    print("\n🔍 診斷信息:")
                    print("   - 這個錯誤表明內存狀態與數據庫不同步")
                    print("   - 檢查 stop_task 方法是否使用了database-first邏輯")
        
        # 6. 再次檢查任務狀態
        print("\n📊 步驟 6: 驗證最終狀態")
        async with session.get(f"{base_url}/api/v1/frontend/tasks") as resp:
            if resp.status == 200:
                tasks = await resp.json()
                final_task = None
                for task in tasks:
                    if str(task["id"]) == task_id:
                        final_task = task
                        break
                
                if final_task:
                    print(f"✅ 任務最終狀態: {final_task['status']}")
                    if final_task['status'] in ['stopped', 'completed', 'failed']:
                        print("✅ 任務已正確停止")
                    else:
                        print(f"⚠️  任務狀態異常: {final_task['status']}")
                else:
                    print("ℹ️  任務可能已從活動列表移除（正常情況）")

async def test_stop_nonexistent_task():
    """測試停止不存在任務的情況"""
    
    print("\n" + "=" * 50)
    print("🧪 測試停止不存在的任務")
    
    base_url = "http://localhost:8001"
    fake_task_id = "99999"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/api/v1/frontend/tasks/{fake_task_id}/stop") as resp:
            response_text = await resp.text()
            if resp.status == 404:
                print("✅ 正確回應404錯誤 - 任務不存在")
            elif resp.status == 200:
                print("⚠️  意外成功響應 - 可能邏輯有問題")
            else:
                print(f"❌ 意外錯誤: {resp.status} - {response_text}")

async def main():
    """主測試函數"""
    print("🔧 任務停止功能修復測試")
    print("測試目標: 驗證database-first stop_task邏輯")
    print("=" * 50)
    
    try:
        # 檢查服務器是否運行
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8001/api/v1/frontend/stats") as resp:
                if resp.status != 200:
                    print("❌ 服務器未運行，請先啟動系統")
                    return
        
        await test_task_lifecycle()
        await test_stop_nonexistent_task()
        
        print("\n" + "=" * 50)
        print("✅ 測試完成!")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(main())