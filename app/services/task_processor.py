"""
分析任務處理器 - 執行實際的YOLO分析並保存到資料庫
"""

import cv2
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from ultralytics import YOLO
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import main_logger as logger
from app.services.new_database_service import DatabaseService
from app.models.database import AnalysisTask, DetectionResult


class TaskProcessor:
    """任務處理器 - 負責執行分析任務並保存結果"""
    
    def __init__(self):
        # 初始化YOLO模型
        self.model_path = "yolo11n.pt"
        self.model = None
        self._load_model()
        
        # 資料庫服務
        self.db_service = DatabaseService()
        
        logger.info("TaskProcessor 初始化完成")
    
    def _load_model(self):
        """載入YOLO模型"""
        try:
            if Path(self.model_path).exists():
                self.model = YOLO(self.model_path)
                logger.info(f"✅ YOLO模型載入成功: {self.model_path}")
            else:
                logger.error(f"❌ YOLO模型檔案不存在: {self.model_path}")
                raise FileNotFoundError(f"YOLO模型檔案不存在: {self.model_path}")
        except Exception as e:
            logger.error(f"❌ YOLO模型載入失敗: {e}")
            raise
    
    async def process_video_file_task(self, db: AsyncSession, task: AnalysisTask) -> Dict[str, Any]:
        """
        處理影片檔案分析任務
        
        Args:
            db: 資料庫會話
            task: 分析任務物件
            
        Returns:
            分析結果摘要
        """
        try:
            # 更新任務狀態為執行中
            await self.db_service.update_task_status(db, task.id, "running")
            
            # 從source_info獲取檔案路徑
            source_info = task.source_info
            if isinstance(source_info, str):
                source_info = json.loads(source_info)
            
            video_path = source_info.get('file_path')
            if not video_path:
                raise ValueError("source_info中缺少file_path")
            
            # 檢查檔案是否存在
            if not Path(video_path).exists():
                raise FileNotFoundError(f"影片檔案不存在: {video_path}")
            
            logger.info(f"🎬 開始分析影片: {video_path}")
            
            # 開啟影片
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"無法開啟影片檔案: {video_path}")
            
            try:
                # 獲取影片資訊
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                logger.info(f"📹 影片資訊: {total_frames} 幀, {fps} FPS, {frame_width}x{frame_height}")
                
                # 獲取信心度閾值
                confidence_threshold = source_info.get('confidence_threshold', 0.5)
                
                # 處理影片幀
                detection_count = 0
                frame_number = 0
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 每隔3幀處理一次（提高效能）
                    if frame_number % 3 == 0:
                        detections = await self._process_frame(
                            db, task.id, frame, frame_number, 
                            frame_width, frame_height, fps, confidence_threshold
                        )
                        detection_count += len(detections)
                    
                    frame_number += 1
                    
                    # 每處理100幀輸出進度
                    if frame_number % 300 == 0:  # 每100個處理的幀（300個實際幀）
                        progress = (frame_number / total_frames) * 100
                        logger.info(f"🔄 處理進度: {progress:.1f}% ({frame_number}/{total_frames})")
                
                # 更新任務狀態為完成
                await self.db_service.update_task_status(db, task.id, "completed")
                
                result = {
                    "success": True,
                    "task_id": task.id,
                    "processed_frames": frame_number,
                    "detection_count": detection_count,
                    "message": f"影片分析完成，共處理 {frame_number} 幀，檢測到 {detection_count} 個物件"
                }
                
                logger.info(f"✅ 影片分析完成: {result['message']}")
                return result
                
            finally:
                cap.release()
                
        except Exception as e:
            logger.error(f"❌ 影片分析失敗: {e}")
            # 更新任務狀態為失敗
            try:
                await self.db_service.update_task_status(db, task.id, "failed")
            except:
                pass  # 避免雙重錯誤
            raise
    
    async def _process_frame(
        self, db: AsyncSession, task_id: int, frame: np.ndarray, 
        frame_number: int, frame_width: int, frame_height: int, 
        fps: float, confidence_threshold: float = 0.5
    ) -> List[DetectionResult]:
        """
        處理單一影片幀
        
        Args:
            db: 資料庫會話
            task_id: 任務ID
            frame: 影片幀
            frame_number: 幀號碼
            frame_width: 幀寬度
            frame_height: 幀高度
            fps: 影片幀率
            confidence_threshold: 信心度閾值
            
        Returns:
            檢測結果列表
        """
        try:
            # 使用YOLO進行檢測
            results = self.model(frame, verbose=False)
            
            detections = []
            
            if results and len(results) > 0:
                result = results[0]  # 取第一個結果
                
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes
                    
                    for i in range(len(boxes)):
                        # 獲取檢測資訊
                        confidence = float(boxes.conf[i])
                        
                        # 過濾低信心度檢測
                        if confidence < confidence_threshold:
                            continue
                        
                        # 獲取邊界框座標（YOLO格式：x1, y1, x2, y2）
                        bbox = boxes.xyxy[i].cpu().numpy()
                        x1, y1, x2, y2 = bbox
                        
                        # 轉換為Unity座標系統（左下角為(0,0)）
                        # OpenCV/YOLO座標系：左上角為(0,0)，Y軸向下
                        # Unity座標系：左下角為(0,0)，Y軸向上
                        unity_y1 = frame_height - y2  # 原來的y2變成新的y1（左下角Y）
                        unity_y2 = frame_height - y1  # 原來的y1變成新的y2（右上角Y）
                        
                        # 計算中心點（Unity座標系）
                        center_x = (x1 + x2) / 2
                        center_y = (unity_y1 + unity_y2) / 2
                        
                        # 獲取物件類別
                        class_id = int(boxes.cls[i])
                        object_type = self.model.names[class_id]
                        
                        # 計算時間戳（相對於影片開始時間）
                        timestamp = datetime.now() + timedelta(seconds=frame_number / fps)
                        
                        # 創建檢測記錄
                        detection_data = {
                            'task_id': task_id,
                            'frame_number': frame_number,
                            'timestamp': timestamp,
                            'object_type': object_type,
                            'confidence': confidence,
                            'bbox_x1': float(x1),           # Unity座標：左下角X（與OpenCV相同）
                            'bbox_y1': float(unity_y1),     # Unity座標：左下角Y（轉換後）
                            'bbox_x2': float(x2),           # Unity座標：右上角X（與OpenCV相同）
                            'bbox_y2': float(unity_y2),     # Unity座標：右上角Y（轉換後）
                            'center_x': float(center_x),    # Unity座標：中心X
                            'center_y': float(center_y)     # Unity座標：中心Y
                        }
                        
                        # 保存到資料庫
                        detection_record = await self.db_service.save_detection_result(db, detection_data)
                        detections.append(detection_record)
            
            return detections
            
        except Exception as e:
            logger.error(f"處理幀 {frame_number} 時發生錯誤: {e}")
            return []


# 全域處理器實例
_task_processor = None

def get_task_processor():
    """獲取任務處理器實例（單例模式）"""
    global _task_processor
    if _task_processor is None:
        _task_processor = TaskProcessor()
    return _task_processor
