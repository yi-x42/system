"""
任務服務
管理YOLO檢測任務的創建、執行、監控和停止
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_

from app.core.logger import api_logger
from app.models.database import AnalysisTask, DetectionResult

class TaskService:
    """任務管理服務"""
    
    def __init__(self):
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self._camera_service = None
    
    @property
    def camera_service(self):
        """延遲載入 CameraService"""
        if self._camera_service is None:
            from app.services.camera_service import CameraService
            self._camera_service = CameraService()
        return self._camera_service

    async def create_task(
        self,
        task_name: str,
        task_type: str,
        config: Dict[str, Any],
        db: AsyncSession = None
    ) -> str:
        """創建新任務"""
        try:
            task_id = str(uuid.uuid4())
            
            # 創建任務記錄
            task_data = {
                "id": task_id,
                "name": task_name,
                "type": task_type,  # realtime_camera, video_file, batch, training
                "status": "created",
                "config": config,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "progress": 0,
                "results": []
            }
            
            self.active_tasks[task_id] = task_data
            
            # 如果有資料庫連接，保存到資料庫
            if db:
                # 根據資料庫設計，AnalysisTask 的字段：
                # id, task_type, status, source_info, start_time, end_time, created_at
                db_task = AnalysisTask(
                    task_type=task_type,
                    status="pending",  # 使用有效的狀態值
                    source_info={
                        'task_id': task_id,
                        'task_name': task_name,
                        'config': config
                    },
                    created_at=datetime.now()
                )
                db.add(db_task)
                await db.commit()
                await db.refresh(db_task)
                
                # 更新任務數據中的資料庫ID
                task_data['db_id'] = db_task.id
            
            api_logger.info(f"任務創建成功: {task_id} - {task_name}")
            return task_id
            
        except Exception as e:
            api_logger.error(f"任務創建失敗: {e}")
            raise

    async def start_task(self, task_id: str, db: AsyncSession = None) -> bool:
        """啟動任務"""
        try:
            if task_id not in self.active_tasks:
                # 從資料庫載入任務
                if db:
                    result = await db.execute(
                        select(AnalysisTask).where(AnalysisTask.id == task_id)
                    )
                    task = result.scalar_one_or_none()
                    if task:
                        source_info = task.source_info or {}
                        self.active_tasks[task_id] = {
                            "id": source_info.get('task_id', task_id),
                            "name": source_info.get('task_name', 'Unknown'),
                            "type": task.task_type,
                            "status": task.status,
                            "config": source_info.get('config', {}),
                            "created_at": task.created_at,
                            "updated_at": datetime.now(),
                            "progress": 0,
                            "results": []
                        }
                    else:
                        api_logger.error(f"任務不存在: {task_id}")
                        return False
                else:
                    api_logger.error(f"任務不存在且無資料庫連接: {task_id}")
                    return False
            
            task = self.active_tasks[task_id]
            
            if task["status"] == "running":
                api_logger.warning(f"任務已在運行: {task_id}")
                return False
            
            # 更新任務狀態
            task["status"] = "running"
            task["updated_at"] = datetime.now()
            task["start_time"] = datetime.now()
            
            # 更新資料庫狀態為 running
            if db:
                result = await db.execute(
                    select(AnalysisTask).where(AnalysisTask.id == task_id)
                )
                db_task = result.scalar_one_or_none()
                if db_task:
                    db_task.status = "running"
                    db_task.start_time = datetime.now()
                    await db.commit()
            
            # 根據任務類型啟動相應的處理
            if task["type"] == "realtime_camera":
                asyncio.create_task(self._run_realtime_task(task_id))
            elif task["type"] == "video_file":
                asyncio.create_task(self._run_video_task(task_id))
            elif task["type"] == "batch":
                asyncio.create_task(self._run_batch_task(task_id))
            elif task["type"] == "training":
                asyncio.create_task(self._run_training_task(task_id))
            
            api_logger.info(f"任務啟動成功: {task_id}")
            return True
            
        except Exception as e:
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "error"
            api_logger.error(f"任務啟動失敗 {task_id}: {e}")
            return False

    async def stop_task(self, task_id: str, db: AsyncSession = None) -> bool:
        """停止任務"""
        try:
            if task_id not in self.active_tasks:
                api_logger.error(f"任務不存在: {task_id}")
                return False
            
            task = self.active_tasks[task_id]
            
            if task["status"] != "running":
                api_logger.warning(f"任務未在運行: {task_id}")
                return False
            
            # 更新任務狀態
            task["status"] = "stopped"
            task["updated_at"] = datetime.now()
            task["end_time"] = datetime.now()
            
            # 更新資料庫
            if db:
                result = await db.execute(
                    select(AnalysisTask).where(AnalysisTask.id == task_id)
                )
                db_task = result.scalar_one_or_none()
                if db_task:
                    db_task.status = "stopped"
                    db_task.end_time = datetime.now()
                    await db.commit()
            
            api_logger.info(f"任務停止成功: {task_id}")
            return True
            
        except Exception as e:
            api_logger.error(f"任務停止失敗 {task_id}: {e}")
            return False

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """獲取任務狀態"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].copy()
        return None

    async def get_all_tasks(self) -> List[Dict[str, Any]]:
        """獲取所有任務"""
        return list(self.active_tasks.values())

    async def delete_task(self, task_id: str, db: AsyncSession = None) -> bool:
        """刪除任務"""
        try:
            # 如果任務在運行，先停止
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                if task["status"] == "running":
                    await self.stop_task(task_id, db)
                
                # 從記憶體中移除
                del self.active_tasks[task_id]
            
            # 從資料庫中刪除
            if db:
                # 刪除相關的檢測結果
                await db.execute(
                    select(DetectionResult).where(DetectionResult.task_id == task_id)
                )
                
                # 刪除任務記錄
                result = await db.execute(
                    select(AnalysisTask).where(AnalysisTask.id == task_id)
                )
                db_task = result.scalar_one_or_none()
                if db_task:
                    await db.delete(db_task)
                    await db.commit()
            
            api_logger.info(f"任務刪除成功: {task_id}")
            return True
            
        except Exception as e:
            api_logger.error(f"任務刪除失敗 {task_id}: {e}")
            return False

    async def _run_realtime_task(self, task_id: str):
        """運行即時攝影機檢測任務"""
        try:
            from app.services.realtime_detection_service import get_realtime_detection_service
            from app.services.new_database_service import DatabaseService
            from app.core.config import settings
            
            task = self.active_tasks[task_id]
            config = task["config"]
            camera_index = config.get("camera_index", 0)
            
            # 獲取服務實例
            realtime_service = get_realtime_detection_service()
            db_service = DatabaseService()
            
            # 啟動實時檢測
            success = await realtime_service.start_realtime_detection(
                task_id=task_id,
                camera_id=f"camera_{camera_index}",
                device_index=camera_index,
                db_service=db_service,
                model_path=settings.model_path
            )
            
            if not success:
                api_logger.error(f"實時檢測啟動失敗: {task_id}")
                task["status"] = "error"
                return
            
            # 監控檢測狀態
            while task["status"] == "running":
                # 獲取檢測狀態
                status = realtime_service.get_session_status(task_id)
                if status:
                    task["progress"] = min(status["frame_count"] // 10, 100)  # 以處理的幀數計算進度
                    task["updated_at"] = datetime.now()
                    task["detection_count"] = status["detection_count"]
                    task["fps"] = status["fps"]
                
                await asyncio.sleep(2)  # 每2秒更新一次狀態
            
            # 停止實時檢測
            await realtime_service.stop_realtime_detection(task_id)
            
            # 完成任務
            task["status"] = "completed" if task["status"] == "running" else task["status"]
            task["end_time"] = datetime.now()
            
        except Exception as e:
            api_logger.error(f"即時任務執行失敗 {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "error"

    async def _run_video_task(self, task_id: str):
        """運行影片檔案分析任務"""
        try:
            task = self.active_tasks[task_id]
            config = task["config"]
            
            # 模擬影片分析
            total_frames = config.get("total_frames", 1000)
            
            for frame in range(total_frames):
                if task["status"] != "running":
                    break
                
                # 更新進度
                task["progress"] = int((frame + 1) / total_frames * 100)
                task["updated_at"] = datetime.now()
                
                # 模擬檢測結果
                if frame % 10 == 0:  # 每10幀記錄一次結果
                    result = {
                        "frame_number": frame,
                        "timestamp": datetime.now().isoformat(),
                        "objects_detected": frame % 3 + 1
                    }
                    task["results"].append(result)
                
                await asyncio.sleep(0.01)  # 模擬處理時間
            
            # 完成任務
            if task["status"] == "running":
                task["status"] = "completed"
                task["progress"] = 100
                task["end_time"] = datetime.now()
                
        except Exception as e:
            api_logger.error(f"影片任務執行失敗 {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "error"

    async def _run_batch_task(self, task_id: str):
        """運行批次處理任務"""
        try:
            task = self.active_tasks[task_id]
            config = task["config"]
            
            # 模擬批次處理
            total_files = config.get("file_count", 10)
            
            for i in range(total_files):
                if task["status"] != "running":
                    break
                
                # 更新進度
                task["progress"] = int((i + 1) / total_files * 100)
                task["updated_at"] = datetime.now()
                
                # 模擬處理結果
                result = {
                    "file_index": i,
                    "filename": f"file_{i}.jpg",
                    "processed_at": datetime.now().isoformat(),
                    "objects_detected": i % 3 + 1
                }
                
                task["results"].append(result)
                
                await asyncio.sleep(0.5)  # 模擬處理時間
            
            # 完成任務
            if task["status"] == "running":
                task["status"] = "completed"
                task["progress"] = 100
                task["end_time"] = datetime.now()
                
        except Exception as e:
            api_logger.error(f"批次任務執行失敗 {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "error"

    async def _run_training_task(self, task_id: str):
        """運行訓練任務"""
        try:
            task = self.active_tasks[task_id]
            config = task["config"]
            
            # 模擬訓練過程
            total_epochs = config.get("epochs", 20)
            
            for epoch in range(total_epochs):
                if task["status"] != "running":
                    break
                
                # 更新進度
                task["progress"] = int((epoch + 1) / total_epochs * 100)
                task["updated_at"] = datetime.now()
                
                # 模擬訓練指標
                result = {
                    "epoch": epoch + 1,
                    "loss": 1.0 - (epoch / total_epochs) * 0.8,
                    "accuracy": (epoch / total_epochs) * 0.9 + 0.1,
                    "timestamp": datetime.now().isoformat()
                }
                
                task["results"].append(result)
                
                await asyncio.sleep(2)  # 模擬訓練時間
            
            # 完成訓練
            if task["status"] == "running":
                task["status"] = "completed"
                task["progress"] = 100
                task["end_time"] = datetime.now()
                
        except Exception as e:
            api_logger.error(f"訓練任務執行失敗 {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "error"

# 全局實例
_task_service_instance = None

def get_task_service():
    """依賴注入函數，提供 TaskService 的單例"""
    global _task_service_instance
    if _task_service_instance is None:
        _task_service_instance = TaskService()
    return _task_service_instance
