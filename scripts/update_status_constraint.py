#!/usr/bin/env python3
"""
修改任務狀態約束
移除舊約束並新增支援所有狀態的新約束
"""

import asyncio
import asyncpg
import sys
import os

# 將 yolo_backend 加入路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

from app.core.config import settings

async def update_task_status_constraint():
    """更新任務狀態約束，支援所有前端需要的狀態"""
    
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    
    print("🔧 更新任務狀態約束")
    print("支援狀態：pending, running, paused, stopping, completed, failed")
    print("=" * 60)
    
    try:
        # 連接資料庫
        conn = await asyncpg.connect(db_url)
        
        # 步驟 1: 檢查當前約束
        print("📋 檢查當前狀態約束...")
        
        status_constraint = await conn.fetchrow("""
            SELECT conname, pg_get_constraintdef(oid) as definition
            FROM pg_constraint 
            WHERE conrelid = 'analysis_tasks'::regclass 
            AND contype = 'c'
            AND conname LIKE '%status%';
        """)
        
        if status_constraint:
            print(f"找到狀態約束：{status_constraint['conname']}")
            print(f"定義：{status_constraint['definition']}")
        else:
            print("沒有找到狀態約束")
        
        # 步驟 2: 移除舊約束
        if status_constraint:
            print(f"\n🗑️  移除舊的狀態約束...")
            
            await conn.execute(f"""
                ALTER TABLE analysis_tasks 
                DROP CONSTRAINT {status_constraint['conname']};
            """)
            
            print(f"✓ 已移除約束：{status_constraint['conname']}")
        
        # 步驟 3: 新增新的狀態約束
        print(f"\n➕ 新增支援所有狀態的約束...")
        
        await conn.execute("""
            ALTER TABLE analysis_tasks 
            ADD CONSTRAINT analysis_tasks_status_check 
            CHECK (status IN (
                'pending', 
                'running', 
                'paused', 
                'stopping', 
                'completed', 
                'failed'
            ));
        """)
        
        print("✓ 已新增新的狀態約束")
        
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
        print(f"\n🧪 測試所有狀態值...")
        
        test_statuses = [
            ('pending', '待處理測試'),
            ('running', '運行中測試'),
            ('paused', '已暫停測試'),
            ('stopping', '停止中測試'),
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
                print(f"✓ '{status}' 狀態測試成功，任務ID: {task_id}")
                
            except Exception as e:
                print(f"× '{status}' 狀態測試失敗: {e}")
        
        # 步驟 6: 驗證查詢
        if test_task_ids:
            print(f"\n📊 驗證插入的測試任務...")
            
            test_tasks = await conn.fetch("""
                SELECT id, status, task_name 
                FROM analysis_tasks 
                WHERE id = ANY($1)
                ORDER BY id;
            """, test_task_ids)
            
            for task in test_tasks:
                print(f"  - ID {task['id']}: '{task['status']}' - {task['task_name']}")
        
        # 步驟 7: 清理測試資料
        if test_task_ids:
            print(f"\n🧹 清理測試資料...")
            
            await conn.execute("""
                DELETE FROM analysis_tasks 
                WHERE id = ANY($1);
            """, test_task_ids)
            
            print(f"✓ 已清理 {len(test_task_ids)} 個測試任務")
        
        # 步驟 8: 顯示最終狀態
        print(f"\n📋 更新後支援的所有狀態：")
        status_descriptions = [
            ('pending', '待處理 - 任務已建立但尚未開始'),
            ('running', '運行中 - 任務正在執行'),
            ('paused', '已暫停 - 任務暫時停止，可恢復'),
            ('stopping', '停止中 - 任務正在停止過程中'),
            ('completed', '已完成 - 任務正常完成'),
            ('failed', '失敗 - 任務執行失敗')
        ]
        
        for status, description in status_descriptions:
            print(f"  ✓ '{status}' - {description}")
        
        await conn.close()
        
        print(f"\n🎉 任務狀態約束更新完成！")
        print("現在 PostgreSQL 支援前端所需的所有狀態。")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新狀態約束時發生錯誤: {e}")
        return False

if __name__ == '__main__':
    try:
        success = asyncio.run(update_task_status_constraint())
        if not success:
            sys.exit(1)
        else:
            print(f"\n✅ 狀態約束更新完成！")
    except KeyboardInterrupt:
        print("\n⚠️  操作被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤: {e}")
        sys.exit(1)