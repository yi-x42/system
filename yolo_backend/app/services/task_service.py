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
        print("🔧 TaskService 初始化")
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self._camera_service = None
        print("🔧 TaskService 初始化完成")
    
    @property
    def camera_service(self):
        """延遲載入 CameraService"""
        if self._camera_service is None:
            from app.services.camera_service import CameraService
            self._camera_service = CameraService()
        return self._camera_service
    
    async def create_task(
        self,
        task_name: str,  # 修改參數名
        task_type: str,
        config: Dict[str, Any] = None,  # 添加config參數
        camera_id: Optional[str] = None,
        description: str = "",
        db: AsyncSession = None
    ) -> str:
        """創建新任務 - 已修復字段映射問題"""
        print("🔧 修復版本的 create_task 被調用")  # 調試輸出
        print(f"🔧 參數: task_name={task_name}, task_type={task_type}, config={config}")
        try:
            # 從config中提取參數
            if config:
                camera_id = config.get('camera_id', camera_id)
                description = config.get('description', description)
            
            task_id = str(uuid.uuid4())
            print(f"🔧 生成 task_id: {task_id}")
            
            # 準備 AnalysisTask 參數
            analysis_task_params = {
                'task_type': task_type,
                'status': 'pending',
                'source_info': {
                    'name': task_name,  # 使用修改後的參數名
                    'camera_id': camera_id,
                    'description': description
                },
                'created_at': datetime.utcnow()
            }
            print(f"🔧 AnalysisTask 參數: {analysis_task_params}")
            
            # 創建分析任務記錄
            try:
                analysis_task = AnalysisTask(**analysis_task_params)
                print("🔧 AnalysisTask 創建成功")
            except Exception as e:
                print(f"🔧 AnalysisTask 創建失敗: {e}")
                print(f"🔧 AnalysisTask 可用字段: {[attr for attr in dir(AnalysisTask) if not attr.startswith('_')]}")
                raise
            
            if db:
                print("🔧 保存到資料庫")
                db.add(analysis_task)
                await db.commit()
                await db.refresh(analysis_task)
                task_id = str(analysis_task.id)
                print(f"🔧 資料庫保存成功，新 task_id: {task_id}")
            
            # 在記憶體中追踪任務
            self.active_tasks[task_id] = {
                "id": task_id,
                "name": task_name,  # 使用新的參數名
                "type": task_type,
                "status": "pending",
                "progress": 0,
                "camera_id": camera_id,
                "description": description,
                "created_at": datetime.utcnow(),
                "start_time": None,
                "end_time": None
            }
            
            api_logger.info(f"任務已創建: {task_id} - {task_name}")  # 使用新的參數名
            return task_id
            
        except Exception as e:
            print(f"🔧 create_task 異常: {e}")
            import traceback
            traceback.print_exc()
            api_logger.error(f"創建任務失敗: {e}")
            raise
    
    async def start_task(self, task_id: str, db: AsyncSession = None) -> bool:
        """啟動任務"""
        try:
            if task_id not in self.active_tasks:
                # 從資料庫載入任務
                if db:
                    query = select(AnalysisTask).where(AnalysisTask.id == int(task_id))
                    result = await db.execute(query)
                    task = result.scalar_one_or_none()
                    
                    if task:
                        self.active_tasks[task_id] = {
                            "id": task_id,
                            "name": task.source_info.get('name', f'Task-{task_id}'),
                            "type": task.task_type,
                            "status": task.status,
                            "progress": 0,
                            "camera_id": task.source_info.get('camera_id'),
                            "description": task.source_info.get('description', ''),
                            "created_at": task.created_at,
                            "start_time": None,
                            "end_time": None
                        }
                    else:
                        api_logger.error(f"任務不存在: {task_id}")
                        return False
                else:
                    api_logger.error(f"任務不存在: {task_id}")
                    return False
            
            task = self.active_tasks[task_id]
            
            if task["status"] == "running":
                api_logger.warning(f"任務已在運行: {task_id}")
                return True
            
            # 更新任務狀態
            task["status"] = "running"
            task["start_time"] = datetime.utcnow()
            task["progress"] = 0
            
            # 更新資料庫
            if db:
                try:
                    query = select(AnalysisTask).where(AnalysisTask.id == int(task_id))
                    result = await db.execute(query)
                    db_task = result.scalar_one_or_none()
                    
                    if db_task:
                        db_task.status = 'running'
                        db_task.start_time = datetime.utcnow()
                        await db.commit()
                except Exception as e:
                    api_logger.error(f"更新資料庫任務狀態失敗: {e}")
            
            # 根據任務類型啟動相應的處理
            if task["type"] == "realtime":
                await self._start_realtime_task(task_id)
            elif task["type"] == "batch":
                await self._start_batch_task(task_id)
            elif task["type"] == "training":
                await self._start_training_task(task_id)
            
            api_logger.info(f"任務已啟動: {task_id}")
            return True
            
        except Exception as e:
            api_logger.error(f"啟動任務失敗 {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "failed"
            return False
    
    async def stop_task(self, task_id: str, db: AsyncSession = None) -> bool:
        """停止任務"""
        try:
            if task_id not in self.active_tasks:
                api_logger.warning(f"任務不存在: {task_id}")
                return False
            
            task = self.active_tasks[task_id]
            
            if task["status"] not in ["running", "paused"]:
                api_logger.warning(f"任務未在運行: {task_id}, 狀態: {task['status']}")
                return True
            
            # 停止實際的檢測服務
            try:
                from app.services.realtime_detection_service import realtime_detection_service
                success = await realtime_detection_service.stop_realtime_detection(task_id)
                if success:
                    api_logger.info(f"實時檢測服務已停止: {task_id}")
                else:
                    api_logger.warning(f"實時檢測服務停止失敗或任務不存在: {task_id}")
            except Exception as e:
                api_logger.error(f"停止實時檢測服務失敗: {e}")
            
            # 更新任務狀態
            task["status"] = "stopped"
            task["end_time"] = datetime.utcnow()
            
            # 更新資料庫
            if db:
                try:
                    query = select(AnalysisTask).where(AnalysisTask.id == int(task_id))
                    result = await db.execute(query)
                    db_task = result.scalar_one_or_none()
                    
                    if db_task:
                        db_task.status = 'completed'
                        db_task.end_time = datetime.utcnow()
                        await db.commit()
                except Exception as e:
                    api_logger.error(f"更新資料庫任務狀態失敗: {e}")
            
            api_logger.info(f"任務已停止: {task_id}")
            return True
            
        except Exception as e:
            api_logger.error(f"停止任務失敗 {task_id}: {e}")
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """獲取任務狀態"""
        return self.active_tasks.get(task_id)
    
    async def get_all_tasks(self, db: AsyncSession = None) -> List[Dict[str, Any]]:
        """獲取所有任務"""
        tasks = list(self.active_tasks.values())
        
        # 如果有資料庫連接，也載入資料庫中的任務
        if db:
            try:
                query = select(AnalysisTask).order_by(AnalysisTask.created_at.desc()).limit(50)
                result = await db.execute(query)
                db_tasks = result.scalars().all()
                
                for db_task in db_tasks:
                    task_id = str(db_task.id)
                    if task_id not in self.active_tasks:
                        tasks.append({
                            "id": task_id,
                            "name": db_task.source_info.get('name', f'Task-{task_id}'),
                            "type": db_task.task_type,
                            "status": db_task.status,
                            "progress": 100 if db_task.status == 'completed' else 0,
                            "camera_id": db_task.source_info.get('camera_id'),
                            "description": db_task.source_info.get('description', ''),
                            "created_at": db_task.created_at,
                            "start_time": db_task.start_time,
                            "end_time": db_task.end_time
                        })
            except Exception as e:
                api_logger.error(f"載入資料庫任務失敗: {e}")
        
        return tasks
    
    async def get_task_statistics(self, db: AsyncSession = None) -> Dict[str, int]:
        """獲取任務統計"""
        stats = {
            "running": 0,
            "pending": 0,
            "completed": 0,
            "failed": 0
        }
        
        # 統計記憶體中的任務
        for task in self.active_tasks.values():
            status = task["status"]
            if status in stats:
                stats[status] += 1
        
        # 統計資料庫中的任務
        if db:
            try:
                yesterday = datetime.utcnow() - timedelta(days=1)
                
                for status in stats.keys():
                    query = select(func.count(AnalysisTask.id)).where(
                        and_(
                            AnalysisTask.status == status,
                            AnalysisTask.created_at >= yesterday
                        )
                    )
                    result = await db.execute(query)
                    count = result.scalar()
                    stats[status] = max(stats[status], count)
                    
            except Exception as e:
                api_logger.error(f"統計任務失敗: {e}")
        
        return stats
    
    async def start_realtime_task(self, task_id: str, db: AsyncSession = None):
        """公共方法：啟動即時分析任務"""
        try:
            if task_id in self.active_tasks:
                await self.start_task(task_id, db)
            else:
                api_logger.error(f"任務不存在: {task_id}")
                
        except Exception as e:
            api_logger.error(f"啟動即時任務失敗 {task_id}: {e}")

    async def _start_realtime_task(self, task_id: str):
        """啟動即時監控任務"""
        try:
            task = self.active_tasks[task_id]
            camera_id = task.get("camera_id")
            
            if camera_id:
                # 啟動攝影機
                success = await self.camera_service.toggle_camera(camera_id)
                if not success:
                    task["status"] = "failed"
                    api_logger.error(f"啟動攝影機失敗: {camera_id}")
                    return
            
            # 模擬即時處理進度
            asyncio.create_task(self._simulate_realtime_progress(task_id))
            
        except Exception as e:
            api_logger.error(f"啟動即時任務失敗 {task_id}: {e}")
            self.active_tasks[task_id]["status"] = "failed"
    
    async def _start_batch_task(self, task_id: str):
        """啟動批次分析任務"""
        try:
            # 模擬批次處理進度
            asyncio.create_task(self._simulate_batch_progress(task_id))
            
        except Exception as e:
            api_logger.error(f"啟動批次任務失敗 {task_id}: {e}")
            self.active_tasks[task_id]["status"] = "failed"
    
    async def _start_training_task(self, task_id: str):
        """啟動模型訓練任務"""
        try:
            # 模擬訓練進度
            asyncio.create_task(self._simulate_training_progress(task_id))
            
        except Exception as e:
            api_logger.error(f"啟動訓練任務失敗 {task_id}: {e}")
            self.active_tasks[task_id]["status"] = "failed"
    
    async def _simulate_realtime_progress(self, task_id: str):
        """模擬即時任務進度"""
        try:
            while task_id in self.active_tasks and self.active_tasks[task_id]["status"] == "running":
                task = self.active_tasks[task_id]
                # 即時任務保持在固定進度
                task["progress"] = 85
                await asyncio.sleep(5)
        except Exception as e:
            api_logger.error(f"即時任務進度模擬失敗 {task_id}: {e}")
    
    async def _simulate_batch_progress(self, task_id: str):
        """模擬批次任務進度"""
        try:
            for progress in range(0, 101, 10):
                if task_id not in self.active_tasks or self.active_tasks[task_id]["status"] != "running":
                    break
                
                self.active_tasks[task_id]["progress"] = progress
                await asyncio.sleep(2)
            
            if task_id in self.active_tasks and self.active_tasks[task_id]["status"] == "running":
                self.active_tasks[task_id]["status"] = "completed"
                self.active_tasks[task_id]["progress"] = 100
                self.active_tasks[task_id]["end_time"] = datetime.utcnow()
                
        except Exception as e:
            api_logger.error(f"批次任務進度模擬失敗 {task_id}: {e}")
    
    async def _simulate_training_progress(self, task_id: str):
        """模擬訓練任務進度"""
        try:
            for progress in range(0, 101, 5):
                if task_id not in self.active_tasks or self.active_tasks[task_id]["status"] != "running":
                    break
                
                self.active_tasks[task_id]["progress"] = progress
                await asyncio.sleep(3)
            
            if task_id in self.active_tasks and self.active_tasks[task_id]["status"] == "running":
                self.active_tasks[task_id]["status"] = "completed"
                self.active_tasks[task_id]["progress"] = 100
                self.active_tasks[task_id]["end_time"] = datetime.utcnow()
                
        except Exception as e:
            api_logger.error(f"訓練任務進度模擬失敗 {task_id}: {e}")

_task_service_instance = None

def get_task_service():
    """依賴注入函數，提供 TaskService 的單例"""
    global _task_service_instance
    if _task_service_instance is None:
        print("🔧 創建新的 TaskService 實例")
        _task_service_instance = TaskService()
        print(f"🔧 TaskService 實例創建完成: {_task_service_instance}")
    else:
        print(f"🔧 使用現有的 TaskService 實例: {_task_service_instance}")
    return _task_service_instance