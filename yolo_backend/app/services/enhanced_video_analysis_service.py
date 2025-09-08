"""
增強的影片分析服務 - 帶資料庫整合
"""

import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import uuid
from ultralytics import YOLO

from app.core.logger import main_logger as logger
from app.services.video_analysis_service import VideoAnalysisService, DetectionRecord, BehaviorEvent
from app.services.new_database_service import DatabaseService
from app.models.analysis import AnalysisRecord


class EnhancedVideoAnalysisService(VideoAnalysisService):
    """增強的影片分析服務 - 支援資料庫保存"""
    
    def __init__(self, model_path: str = "yolo11n.pt", device: str = "auto", db_service: Optional[DatabaseService] = None):
        # 只傳遞 model_path 給父類
        super().__init__(model_path)
        # 單獨設定 device
        self.device = device
        # 如果指定了 device，設定模型的設備
        if device != "auto":
            try:
                # 設定 YOLO 模型的設備
                self.model.to(device)
                logger.info(f"YOLO 模型已設定到設備: {device}")
            except Exception as e:
                logger.warning(f"無法設定設備 {device}: {e}")
        
        self.db_service = db_service
        self.current_analysis_record: Optional[AnalysisRecord] = None
    
    def set_database_service(self, db_service: DatabaseService):
        """設定資料庫服務"""
        self.db_service = db_service
    
    async def analyze_video_with_database(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        confidence_threshold: float = 0.5,
        track_objects: bool = True,
        detect_behaviors: bool = True,
        annotate_video: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用資料庫的影片分析
        """
        start_time = datetime.now()
        video_name = Path(video_path).name
        
        try:
            # 1. 創建分析記錄
            if self.db_service:
                self.current_analysis_record = await self.db_service.create_analysis_record(
                    video_path=video_path,
                    video_name=video_name,
                    analysis_type="detection_with_annotation" if annotate_video else "detection",
                    status="processing"
                )
                logger.info(f"🗄️ 創建資料庫記錄: {self.current_analysis_record.id}")
            
            # 2. 執行傳統分析
            results = await self._perform_video_analysis(
                video_path, output_dir, confidence_threshold, 
                track_objects, detect_behaviors, annotate_video, **kwargs
            )
            
            # 3. 保存分析結果到資料庫
            if self.db_service and self.current_analysis_record:
                await self._save_results_to_database(results)
                
                # 更新分析記錄狀態
                end_time = datetime.now()
                analysis_duration = (end_time - start_time).total_seconds()
                
                await self.db_service.update_analysis_record(
                    self.current_analysis_record.id,
                    status="completed",
                    analysis_duration=analysis_duration,
                    total_detections=results.get("total_detections", 0),
                    unique_objects=len(results.get("detection_summary", {})),
                    csv_file_path=results.get("csv_file"),
                    annotated_video_path=results.get("annotated_video_path"),
                    duration=results.get("video_info", {}).get("duration"),
                    fps=results.get("video_info", {}).get("fps"),
                    total_frames=results.get("video_info", {}).get("total_frames"),
                    resolution=results.get("video_info", {}).get("resolution")
                )
                
                results["analysis_record_id"] = self.current_analysis_record.id
            
            return results
            
        except Exception as e:
            # 更新錯誤狀態
            if self.db_service and self.current_analysis_record:
                try:
                    await self.db_service.update_analysis_record(
                        self.current_analysis_record.id,
                        status="failed",
                        error_message=str(e)
                    )
                except Exception as db_error:
                    logger.error(f"❌ 更新錯誤狀態失敗: {db_error}")
            
            logger.error(f"❌ 影片分析失敗: {e}")
            raise
    
    async def _perform_video_analysis(self, video_path: str, output_dir: Optional[str] = None,
                                    confidence_threshold: float = 0.5, track_objects: bool = True,
                                    detect_behaviors: bool = True, annotate_video: bool = True,
                                    **kwargs) -> Dict[str, Any]:
        """執行實際的影片分析（同步包裝）"""
        # 使用父類的同步方法進行基本分析
        results = super().analyze_video_file(video_path)
        
        # 從父類別取得檢測記錄和行為事件
        # 父類別將資料儲存在 self.detection_records 和 self.behavior_events 中
        detections = []
        for detection_record in self.detection_records:
            detections.append(detection_record)
            
        behavior_events = []
        for behavior_event in self.behavior_events:
            behavior_events.append(behavior_event)
        
        # 將檢測資料加入結果中
        results["detections"] = detections
        results["behavior_events"] = behavior_events
        results["total_detections"] = len(detections)
        
        return results
    
    async def _save_results_to_database(self, results: Dict[str, Any]):
        """保存分析結果到資料庫"""
        if not self.db_service or not self.current_analysis_record:
            return
        
        try:
            # 保存檢測結果
            detections = results.get("detections", [])
            if detections:
                detection_records = []
                
                for detection in detections:
                    # 轉換檢測資料格式
                    detection_data = self._convert_detection_to_db_format(detection)
                    detection_records.append(detection_data)
                
                if detection_records:
                    await self.db_service.save_detection_results(
                        self.current_analysis_record.id,
                        detection_records
                    )
            
            # 保存行為事件
            behavior_events = results.get("behavior_events", [])
            if behavior_events:
                for event in behavior_events:
                    await self._save_behavior_event_to_db(event)
            
            logger.info(f"✅ 保存 {len(detections)} 個檢測結果和 {len(behavior_events)} 個行為事件到資料庫")
            
        except Exception as e:
            logger.error(f"❌ 保存結果到資料庫失敗: {e}")
            raise
    
    def _convert_detection_to_db_format(self, detection: DetectionRecord) -> Dict[str, Any]:
        """轉換檢測記錄為資料庫格式"""
        try:
            return {
                "frame_number": detection.frame_number,
                "frame_time": float(detection.frame_number) / 30.0,  # 假設30fps
                "object_id": str(detection.object_id),
                "object_type": detection.object_type,
                "object_chinese": self._get_chinese_name(detection.object_type),
                "confidence": detection.confidence,
                "bbox_x1": detection.bbox_x1,
                "bbox_y1": detection.bbox_y1,
                "bbox_x2": detection.bbox_x2,
                "bbox_y2": detection.bbox_y2,
                "center_x": detection.center_x,
                "center_y": detection.center_y,
                "width": detection.width,
                "height": detection.height,
                "area": detection.area,
                "zone": detection.zone or "unknown",
                "zone_chinese": self._get_chinese_zone_name(detection.zone),
                "velocity_x": 0.0,  # 可以從追蹤資料中計算
                "velocity_y": 0.0,
                "speed": detection.speed or 0.0,
                "direction": self._calculate_direction(detection.direction) if detection.direction else None,
                "direction_chinese": self._get_chinese_direction(detection.direction) if detection.direction else None,
                "detection_quality": self._assess_detection_quality(detection.confidence)
            }
        except Exception as e:
            logger.error(f"❌ 轉換檢測記錄格式失敗: {e}")
            return {}
    
    async def _save_behavior_event_to_db(self, event: BehaviorEvent):
        """保存行為事件到資料庫"""
        try:
            await self.db_service.save_behavior_event(
                analysis_id=self.current_analysis_record.id,
                event_type=event.behavior,
                event_chinese=self._get_chinese_behavior_name(event.behavior),
                object_id=str(event.object_id),
                object_type=event.object_type,
                object_chinese=self._get_chinese_name(event.object_type),
                zone=event.zone,
                zone_chinese=self._get_chinese_zone_name(event.zone),
                position_x=event.position_x,
                position_y=event.position_y,
                duration=event.duration,
                confidence_level=event.confidence,
                description=f"{event.object_type} 在 {event.zone} 發生 {event.behavior} 行為",
                additional_data=json.loads(event.metadata) if event.metadata != "{}" else None
            )
        except Exception as e:
            logger.error(f"❌ 保存行為事件失敗: {e}")
    
    def _get_chinese_name(self, object_type: str) -> str:
        """獲取物件中文名稱"""
        chinese_names = {
            "person": "人",
            "bicycle": "腳踏車",
            "car": "汽車",
            "motorcycle": "機車",
            "airplane": "飛機",
            "bus": "公車",
            "train": "火車",
            "truck": "卡車",
            "boat": "船",
            "traffic light": "交通燈",
            "fire hydrant": "消防栓",
            "stop sign": "停止標誌",
            "parking meter": "停車計時器",
            "bench": "長椅",
            "bird": "鳥",
            "cat": "貓",
            "dog": "狗",
            "horse": "馬",
            "sheep": "羊",
            "cow": "牛"
        }
        return chinese_names.get(object_type, object_type)
    
    def _get_chinese_zone_name(self, zone: Optional[str]) -> Optional[str]:
        """獲取區域中文名稱"""
        if not zone:
            return None
        
        chinese_zones = {
            "entrance": "入口區域",
            "exit": "出口區域",
            "center_area": "中央區域",
            "left_area": "左側區域",
            "right_area": "右側區域",
            "unknown_area": "未知區域"
        }
        return chinese_zones.get(zone, zone)
    
    def _calculate_direction(self, direction_angle: float) -> str:
        """根據角度計算方向"""
        if direction_angle is None:
            return "unknown"
        
        # 將角度轉換為方向
        angle = float(direction_angle) % 360
        if 337.5 <= angle or angle < 22.5:
            return "north"
        elif 22.5 <= angle < 67.5:
            return "northeast"
        elif 67.5 <= angle < 112.5:
            return "east"
        elif 112.5 <= angle < 157.5:
            return "southeast"
        elif 157.5 <= angle < 202.5:
            return "south"
        elif 202.5 <= angle < 247.5:
            return "southwest"
        elif 247.5 <= angle < 292.5:
            return "west"
        elif 292.5 <= angle < 337.5:
            return "northwest"
        else:
            return "unknown"
    
    def _get_chinese_direction(self, direction_angle: float) -> str:
        """獲取方向中文名稱"""
        direction = self._calculate_direction(direction_angle)
        chinese_directions = {
            "north": "北",
            "northeast": "東北",
            "east": "東",
            "southeast": "東南",
            "south": "南",
            "southwest": "西南",
            "west": "西",
            "northwest": "西北",
            "unknown": "未知"
        }
        return chinese_directions.get(direction, "未知")
    
    def _get_chinese_behavior_name(self, behavior: str) -> str:
        """獲取行為中文名稱"""
        chinese_behaviors = {
            "entering": "進入",
            "exiting": "離開",
            "loitering": "逗留",
            "crowding": "聚集",
            "running": "跑動",
            "stopping": "停止",
            "moving": "移動",
            "interaction": "互動",
            "unknown": "未知行為"
        }
        return chinese_behaviors.get(behavior, behavior)
    
    def _assess_detection_quality(self, confidence: float) -> str:
        """評估檢測品質"""
        if confidence >= 0.9:
            return "excellent"
        elif confidence >= 0.7:
            return "good"
        elif confidence >= 0.5:
            return "fair"
        else:
            return "poor"
    
    async def get_analysis_history(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[AnalysisRecord]:
        """獲取分析歷史記錄"""
        if not self.db_service:
            return []
        
        return await self.db_service.get_analysis_records(skip, limit, status)
    
    async def get_analysis_details(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """獲取分析詳細資訊"""
        if not self.db_service:
            return None
        
        # 獲取分析記錄
        analysis_record = await self.db_service.get_analysis_record(analysis_id)
        if not analysis_record:
            return None
        
        # 獲取檢測結果
        detection_results = await self.db_service.get_detection_results(analysis_id)
        
        # 獲取行為事件
        behavior_events = await self.db_service.get_behavior_events(analysis_id)
        
        return {
            "analysis_record": analysis_record,
            "detection_count": len(detection_results),
            "detections": detection_results[:100],  # 限制返回數量
            "behavior_events": behavior_events,
            "has_more_detections": len(detection_results) > 100
        }
    
    async def get_analysis_statistics(self) -> Dict[str, Any]:
        """獲取分析統計資訊"""
        if not self.db_service:
            return {}
        
        return await self.db_service.get_analysis_statistics()
