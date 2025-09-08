"""
資料庫基礎模型
"""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, DateTime, func
from datetime import datetime
from typing import Optional

class Base(DeclarativeBase):
    """資料庫基礎模型"""
    pass

class BaseModel(Base):
    """基礎模型類"""
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主鍵ID")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        comment="建立時間"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment="更新時間"
    )
