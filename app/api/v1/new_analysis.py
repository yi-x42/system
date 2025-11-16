# 新的 API 路由 - 根據新資料庫架構設計

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
import shutil

from app.core.database import get_db
from app.services.new_database_service import DatabaseService
from app.services.enhanced_video_analysis_service import EnhancedVideoAnalysisService
from app.services.task_processor import get_task_processor
from app.models.database import AnalysisTask, DetectionResult, DataSource, SystemConfig
from app.core.logger import main_logger as logger
from app.utils.media_info import probe_resolution

router = APIRouter()
db_service = DatabaseService()

# 觸發重載

# ============================================================================
# 分析任務相關 API
# ============================================================================

@router.post("/tasks/create", summary="創建分析任務（前端專用）")
async def create_analysis_task_api(
    task_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    創建分析任務並保存到 analysis_tasks 表
    專為前端「開始分析」按鈕設計
    
    請求格式:
    {
        "task_type": "video_file",
        "source_info": {
            "file_path": "/path/to/video.mp4",
            "original_filename": "test.mp4",
            "confidence_threshold": 0.8
        },
        "source_width": 1920,
        "source_height": 1080,
        "source_fps": 30.0
    }
    """
    try:
        # 驗證必要欄位
        if not task_data.get('task_type'):
            raise HTTPException(status_code=400, detail="task_type 是必要欄位")
        
        if not task_data.get('source_info'):
            raise HTTPException(status_code=400, detail="source_info 是必要欄位")
        
        # 如果是 video_file 類型，檢查檔案路徑
        if task_data['task_type'] == 'video_file':
            file_path = task_data['source_info'].get('file_path')
            if not file_path:
                raise HTTPException(status_code=400, detail="影片檔案分析需要提供 file_path")
            
            # 檢查檔案是否存在
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"檔案不存在: {file_path}")
            
            # 如果沒有提供解析度資訊，嘗試獲取
            if not task_data.get('source_width') or not task_data.get('source_height'):
                try:
                    import cv2
                    cap = cv2.VideoCapture(file_path)
                    if cap.isOpened():
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                        cap.release()
                        
                        if not task_data.get('source_width'):
                            task_data['source_width'] = width
                        if not task_data.get('source_height'):
                            task_data['source_height'] = height
                        if not task_data.get('source_fps'):
                            task_data['source_fps'] = fps
                    else:
                        # 無法讀取影片時使用預設值
                        task_data.setdefault('source_width', 1920)
                        task_data.setdefault('source_height', 1080)
                        task_data.setdefault('source_fps', 25.0)
                except Exception as e:
                    logger.warning(f"無法獲取影片資訊: {e}")
                    # 使用預設值
                    task_data.setdefault('source_width', 1920)
                    task_data.setdefault('source_height', 1080)
                    task_data.setdefault('source_fps', 25.0)
        
        # 創建分析任務
        task = await db_service.create_analysis_task(db, task_data)
        
        logger.info(f"✅ 分析任務已創建: {task.id}")
        
        return {
            'success': True,
            'task_id': task.id,
            'message': '分析任務已創建成功',
            'task': task.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建分析任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"創建分析任務失敗: {str(e)}")


@router.post("/tasks/create-and-execute", summary="創建並執行分析任務")
async def create_and_execute_analysis_task(
    task_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    創建分析任務並立即開始執行
    適合前端「開始分析」按鈕直接調用
    """
    try:
        # 先創建任務
        task_response = await create_analysis_task_api(task_data, db)
        
        if not task_response['success']:
            return task_response
        
        task_id = task_response['task_id']
        
        # 獲取任務
        task = await db_service.get_analysis_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="剛創建的分析任務不存在")
        
        # 獲取任務處理器並開始執行
        processor = get_task_processor()
        
        if task.task_type == "video_file":
            background_tasks.add_task(processor.process_video_file_task, db, task)
        else:
            raise HTTPException(status_code=400, detail=f"不支援的任務類型: {task.task_type}")
        
        logger.info(f"🚀 分析任務 {task_id} 已創建並開始執行")
        
        return {
            'success': True,
            'task_id': task_id,
            'message': '分析任務已創建並開始執行',
            'status': 'scheduled',
            'task': task_response['task']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建並執行分析任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建並執行分析任務失敗: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建分析任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"創建分析任務失敗: {str(e)}")


