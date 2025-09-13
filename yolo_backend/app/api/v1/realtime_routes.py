"""
實時檢測 API 路由
提供啟動、停止和監控實時攝影機檢測的 API 端點
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional

from app.services.realtime_detection_service import get_realtime_detection_service
from app.services.new_database_service import DatabaseService
from app.core.database import get_async_db
from app.core.logger import api_logger

router = APIRouter(prefix="/realtime", tags=["實時檢測"])

@router.post("/start/{camera_index}")
async def start_realtime_detection(
    camera_index: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """啟動實時攝影機檢測"""
    try:
        realtime_service = get_realtime_detection_service()
        db_service = DatabaseService()
        
        # 生成任務 ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # 獲取攝影機實際解析度 (使用攝影機流管理器)
        from app.services.camera_stream_manager import camera_stream_manager
        import cv2  # 仍需要用於其他地方
        resolution_info = camera_stream_manager.get_camera_resolution(camera_index)
        if resolution_info:
            width = resolution_info['width']
            height = resolution_info['height']
            fps = resolution_info['fps']
        else:
            # 如果無法獲取攝影機解析度，使用預設值
            width, height, fps = 640, 480, 30.0
        
        # 在資料庫中創建任務記錄
        task_data = {
            "task_type": "realtime_camera",
            "status": "pending",
            "source_info": {
                "camera_index": camera_index,
                "camera_type": "USB",
                "backend": "CAP_DSHOW" if hasattr(cv2, 'CAP_DSHOW') else "default"
            },
            "source_width": width,
            "source_height": height,
            "source_fps": fps
        }
        
        db_task = await db_service.create_analysis_task(db, task_data)
        db_task_id = db_task.id
        
        # 啟動實時檢測
        success = await realtime_service.start_realtime_detection(
            task_id=str(db_task_id),
            camera_id=f"camera_{camera_index}",
            device_index=camera_index,
            db_service=db_service
        )
        
        if not success:
            # 如果啟動失敗，更新資料庫狀態
            await db_service.update_task_status(db, db_task_id, "failed")
            raise HTTPException(status_code=500, detail="實時檢測啟動失敗")
        
        # 更新任務狀態為運行中
        await db_service.update_task_status(db, db_task_id, "running")
        
        api_logger.info(f"實時檢測啟動成功: 任務 {db_task_id}, 攝影機 {camera_index}")
        
        return {
            "status": "success",
            "message": "實時檢測已啟動",
            "task_id": str(db_task_id),
            "camera_index": camera_index,
            "websocket_endpoint": f"ws://26.86.64.166:8001/ws/detection"
        }
        
    except Exception as e:
        api_logger.error(f"啟動實時檢測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動實時檢測失敗: {str(e)}")


@router.post("/stop/{camera_index}")
async def stop_realtime_detection(
    camera_index: int,
    db: AsyncSession = Depends(get_async_db)
):
    """停止攝影機的實時檢測"""
    try:
        realtime_service = get_realtime_detection_service()
        db_service = DatabaseService()
        
        # 根據攝影機索引找到對應的任務
        sessions = realtime_service.get_all_sessions()
        target_task_id = None
        total_detections = 0
        
        for session in sessions:
            if session.get('camera_index') == camera_index and session.get('running'):
                target_task_id = session.get('task_id')
                total_detections = session.get('detection_count', 0)
                break
        
        if not target_task_id:
            raise HTTPException(status_code=404, detail=f"攝影機 {camera_index} 沒有運行中的檢測任務")
        
        # 停止實時檢測
        success = await realtime_service.stop_realtime_detection(target_task_id)
        
        if success:
            # 更新資料庫任務狀態
            await db_service.update_task_status(db, target_task_id, "completed")
            
            api_logger.info(f"實時檢測停止成功: 攝影機 {camera_index}, 任務 {target_task_id}")
            
            return {
                "status": "success",
                "message": "實時檢測已停止",
                "task_id": target_task_id,
                "camera_index": camera_index,
                "total_detections": total_detections
            }
        else:
            return {
                "status": "warning",
                "message": "任務可能已經停止或不存在",
                "task_id": target_task_id,
                "camera_index": camera_index
            }
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"停止實時檢測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止實時檢測失敗: {str(e)}")


@router.get("/status/{camera_index}")
async def get_detection_status(camera_index: int):
    """獲取攝影機的實時檢測狀態"""
    try:
        realtime_service = get_realtime_detection_service()
        
        # 根據攝影機索引找到對應的會話
        sessions = realtime_service.get_all_sessions()
        
        for session in sessions:
            if session.get('camera_index') == camera_index:
                return {
                    "running": session.get('running', False),
                    "task_id": session.get('task_id'),
                    "camera_index": camera_index,
                    "start_time": session.get('start_time'),
                    "detection_count": session.get('detection_count', 0)
                }
        
        # 沒有找到對應的會話
        return {
            "running": False,
            "camera_index": camera_index,
            "detection_count": 0
        }
        
    except Exception as e:
        api_logger.error(f"獲取檢測狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取檢測狀態失敗: {str(e)}")


@router.get("/status/task/{task_id}")
async def get_task_detection_status(task_id: str):
    """根據任務ID獲取實時檢測狀態"""
    try:
        realtime_service = get_realtime_detection_service()
        
        status = realtime_service.get_session_status(task_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail="檢測任務不存在")
        
        return {
            "status": "success",
            "data": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"獲取檢測狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取檢測狀態失敗: {str(e)}")


@router.get("/sessions")
async def get_all_detection_sessions():
    """獲取所有實時檢測會話"""
    try:
        realtime_service = get_realtime_detection_service()
        
        sessions = realtime_service.get_all_sessions()
        
        return {
            "status": "success",
            "data": sessions,
            "total": len(sessions)
        }
        
    except Exception as e:
        api_logger.error(f"獲取檢測會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取檢測會話失敗: {str(e)}")


@router.get("/detection-results/{task_id}")
async def get_realtime_detection_results(
    task_id: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
):
    """獲取實時檢測結果"""
    try:
        db_service = DatabaseService()
        
        # 從資料庫獲取檢測結果
        results = await db_service.get_detection_results(
            task_id=task_id,
            limit=limit,
            offset=offset,
            db=db
        )
        
        return {
            "status": "success",
            "data": results,
            "task_id": task_id,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        api_logger.error(f"獲取檢測結果失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取檢測結果失敗: {str(e)}")


@router.get("/statistics/{task_id}")
async def get_detection_statistics(
    task_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """獲取檢測統計資訊"""
    try:
        realtime_service = get_realtime_detection_service()
        db_service = DatabaseService()
        
        # 獲取即時狀態
        session_status = realtime_service.get_session_status(task_id)
        
        # 獲取資料庫統計
        db_stats = await db_service.get_task_statistics(task_id, db=db)
        
        return {
            "status": "success",
            "data": {
                "session_status": session_status,
                "database_statistics": db_stats,
                "task_id": task_id
            }
        }
        
    except Exception as e:
        api_logger.error(f"獲取檢測統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取檢測統計失敗: {str(e)}")


@router.delete("/cleanup")
async def cleanup_all_sessions():
    """清理所有檢測會話（緊急停止）"""
    try:
        realtime_service = get_realtime_detection_service()
        
        await realtime_service.cleanup()
        
        api_logger.info("所有實時檢測會話已清理")
        
        return {
            "status": "success",
            "message": "所有實時檢測會話已停止並清理"
        }
        
    except Exception as e:
        api_logger.error(f"清理檢測會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清理檢測會話失敗: {str(e)}")
