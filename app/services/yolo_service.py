"""
YOLOv11 數位雙生分析系統 - YOLOv11 服務層
基於文件建議的優化實作，包含線程安全與效能優化
"""

import asyncio
import gc
import time
import threading
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import uuid

import torch
import numpy as np
from ultralytics import YOLO
from PIL import Image
import cv2

from app.core.config import settings, YOLO_CLASSES
from app.core.logger import detection_logger, performance_logger, log_performance
from app.utils.exceptions import ModelNotLoadedException, InferenceException


@contextmanager
def gpu_memory_manager():
    """GPU 記憶體管理上下文管理器"""
    try:
        yield
    finally:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()


class YOLOService:
    """
    YOLOv11 服務類別 - 單例模式實作
    支援異步推論、線程安全與記憶體優化
    """
    
    _instance: Optional['YOLOService'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._model: Optional[YOLO] = None
        self._model_path: Optional[str] = None
        self._device: str = settings.device
        self._initialized = True
        
        # 抑制 ultralytics 輸出
        import logging
        import os
        
        # 設置 ultralytics 日誌級別
        ultralytics_logger = logging.getLogger('ultralytics')
        ultralytics_logger.setLevel(logging.WARNING)
        
        # 設置環境變量來抑制 YOLO 輸出
        os.environ['YOLO_VERBOSE'] = 'False'
        
        # 線程池執行器，用於同步推論操作
        self.executor = ThreadPoolExecutor(max_workers=settings.workers)
        
        # 線程本地儲存，為每個線程建立獨立模型實例
        self._local = threading.local()
        
        detection_logger.info("YOLOService 初始化完成")
    
    @property
    def is_loaded(self) -> bool:
        """檢查模型是否已載入"""
        return self._model is not None
    
    async def load_model(self, model_path: str = None) -> bool:
        """
        異步載入模型，避免阻塞
        
        Args:
            model_path: 模型檔案路徑，預設使用設定檔中的路徑
            
        Returns:
            bool: 載入是否成功
        """
        model_path = model_path or settings.model_path
        
        async with self._lock:
            if self._model is not None and self._model_path == model_path:
                detection_logger.info(f"模型已載入: {model_path}")
                return True
                
            try:
                detection_logger.info(f"開始載入模型: {model_path}")
                start_time = time.time()
                
                # 在執行器中載入模型避免阻塞
                loop = asyncio.get_event_loop()
                self._model = await loop.run_in_executor(
                    self.executor, self._load_model_sync, model_path
                )
                
                self._model_path = model_path
                load_time = time.time() - start_time
                
                detection_logger.info(
                    f"模型載入成功: {model_path}, 耗時: {load_time:.2f}秒"
                )
                
                return True
                
            except Exception as e:
                detection_logger.log_error(e, {"model_path": model_path})
                return False
    
    def _load_model_sync(self, model_path: str) -> YOLO:
        """同步載入模型（在執行器中運行）"""
        with gpu_memory_manager():
            model = YOLO(model_path)
            
            # 設定設備
            if self._device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self._device
                
            model.to(device)
            
            # 預熱模型（執行一次虛擬推論）
            dummy_input = np.zeros((640, 640, 3), dtype=np.uint8)
            model.predict(
                dummy_input, 
                verbose=False, 
                save=False, 
                show=False,
                stream=False,
                plots=False,
                visualize=False
            )
            
            return model
    
    def get_thread_local_model(self) -> YOLO:
        """為每個線程取得獨立的模型實例"""
        if not hasattr(self._local, 'model') or self._local.model is None:
            if self._model_path is None:
                raise ModelNotLoadedException("主模型尚未載入")
                
            with gpu_memory_manager():
                self._local.model = YOLO(self._model_path)
                if self._device == "auto":
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                else:
                    device = self._device
                self._local.model.to(device)
                
        return self._local.model
    
    @log_performance("yolo_predict")
    async def predict(self, 
                     image_data: Union[bytes, np.ndarray, str], 
                     conf_threshold: float = None,
                     iou_threshold: float = None,
                     max_detections: int = None) -> Dict[str, Any]:
        """
        執行物件偵測推論
        
        Args:
            image_data: 圖片資料（bytes、numpy array 或檔案路徑）
            conf_threshold: 信心值閾值
            iou_threshold: IOU 閾值
            max_detections: 最大偵測數量
            
        Returns:
            Dict: 偵測結果
        """
        if self._model is None:
            raise ModelNotLoadedException("模型尚未載入")
        
        # 使用預設值
        conf_threshold = conf_threshold or settings.confidence_threshold
        iou_threshold = iou_threshold or settings.iou_threshold
        max_detections = max_detections or settings.max_detections
        
        try:
            # 在執行器中執行推論
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor, 
                self._predict_sync, 
                image_data, 
                conf_threshold, 
                iou_threshold,
                max_detections
            )
            
            # 生成唯一圖片 ID
            image_id = str(uuid.uuid4())
            
            # 記錄偵測事件
            detection_logger.log_detection(
                image_id=image_id,
                detections=results["detections"],
                inference_time=results["inference_time"],
                model_version=self._model_path
            )
            
            return {
                "image_id": image_id,
                **results
            }
            
        except Exception as e:
            detection_logger.log_error(e, {
                "conf_threshold": conf_threshold,
                "iou_threshold": iou_threshold
            })
            raise InferenceException(f"推論失敗: {str(e)}")
    
    def predict_frame(self, frame: np.ndarray, conf_threshold: float = None, iou_threshold: float = None) -> List[Dict[str, Any]]:
        """
        同步預測單一幀（適用於即時檢測）
        
        Args:
            frame: OpenCV 圖像幀（numpy array）
            conf_threshold: 信心值閾值
            iou_threshold: IOU 閾值
            
        Returns:
            List[Dict]: 檢測結果列表
        """
        try:
            if self._model is None:
                raise ModelNotLoadedException("模型尚未載入")
                
            # 使用預設值
            conf = conf_threshold if conf_threshold is not None else 0.5
            iou = iou_threshold if iou_threshold is not None else 0.45
            
            # 調用同步預測
            results = self._predict_sync(
                image_data=frame,
                conf_threshold=conf,
                iou_threshold=iou,
                max_detections=100  # 預設最大檢測數量
            )
            
            # 返回檢測結果
            return results.get("detections", [])
            
        except Exception as e:
            print(f"❌ 幀預測失敗: {e}")
            return []
    
    def _predict_sync(self, 
                     image_data: Union[bytes, np.ndarray, str],
                     conf_threshold: float,
                     iou_threshold: float,
                     max_detections: int) -> Dict[str, Any]:
        """同步推論（在執行器中運行）"""
        start_time = time.time()
        
        # 開始推論
        with gpu_memory_manager():
            model = self.get_thread_local_model()
            
            # 處理輸入圖片
            if isinstance(image_data, bytes):
                # 從 bytes 載入圖片
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            elif isinstance(image_data, np.ndarray):
                image = image_data
            elif isinstance(image_data, str):
                # 從檔案路徑載入
                image = cv2.imread(image_data)
            else:
                raise ValueError("不支援的圖片格式")
            
            if image is None:
                raise ValueError("無法載入圖片")
            
            # 執行推論
            results = model.predict(
                image,
                conf=conf_threshold,
                iou=iou_threshold,
                verbose=False,
                save=False,
                show=False,
                stream=False,
                plots=False,
                visualize=False,
                max_det=max_detections
            )
            
            inference_time = time.time() - start_time
            
            # 格式化結果
            formatted_result = self._format_results(results, inference_time, image.shape)
            return formatted_result
    
    def _format_results(self, 
                       results, 
                       inference_time: float,
                       image_shape: tuple) -> Dict[str, Any]:
        """格式化偵測結果"""
        detections = []
        
        if results and len(results) > 0:
            result = results[0]  # 取第一個結果
            
            if result.boxes is not None:
                boxes = result.boxes.cpu().numpy()
                
                for i in range(len(boxes)):
                    # 邊界框座標
                    xyxy = boxes.xyxy[i]
                    conf = float(boxes.conf[i])
                    cls = int(boxes.cls[i])
                    
                    detection = {
                        "class_id": cls,
                        "class": YOLO_CLASSES.get(cls, f"class_{cls}"),  # 使用 'class' 鍵名保持一致
                        "class_name": YOLO_CLASSES.get(cls, f"class_{cls}"),
                        "confidence": conf,
                        "bbox": [float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])],  # 簡化格式
                        "bbox_detailed": {
                            "x1": float(xyxy[0]),
                            "y1": float(xyxy[1]),
                            "x2": float(xyxy[2]),
                            "y2": float(xyxy[3])
                        },
                        "center": {
                            "x": float((xyxy[0] + xyxy[2]) / 2),
                            "y": float((xyxy[1] + xyxy[3]) / 2)
                        },
                        "area": float((xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1]))
                    }
                    
                    detections.append(detection)
        
        return {
            "detections": detections,
            "objects": detections,  # 為向後兼容性添加
            "inference_time": inference_time,
            "image_shape": image_shape,
            "image_size": list(image_shape),  # 為向後兼容性添加
            "detection_count": len(detections),
            "timestamp": time.time()
        }
    
    @log_performance("yolo_track")
    async def track(self, 
                   image_data: Union[bytes, np.ndarray, str],
                   tracker: str = None,
                   conf_threshold: float = None,
                   iou_threshold: float = None) -> Dict[str, Any]:
        """
        執行物件偵測與追蹤
        
        Args:
            image_data: 圖片資料
            tracker: 追蹤器類型
            conf_threshold: 信心值閾值
            iou_threshold: IOU 閾值
            
        Returns:
            Dict: 偵測與追蹤結果
        """
        if self._model is None:
            raise ModelNotLoadedException("模型尚未載入")
        
        tracker = tracker or settings.tracker
        conf_threshold = conf_threshold or settings.confidence_threshold
        iou_threshold = iou_threshold or settings.iou_threshold
        
        try:
            # 在執行器中執行追蹤
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                self._track_sync,
                image_data,
                tracker,
                conf_threshold,
                iou_threshold
            )
            
            # 生成唯一圖片 ID
            image_id = str(uuid.uuid4())
            
            return {
                "image_id": image_id,
                **results
            }
            
        except Exception as e:
            detection_logger.log_error(e, {"tracker": tracker})
            raise InferenceException(f"追蹤失敗: {str(e)}")
    
    def _track_sync(self, 
                   image_data: Union[bytes, np.ndarray, str],
                   tracker: str,
                   conf_threshold: float,
                   iou_threshold: float) -> Dict[str, Any]:
        """同步追蹤（在執行器中運行）"""
        start_time = time.time()
        
        with gpu_memory_manager():
            model = self.get_thread_local_model()
            
            # 處理輸入圖片（同 _predict_sync）
            if isinstance(image_data, bytes):
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            elif isinstance(image_data, np.ndarray):
                image = image_data
            elif isinstance(image_data, str):
                image = cv2.imread(image_data)
            else:
                raise ValueError("不支援的圖片格式")
            
            if image is None:
                raise ValueError("無法載入圖片")
            
            # 執行追蹤
            results = model.track(
                image,
                conf=conf_threshold,
                iou=iou_threshold,
                tracker=tracker,
                verbose=False,
                save=False,
                show=False
            )
            
            inference_time = time.time() - start_time
            
            # 格式化追蹤結果
            return self._format_tracking_results(results, inference_time, image.shape)
    
    def _format_tracking_results(self, 
                               results, 
                               inference_time: float,
                               image_shape: tuple) -> Dict[str, Any]:
        """格式化追蹤結果"""
        detections = []
        tracks = []
        
        if results and len(results) > 0:
            result = results[0]
            
            if result.boxes is not None:
                boxes = result.boxes.cpu().numpy()
                
                for i in range(len(boxes)):
                    xyxy = boxes.xyxy[i]
                    conf = float(boxes.conf[i])
                    cls = int(boxes.cls[i])
                    
                    # 基本偵測資訊
                    detection = {
                        "class_id": cls,
                        "class_name": YOLO_CLASSES.get(cls, f"class_{cls}"),
                        "confidence": conf,
                        "bbox": {
                            "x1": float(xyxy[0]),
                            "y1": float(xyxy[1]),
                            "x2": float(xyxy[2]),
                            "y2": float(xyxy[3])
                        },
                        "center": {
                            "x": float((xyxy[0] + xyxy[2]) / 2),
                            "y": float((xyxy[1] + xyxy[3]) / 2)
                        },
                        "area": float((xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1]))
                    }
                    
                    # 追蹤資訊
                    if hasattr(boxes, 'id') and boxes.id is not None:
                        track_id = int(boxes.id[i]) if i < len(boxes.id) else None
                        if track_id is not None:
                            detection["track_id"] = track_id
                            
                            # 建立追蹤記錄
                            track = {
                                "track_id": track_id,
                                "class_id": cls,
                                "class_name": detection["class_name"],
                                "bbox": detection["bbox"],
                                "center": detection["center"],
                                "confidence": conf,
                                "timestamp": time.time()
                            }
                            tracks.append(track)
                    
                    detections.append(detection)
        
        return {
            "detections": detections,
            "tracks": tracks,
            "inference_time": inference_time,
            "image_shape": image_shape,
            "detection_count": len(detections),
            "track_count": len(tracks),
            "timestamp": time.time()
        }
    
    def __del__(self):
        """清理資源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)


# 建立全域 YOLOService 實例
# 延遲初始化的全域服務實例
_yolo_service = None

def get_yolo_service():
    """獲取 YOLO 服務實例（延遲初始化）"""
    global _yolo_service
    if _yolo_service is None:
        _yolo_service = YOLOService()
    return _yolo_service
