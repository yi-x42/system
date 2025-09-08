"""
分析記錄資料庫服務
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.analysis import AnalysisRecord
from app.core.logger import main_logger as logger

class AnalysisRecordService:
    """分析記錄資料庫服務類"""
    
    @staticmethod
    async def create_analysis_record(
        db: AsyncSession,
        video_path: str,
        video_name: str,
        analysis_type: str,
        **kwargs
    ) -> AnalysisRecord:
        """建立分析記錄"""
        try:
            record = AnalysisRecord(
                video_path=video_path,
                video_name=video_name,
                analysis_type=analysis_type,
                status="processing",
                **kwargs
            )
            
            db.add(record)
            await db.flush()  # 獲取 ID 但不提交
            await db.refresh(record)
            
            logger.info(f"✅ 建立分析記錄成功: ID={record.id}")
            return record
            
        except Exception as e:
            logger.error(f"❌ 建立分析記錄失敗: {e}")
            raise
    
    @staticmethod
    async def get_analysis_record(db: AsyncSession, record_id: int) -> Optional[AnalysisRecord]:
        """獲取分析記錄"""
        try:
            result = await db.execute(
                select(AnalysisRecord).where(AnalysisRecord.id == record_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ 獲取分析記錄失敗: {e}")
            return None
    
    @staticmethod
    async def update_analysis_record(
        db: AsyncSession,
        record_id: int,
        **updates
    ) -> bool:
        """更新分析記錄"""
        try:
            result = await db.execute(
                update(AnalysisRecord)
                .where(AnalysisRecord.id == record_id)
                .values(**updates)
            )
            
            if result.rowcount > 0:
                logger.info(f"✅ 更新分析記錄成功: ID={record_id}")
                return True
            else:
                logger.warning(f"⚠️ 分析記錄不存在: ID={record_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 更新分析記錄失敗: {e}")
            return False
    
    @staticmethod
    async def get_recent_analyses(
        db: AsyncSession,
        limit: int = 10,
        analysis_type: Optional[str] = None
    ) -> List[AnalysisRecord]:
        """獲取最近的分析記錄"""
        try:
            query = select(AnalysisRecord).order_by(AnalysisRecord.created_at.desc()).limit(limit)
            
            if analysis_type:
                query = query.where(AnalysisRecord.analysis_type == analysis_type)
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"❌ 獲取最近分析記錄失敗: {e}")
            return []
    
    @staticmethod
    async def get_analysis_statistics(db: AsyncSession) -> Dict[str, Any]:
        """獲取分析統計資訊"""
        try:
            # 這裡可以添加統計查詢
            # 目前返回基本資訊
            total_result = await db.execute(
                select(AnalysisRecord.id).count()
            )
            total_analyses = total_result.scalar()
            
            return {
                "total_analyses": total_analyses,
                "detection_analyses": 0,  # 可以添加具體統計
                "annotation_analyses": 0,
                "successful_analyses": 0,
                "failed_analyses": 0
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取分析統計失敗: {e}")
            return {}

# 全域實例
analysis_record_service = AnalysisRecordService()
