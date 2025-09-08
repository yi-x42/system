#!/usr/bin/env python3
"""
資料庫遷移腳本：添加解析度追蹤欄位
目的：為現有的 analysis_tasks 表添加 source_width, source_height, source_fps 欄位
並從 source_info JSON 中提取現有的解析度資訊
"""

import asyncio
import asyncpg
import json
import sys
from pathlib import Path

# 添加後端路徑
sys.path.append(str(Path(__file__).parent / "yolo_backend"))

from app.core.config import settings

async def migrate_resolution_fields():
    """遷移解析度欄位"""
    print("🔄 開始資料庫遷移：添加解析度追蹤欄位")
    print("=" * 60)
    
    # 資料庫連接配置
    conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB
    )
    
    try:
        # 1. 檢查欄位是否已存在
        print("📋 檢查現有表結構...")
        columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'analysis_tasks'
        """)
        
        existing_columns = {row['column_name'] for row in columns}
        print(f"現有欄位: {sorted(existing_columns)}")
        
        # 2. 添加新欄位（如果不存在）
        new_columns = ['source_width', 'source_height', 'source_fps']
        for column in new_columns:
            if column not in existing_columns:
                print(f"➕ 添加欄位: {column}")
                if column == 'source_fps':
                    await conn.execute(f"ALTER TABLE analysis_tasks ADD COLUMN {column} FLOAT")
                else:
                    await conn.execute(f"ALTER TABLE analysis_tasks ADD COLUMN {column} INTEGER")
            else:
                print(f"✅ 欄位已存在: {column}")
        
        # 3. 更新現有記錄
        print("\n📊 更新現有記錄的解析度資訊...")
        
        tasks = await conn.fetch("SELECT id, task_type, source_info FROM analysis_tasks")
        print(f"找到 {len(tasks)} 個任務記錄")
        
        updated_count = 0
        for task in tasks:
            task_id = task['id']
            task_type = task['task_type']
            source_info = task['source_info'] or {}
            
            # 從 source_info 中提取解析度資訊
            width = None
            height = None
            fps = None
            
            if isinstance(source_info, dict):
                # 檢查各種可能的欄位名稱
                width = source_info.get('frame_width') or source_info.get('width')
                height = source_info.get('frame_height') or source_info.get('height')
                fps = source_info.get('fps') or source_info.get('framerate')
            
            # 如果沒有找到解析度資訊，使用預設值
            if not width or not height:
                if task_type == 'realtime_camera':
                    width, height, fps = 640, 480, 30.0
                else:  # video_file
                    width, height, fps = 1920, 1080, 25.0
                print(f"  任務 {task_id} ({task_type}): 使用預設值 {width}x{height}@{fps}fps")
            else:
                print(f"  任務 {task_id} ({task_type}): 提取到 {width}x{height}@{fps}fps")
            
            # 更新記錄
            await conn.execute("""
                UPDATE analysis_tasks 
                SET source_width = $1, source_height = $2, source_fps = $3
                WHERE id = $4
            """, width, height, fps or 25.0, task_id)
            
            updated_count += 1
        
        print(f"\n✅ 成功更新 {updated_count} 個任務記錄")
        
        # 4. 驗證遷移結果
        print("\n🔍 驗證遷移結果...")
        result = await conn.fetch("""
            SELECT 
                task_type,
                COUNT(*) as count,
                AVG(source_width) as avg_width,
                AVG(source_height) as avg_height,
                AVG(source_fps) as avg_fps
            FROM analysis_tasks 
            WHERE source_width IS NOT NULL
            GROUP BY task_type
        """)
        
        for row in result:
            print(f"  {row['task_type']}: {row['count']} 個任務")
            print(f"    平均解析度: {row['avg_width']:.0f}x{row['avg_height']:.0f}")
            print(f"    平均幀率: {row['avg_fps']:.1f}fps")
        
        print("\n🎉 資料庫遷移完成！")
        
    except Exception as e:
        print(f"❌ 遷移失敗: {e}")
        raise
    finally:
        await conn.close()

async def rollback_migration():
    """回滾遷移（移除新增的欄位）"""
    print("⚠️  開始回滾遷移：移除解析度欄位")
    
    conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB
    )
    
    try:
        columns_to_remove = ['source_width', 'source_height', 'source_fps']
        for column in columns_to_remove:
            print(f"🗑️  移除欄位: {column}")
            await conn.execute(f"ALTER TABLE analysis_tasks DROP COLUMN IF EXISTS {column}")
        
        print("✅ 回滾完成")
        
    except Exception as e:
        print(f"❌ 回滾失敗: {e}")
        raise
    finally:
        await conn.close()

async def check_migration_status():
    """檢查遷移狀態"""
    print("🔍 檢查遷移狀態")
    
    conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB
    )
    
    try:
        # 檢查表結構
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'analysis_tasks'
            ORDER BY ordinal_position
        """)
        
        print("現有表結構:")
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']}")
        
        # 檢查資料
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(source_width) as tasks_with_resolution,
                MIN(source_width) as min_width,
                MAX(source_width) as max_width,
                MIN(source_height) as min_height,
                MAX(source_height) as max_height
            FROM analysis_tasks
        """)
        
        print(f"\n資料統計:")
        print(f"  總任務數: {stats['total_tasks']}")
        print(f"  有解析度資料的任務: {stats['tasks_with_resolution']}")
        if stats['tasks_with_resolution'] > 0:
            print(f"  寬度範圍: {stats['min_width']} - {stats['max_width']}")
            print(f"  高度範圍: {stats['min_height']} - {stats['max_height']}")
        
    finally:
        await conn.close()

def main():
    """主函數"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python migrate_resolution.py migrate   # 執行遷移")
        print("  python migrate_resolution.py rollback  # 回滾遷移")
        print("  python migrate_resolution.py status    # 檢查狀態")
        return
    
    command = sys.argv[1]
    
    if command == 'migrate':
        asyncio.run(migrate_resolution_fields())
    elif command == 'rollback':
        asyncio.run(rollback_migration())
    elif command == 'status':
        asyncio.run(check_migration_status())
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main()
