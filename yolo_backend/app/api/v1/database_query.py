#!/usr/bin/env python3
"""
資料庫查詢 API - 分析任務表和檢測結果表查詢
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_async_db
from app.models.database import AnalysisTask, DetectionResult

# 創建資料庫查詢路由器
db_query_router = APIRouter(prefix="/api/v1/database", tags=["資料庫查詢"])

@db_query_router.get("/tasks", summary="查看分析任務表")
async def get_analysis_tasks(
    limit: int = Query(50, ge=1, le=10000, description="限制筆數"),
    offset: int = Query(0, ge=0, description="偏移量"),
    task_type: Optional[str] = Query(None, description="任務類型過濾 (realtime_camera/video_file)"),
    status: Optional[str] = Query(None, description="狀態過濾 (pending/running/completed/failed)"),
    start_date: Optional[str] = Query(None, description="開始日期過濾 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="結束日期過濾 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    查看分析任務表
    
    - **limit**: 每頁顯示筆數 (1-200)
    - **offset**: 偏移量，用於分頁
    - **task_type**: 過濾任務類型
    - **status**: 過濾任務狀態
    - **start_date**: 開始日期過濾
    - **end_date**: 結束日期過濾
    """
    try:
        # 建立基本查詢
        query = select(AnalysisTask)
        count_query = select(func.count(AnalysisTask.id))
        
        # 建立過濾條件
        filters = []
        
        if task_type:
            filters.append(AnalysisTask.task_type == task_type)
        
        if status:
            filters.append(AnalysisTask.status == status)
            
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                filters.append(AnalysisTask.created_at >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="開始日期格式錯誤，請使用 YYYY-MM-DD")
                
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                filters.append(AnalysisTask.created_at < end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="結束日期格式錯誤，請使用 YYYY-MM-DD")
        
        # 應用過濾條件
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # 執行計數查詢
        total_result = await db.execute(count_query)
        total_count = total_result.scalar()
        
        # 執行主查詢
        query = query.order_by(desc(AnalysisTask.created_at)).limit(limit).offset(offset)
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 轉換為字典
        tasks_data = [task.to_dict() for task in tasks]
        
        return {
            "success": True,
            "data": tasks_data,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total_count,
                "has_prev": offset > 0
            },
            "filters": {
                "task_type": task_type,
                "status": status,
                "start_date": start_date,
                "end_date": end_date
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢分析任務失敗: {str(e)}")

@db_query_router.get("/detection-results", summary="查看檢測結果表")
async def get_detection_results(
    limit: int = Query(100, ge=1, le=10000, description="限制筆數"),
    offset: int = Query(0, ge=0, description="偏移量"),
    task_id: Optional[int] = Query(None, description="特定任務ID過濾"),
    object_type: Optional[str] = Query(None, description="物件類型過濾"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="最小信心度過濾"),
    start_date: Optional[str] = Query(None, description="開始日期過濾 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="結束日期過濾 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    查看檢測結果表
    
    - **limit**: 每頁顯示筆數 (1-10000)
    - **offset**: 偏移量，用於分頁
    - **task_id**: 過濾特定任務的檢測結果
    - **object_type**: 過濾物件類型 (person, car, bike 等)
    - **min_confidence**: 最小信心度閾值
    - **start_date**: 開始日期過濾
    - **end_date**: 結束日期過濾
    """
    try:
        # 建立基本查詢
        query = select(DetectionResult)
        count_query = select(func.count(DetectionResult.id))
        
        # 建立過濾條件
        filters = []
        
        if task_id is not None:
            filters.append(DetectionResult.task_id == task_id)
            
        if object_type:
            filters.append(DetectionResult.object_type == object_type)
            
        if min_confidence is not None:
            filters.append(DetectionResult.confidence >= min_confidence)
            
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                filters.append(DetectionResult.timestamp >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="開始日期格式錯誤，請使用 YYYY-MM-DD")
                
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                filters.append(DetectionResult.timestamp < end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="結束日期格式錯誤，請使用 YYYY-MM-DD")
        
        # 應用過濾條件
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # 執行計數查詢
        total_result = await db.execute(count_query)
        total_count = total_result.scalar()
        
        # 執行主查詢
        query = query.order_by(desc(DetectionResult.timestamp)).limit(limit).offset(offset)
        result = await db.execute(query)
        detections = result.scalars().all()
        
        # 轉換為字典
        detections_data = [detection.to_dict() for detection in detections]
        
        return {
            "success": True,
            "data": detections_data,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total_count,
                "has_prev": offset > 0
            },
            "filters": {
                "task_id": task_id,
                "object_type": object_type,
                "min_confidence": min_confidence,
                "start_date": start_date,
                "end_date": end_date
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢檢測結果失敗: {str(e)}")

@db_query_router.get("/tasks/{task_id}", summary="查看特定分析任務詳情")
async def get_analysis_task_detail(
    task_id: int,
    include_detections: bool = Query(False, description="是否包含檢測結果"),
    detection_limit: int = Query(50, ge=1, le=10000, description="檢測結果限制筆數"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    查看特定分析任務的詳細資訊
    
    - **task_id**: 任務ID
    - **include_detections**: 是否包含該任務的檢測結果
    - **detection_limit**: 如果包含檢測結果，限制筆數
    """
    try:
        # 查詢任務
        task_result = await db.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
        task = task_result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail=f"找不到任務 ID: {task_id}")
        
        task_data = task.to_dict()
        
        # 如果需要包含檢測結果
        if include_detections:
            detection_query = select(DetectionResult).where(
                DetectionResult.task_id == task_id
            ).order_by(desc(DetectionResult.timestamp)).limit(detection_limit)
            
            detection_result = await db.execute(detection_query)
            detections = detection_result.scalars().all()
            
            # 統計資訊
            stats_query = select(
                func.count(DetectionResult.id).label('total_detections'),
                func.count(func.distinct(DetectionResult.object_type)).label('unique_object_types'),
                func.avg(DetectionResult.confidence).label('avg_confidence'),
                func.max(DetectionResult.confidence).label('max_confidence'),
                func.min(DetectionResult.confidence).label('min_confidence')
            ).where(DetectionResult.task_id == task_id)
            
            stats_result = await db.execute(stats_query)
            stats = stats_result.first()
            
            task_data["detection_summary"] = {
                "total_detections": stats.total_detections if stats else 0,
                "unique_object_types": stats.unique_object_types if stats else 0,
                "avg_confidence": round(float(stats.avg_confidence), 3) if stats and stats.avg_confidence else 0,
                "max_confidence": float(stats.max_confidence) if stats and stats.max_confidence else 0,
                "min_confidence": float(stats.min_confidence) if stats and stats.min_confidence else 0,
                "returned_results": len(detections),
                "limit_applied": detection_limit
            }
            
            task_data["detection_results"] = [detection.to_dict() for detection in detections]
        
        return {
            "success": True,
            "data": task_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢任務詳情失敗: {str(e)}")

@db_query_router.get("/stats", summary="資料庫統計資訊")
async def get_database_stats(db: AsyncSession = Depends(get_async_db)):
    """
    取得資料庫統計資訊
    """
    try:
        # 基本統計
        task_count = await db.execute(select(func.count(AnalysisTask.id)))
        detection_count = await db.execute(select(func.count(DetectionResult.id)))
        
        # 任務狀態統計
        task_status_query = select(
            AnalysisTask.status,
            func.count(AnalysisTask.id).label('count')
        ).group_by(AnalysisTask.status)
        task_status_result = await db.execute(task_status_query)
        task_status_stats = {row.status: row.count for row in task_status_result}
        
        # 任務類型統計
        task_type_query = select(
            AnalysisTask.task_type,
            func.count(AnalysisTask.id).label('count')
        ).group_by(AnalysisTask.task_type)
        task_type_result = await db.execute(task_type_query)
        task_type_stats = {row.task_type: row.count for row in task_type_result}
        
        # 物件類型統計
        object_type_query = select(
            DetectionResult.object_type,
            func.count(DetectionResult.id).label('count')
        ).group_by(DetectionResult.object_type).order_by(desc(func.count(DetectionResult.id))).limit(10)
        object_type_result = await db.execute(object_type_query)
        object_type_stats = {row.object_type: row.count for row in object_type_result}
        
        # 最新活動
        latest_task_query = select(AnalysisTask.created_at).order_by(desc(AnalysisTask.created_at)).limit(1)
        latest_task_result = await db.execute(latest_task_query)
        latest_task_time = latest_task_result.scalar_one_or_none()
        
        latest_detection_query = select(DetectionResult.timestamp).order_by(desc(DetectionResult.timestamp)).limit(1)
        latest_detection_result = await db.execute(latest_detection_query)
        latest_detection_time = latest_detection_result.scalar_one_or_none()
        
        return {
            "success": True,
            "data": {
                "summary": {
                    "total_tasks": task_count.scalar(),
                    "total_detections": detection_count.scalar(),
                    "latest_task": latest_task_time.isoformat() if latest_task_time else None,
                    "latest_detection": latest_detection_time.isoformat() if latest_detection_time else None
                },
                "task_status_distribution": task_status_stats,
                "task_type_distribution": task_type_stats,
                "top_object_types": object_type_stats
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢統計資訊失敗: {str(e)}")