@router.post("/tasks/{task_id}/execute", summary="執行分析任務")
async def execute_analysis_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    執行指定的分析任務
    這個API會在背景執行實際的YOLO分析並保存結果到資料庫
    """
    try:
        # 獲取任務
        task = await db_service.get_analysis_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="分析任務不存在")
        
        # 檢查任務狀態
        if task.status != "pending":
            raise HTTPException(status_code=400, detail=f"任務狀態不正確: {task.status}")
        
        # 獲取任務處理器
        processor = get_task_processor()
        
        # 在背景執行分析
        if task.task_type == "video_file":
            background_tasks.add_task(processor.process_video_file_task, db, task)
        else:
            raise HTTPException(status_code=400, detail=f"不支援的任務類型: {task.task_type}")
        
        logger.info(f"🚀 分析任務 {task_id} 已排程執行")
        
        return {
            'success': True,
            'task_id': task_id,
            'message': '分析任務已開始執行',
            'status': 'scheduled'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"執行分析任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"執行分析任務失敗: {str(e)}")


@router.get("/tasks/{task_id}", summary="獲取分析任務狀態")
async def get_analysis_task_status(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """獲取分析任務的詳細狀態"""
    try:
        task = await db_service.get_analysis_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="分析任務不存在")
        
        return task.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取任務狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取任務狀態失敗: {str(e)}")


@router.get("/tasks/{task_id}/results", summary="獲取分析任務的檢測結果")
async def get_analysis_task_results(
    task_id: int,
    limit: int = 1000,
    frame_start: Optional[int] = None,
    frame_end: Optional[int] = None,
    object_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """獲取分析任務的檢測結果"""
    try:
        # 檢查任務是否存在
        task = await db_service.get_analysis_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="分析任務不存在")
        
        # 獲取檢測結果
        detections = await db_service.get_detection_results(
            db, task_id, frame_start, frame_end, object_type, limit
        )
        
        # 獲取統計資訊
        statistics = await db_service.get_detection_statistics(db, task_id)
        
        return {
            'task_id': task_id,
            'task_status': task.status,
            'detections': [detection.to_dict() for detection in detections],
            'statistics': statistics,
            'total_detections': len(detections)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取檢測結果失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取檢測結果失敗: {str(e)}")

@router.post("/new-analysis/start-video-analysis", summary="開始影片檔案分析")
async def start_video_analysis(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    source_id: Optional[int] = Form(None),
    file_path: Optional[str] = Form(None),
    task_name: str = Form("影片分析任務"),
    model_id: str = Form("yolo11n"),  # 可能是內建名稱或資料庫數字ID (字串型態)
    confidence_threshold: float = Form(0.5),
    db: AsyncSession = Depends(get_db)
):
    """上傳影片並開始分析"""
    try:
        # 驗證至少提供檔案或檔案路徑其中一個
        if not file and not file_path:
            raise HTTPException(status_code=400, detail="必須提供檔案或檔案路徑")
        
        actual_file_path = None
        
        # 如果提供了檔案路徑，使用伺服器上的檔案
        if file_path:
            logger.info(f"🎬 使用伺服器檔案: {file_path}")
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="指定的影片檔案不存在")
            
            # 檢查檔案格式
            if not file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                raise HTTPException(status_code=400, detail="不支援的影片格式")
            
            actual_file_path = file_path
            original_filename = os.path.basename(file_path)
        else:
            # 處理上傳的檔案
            logger.info(f"🎬 處理上傳檔案: {file.filename}")
            # 檢查檔案格式
            if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                raise HTTPException(status_code=400, detail="不支援的影片格式")
            
            # 儲存上傳的影片
            upload_dir = "uploads/videos"
            os.makedirs(upload_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            actual_file_path = f"{upload_dir}/{timestamp}_{file.filename}"
            
            with open(actual_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            original_filename = file.filename
        
        logger.info(f"🎬 分析檔案路徑: {actual_file_path}")

        # 解析模型：支援傳入數字型 ID（資料庫）或直接給檔名/別名
        selected_model_id: Optional[int] = None
        model_path_resolved: Optional[str] = None
        try:
            # 嘗試將 model_id 解析為整數 ID
            numeric_id = int(model_id)
            selected_model_id = numeric_id
            from sqlalchemy import select
            from app.models.database import Model
            q = select(Model).where(Model.id == numeric_id)
            res = await db.execute(q)
            m = res.scalar_one_or_none()
            if not m:
                raise HTTPException(status_code=404, detail=f"模型 ID {numeric_id} 不存在")
            model_path_resolved = m.path
            logger.info(f"📦 使用資料庫模型 ID={numeric_id} path={model_path_resolved}")
        except ValueError:
            # 非數字，視為直接提供的模型名稱或路徑
            logger.info(f"📦 使用直接提供模型識別: {model_id}")
            model_path_resolved = model_id  # 可能是 yolo11n.pt 或 'yolo11n'
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"解析模型失敗: {e}")
            raise HTTPException(status_code=500, detail="解析模型失敗")

        # 建立分析任務（保留原始 model_id 方便追蹤）
        task_data = {
            'task_type': 'video_file',
            'source_info': {
                'source_id': source_id,
                'file_path': actual_file_path,
                'original_filename': original_filename
            },
            'task_name': task_name,
            'model_id': model_id,
            'confidence_threshold': confidence_threshold
        }

        # 量測來源解析度和FPS並寫入專用欄位（若量測失敗則略過，不阻斷流程）
        try:
            import cv2
            cap = cv2.VideoCapture(actual_file_path)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps <= 0:  # 如果無法獲取 FPS
                    fps = 25.0  # 影片預設值
                cap.release()
                
                task_data['source_width'] = width
                task_data['source_height'] = height
                task_data['source_fps'] = fps
            else:
                # 無法開啟影片，使用預設值
                task_data['source_width'] = 1920
                task_data['source_height'] = 1080
                task_data['source_fps'] = 25.0
        except Exception as e:
            logger.warning(f"無法獲取影片解析度: {e}")
            # 發生錯誤時使用預設值
            task_data['source_width'] = 1920
            task_data['source_height'] = 1080
            task_data['source_fps'] = 25.0
        
        task = await db_service.create_analysis_task(db, task_data)
        logger.info(f"🎬 分析任務已建立: {task.id}")
        
        # 在背景執行影片分析
        background_tasks.add_task(process_video_analysis, task.id, actual_file_path, model_path_resolved)
        
        return {
            'success': True,
            'task_id': task.id,
            'message': '影片分析任務已建立',
            'task': task.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"影片分析啟動失敗: {str(e)}")

@router.post("/analysis/camera/{source_id}", summary="開始即時攝影機分析")
async def start_camera_analysis(
    source_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """開始即時攝影機分析"""
    try:
        # 檢查資料來源是否存在
        data_source = await db_service.get_data_source(db, source_id)
        if not data_source:
            raise HTTPException(status_code=404, detail="資料來源不存在")
        
        if data_source.source_type != 'camera':
            raise HTTPException(status_code=400, detail="資料來源不是攝影機類型")
        
        # 檢查是否已有正在運行的任務
        running_tasks = await db_service.get_running_tasks(db)
        for task in running_tasks:
            if task.source_info and task.source_info.get('source_id') == source_id:
                raise HTTPException(status_code=400, detail="此攝影機已在分析中")
        
    # 建立分析任務
        task_data = {
            'task_type': 'realtime_camera',
            'source_info': {
                'source_id': source_id,
                'camera_config': data_source.config
            }
        }

        # 嘗試從攝影機設定推導來源 URL 來量測解析度
        try:
            cam_cfg = data_source.config or {}
            source_url = None
            if isinstance(cam_cfg, dict):
                source_url = cam_cfg.get('rtsp_url') or cam_cfg.get('url')
                if not source_url:
                    ip = cam_cfg.get('ip')
                    port = cam_cfg.get('port')
                    if ip and port:
                        source_url = f"http://{ip}:{port}"
            if source_url:
                w, h = probe_resolution(source_url)
                if w and h:
                    task_data['source_info']['frame_width'] = int(w)
                    task_data['source_info']['frame_height'] = int(h)
        except Exception:
            pass
        
        task = await db_service.create_analysis_task(db, task_data)
        
        # 在背景執行攝影機分析
        background_tasks.add_task(process_camera_analysis, task.id, data_source.config)
        
        return {
            'success': True,
            'task_id': task.id,
            'message': '攝影機分析任務已開始',
            'task': task.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"攝影機分析啟動失敗: {str(e)}")

@router.post("/analysis/{task_id}/stop", summary="停止分析任務")
async def stop_analysis(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """停止正在運行的分析任務"""
    try:
        task = await db_service.get_analysis_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        if task.status != 'running':
            raise HTTPException(status_code=400, detail="任務不在運行狀態")
        
        # 更新任務狀態
        success = await db_service.complete_analysis_task(db, task_id, 'completed')
        
        if success:
            return {
                'success': True,
                'message': '任務已停止',
                'task_id': task_id
            }
        else:
            raise HTTPException(status_code=500, detail="停止任務失敗")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止任務失敗: {str(e)}")

@router.get("/analysis/tasks", summary="取得分析任務列表")
async def get_analysis_tasks(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """取得分析任務列表"""
    try:
        tasks = await db_service.get_analysis_tasks(db, task_type, status, limit)
        
        return {
            'success': True,
            'tasks': [task.to_dict() for task in tasks],
            'count': len(tasks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得任務列表失敗: {str(e)}")

@router.delete("/analysis/tasks/{task_id}", summary="刪除分析任務")
async def delete_analysis_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    刪除分析任務及其相關資料
    - 刪除任務本身
    - 級聯刪除所有相關的檢測結果
    - 只允許刪除非運行狀態的任務
    """
    try:
        # 檢查任務是否存在
        task = await db_service.get_analysis_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        # 檢查任務狀態，不允許刪除運行中的任務
        if task.status == 'running':
            raise HTTPException(
                status_code=400, 
                detail="無法刪除運行中的任務，請先停止任務"
            )
        
        # 執行級聯刪除
        deleted_detections = await db_service.delete_analysis_task_cascade(db, task_id)
        
        return {
            'success': True,
            'message': f"任務 {task_id} 已刪除",
            'task_id': task_id,
            'deleted_detections': deleted_detections
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除任務失敗: {str(e)}")

@router.get("/analysis/{task_id}", summary="取得分析任務詳情")
async def get_analysis_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """取得特定分析任務的詳細資訊"""
    try:
        task = await db_service.get_analysis_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        # 取得統計資料
        statistics = await db_service.get_detection_statistics(db, task_id)
        
        return {
            'success': True,
            'task': task.to_dict(),
            'statistics': statistics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得任務詳情失敗: {str(e)}")

@router.get("/analysis/{task_id}/resolution", summary="取得任務來源解析度")
async def get_task_resolution(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """回傳 source_info 中的 frame_width/frame_height（若存在）。"""
    try:
        task = await db_service.get_analysis_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")
        info = task.source_info or {}
        w = info.get('frame_width')
        h = info.get('frame_height')
        return {
            'success': True,
            'task_id': task_id,
            'frame_width': w,
            'frame_height': h
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得來源解析度失敗: {str(e)}")

# ============================================================================
# 檢測結果相關 API
# ============================================================================

@router.get("/detection/{task_id}/results", summary="取得檢測結果")
async def get_detection_results(
    task_id: int,
    frame_start: Optional[int] = None,
    frame_end: Optional[int] = None,
    object_type: Optional[str] = None,
    limit: int = 10000,
    db: AsyncSession = Depends(get_db)
):
    """取得檢測結果"""
    try:
        results = await db_service.get_detection_results(
            db, task_id, frame_start, frame_end, object_type, limit
        )
        
        return {
            'success': True,
            'results': [result.to_dict() for result in results],
            'count': len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得檢測結果失敗: {str(e)}")

@router.get("/detection/{task_id}/statistics", summary="取得檢測統計")
async def get_detection_statistics(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """取得檢測統計資料"""
    try:
        statistics = await db_service.get_detection_statistics(db, task_id)
        
        return {
            'success': True,
            'statistics': statistics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得檢測統計失敗: {str(e)}")

# ============================================================================
# 資料來源相關 API
# ============================================================================

@router.get("/sources", summary="取得資料來源列表")
async def get_data_sources(
    source_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """取得資料來源列表"""
    try:
        sources = await db_service.get_data_sources(db, source_type, status)
        
        return {
            'success': True,
            'sources': [source.to_dict() for source in sources],
            'count': len(sources)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得資料來源失敗: {str(e)}")

@router.post("/sources", summary="建立資料來源")
async def create_data_source(
    source_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """建立新的資料來源"""
    try:
        source = await db_service.create_data_source(db, source_data)
        
        return {
            'success': True,
            'source': source.to_dict(),
            'message': '資料來源建立成功'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立資料來源失敗: {str(e)}")

@router.get("/sources/{source_id}", summary="取得資料來源詳情")
async def get_data_source(
    source_id: int,
    db: AsyncSession = Depends(get_db)
):
    """取得特定資料來源的詳細資訊"""
    try:
        source = await db_service.get_data_source(db, source_id)
        if not source:
            raise HTTPException(status_code=404, detail="資料來源不存在")
        
        return {
            'success': True,
            'source': source.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得資料來源失敗: {str(e)}")

# ============================================================================
# 系統配置相關 API
# ============================================================================

@router.get("/config", summary="取得系統配置")
async def get_system_configs(
    config_type: str = Query("kv"),
    db: AsyncSession = Depends(get_db)
):
    """取得所有系統配置"""
    try:
        configs = await db.execute(
            select(SystemConfig).where(SystemConfig.config_type == config_type)
        )
        
        return {
            'success': True,
            'configs': [config.to_dict() for config in configs.scalars().all()],
            'count': configs.rowcount or 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得系統配置失敗: {str(e)}")

@router.get("/config/{key}", summary="取得特定配置")
async def get_config_value(
    key: str,
    config_type: str = Query("kv"),
    db: AsyncSession = Depends(get_db)
):
    """取得特定配置值"""
    try:
        result = await db.execute(
            select(SystemConfig).where(
                SystemConfig.config_type == config_type, SystemConfig.config_key == key
            )
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        return {
            'success': True,
            'key': key,
            'value': config.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得配置失敗: {str(e)}")

@router.post("/config/{key}", summary="設定系統配置")
async def set_config_value(
    key: str,
    config_data: Dict[str, str],
    config_type: str = Query("kv"),
    db: AsyncSession = Depends(get_db)
):
    """設定系統配置值"""
    try:
        value = config_data.get('value')
        description = config_data.get('description')
        
        if value is None:
            raise HTTPException(status_code=400, detail="配置值不能為空")
        
        success = await db_service.set_config(db, key, value, description, config_type=config_type)
        
        if success:
            return {
                'success': True,
                'message': '配置設定成功',
                'key': key,
                'value': value
            }
        else:
            raise HTTPException(status_code=500, detail="配置設定失敗")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"設定配置失敗: {str(e)}")

# ============================================================================
# 系統統計相關 API
# ============================================================================

@router.get("/statistics", summary="取得系統統計")
async def get_system_statistics(
    db: AsyncSession = Depends(get_db)
):
    """取得系統整體統計資料"""
    try:
        statistics = await db_service.get_system_statistics(db)
        
        return {
            'success': True,
            'statistics': statistics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得系統統計失敗: {str(e)}")

# ============================================================================
# 背景任務處理函數
# ============================================================================

async def process_video_analysis(task_id: int, file_path: str, model_path: Optional[str] = None):
    """背景處理影片分析 (支援動態模型)"""
    logger.info(f"🎬 開始處理影片分析任務 {task_id}: {file_path}")
    
    # 需要創建新的資料庫會話用於背景任務
    from app.core.database import AsyncSessionLocal
    
    try:
        # 確保檔案存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"影片檔案不存在: {file_path}")
        
        logger.info(f"📁 影片檔案存在，開始分析: {file_path}")
        
        # 初始化基本的影片分析服務（不使用資料庫整合版）
        from app.services.video_analysis_service import VideoAnalysisService
        # 若未顯式傳入，嘗試從任務紀錄解析 model_id；否則 fallback 預設
        resolved_model_path = model_path or "yolo11n.pt"
        if model_path is None:
            try:
                from app.models.database import AnalysisTask, Model
                from sqlalchemy import select
                async with AsyncSessionLocal() as s2:
                    task_obj = await s2.get(AnalysisTask, task_id)
                    if task_obj and task_obj.model_id:
                        # 嘗試轉 int
                        try:
                            mid = int(task_obj.model_id)
                            q = select(Model).where(Model.id == mid)
                            r = await s2.execute(q)
                            mm = r.scalar_one_or_none()
                            if mm:
                                resolved_model_path = mm.path
                                logger.info(f"📦 從任務 model_id 解析模型路徑: {resolved_model_path}")
                        except ValueError:
                            # 非數值就直接當作路徑或名稱
                            resolved_model_path = task_obj.model_id
            except Exception as ie:
                logger.warning(f"嘗試從任務解析模型失敗，使用預設: {ie}")
        analysis_service = VideoAnalysisService(model_path=resolved_model_path)
        logger.info(f"🎯 使用影片分析模型: {resolved_model_path}")
        
        # 執行影片分析
        results = analysis_service.analyze_video_file(file_path)
        logger.info(f"📊 分析完成，共檢測到 {len(analysis_service.detection_records)} 個目標")
        
        # 手動保存檢測結果到資料庫
        async with AsyncSessionLocal() as session:
            db_service = DatabaseService()
            
            # 開始任務
            await db_service.start_analysis_task(session, task_id)
            
            # 準備檢測結果資料
            detection_data = []
            for detection in analysis_service.detection_records:
                detection_record = {
                    "frame_number": detection.frame_number,
                    "timestamp": datetime.now(),
                    "object_type": detection.object_type,
                    "confidence": detection.confidence,
                    "bbox_x1": detection.bbox_x1,
                    "bbox_y1": detection.bbox_y1,
                    "bbox_x2": detection.bbox_x2,
                    "bbox_y2": detection.bbox_y2,
                    "center_x": detection.center_x,
                    "center_y": detection.center_y
                }
                detection_data.append(detection_record)
            
            # 保存檢測結果
            if detection_data:
                await db_service.save_detection_results(session, task_id, detection_data)
                logger.info(f"✅ 已保存 {len(detection_data)} 個檢測結果到資料庫")
            
            # 完成任務
            await db_service.complete_analysis_task(session, task_id, "completed")
            
            # 更新任務詳細結果
            task = await session.get(AnalysisTask, task_id)
            if task:
                task.result_data = json.dumps({
                    "total_detections": len(detection_data),
                    "video_info": results.get("video_info", {}),
                    "detection_summary": results.get("detection_summary", {}),
                    "analysis_duration": results.get("analysis_duration", 0)
                }, ensure_ascii=False, default=str)
                await session.commit()
            
            logger.info(f"🎉 影片分析任務 {task_id} 完成")
        
    except Exception as e:
        logger.error(f"❌ 影片分析任務 {task_id} 失敗: {str(e)}")
        
        # 更新任務狀態為失敗
        try:
            async with AsyncSessionLocal() as session:
                db_service = DatabaseService()
                await db_service.complete_analysis_task(session, task_id, "failed")
                
                task = await session.get(AnalysisTask, task_id)
                if task:
                    task.error_message = str(e)
                    await session.commit()
                    logger.info(f"❌ 任務 {task_id} 狀態已更新為失敗")
        except Exception as update_error:
            logger.error(f"❌ 更新失敗任務狀態失敗: {update_error}")
        
        raise

async def process_camera_analysis(task_id: int, camera_config: Dict[str, Any]):
    """背景處理即時攝影機分析"""
    # 這裡會整合即時攝影機分析邏輯
    print(f"開始處理攝影機分析任務 {task_id}: {camera_config}")
    # TODO: 實作攝影機分析邏輯

# ============================================================================
# 資料庫查看 API - 用於檢視資料庫內容
# ============================================================================

@router.get("/database/detection_results", summary="查看檢測結果表內容")
async def view_detection_results_table(
    task_id: Optional[int] = None,
    object_type: Optional[str] = None,
    limit: int = 10000,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    查看 detection_results 表的內容
    
    參數:
    - task_id: 可選，按特定任務ID過濾
    - object_type: 可選，按物件類型過濾 (person, car, bike等)
    - limit: 每頁顯示數量，預設10000 (最大)
    - offset: 偏移量，用於分頁
    """
    try:
        from sqlalchemy import select, func
        from app.models.database import DetectionResult
        
        # 建構查詢
        query = select(DetectionResult)
        count_query = select(func.count(DetectionResult.id))
        
        # 應用過濾條件
        if task_id:
            query = query.where(DetectionResult.task_id == task_id)
            count_query = count_query.where(DetectionResult.task_id == task_id)
            
        if object_type:
            query = query.where(DetectionResult.object_type == object_type)
            count_query = count_query.where(DetectionResult.object_type == object_type)
        
        # 添加分頁和排序
        query = query.order_by(DetectionResult.id.desc()).limit(limit).offset(offset)
        
        # 執行查詢
        result = await db.execute(query)
        detection_results = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        # 轉換為字典格式
        results_data = []
        for detection in detection_results:
            results_data.append({
                'id': detection.id,
                'task_id': detection.task_id,
                'frame_number': detection.frame_number,
                'timestamp': detection.frame_timestamp.isoformat() if detection.frame_timestamp else None,
                'object_type': detection.object_type,
                'confidence': detection.confidence,
                'bbox_x1': detection.bbox_x1,
                'bbox_y1': detection.bbox_y1,
                'bbox_x2': detection.bbox_x2,
                'bbox_y2': detection.bbox_y2,
                'center_x': detection.center_x,
                'center_y': detection.center_y
            })
        
        return {
            'success': True,
            'table_name': 'detection_results',
            'total_count': total_count,
            'current_page_count': len(results_data),
            'limit': limit,
            'offset': offset,
            'data': results_data,
            'filters_applied': {
                'task_id': task_id,
                'object_type': object_type
            }
        }
        
    except Exception as e:
        logger.error(f"查看檢測結果表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查看檢測結果表失敗: {str(e)}")

@router.get("/database/analysis_tasks", summary="查看分析任務表內容")
async def view_analysis_tasks_table(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    查看 analysis_tasks 表的內容，特別關注 source_info 字段
    
    參數:
    - task_type: 可選，按任務類型過濾 ('realtime_camera' 或 'video_file')
    - status: 可選，按狀態過濾 ('pending', 'running', 'completed', 'failed')
    - limit: 每頁顯示數量，預設50
    - offset: 偏移量，用於分頁
    """
    try:
        from sqlalchemy import select, func
        from app.models.database import AnalysisTask
        
        # 建構查詢
        query = select(AnalysisTask)
        count_query = select(func.count(AnalysisTask.id))
        
        # 應用過濾條件
        if task_type:
            query = query.where(AnalysisTask.task_type == task_type)
            count_query = count_query.where(AnalysisTask.task_type == task_type)
            
        if status:
            query = query.where(AnalysisTask.status == status)
            count_query = count_query.where(AnalysisTask.status == status)
        
        # 添加分頁和排序
        query = query.order_by(AnalysisTask.id.desc()).limit(limit).offset(offset)
        
        # 執行查詢
        result = await db.execute(query)
        analysis_tasks = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        # 轉換為字典格式，特別處理 source_info
        tasks_data = []
        for task in analysis_tasks:
            # 解析 source_info JSON
            source_info_parsed = None
            if task.source_info:
                try:
                    if isinstance(task.source_info, str):
                        source_info_parsed = json.loads(task.source_info)
                    else:
                        source_info_parsed = task.source_info
                except json.JSONDecodeError:
                    source_info_parsed = {"error": "無法解析JSON", "raw_value": task.source_info}
            
            tasks_data.append({
                'id': task.id,
                'task_type': task.task_type,
                'status': task.status,
                'source_info': source_info_parsed,  # 結構化的 source_info
                'source_info_raw': task.source_info,  # 原始的 source_info
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'created_at': task.created_at.isoformat() if task.created_at else None
            })
        
        return {
            'success': True,
            'table_name': 'analysis_tasks',
            'total_count': total_count,
            'current_page_count': len(tasks_data),
            'limit': limit,
            'offset': offset,
            'data': tasks_data,
            'filters_applied': {
                'task_type': task_type,
                'status': status
            },
            'source_info_examples': {
                'camera_example': {
                    'camera_index': 0,
                    'resolution': {'width': 640, 'height': 480},
                    'backend': 'DEFAULT'
                },
                'video_file_example': {
                    'file_path': '/path/to/video.mp4',
                    'resolution': {'width': 1920, 'height': 1080},
                    'duration': 120.5
                }
            }
        }
        
    except Exception as e:
        logger.error(f"查看分析任務表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查看分析任務表失敗: {str(e)}")

@router.get("/database/source_info/{task_id}", summary="查看特定任務的source_info詳情")
async def view_task_source_info(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    查看特定分析任務的 source_info 詳細資訊
    
    參數:
    - task_id: 任務ID
    """
    try:
        from sqlalchemy import select
        from app.models.database import AnalysisTask
        
        # 查詢特定任務
        query = select(AnalysisTask).where(AnalysisTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail=f"找不到ID為 {task_id} 的任務")
        
        # 解析 source_info
        source_info_parsed = None
        source_info_type = type(task.source_info).__name__
        
        if task.source_info:
            try:
                if isinstance(task.source_info, str):
                    source_info_parsed = json.loads(task.source_info)
                else:
                    source_info_parsed = task.source_info
            except json.JSONDecodeError as e:
                source_info_parsed = {
                    "error": "JSON解析失敗",
                    "error_message": str(e),
                    "raw_value": task.source_info
                }
        
        return {
            'success': True,
            'task_id': task_id,
            'task_basic_info': {
                'id': task.id,
                'task_type': task.task_type,
                'status': task.status,
                'created_at': task.created_at.isoformat() if task.created_at else None
            },
            'source_info_analysis': {
                'data_type': source_info_type,
                'is_null': task.source_info is None,
                'raw_value': task.source_info,
                'parsed_value': source_info_parsed,
                'size_bytes': len(str(task.source_info)) if task.source_info else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查看任務source_info失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查看任務source_info失敗: {str(e)}")

@router.get("/database/tables_summary", summary="資料庫表格概覽")
async def view_database_tables_summary(db: AsyncSession = Depends(get_db)):
    """
    取得資料庫各表格的基本統計資訊
    """
    try:
        from sqlalchemy import select, func, text
        from app.models.database import AnalysisTask, DetectionResult, DataSource, SystemConfig
        
        summary = {}
        
        # 分析任務表統計
        task_count = await db.execute(select(func.count(AnalysisTask.id)))
        task_count = task_count.scalar()
        
        task_by_type = await db.execute(
            select(AnalysisTask.task_type, func.count(AnalysisTask.id))
            .group_by(AnalysisTask.task_type)
        )
        task_by_type = {row[0]: row[1] for row in task_by_type.fetchall()}
        
        task_by_status = await db.execute(
            select(AnalysisTask.status, func.count(AnalysisTask.id))
            .group_by(AnalysisTask.status)
        )
        task_by_status = {row[0]: row[1] for row in task_by_status.fetchall()}
        
        # 檢測結果表統計
        detection_count = await db.execute(select(func.count(DetectionResult.id)))
        detection_count = detection_count.scalar()
        
        detection_by_type = await db.execute(
            select(DetectionResult.object_type, func.count(DetectionResult.id))
            .group_by(DetectionResult.object_type)
        )
        detection_by_type = {row[0]: row[1] for row in detection_by_type.fetchall()}
        
        # 資料來源表統計
        source_count = await db.execute(select(func.count(DataSource.id)))
        source_count = source_count.scalar()
        
        # 系統配置表統計
        config_count = await db.execute(select(func.count(SystemConfig.id)))
        config_count = config_count.scalar()
        
        summary = {
            'success': True,
            'database_overview': {
                'analysis_tasks': {
                    'total_count': task_count,
                    'by_task_type': task_by_type,
                    'by_status': task_by_status
                },
                'detection_results': {
                    'total_count': detection_count,
                    'by_object_type': detection_by_type
                },
                'data_sources': {
                    'total_count': source_count
                },
                'system_config': {
                    'total_count': config_count
                }
            },
            'available_endpoints': {
                'view_detection_results': '/api/v1/database/detection_results',
                'view_analysis_tasks': '/api/v1/database/analysis_tasks',
                'view_source_info': '/api/v1/database/source_info/{task_id}',
                'view_tables_summary': '/api/v1/database/tables_summary'
            }
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"取得資料庫概覽失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取得資料庫概覽失敗: {str(e)}")
