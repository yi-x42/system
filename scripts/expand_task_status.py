#!/usr/bin/env python3
"""
擴展任務狀態定義
新增 'paused' 和 'stopping' 狀態支援前端任務管理
"""

import asyncio
import asyncpg
import sys
import os

# 將 yolo_backend 加入路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

from app.core.config import settings

async def expand_task_status_definition():
    """擴展任務狀態定義，新增 paused 和 stopping 狀態"""
    
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    
    print("🔧 擴展任務狀態定義")
    print("新增狀態：'paused' (已暫停) 和 'stopping' (停止中)")
    print("=" * 50)
    
    try:
        # 連接資料庫
        conn = await asyncpg.connect(db_url)
        
        # 檢查當前狀態約束
        print("📋 檢查當前狀態約束...")
        
        constraints = await conn.fetch("""
            SELECT conname, pg_get_constraintdef(oid) as definition
            FROM pg_constraint 
            WHERE conrelid = 'analysis_tasks'::regclass 
            AND contype = 'c';
        """)
        
        print(f"找到 {len(constraints)} 個約束：")
        for constraint in constraints:
            print(f"  - {constraint['conname']}: {constraint['definition']}")
        
        # 檢查當前狀態欄位的資料類型
        status_info = await conn.fetchrow("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'analysis_tasks'
            AND column_name = 'status';
        """)
        
        if status_info:
            print(f"\n📊 當前 status 欄位資訊：")
            print(f"  - 資料類型: {status_info['data_type']}")
            print(f"  - 最大長度: {status_info['character_maximum_length']}")
        
        # 檢查現有的狀態值
        existing_statuses = await conn.fetch("""
            SELECT DISTINCT status, COUNT(*) as count
            FROM analysis_tasks 
            WHERE status IS NOT NULL
            GROUP BY status
            ORDER BY status;
        """)
        
        print(f"\n📈 現有任務狀態分佈：")
        if existing_statuses:
            for status_row in existing_statuses:
                print(f"  - '{status_row['status']}': {status_row['count']} 個任務")
        else:
            print("  (目前沒有任務資料)")
        
        # 測試新增狀態值
        print(f"\n🧪 測試新增 'paused' 和 'stopping' 狀態...")
        
        # 測試插入 paused 狀態的任務
        paused_task_id = await conn.fetchval("""
            INSERT INTO analysis_tasks (
                task_type, status, source_info, 
                task_name, model_id, confidence_threshold
            ) VALUES (
                'realtime_camera', 'paused', '{"camera_id": "test_paused"}',
                '測試暫停任務', 'yolo11n.pt', 0.5
            ) RETURNING id;
        """)
        
        print(f"✓ 成功插入 'paused' 狀態任務，ID: {paused_task_id}")
        
        # 測試插入 stopping 狀態的任務
        stopping_task_id = await conn.fetchval("""
            INSERT INTO analysis_tasks (
                task_type, status, source_info, 
                task_name, model_id, confidence_threshold
            ) VALUES (
                'realtime_camera', 'stopping', '{"camera_id": "test_stopping"}',
                '測試停止中任務', 'yolo11n.pt', 0.5
            ) RETURNING id;
        """)
        
        print(f"✓ 成功插入 'stopping' 狀態任務，ID: {stopping_task_id}")
        
        # 驗證查詢
        new_status_tasks = await conn.fetch("""
            SELECT id, status, task_name 
            FROM analysis_tasks 
            WHERE id IN ($1, $2)
            ORDER BY id;
        """, paused_task_id, stopping_task_id)
        
        print(f"\n📊 驗證新狀態任務：")
        for task in new_status_tasks:
            print(f"  - ID {task['id']}: {task['status']} - {task['task_name']}")
        
        # 測試狀態轉換
        print(f"\n🔄 測試狀態轉換...")
        
        # paused -> running
        await conn.execute("""
            UPDATE analysis_tasks 
            SET status = 'running' 
            WHERE id = $1;
        """, paused_task_id)
        
        # stopping -> completed
        await conn.execute("""
            UPDATE analysis_tasks 
            SET status = 'completed' 
            WHERE id = $1;
        """, stopping_task_id)
        
        print("✓ 狀態轉換測試成功")
        
        # 清理測試資料
        await conn.execute("""
            DELETE FROM analysis_tasks 
            WHERE id IN ($1, $2);
        """, paused_task_id, stopping_task_id)
        
        print("✓ 清理測試資料完成")
        
        # 顯示完整的狀態列表
        print(f"\n📋 支援的任務狀態列表：")
        status_list = [
            ('pending', '待處理'),
            ('running', '運行中'),
            ('paused', '已暫停'),
            ('stopping', '停止中'),
            ('completed', '已完成'),
            ('failed', '失敗')
        ]
        
        for status, description in status_list:
            print(f"  ✓ '{status}' - {description}")
        
        await conn.close()
        
        print(f"\n🎉 任務狀態擴展完成！")
        print("PostgreSQL 現在支援所有前端需要的狀態。")
        
        return True
        
    except Exception as e:
        print(f"❌ 擴展狀態定義時發生錯誤: {e}")
        return False

if __name__ == '__main__':
    try:
        success = asyncio.run(expand_task_status_definition())
        if not success:
            sys.exit(1)
        else:
            print(f"\n✅ 任務狀態擴展測試完成！")
    except KeyboardInterrupt:
        print("\n⚠️  操作被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤: {e}")
        sys.exit(1)