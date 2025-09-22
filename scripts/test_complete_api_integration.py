#!/usr/bin/env python3
"""
完整的 API 整合測試
創建一個新的即時分析任務來測試三個新欄位
"""

import asyncio
import aiohttp
import json
import asyncpg
import sys
import os

# 將 yolo_backend 加入路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

from app.core.config import settings

async def test_complete_api_integration():
    """完整的 API 整合測試"""
    
    print("🧪 完整的 API 整合測試")
    print("創建一個新任務並檢查三個新欄位是否寫入")
    print("=" * 70)
    
    # 測試數據
    test_task_name = "測試任務_API整合"
    test_model_id = "yolo11n"
    test_confidence = 0.75
    test_camera_id = "79"  # 使用實際存在的攝影機 ID
    
    try:
        # 1. 調用即時分析 API
        print("📡 調用即時分析 API...")
        
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:8001/api/v1/frontend/analysis/start-realtime"
            
            payload = {
                "task_name": test_task_name,
                "camera_id": test_camera_id,
                "model_id": test_model_id,
                "confidence": test_confidence,
                "iou_threshold": 0.45,
                "description": "API整合測試任務"
            }
            
            print(f"  請求URL: {url}")
            print(f"  請求數據: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            try:
                async with session.post(url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"  ✅ API 調用成功！")
                        print(f"  任務ID: {result.get('task_id')}")
                        print(f"  狀態: {result.get('status')}")
                        print(f"  訊息: {result.get('message')}")
                        
                        task_id = result.get('task_id')
                        
                    else:
                        error_text = await response.text()
                        print(f"  ❌ API 調用失敗 (HTTP {response.status})")
                        print(f"  錯誤: {error_text}")
                        return False
                        
            except asyncio.TimeoutError:
                print("  ❌ API 調用超時")
                return False
            except Exception as e:
                print(f"  ❌ API 調用異常: {e}")
                return False
        
        # 等待一下讓資料庫寫入完成
        await asyncio.sleep(2)
        
        # 2. 檢查資料庫中的記錄
        print(f"\n🔍 檢查資料庫中的任務記錄...")
        
        db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        
        # 查找剛才創建的任務
        task_record = await conn.fetchrow("""
            SELECT 
                id, task_type, status,
                task_name, model_id, confidence_threshold,
                source_info, created_at
            FROM analysis_tasks 
            WHERE id = $1;
        """, int(task_id))
        
        if task_record:
            print(f"  ✅ 找到任務記錄 (ID: {task_record['id']})")
            print(f"  任務類型: {task_record['task_type']}")
            print(f"  狀態: {task_record['status']}")
            print(f"  任務名稱: '{task_record['task_name']}'")
            print(f"  模型ID: '{task_record['model_id']}'")
            print(f"  信心度: {task_record['confidence_threshold']}")
            print(f"  來源資訊: {json.dumps(task_record['source_info'], indent=2, ensure_ascii=False)}")
            print(f"  建立時間: {task_record['created_at']}")
            
            # 驗證三個新欄位
            success = True
            if task_record['task_name'] != test_task_name:
                print(f"  ❌ 任務名稱不匹配: 期望 '{test_task_name}', 實際 '{task_record['task_name']}'")
                success = False
            else:
                print(f"  ✅ 任務名稱匹配")
            
            if task_record['model_id'] != test_model_id:
                print(f"  ❌ 模型ID不匹配: 期望 '{test_model_id}', 實際 '{task_record['model_id']}'")
                success = False
            else:
                print(f"  ✅ 模型ID匹配")
            
            if abs(task_record['confidence_threshold'] - test_confidence) > 0.001:
                print(f"  ❌ 信心度不匹配: 期望 {test_confidence}, 實際 {task_record['confidence_threshold']}")
                success = False
            else:
                print(f"  ✅ 信心度匹配")
            
            await conn.close()
            return success
            
        else:
            print(f"  ❌ 沒有找到任務記錄 (ID: {task_id})")
            await conn.close()
            return False
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

if __name__ == '__main__':
    try:
        print("確保系統已啟動在 http://localhost:8001")
        print("如果系統未啟動，請先執行: python start.py")
        print()
        
        success = asyncio.run(test_complete_api_integration())
        
        if success:
            print(f"\n🎉 完整 API 整合測試成功！")
            print("✅ 三個新欄位 (task_name, model_id, confidence_threshold) 正確寫入資料庫")
        else:
            print(f"\n❌ API 整合測試失敗")
            print("需要檢查 API 實現和資料庫寫入邏輯")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 執行測試時發生錯誤: {e}")
        sys.exit(1)