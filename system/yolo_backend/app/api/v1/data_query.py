#!/usr/bin/env python3
"""
資料查詢 API 端點 - 提供給組員存取資料庫內容
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO

from app.core.database import get_async_db
from app.models.analysis import AnalysisRecord, DetectionResult, BehaviorEvent

# 創建專用的資料查詢路由器
data_router = APIRouter(prefix="/api/v1/data", tags=["資料查詢"])

@data_router.get("/summary", summary="資料庫總覽")
async def get_database_summary(db: AsyncSession = Depends(get_async_db)):
    """取得資料庫總覽統計"""
    try:
        # 基本統計
        analysis_count = await db.execute(select(func.count(AnalysisRecord.id)))
        detection_count = await db.execute(select(func.count(DetectionResult.id)))
        event_count = await db.execute(select(func.count(BehaviorEvent.id)))
        
        # 最新分析時間
        latest_analysis = await db.execute(
            select(AnalysisRecord.created_at).order_by(desc(AnalysisRecord.created_at)).limit(1)
        )
        latest_time = latest_analysis.scalar_one_or_none()
        
        return {
            "database_name": "yolo_analysis",
            "total_analyses": analysis_count.scalar(),
            "total_detections": detection_count.scalar(),
            "total_events": event_count.scalar(),
            "latest_analysis": latest_time,
            "status": "active",
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

@data_router.get("/analyses", summary="分析記錄列表")
async def get_analyses(
    limit: int = Query(20, ge=1, le=100, description="限制筆數"),
    offset: int = Query(0, ge=0, description="偏移量"),
    status: Optional[str] = Query(None, description="狀態篩選"),
    db: AsyncSession = Depends(get_async_db)
):
    """取得分析記錄列表"""
    try:
        query = select(AnalysisRecord).order_by(desc(AnalysisRecord.created_at))
        
        if status:
            query = query.where(AnalysisRecord.status == status)
            
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        analyses = result.scalars().all()
        
        return [
            {
                "id": analysis.id,
                "video_name": analysis.video_name,
                "analysis_type": analysis.analysis_type,
                "status": analysis.status,
                "duration": analysis.duration,
                "fps": analysis.fps,
                "total_frames": analysis.total_frames,
                "total_detections": analysis.total_detections,
                "unique_objects": analysis.unique_objects,
                "created_at": analysis.created_at,
                "analysis_duration": analysis.analysis_duration
            }
            for analysis in analyses
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

@data_router.get("/analyses/{analysis_id}", summary="特定分析詳情")
async def get_analysis_detail(
    analysis_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """取得特定分析的詳細資訊"""
    try:
        # 取得分析記錄
        result = await db.execute(
            select(AnalysisRecord).where(AnalysisRecord.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="分析記錄不存在")
        
        # 統計檢測結果
        detection_stats = await db.execute(
            text("""
                SELECT 
                    object_type,
                    object_chinese,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM detection_results 
                WHERE analysis_id = :analysis_id
                GROUP BY object_type, object_chinese
                ORDER BY count DESC
            """),
            {"analysis_id": analysis_id}
        )
        
        detection_summary = []
        for row in detection_stats:
            detection_summary.append({
                "object_type": row.object_type,
                "object_chinese": row.object_chinese or row.object_type,
                "count": row.count,
                "avg_confidence": round(float(row.avg_confidence), 3) if row.avg_confidence else 0
            })
        
        # 統計行為事件
        event_count = await db.execute(
            select(func.count(BehaviorEvent.id)).where(BehaviorEvent.analysis_id == analysis_id)
        )
        
        return {
            "analysis": {
                "id": analysis.id,
                "video_name": analysis.video_name,
                "analysis_type": analysis.analysis_type,
                "status": analysis.status,
                "duration": analysis.duration,
                "fps": analysis.fps,
                "total_frames": analysis.total_frames,
                "total_detections": analysis.total_detections,
                "unique_objects": analysis.unique_objects,
                "created_at": analysis.created_at,
                "analysis_duration": analysis.analysis_duration
            },
            "detection_summary": detection_summary,
            "event_count": event_count.scalar()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

@data_router.get("/analyses/{analysis_id}/detections", summary="特定分析的檢測結果")
async def get_analysis_detections(
    analysis_id: int,
    limit: int = Query(50, ge=1, le=500, description="限制筆數"),
    offset: int = Query(0, ge=0, description="偏移量"),
    object_type: Optional[str] = Query(None, description="物件類型篩選"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="最低信心度"),
    db: AsyncSession = Depends(get_async_db)
):
    """取得特定分析的檢測結果"""
    try:
        query = select(DetectionResult).where(DetectionResult.analysis_id == analysis_id)
        
        if object_type:
            query = query.where(DetectionResult.object_type == object_type)
            
        if min_confidence is not None:
            query = query.where(DetectionResult.confidence >= min_confidence)
            
        query = query.order_by(DetectionResult.frame_number).offset(offset).limit(limit)
        result = await db.execute(query)
        detections = result.scalars().all()
        
        return [
            {
                "id": det.id,
                "timestamp": det.timestamp,
                "frame_number": det.frame_number,
                "object_type": det.object_type,
                "object_chinese": det.object_chinese,
                "confidence": det.confidence,
                "center_x": det.center_x,
                "center_y": det.center_y,
                "bbox_x1": det.bbox_x1,
                "bbox_y1": det.bbox_y1,
                "bbox_x2": det.bbox_x2,
                "bbox_y2": det.bbox_y2,
                "width": det.width,
                "height": det.height,
                "area": det.area,
                "zone": det.zone,
                "zone_chinese": det.zone_chinese,
                "velocity_x": det.velocity_x,
                "velocity_y": det.velocity_y,
                "speed": det.speed,
                "direction": det.direction,
                "direction_chinese": det.direction_chinese,
                "detection_quality": det.detection_quality,
                "created_at": det.created_at
            }
            for det in detections
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

@data_router.get("/detections/stats", summary="檢測統計")
async def get_detection_stats(
    days: int = Query(7, ge=1, le=365, description="統計天數"),
    db: AsyncSession = Depends(get_async_db)
):
    """取得檢測統計資訊"""
    try:
        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 按物件類型統計
        result = await db.execute(
            text("""
                SELECT 
                    dr.object_type,
                    dr.object_chinese,
                    COUNT(*) as detection_count,
                    AVG(dr.confidence) as avg_confidence,
                    COUNT(DISTINCT dr.analysis_id) as analysis_count
                FROM detection_results dr
                WHERE dr.created_at >= :start_date
                GROUP BY dr.object_type, dr.object_chinese
                ORDER BY detection_count DESC
                LIMIT 20
            """),
            {"start_date": start_date}
        )
        
        stats = []
        for row in result:
            stats.append({
                "object_type": row.object_type,
                "object_chinese": row.object_chinese or row.object_type,
                "detection_count": row.detection_count,
                "avg_confidence": round(float(row.avg_confidence), 3),
                "analysis_count": row.analysis_count
            })
        
        return {
            "period": f"{days} 天",
            "start_date": start_date,
            "end_date": end_date,
            "total_types": len(stats),
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計查詢失敗: {str(e)}")

@data_router.get("/events", summary="行為事件列表")
async def get_behavior_events(
    limit: int = Query(20, ge=1, le=100, description="限制筆數"),
    offset: int = Query(0, ge=0, description="偏移量"),
    event_type: Optional[str] = Query(None, description="事件類型篩選"),
    severity: Optional[str] = Query(None, description="嚴重程度篩選"),
    db: AsyncSession = Depends(get_async_db)
):
    """取得行為事件列表"""
    try:
        query = select(BehaviorEvent).order_by(desc(BehaviorEvent.created_at))
        
        if event_type:
            query = query.where(BehaviorEvent.event_type == event_type)
            
        if severity:
            query = query.where(BehaviorEvent.severity == severity)
            
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        events = result.scalars().all()
        
        return [
            {
                "id": event.id,
                "analysis_id": event.analysis_id,
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "event_chinese": event.event_chinese,
                "object_type": event.object_type,
                "object_chinese": event.object_chinese,
                "duration": event.duration,
                "severity": event.severity,
                "severity_chinese": event.severity_chinese,
                "description": event.description,
                "zone": event.zone,
                "zone_chinese": event.zone_chinese,
                "position_x": event.position_x,
                "position_y": event.position_y,
                "created_at": event.created_at
            }
            for event in events
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

@data_router.get("/search", summary="搜尋資料")
async def search_data(
    keyword: str = Query(..., description="搜尋關鍵字"),
    table: str = Query("all", description="搜尋範圍: all, analyses, detections, events"),
    limit: int = Query(20, ge=1, le=100, description="限制筆數"),
    db: AsyncSession = Depends(get_async_db)
):
    """搜尋資料庫內容"""
    try:
        results = {}
        
        if table in ["all", "analyses"]:
            # 搜尋分析記錄
            query = select(AnalysisRecord).where(
                AnalysisRecord.video_name.ilike(f"%{keyword}%")
            ).order_by(desc(AnalysisRecord.created_at)).limit(limit)
            result = await db.execute(query)
            analyses = result.scalars().all()
            
            results["analyses"] = [
                {
                    "id": item.id,
                    "video_name": item.video_name,
                    "analysis_type": item.analysis_type,
                    "status": item.status,
                    "total_detections": item.total_detections,
                    "created_at": item.created_at
                }
                for item in analyses
            ]
        
        if table in ["all", "detections"]:
            # 搜尋檢測結果 (資料庫已儲存 Unity 座標)
            query = select(DetectionResult).where(
                DetectionResult.object_type.ilike(f"%{keyword}%") |
                DetectionResult.object_chinese.ilike(f"%{keyword}%")
            ).order_by(desc(DetectionResult.created_at)).limit(limit)
            result = await db.execute(query)
            detections = result.scalars().all()
            
            results["detections"] = [
                {
                    "id": item.id,
                    "analysis_id": item.analysis_id,
                    "timestamp": item.timestamp,
                    "frame_number": item.frame_number,
                    "object_type": item.object_type,
                    "object_chinese": item.object_chinese,
                    "confidence": item.confidence,
                    # Unity 螢幕座標 (已在資料庫中儲存)
                    "center_x": item.center_x,      # Unity 座標
                    "center_y": item.center_y,      # Unity 座標 (Y軸向上)
                    "bbox_x1": item.bbox_x1,        # Unity 座標 (左下角)
                    "bbox_y1": item.bbox_y1,        # Unity 座標 (左下角)
                    "bbox_x2": item.bbox_x2,        # Unity 座標 (右上角)
                    "bbox_y2": item.bbox_y2,        # Unity 座標 (右上角)
                    "width": item.width,
                    "height": item.height,
                    "area": item.area,
                    "zone": item.zone,
                    "zone_chinese": item.zone_chinese,
                    "velocity_x": item.velocity_x,
                    "velocity_y": item.velocity_y,  # Y軸向上為正
                    "speed": item.speed,
                    "direction": item.direction,
                    "direction_chinese": item.direction_chinese,
                    "track_id": getattr(item, 'track_id', None),
                    "velocity_magnitude": getattr(item, 'velocity_magnitude', item.speed),
                    "created_at": item.created_at,
                    "coordinate_system": "Unity Screen Space (left-bottom origin, Y-up)"
                }
                for item in detections
            ]
        
        if table in ["all", "events"]:
            # 搜尋行為事件
            query = select(BehaviorEvent).where(
                BehaviorEvent.event_type.ilike(f"%{keyword}%") |
                BehaviorEvent.event_chinese.ilike(f"%{keyword}%") |
                BehaviorEvent.description.ilike(f"%{keyword}%")
            ).order_by(desc(BehaviorEvent.created_at)).limit(limit)
            result = await db.execute(query)
            events = result.scalars().all()
            
            results["events"] = [
                {
                    "id": item.id,
                    "analysis_id": item.analysis_id,
                    "event_type": item.event_type,
                    "event_chinese": item.event_chinese,
                    "description": item.description,
                    "created_at": item.created_at
                }
                for item in events
            ]
        
        # 統計結果
        total_results = sum(len(v) if isinstance(v, list) else 0 for v in results.values())
        
        return {
            "keyword": keyword,
            "search_scope": table,
            "coordinate_system": "Unity Screen Space (left-bottom origin, Y-up)",
            "total_results": total_results,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜尋失敗: {str(e)}")

@data_router.get("/export/csv", summary="匯出 CSV 資料")
async def export_csv_data(
    table: str = Query(..., description="資料表名稱: analyses, detections, events"),
    analysis_id: Optional[int] = Query(None, description="特定分析ID"),
    limit: Optional[int] = Query(1000, ge=1, le=5000, description="限制筆數"),
    db: AsyncSession = Depends(get_async_db)
):
    """匯出資料為 CSV 格式"""
    try:
        if table == "analyses":
            query = select(AnalysisRecord).order_by(desc(AnalysisRecord.created_at)).limit(limit)
            result = await db.execute(query)
            data = result.scalars().all()
            
            csv_data = []
            for item in data:
                csv_data.append({
                    "ID": item.id,
                    "影片名稱": item.video_name,
                    "分析類型": item.analysis_type,
                    "狀態": item.status,
                    "影片長度": item.duration,
                    "幀率": item.fps,
                    "總幀數": item.total_frames,
                    "總檢測數": item.total_detections,
                    "唯一物件": item.unique_objects,
                    "分析耗時": item.analysis_duration,
                    "建立時間": item.created_at
                })
                
        elif table == "detections":
            query = select(DetectionResult).order_by(DetectionResult.analysis_id, DetectionResult.frame_number)
            if analysis_id:
                query = query.where(DetectionResult.analysis_id == analysis_id)
            query = query.limit(limit)
            
            result = await db.execute(query)
            data = result.scalars().all()
            
            csv_data = []
            for item in data:
                csv_data.append({
                    "分析ID": item.analysis_id,
                    "幀編號": item.frame_number,
                    "時間點": item.frame_time,
                    "物件類型": item.object_type,
                    "物件中文": item.object_chinese,
                    "信心度": item.confidence,
                    "中心X": item.center_x,
                    "中心Y": item.center_y,
                    "寬度": item.width,
                    "高度": item.height,
                    "區域": item.zone,
                    "區域中文": item.zone_chinese,
                    "檢測時間": item.created_at
                })
                
        elif table == "events":
            query = select(BehaviorEvent).order_by(desc(BehaviorEvent.created_at)).limit(limit)
            result = await db.execute(query)
            data = result.scalars().all()
            
            csv_data = []
            for item in data:
                csv_data.append({
                    "分析ID": item.analysis_id,
                    "時間戳": item.timestamp,
                    "事件類型": item.event_type,
                    "事件中文": item.event_chinese,
                    "物件類型": item.object_type,
                    "物件中文": item.object_chinese,
                    "持續時間": item.duration,
                    "嚴重程度": item.severity,
                    "嚴重程度中文": item.severity_chinese,
                    "嚴重程度": item.severity,
                    "描述": item.description,
                    "區域": item.zone,
                    "區域中文": item.zone_chinese,
                    "發生時間": item.created_at
                })
        else:
            raise HTTPException(status_code=400, detail="不支援的資料表類型")
        
        # 轉換為 CSV
        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_content = csv_buffer.getvalue()
            
            return {
                "table": table,
                "analysis_id": analysis_id,
                "record_count": len(csv_data),
                "csv_content": csv_content,
                "filename": f"{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        else:
            return {
                "table": table,
                "analysis_id": analysis_id,
                "record_count": 0,
                "csv_content": "",
                "message": "沒有找到符合條件的資料"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}")

# 健康檢查端點
@data_router.get("/health", summary="API 健康檢查")
async def health_check(db: AsyncSession = Depends(get_async_db)):
    """檢查 API 和資料庫連接狀態"""
    try:
        # 測試資料庫連接
        result = await db.execute(text("SELECT 1"))
        db_status = "connected" if result.scalar() == 1 else "error"
        
        return {
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.now(),
            "api_version": "v1.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.now()
        }
