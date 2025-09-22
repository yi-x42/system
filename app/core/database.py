"""
資料庫連接配置
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from typing import AsyncGenerator
from .config import settings

logger = logging.getLogger(__name__)

# 異步資料庫引擎
async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DATABASE_ECHO,
    future=True
)

# 為了向後兼容性
engine = async_engine

# 異步會話工廠
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 同步資料庫引擎 (用於 Alembic 遷移)
sync_database_url = settings.DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql://"
)
sync_engine = create_engine(sync_database_url)
SyncSessionLocal = sessionmaker(bind=sync_engine)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """獲取異步資料庫會話"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"資料庫會話錯誤: {e}")
            raise
        finally:
            await session.close()

# 別名，供後台管理使用
get_db = get_async_db

async def init_database():
    """初始化資料庫"""
    try:
        from app.models.base import Base
        
        async with async_engine.begin() as conn:
            # 創建所有表格
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ 資料庫初始化完成")
        return True
    except Exception as e:
        logger.error(f"❌ 資料庫初始化失敗: {e}")
        return False

async def check_database_connection():
    """檢查資料庫連接"""
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar_one()  # 修正：使用 scalar_one() 而不是 fetchone()
        logger.info("✅ 資料庫連接正常")
        return True
    except Exception as e:
        logger.error(f"❌ 資料庫連接失敗: {e}")
        return False
