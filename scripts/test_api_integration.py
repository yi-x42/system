#!/usr/bin/env python3
"""
測試三個新欄位的 API 整合
驗證即時分析和影片分析 API 是否正確寫入 task_name, model_id, confidence_threshold
"""

import asyncio
import asyncpg
import sys
import os

# 將 yolo_backend 加入路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

from app.core.config import settings

async def test_api_integration():
    """測試三個新欄位的 API 整合"""
    
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    
    print("🧪 測試三個新欄位的 API 整合")
    print("驗證 task_name, model_id, confidence_threshold 是否正確寫入")
    print("=" * 70)
    
    try:
        # 連接資料庫
        conn = await asyncpg.connect(db_url)
        
        # 測試 1: 檢查最近的任務記錄
        print("📊 檢查最近的任務記錄...")
        
        recent_tasks = await conn.fetch("""
            SELECT 
                id, task_type, status,
                task_name, model_id, confidence_threshold,
                created_at
            FROM analysis_tasks 
            ORDER BY created_at DESC 
            LIMIT 10;
        """)
        
        if recent_tasks:
            print(f"找到 {len(recent_tasks)} 個最近的任務：")
            for task in recent_tasks:
                print(f"  - ID {task['id']}: {task['task_type']}")
                print(f"    任務名稱: {task['task_name'] or '(未設定)'}")
                print(f"    模型ID: {task['model_id'] or '(未設定)'}")
                print(f"    信心度: {task['confidence_threshold'] or '(未設定)'}")
                print(f"    建立時間: {task['created_at']}")
                print()
        else:
            print("沒有找到任務記錄")
        
        # 測試 2: 檢查三個新欄位的使用情況
        print("📈 統計三個新欄位的使用情況...")
        
        field_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(task_name) as tasks_with_name,
                COUNT(model_id) as tasks_with_model,
                COUNT(confidence_threshold) as tasks_with_confidence,
                COUNT(CASE WHEN task_name IS NOT NULL AND model_id IS NOT NULL AND confidence_threshold IS NOT NULL THEN 1 END) as complete_tasks
            FROM analysis_tasks;
        """)
        
        if field_stats:
            total = field_stats['total_tasks']
            with_name = field_stats['tasks_with_name']
            with_model = field_stats['tasks_with_model']
            with_confidence = field_stats['tasks_with_confidence']
            complete = field_stats['complete_tasks']
            
            print(f"  ✓ 總任務數: {total}")
            print(f"  ✓ 有任務名稱: {with_name} ({(with_name/total*100) if total > 0 else 0:.1f}%)")
            print(f"  ✓ 有模型ID: {with_model} ({(with_model/total*100) if total > 0 else 0:.1f}%)")
            print(f"  ✓ 有信心度: {with_confidence} ({(with_confidence/total*100) if total > 0 else 0:.1f}%)")
            print(f"  ✓ 三欄位完整: {complete} ({(complete/total*100) if total > 0 else 0:.1f}%)")
        
        # 測試 3: 檢查各任務類型的新欄位使用情況
        print(f"\n📋 各任務類型的新欄位使用情況...")
        
        type_stats = await conn.fetch("""
            SELECT 
                task_type,
                COUNT(*) as count,
                COUNT(task_name) as with_name,
                COUNT(model_id) as with_model,
                COUNT(confidence_threshold) as with_confidence
            FROM analysis_tasks 
            GROUP BY task_type
            ORDER BY task_type;
        """)
        
        for stat in type_stats:
            task_type = stat['task_type']
            count = stat['count']
            with_name = stat['with_name']
            with_model = stat['with_model']
            with_confidence = stat['with_confidence']
            
            print(f"  {task_type}:")
            print(f"    - 總數: {count}")
            print(f"    - 有任務名稱: {with_name} ({(with_name/count*100) if count > 0 else 0:.1f}%)")
            print(f"    - 有模型ID: {with_model} ({(with_model/count*100) if count > 0 else 0:.1f}%)")
            print(f"    - 有信心度: {with_confidence} ({(with_confidence/count*100) if count > 0 else 0:.1f}%)")
        
        # 測試 4: 檢查最新任務的完整性
        print(f"\n🔍 檢查最新任務的完整性...")
        
        latest_complete_task = await conn.fetchrow("""
            SELECT 
                id, task_type, status,
                task_name, model_id, confidence_threshold,
                created_at
            FROM analysis_tasks 
            WHERE task_name IS NOT NULL 
            AND model_id IS NOT NULL 
            AND confidence_threshold IS NOT NULL
            ORDER BY created_at DESC 
            LIMIT 1;
        """)
        
        if latest_complete_task:
            print("✓ 找到最新的完整任務:")
            print(f"  - ID: {latest_complete_task['id']}")
            print(f"  - 類型: {latest_complete_task['task_type']}")
            print(f"  - 狀態: {latest_complete_task['status']}")
            print(f"  - 任務名稱: '{latest_complete_task['task_name']}'")
            print(f"  - 模型ID: '{latest_complete_task['model_id']}'")
            print(f"  - 信心度: {latest_complete_task['confidence_threshold']}")
            print(f"  - 建立時間: {latest_complete_task['created_at']}")
        else:
            print("❌ 沒有找到完整的任務記錄（包含所有三個新欄位）")
        
        # 測試 5: 建議
        print(f"\n💡 API 整合建議...")
        
        if field_stats and field_stats['total_tasks'] > 0:
            completion_rate = (field_stats['complete_tasks'] / field_stats['total_tasks']) * 100
            
            if completion_rate >= 90:
                print("🎉 優秀！大部分任務都包含完整的新欄位")
            elif completion_rate >= 70:
                print("✅ 良好！多數任務包含新欄位，但仍有改進空間")
            elif completion_rate >= 50:
                print("⚠️  需要注意！只有一半的任務包含完整的新欄位")
            else:
                print("❌ 需要修正！多數任務缺少新欄位，API 整合可能有問題")
            
            if completion_rate < 100:
                print("\n🔧 改進建議：")
                print("  1. 確保前端調用 API 時傳送 task_name, model_id, confidence_threshold")
                print("  2. 檢查後端 API 是否正確處理這些參數")
                print("  3. 驗證資料庫寫入邏輯是否包含新欄位")
        
        await conn.close()
        
        print(f"\n🎯 總結：")
        if latest_complete_task:
            print("✅ API 整合基本正常，新欄位可以正確寫入")
        else:
            print("❌ API 整合可能有問題，需要檢查和修正")
        
        return latest_complete_task is not None
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

if __name__ == '__main__':
    try:
        success = asyncio.run(test_api_integration())
        if not success:
            print(f"\n⚠️  建議檢查 API 整合並進行測試")
            sys.exit(1)
        else:
            print(f"\n✅ API 整合測試完成！")
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 執行測試時發生錯誤: {e}")
        sys.exit(1)