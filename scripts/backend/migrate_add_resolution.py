#!/usr/bin/env python3
"""
資料庫遷移腳本：添加解析度欄位到 analysis_tasks 表
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

# 添加後端路徑
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings

async def add_resolution_fields():
    """添加解析度欄位到 analysis_tasks 表"""
    print("🔄 開始資料庫遷移：添加解析度欄位")
    print("=" * 50)
    
    # 替換 URL 為同步版本
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # 檢查現有欄位
        print("📋 檢查現有表結構...")
        columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'analysis_tasks'
        """)
        
        existing_columns = {col['column_name'] for col in columns}
        print(f"現有欄位: {sorted(existing_columns)}")
        
        # 要添加的欄位
        fields_to_add = [
            ('source_width', 'INTEGER'),
            ('source_height', 'INTEGER'),
            ('source_fps', 'REAL')  # PostgreSQL 中 REAL = FLOAT
        ]
        
        # 添加欄位
        for field_name, field_type in fields_to_add:
            if field_name not in existing_columns:
                print(f"➕ 添加欄位: {field_name} ({field_type})")
                await conn.execute(f"ALTER TABLE analysis_tasks ADD COLUMN {field_name} {field_type}")
            else:
                print(f"✅ 欄位已存在: {field_name}")
        
        # 更新現有記錄
        print("\n📊 更新現有記錄...")
        
        # 查詢現有記錄
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
                
                # 轉換為數值
                try:
                    if width: width = int(width)
                    if height: height = int(height)
                    if fps: fps = float(fps)
                except (ValueError, TypeError):
                    width = height = fps = None
            
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
        
        # 驗證結果
        print("\n🔍 驗證遷移結果...")
        
        # 檢查新的表結構
        new_columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'analysis_tasks'
            ORDER BY ordinal_position
        """)
        
        print("更新後的表結構:")
        for col in new_columns:
            print(f"  {col['column_name']:<20} {col['data_type']}")
        
        # 檢查資料
        stats = await conn.fetch("""
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
        
        print("\n解析度統計:")
        for row in stats:
            print(f"  {row['task_type']}: {row['count']} 個任務")
            print(f"    平均解析度: {row['avg_width']:.0f}x{row['avg_height']:.0f}")
            print(f"    平均幀率: {row['avg_fps']:.1f}fps")
        
        await conn.close()
        
        print("\n🎉 資料庫遷移完成！")
        
    except Exception as e:
        print(f"❌ 遷移失敗: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(add_resolution_fields())
