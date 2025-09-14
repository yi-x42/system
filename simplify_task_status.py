#!/usr/bin/env python3
"""
簡化任務狀態定義
移除 'stopping' 狀態，採用簡化的 5 狀態設計
"""

import asyncio
import asyncpg
import sys
import os

# 將 yolo_backend 加入路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

from app.core.config import settings

async def simplify_task_status():
    """簡化任務狀態，移除 stopping 狀態"""
    
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    
    print("🔧 簡化任務狀態定義")
    print("移除 'stopping' 狀態，採用 5 狀態設計")
    print("=" * 50)
    
    try:
        # 連接資料庫
        conn = await asyncpg.connect(db_url)
        
        # 步驟 1: 檢查是否有 stopping 狀態的任務
        print("📋 檢查是否有 'stopping' 狀態的任務...")
        
        stopping_tasks = await conn.fetch("""
            SELECT id, task_name, status 
            FROM analysis_tasks 
            WHERE status = 'stopping';
        """)
        
        if stopping_tasks:
            print(f"找到 {len(stopping_tasks)} 個 'stopping' 狀態的任務：")
            for task in stopping_tasks:
                print(f"  - ID {task['id']}: {task['task_name']}")
            
            # 將 stopping 狀態的任務改為 completed
            print("🔄 將 'stopping' 狀態任務轉換為 'completed'...")
            
            updated_count = await conn.fetchval("""
                UPDATE analysis_tasks 
                SET status = 'completed', end_time = NOW()
                WHERE status = 'stopping'
                RETURNING COUNT(*);
            """)
            
            print(f"✓ 已將 {updated_count} 個任務從 'stopping' 轉換為 'completed'")
        else:
            print("✓ 沒有找到 'stopping' 狀態的任務")
        
        # 步驟 2: 移除舊約束
        print(f"\n🗑️  移除舊的狀態約束...")
        
        await conn.execute("""
            ALTER TABLE analysis_tasks 
            DROP CONSTRAINT IF EXISTS analysis_tasks_status_check;
        """)
        
        print("✓ 已移除舊約束")
        
        # 步驟 3: 新增簡化的狀態約束
        print(f"\n➕ 新增簡化的狀態約束...")
        
        await conn.execute("""
            ALTER TABLE analysis_tasks 
            ADD CONSTRAINT analysis_tasks_status_check 
            CHECK (status IN (
                'pending', 
                'running', 
                'paused', 
                'completed', 
                'failed'
            ));
        """)
        
        print("✓ 已新增簡化的狀態約束")
        
        # 步驟 4: 驗證新約束
        print(f"\n📋 驗證新約束...")
        
        new_constraint = await conn.fetchrow("""
            SELECT conname, pg_get_constraintdef(oid) as definition
            FROM pg_constraint 
            WHERE conrelid = 'analysis_tasks'::regclass 
            AND contype = 'c'
            AND conname LIKE '%status%';
        """)
        
        if new_constraint:
            print(f"新約束：{new_constraint['conname']}")
            print(f"定義：{new_constraint['definition']}")
        
        # 步驟 5: 測試所有狀態值
        print(f"\n🧪 測試簡化後的狀態值...")
        
        test_statuses = [
            ('pending', '待處理測試'),
            ('running', '運行中測試'),
            ('paused', '已暫停測試'),
            ('completed', '已完成測試'),
            ('failed', '失敗測試')
        ]
        
        test_task_ids = []
        
        for status, task_name in test_statuses:
            try:
                task_id = await conn.fetchval("""
                    INSERT INTO analysis_tasks (
                        task_type, status, source_info, 
                        task_name, model_id, confidence_threshold
                    ) VALUES (
                        'realtime_camera', $1, '{"test": true}',
                        $2, 'yolo11n.pt', 0.5
                    ) RETURNING id;
                """, status, task_name)
                
                test_task_ids.append(task_id)
                print(f"✓ '{status}' 狀態測試成功")
                
            except Exception as e:
                print(f"× '{status}' 狀態測試失敗: {e}")
        
        # 步驟 6: 測試 stopping 狀態是否被拒絕
        print(f"\n❌ 測試 'stopping' 狀態是否被正確拒絕...")
        
        try:
            await conn.fetchval("""
                INSERT INTO analysis_tasks (
                    task_type, status, source_info, 
                    task_name, model_id, confidence_threshold
                ) VALUES (
                    'realtime_camera', 'stopping', '{"test": true}',
                    '應該失敗的測試', 'yolo11n.pt', 0.5
                ) RETURNING id;
            """)
            print("× 錯誤：'stopping' 狀態不應該被允許")
        except Exception:
            print("✓ 正確：'stopping' 狀態被成功拒絕")
        
        # 步驟 7: 清理測試資料
        if test_task_ids:
            await conn.execute("""
                DELETE FROM analysis_tasks 
                WHERE id = ANY($1);
            """, test_task_ids)
            print(f"✓ 已清理 {len(test_task_ids)} 個測試任務")
        
        # 步驟 8: 顯示最終狀態
        print(f"\n📋 簡化後的狀態列表：")
        status_descriptions = [
            ('pending', '待處理 - 任務已建立但尚未開始'),
            ('running', '運行中 - 任務正在執行'),
            ('paused', '已暫停 - 任務暫時停止，可恢復'),
            ('completed', '已完成 - 任務完成（自然完成或用戶停止）'),
            ('failed', '失敗 - 任務執行失敗')
        ]
        
        for status, description in status_descriptions:
            print(f"  ✓ '{status}' - {description}")
        
        print(f"\n🎯 簡化後的工作流程：")
        print("  - 啟動：pending → running")
        print("  - 暫停：running → paused")
        print("  - 恢復：paused → running")
        print("  - 停止：running/paused → completed (直接完成)")
        print("  - 失敗：任何狀態 → failed")
        
        await conn.close()
        
        print(f"\n🎉 任務狀態簡化完成！")
        print("移除了複雜的 'stopping' 過渡狀態。")
        
        return True
        
    except Exception as e:
        print(f"❌ 簡化狀態時發生錯誤: {e}")
        return False

if __name__ == '__main__':
    try:
        success = asyncio.run(simplify_task_status())
        if not success:
            sys.exit(1)
        else:
            print(f"\n✅ 狀態簡化完成！")
    except KeyboardInterrupt:
        print("\n⚠️  操作被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤: {e}")
        sys.exit(1)