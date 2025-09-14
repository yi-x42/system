#!/usr/bin/env python3
"""
PostgreSQL 資料庫遷移腳本
新增任務管理系統所需的欄位到 analysis_tasks 表
"""

import asyncio
import asyncpg
import sys
import os

# 將 yolo_backend 加入路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

from app.core.config import settings

async def add_task_management_columns():
    """新增任務管理系統所需的欄位"""
    
    # 從設定中解析資料庫連接資訊
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    
    print("🔗 連接到 PostgreSQL 資料庫...")
    print(f"資料庫 URL: {db_url.replace(settings.postgres_password, '***')}")
    
    try:
        # 連接資料庫
        conn = await asyncpg.connect(db_url)
        
        # 檢查表格是否存在
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'analysis_tasks'
            );
        """)
        
        if not table_exists:
            print("❌ analysis_tasks 表格不存在，請先初始化資料庫")
            return False
        
        print("✓ 找到 analysis_tasks 表格")
        
        # 檢查現有欄位
        existing_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'analysis_tasks'
            ORDER BY ordinal_position;
        """)
        
        print(f"\n📋 現有 analysis_tasks 表格結構 ({len(existing_columns)} 個欄位):")
        column_names = []
        for col in existing_columns:
            print(f"  - {col['column_name']} ({col['data_type']})")
            column_names.append(col['column_name'])
        
        # 定義需要新增的欄位
        new_columns = [
            ('task_name', 'VARCHAR(200)', None, '任務名稱'),
            ('model_id', 'VARCHAR(100)', None, 'YOLO模型ID'),
            ('confidence_threshold', 'REAL', '0.5', '信心度閾值')
        ]
        
        print(f"\n🔧 開始新增欄位...")
        added_count = 0
        
        for col_name, col_type, default_val, description in new_columns:
            if col_name not in column_names:
                try:
                    # 構建 ALTER TABLE 語句
                    if default_val:
                        sql = f"ALTER TABLE analysis_tasks ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"
                    else:
                        sql = f"ALTER TABLE analysis_tasks ADD COLUMN {col_name} {col_type}"
                    
                    await conn.execute(sql)
                    print(f"✓ 已新增 {col_name} 欄位 ({description})")
                    added_count += 1
                    
                except Exception as e:
                    print(f"× {col_name} 新增失敗: {e}")
            else:
                print(f"• {col_name} 欄位已存在")
        
        # 檢查更新後的表格結構
        if added_count > 0:
            updated_columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'analysis_tasks'
                ORDER BY ordinal_position;
            """)
            
            print(f"\n📋 更新後的 analysis_tasks 表格結構 ({len(updated_columns)} 個欄位):")
            for col in updated_columns:
                default_info = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  - {col['column_name']} ({col['data_type']}{default_info})")
        
        await conn.close()
        print(f"\n✅ 資料庫遷移完成！新增了 {added_count} 個欄位")
        return True
        
    except asyncpg.InvalidCatalogNameError:
        print("❌ 資料庫 'yolo_analysis' 不存在")
        print("💡 請先執行: python yolo_backend/create_database.py")
        return False
        
    except asyncpg.InvalidPasswordError:
        print("❌ 資料庫密碼錯誤")
        print("💡 請檢查 POSTGRES_PASSWORD 環境變數或配置")
        return False
        
    except Exception as e:
        print(f"❌ 連接資料庫時發生錯誤: {e}")
        print("💡 請確認：")
        print("   1. PostgreSQL 服務是否已啟動")
        print("   2. 資料庫連接參數是否正確")
        print("   3. 資料庫是否已建立")
        return False

if __name__ == '__main__':
    import sys
    sys.path.append('yolo_backend')
    
    try:
        success = asyncio.run(add_task_management_columns())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  操作被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤: {e}")
        sys.exit(1)