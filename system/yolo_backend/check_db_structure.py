#!/usr/bin/env python3
"""
檢查資料庫表結構
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

# 添加後端路徑
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings

async def check_database_structure():
    """檢查資料庫表結構"""
    print("🔍 檢查資料庫表結構")
    print("=" * 50)
    
    # 替換 URL 為同步版本
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    print(f"資料庫 URL: {db_url}")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # 檢查 analysis_tasks 表結構
        print("\n📋 analysis_tasks 表結構:")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'analysis_tasks'
            ORDER BY ordinal_position
        """)
        
        if columns:
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  {col['column_name']:<20} {col['data_type']:<15} {nullable}{default}")
        else:
            print("  ❌ 表不存在或沒有欄位")
        
        # 檢查是否有解析度欄位
        resolution_fields = ['source_width', 'source_height', 'source_fps']
        existing_fields = {col['column_name'] for col in columns}
        
        print(f"\n🎯 解析度欄位檢查:")
        for field in resolution_fields:
            if field in existing_fields:
                print(f"  ✅ {field} - 已存在")
            else:
                print(f"  ❌ {field} - 不存在")
        
        # 檢查現有資料
        print(f"\n📊 資料統計:")
        try:
            stats = await conn.fetchrow("SELECT COUNT(*) as total FROM analysis_tasks")
            print(f"  總記錄數: {stats['total']}")
            
            if 'source_width' in existing_fields:
                resolution_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(source_width) as with_resolution,
                        AVG(source_width) as avg_width,
                        AVG(source_height) as avg_height
                    FROM analysis_tasks 
                    WHERE source_width IS NOT NULL
                """)
                print(f"  有解析度資料的記錄: {resolution_stats['with_resolution']}")
                if resolution_stats['with_resolution'] > 0:
                    print(f"  平均解析度: {resolution_stats['avg_width']:.0f}x{resolution_stats['avg_height']:.0f}")
        except Exception as e:
            print(f"  ❌ 無法查詢資料: {e}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")

if __name__ == "__main__":
    asyncio.run(check_database_structure())
