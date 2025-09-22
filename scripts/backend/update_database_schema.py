#!/usr/bin/env python3
"""
資料庫結構更新腳本
為 detection_results 表添加新的擴展欄位
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import engine, AsyncSessionLocal
from app.models.database import Base
from app.core.logger import main_logger as logger

async def check_column_exists(session, table_name: str, column_name: str) -> bool:
    """檢查欄位是否已存在"""
    try:
        result = await session.execute(text(f"""
            SELECT COUNT(*) as count
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' 
            AND column_name = '{column_name}'
        """))
        count = result.scalar()
        return count > 0
    except Exception as e:
        logger.error(f"檢查欄位失敗: {e}")
        return False

async def add_detection_result_columns():
    """為 detection_results 表添加新欄位"""
    
    # 要添加的新欄位列表
    new_columns = [
        ("object_id", "VARCHAR(50)"),
        ("object_chinese", "VARCHAR(50)"),
        ("width", "FLOAT"),
        ("height", "FLOAT"),
        ("area", "FLOAT"),
        ("zone", "VARCHAR(50)"),
        ("zone_chinese", "VARCHAR(50)"),
        ("velocity_x", "FLOAT"),
        ("velocity_y", "FLOAT"),
        ("speed", "FLOAT"),
        ("direction", "FLOAT"),
        ("direction_chinese", "VARCHAR(20)"),
        ("detection_quality", "VARCHAR(20)"),
        ("frame_time", "FLOAT")
    ]
    
    async with AsyncSessionLocal() as session:
        try:
            logger.info("🔄 開始檢查和更新資料庫結構...")
            
            # 檢查表是否存在
            table_exists = await session.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.tables 
                WHERE table_name = 'detection_results'
            """))
            
            if table_exists.scalar() == 0:
                logger.info("📋 detection_results 表不存在，創建完整表結構...")
                # 創建完整的表結構
                await session.execute(text("DROP TABLE IF EXISTS detection_results CASCADE"))
                await session.commit()
                
                # 重新創建所有表
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ 已創建完整的資料庫表結構")
                return
            
            # 檢查並添加缺少的欄位
            added_columns = 0
            for column_name, column_type in new_columns:
                exists = await check_column_exists(session, "detection_results", column_name)
                
                if not exists:
                    try:
                        await session.execute(text(f"""
                            ALTER TABLE detection_results 
                            ADD COLUMN {column_name} {column_type}
                        """))
                        await session.commit()
                        logger.info(f"✅ 已添加欄位: {column_name} ({column_type})")
                        added_columns += 1
                    except Exception as e:
                        logger.error(f"❌ 添加欄位 {column_name} 失敗: {e}")
                        await session.rollback()
                else:
                    logger.info(f"⏭️  欄位 {column_name} 已存在，跳過")
            
            if added_columns > 0:
                logger.info(f"🎉 資料庫更新完成！總共添加了 {added_columns} 個新欄位")
            else:
                logger.info("📋 資料庫結構已是最新版本，無需更新")
                
        except Exception as e:
            logger.error(f"❌ 資料庫更新失敗: {e}")
            await session.rollback()
            raise

async def main():
    """主函數"""
    try:
        logger.info("🚀 開始資料庫結構更新...")
        await add_detection_result_columns()
        logger.info("✨ 資料庫更新完成！")
        
    except Exception as e:
        logger.error(f"❌ 更新過程發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
