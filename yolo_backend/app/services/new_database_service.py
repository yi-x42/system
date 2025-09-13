"""
資料庫服務 - 根據新的資料庫架構重新設計
支援即時攝影機分析和影片檔案分析兩種模式
"""

import threading
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func, and_, or_

from app.models.database import AnalysisTask, DetectionResult, DataSource, SystemConfig
from app.core.database import AsyncSessionLocal
import logging

db_logger = logging.getLogger(__name__)

class DatabaseService:
    """資料庫服務類別 - 提供所有資料庫操作的封裝"""
    
    def __init__(self, db_session: AsyncSession = None):
        self.db = db_session
    
    # ============================================================================
    # 分析任務相關操作
    # ============================================================================
    
    async def create_analysis_task(self, session: AsyncSession, task_data: Dict[str, Any]) -> AnalysisTask:
        """建立新的分析任務"""
        task = AnalysisTask(
            task_type=task_data['task_type'],
            status='pending',
            source_info=task_data.get('source_info'),
            source_width=task_data.get('source_width'),
            source_height=task_data.get('source_height'),
            source_fps=task_data.get('source_fps'),
            created_at=datetime.utcnow()
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task
    
    async def start_analysis_task(self, session: AsyncSession, task_id: int) -> bool:
        """開始執行分析任務"""
        try:
            result = await session.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(
                    status='running',
                    start_time=datetime.utcnow()
                )
            )
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            db_logger.error(f"開始任務失敗: {e}")
            return False
    
    async def complete_analysis_task(self, session: AsyncSession, task_id: int, status: str = 'completed') -> bool:
        """完成分析任務"""
        try:
            result = await session.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(
                    status=status,
                    end_time=datetime.utcnow()
                )
            )
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            db_logger.error(f"完成任務失敗: {e}")
            return False
    
    async def update_task_status(self, db: AsyncSession, task_id: int, status: str) -> bool:
        """更新任務狀態"""
        try:
            # 根據狀態決定是否更新結束時間
            values = {'status': status}
            if status in ['completed', 'failed', 'cancelled']:
                values['end_time'] = datetime.utcnow()
            elif status == 'running':
                values['start_time'] = datetime.utcnow()
            
            result = await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(**values)
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            db_logger.error(f"更新任務狀態失敗: {e}")
            return False
    
    async def get_analysis_task(self, session: AsyncSession, task_id: int) -> Optional[AnalysisTask]:
        """取得特定分析任務"""
        result = await session.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def get_analysis_tasks(self, session: AsyncSession, 
                               task_type: Optional[str] = None,
                               status: Optional[str] = None,
                               limit: int = 100) -> List[AnalysisTask]:
        """取得分析任務列表"""
        query = select(AnalysisTask)
        
        if task_type:
            query = query.where(AnalysisTask.task_type == task_type)
        if status:
            query = query.where(AnalysisTask.status == status)
            
        query = query.order_by(AnalysisTask.created_at.desc()).limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_running_tasks(self, session: AsyncSession) -> List[AnalysisTask]:
        """取得正在運行的任務"""
        result = await session.execute(
            select(AnalysisTask).where(AnalysisTask.status == 'running')
        )
        return result.scalars().all()
    
    # ============================================================================
    # 檢測結果相關操作
    # ============================================================================
    
    async def save_detection_result(self, session: AsyncSession, detection_data: Dict[str, Any]) -> DetectionResult:
        """儲存單個檢測結果"""
        try:
            detection_obj = DetectionResult(
                task_id=detection_data['task_id'],
                frame_number=detection_data['frame_number'],
                timestamp=detection_data.get('timestamp', datetime.utcnow()),
                object_type=detection_data['object_type'],
                confidence=detection_data['confidence'],
                bbox_x1=detection_data['bbox_x1'],
                bbox_y1=detection_data['bbox_y1'],
                bbox_x2=detection_data['bbox_x2'],
                bbox_y2=detection_data['bbox_y2'],
                center_x=detection_data['center_x'],
                center_y=detection_data['center_y']
            )
            
            session.add(detection_obj)
            await session.commit()
            await session.refresh(detection_obj)
            return detection_obj
            
        except Exception as e:
            db_logger.error(f"儲存檢測結果失敗: {e}")
            await session.rollback()
            raise
    
    async def save_detection_results(self, session: AsyncSession, 
                                   task_id: int, 
                                   detections: List[Dict[str, Any]]) -> bool:
        """批量儲存檢測結果"""
        try:
            detection_objects = []
            for detection in detections:
                detection_obj = DetectionResult(
                    task_id=task_id,
                    frame_number=detection['frame_number'],
                    timestamp=detection.get('timestamp', datetime.utcnow()),
                    object_type=detection['object_type'],
                    confidence=detection['confidence'],
                    bbox_x1=detection['bbox_x1'],
                    bbox_y1=detection['bbox_y1'],
                    bbox_x2=detection['bbox_x2'],
                    bbox_y2=detection['bbox_y2'],
                    center_x=detection['center_x'],
                    center_y=detection['center_y']
                )
                detection_objects.append(detection_obj)
            
            session.add_all(detection_objects)
            await session.commit()
            return True
            
        except Exception as e:
            db_logger.error(f"儲存檢測結果失敗: {e}")
            await session.rollback()
            return False
    
    async def get_detection_results(self, session: AsyncSession,
                                  task_id: int,
                                  frame_start: Optional[int] = None,
                                  frame_end: Optional[int] = None,
                                  object_type: Optional[str] = None,
                                  limit: int = 1000) -> List[DetectionResult]:
        """取得檢測結果"""
        query = select(DetectionResult).where(DetectionResult.task_id == task_id)
        
        if frame_start is not None:
            query = query.where(DetectionResult.frame_number >= frame_start)
        if frame_end is not None:
            query = query.where(DetectionResult.frame_number <= frame_end)
        if object_type:
            query = query.where(DetectionResult.object_type == object_type)
            
        query = query.order_by(DetectionResult.frame_number).limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_detection_statistics(self, session: AsyncSession, task_id: int) -> Dict[str, Any]:
        """取得檢測統計資料"""
        # 總檢測數量
        total_count = await session.execute(
            select(func.count(DetectionResult.id)).where(DetectionResult.task_id == task_id)
        )
        total = total_count.scalar()
        
        # 按物件類型統計
        type_stats = await session.execute(
            select(
                DetectionResult.object_type,
                func.count(DetectionResult.id).label('count'),
                func.avg(DetectionResult.confidence).label('avg_confidence')
            )
            .where(DetectionResult.task_id == task_id)
            .group_by(DetectionResult.object_type)
        )
        
        type_statistics = [
            {
                'object_type': row.object_type,
                'count': row.count,
                'avg_confidence': float(row.avg_confidence)
            }
            for row in type_stats
        ]
        
        return {
            'total_detections': total,
            'type_statistics': type_statistics
        }
    
    async def cleanup_old_detections(self, session: AsyncSession, days: int = 7) -> int:
        """清理舊的檢測結果（用於即時攝影機資料）"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 只清理即時攝影機的檢測結果
        subquery = select(AnalysisTask.id).where(
            and_(
                AnalysisTask.task_type == 'realtime_camera',
                AnalysisTask.created_at < cutoff_date
            )
        )
        
        result = await session.execute(
            delete(DetectionResult).where(
                DetectionResult.task_id.in_(subquery)
            )
        )
        
        deleted_count = result.rowcount
        await session.commit()
        
        return deleted_count
    
    # ============================================================================
    # 資料來源相關操作
    # ============================================================================
    
    async def create_data_source(self, session: AsyncSession, source_data: Dict[str, Any]) -> DataSource:
        """建立新的資料來源"""
        source = DataSource(
            source_type=source_data['source_type'],
            name=source_data['name'],
            config=source_data.get('config'),
            status=source_data.get('status', 'active'),
            created_at=datetime.utcnow()
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)
        return source
    
    async def get_data_sources(self, session: AsyncSession, 
                             source_type: Optional[str] = None,
                             status: Optional[str] = None) -> List[DataSource]:
        """取得資料來源列表"""
        query = select(DataSource)
        
        if source_type:
            query = query.where(DataSource.source_type == source_type)
        if status:
            query = query.where(DataSource.status == status)
            
        query = query.order_by(DataSource.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_data_source(self, session: AsyncSession, source_id: int) -> Optional[DataSource]:
        """取得特定資料來源"""
        result = await session.execute(
            select(DataSource).where(DataSource.id == source_id)
        )
        return result.scalar_one_or_none()
    
    async def update_data_source_status(self, session: AsyncSession, 
                                      source_id: int, 
                                      status: str) -> bool:
        """更新資料來源狀態"""
        try:
            result = await session.execute(
                update(DataSource)
                .where(DataSource.id == source_id)
                .values(
                    status=status,
                    last_check=datetime.utcnow()
                )
            )
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            db_logger.error(f"更新資料來源狀態失敗: {e}")
            return False
    
    # ============================================================================
    # 系統配置相關操作
    # ============================================================================
    
    async def get_config(self, session: AsyncSession, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """取得系統配置值"""
        result = await session.execute(
            select(SystemConfig.config_value).where(SystemConfig.config_key == key)
        )
        value = result.scalar_one_or_none()
        return value if value is not None else default_value
    
    async def set_config(self, session: AsyncSession, 
                        key: str, 
                        value: str, 
                        description: Optional[str] = None) -> bool:
        """設定系統配置值"""
        try:
            # 檢查是否已存在
            existing = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == key)
            )
            config = existing.scalar_one_or_none()
            
            if config:
                # 更新現有配置
                await session.execute(
                    update(SystemConfig)
                    .where(SystemConfig.config_key == key)
                    .values(
                        config_value=value,
                        description=description or config.description,
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                # 建立新配置
                new_config = SystemConfig(
                    config_key=key,
                    config_value=value,
                    description=description,
                    updated_at=datetime.utcnow()
                )
                session.add(new_config)
            
            await session.commit()
            return True
            
        except Exception as e:
            db_logger.error(f"設定配置失敗: {e}")
            await session.rollback()
            return False
    
    async def get_all_configs(self, session: AsyncSession) -> List[SystemConfig]:
        """取得所有系統配置"""
        result = await session.execute(
            select(SystemConfig).order_by(SystemConfig.config_key)
        )
        return result.scalars().all()
    
    # ============================================================================
    # 統計和報告功能
    # ============================================================================
    
    async def get_system_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """取得系統整體統計"""
        # 任務統計
        task_stats = await session.execute(
            select(
                AnalysisTask.task_type,
                AnalysisTask.status,
                func.count(AnalysisTask.id).label('count')
            )
            .group_by(AnalysisTask.task_type, AnalysisTask.status)
        )
        
        # 資料來源統計
        source_stats = await session.execute(
            select(
                DataSource.source_type,
                DataSource.status,
                func.count(DataSource.id).label('count')
            )
            .group_by(DataSource.source_type, DataSource.status)
        )
        
        # 最近24小時檢測統計
        recent_detections = await session.execute(
            select(func.count(DetectionResult.id))
            .where(DetectionResult.timestamp >= datetime.utcnow() - timedelta(days=1))
        )
        
        return {
            'task_statistics': [
                {
                    'task_type': row.task_type,
                    'status': row.status,
                    'count': row.count
                }
                for row in task_stats
            ],
            'source_statistics': [
                {
                    'source_type': row.source_type,
                    'status': row.status,
                    'count': row.count
                }
                for row in source_stats
            ],
            'recent_detections_24h': recent_detections.scalar() or 0
        }

    # 同步檢測結果儲存（用於即時檢測）
    # ============================================================================
    
    def create_detection_result_sync(self, detection_data: Dict[str, Any]) -> bool:
        """同步儲存檢測結果（用於即時檢測）- 使用同步資料庫連接"""
        try:
            # 使用同步資料庫連接，避免 asyncio 衝突
            from app.core.database import sync_engine
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            # 建立同步 session
            SyncSessionLocal = sessionmaker(bind=sync_engine)
            
            with SyncSessionLocal() as session:
                # 使用原始 SQL 插入，避免 ORM 的 async 問題
                sql = text("""
                    INSERT INTO detection_results 
                    (task_id, frame_number, timestamp, object_type, confidence, 
                     bbox_x1, bbox_y1, bbox_x2, bbox_y2, center_x, center_y)
                    VALUES 
                    (:task_id, :frame_number, :timestamp, :object_type, :confidence, 
                     :bbox_x1, :bbox_y1, :bbox_x2, :bbox_y2, :center_x, :center_y)
                """)
                
                session.execute(sql, {
                    'task_id': int(detection_data['task_id']),
                    'frame_number': detection_data['frame_number'],
                    'timestamp': detection_data['timestamp'],
                    'object_type': detection_data['object_type'],
                    'confidence': detection_data['confidence'],
                    'bbox_x1': detection_data['bbox_x1'],
                    'bbox_y1': detection_data['bbox_y1'],
                    'bbox_x2': detection_data['bbox_x2'],
                    'bbox_y2': detection_data['bbox_y2'],
                    'center_x': detection_data['center_x'],
                    'center_y': detection_data['center_y']
                })
                
                session.commit()
                db_logger.debug(f"成功同步儲存檢測結果到任務 {detection_data.get('task_id')}")
                return True
                
        except Exception as e:
            db_logger.error(f"同步儲存檢測結果失敗: {e}")
            return False

# 建立服務實例
db_service = DatabaseService()
