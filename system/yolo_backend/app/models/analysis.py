"""
分析相關的資料庫模型
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, Text, DateTime, JSON, Integer
from sqlalchemy.sql import func
from typing import Optional
from datetime import datetime
from .base import BaseModel

class AnalysisRecord(BaseModel):
    """影片分析記錄表"""
    __tablename__ = "analysis_records"
    
    # 基本資訊
    video_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="影片檔案路徑")
    video_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="影片檔案名稱")
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="分析類型：detection/annotation")
    status: Mapped[str] = mapped_column(String(50), default="processing", comment="處理狀態")
    
    # 影片資訊
    duration: Mapped[Optional[float]] = mapped_column(Float, comment="影片長度(秒)")
    fps: Mapped[Optional[float]] = mapped_column(Float, comment="幀率")
    total_frames: Mapped[Optional[int]] = mapped_column(Integer, comment="總幀數")
    resolution: Mapped[Optional[str]] = mapped_column(String(50), comment="解析度")
    
    # 分析結果
    total_detections: Mapped[int] = mapped_column(Integer, default=0, comment="總檢測數量")
    unique_objects: Mapped[int] = mapped_column(Integer, default=0, comment="唯一物件數量")
    analysis_duration: Mapped[Optional[float]] = mapped_column(Float, comment="分析耗時(秒)")
    
    # 檔案路徑
    csv_file_path: Mapped[Optional[str]] = mapped_column(String(500), comment="CSV結果檔案路徑")
    annotated_video_path: Mapped[Optional[str]] = mapped_column(String(500), comment="標註影片檔案路徑")
    
    # 額外資料
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, comment="額外元數據")
    error_message: Mapped[Optional[str]] = mapped_column(Text, comment="錯誤訊息")

class DetectionResult(BaseModel):
    """物件檢測結果表"""
    __tablename__ = "detection_results"
    
    # 關聯分析記錄
    analysis_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="關聯的分析記錄ID")
    
    # 時間資訊
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="檢測時間")
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False, comment="幀編號")
    frame_time: Mapped[float] = mapped_column(Float, nullable=False, comment="影片時間點(秒)")
    
    # 物件資訊
    object_id: Mapped[Optional[str]] = mapped_column(String(100), comment="物件追蹤ID")
    object_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="物件類型")
    object_chinese: Mapped[Optional[str]] = mapped_column(String(50), comment="物件中文名稱")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, comment="信心度")
    
    # 位置資訊 (Unity 螢幕座標系統)
    bbox_x1: Mapped[float] = mapped_column(Float, nullable=False, comment="邊界框左下角X (Unity)")
    bbox_y1: Mapped[float] = mapped_column(Float, nullable=False, comment="邊界框左下角Y (Unity)")
    bbox_x2: Mapped[float] = mapped_column(Float, nullable=False, comment="邊界框右上角X (Unity)")
    bbox_y2: Mapped[float] = mapped_column(Float, nullable=False, comment="邊界框右上角Y (Unity)")
    center_x: Mapped[float] = mapped_column(Float, nullable=False, comment="中心點X (Unity)")
    center_y: Mapped[float] = mapped_column(Float, nullable=False, comment="中心點Y (Unity，Y軸向上)")
    width: Mapped[float] = mapped_column(Float, nullable=False, comment="寬度")
    height: Mapped[float] = mapped_column(Float, nullable=False, comment="高度")
    area: Mapped[float] = mapped_column(Float, nullable=False, comment="面積")
    
    # 空間與運動分析 (Unity 座標系統)
    zone: Mapped[Optional[str]] = mapped_column(String(50), comment="所在區域")
    zone_chinese: Mapped[Optional[str]] = mapped_column(String(50), comment="區域中文名稱")
    velocity_x: Mapped[float] = mapped_column(Float, default=0, comment="X方向速度")
    velocity_y: Mapped[float] = mapped_column(Float, default=0, comment="Y方向速度 (向上為正)")
    speed: Mapped[float] = mapped_column(Float, default=0, comment="移動速度")
    direction: Mapped[Optional[str]] = mapped_column(String(20), comment="移動方向")
    direction_chinese: Mapped[Optional[str]] = mapped_column(String(20), comment="移動方向中文")
    
    # 品質評估
    detection_quality: Mapped[Optional[str]] = mapped_column(String(20), comment="檢測品質")

class BehaviorEvent(BaseModel):
    """行為事件記錄表"""
    __tablename__ = "behavior_events"
    
    # 關聯分析記錄
    analysis_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="關聯的分析記錄ID")
    
    # 事件基本資訊
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="事件發生時間")
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="事件類型")
    event_chinese: Mapped[Optional[str]] = mapped_column(String(100), comment="事件中文名稱")
    object_id: Mapped[Optional[str]] = mapped_column(String(100), comment="相關物件ID")
    object_type: Mapped[Optional[str]] = mapped_column(String(50), comment="物件類型")
    object_chinese: Mapped[Optional[str]] = mapped_column(String(50), comment="物件中文名稱")
    
    # 位置資訊
    zone: Mapped[Optional[str]] = mapped_column(String(50), comment="發生區域")
    zone_chinese: Mapped[Optional[str]] = mapped_column(String(50), comment="區域中文名稱")
    position_x: Mapped[Optional[float]] = mapped_column(Float, comment="事件X座標")
    position_y: Mapped[Optional[float]] = mapped_column(Float, comment="事件Y座標")
    
    # 事件詳情
    duration: Mapped[Optional[float]] = mapped_column(Float, comment="持續時間(秒)")
    severity: Mapped[Optional[str]] = mapped_column(String(20), comment="嚴重程度")
    severity_chinese: Mapped[Optional[str]] = mapped_column(String(20), comment="嚴重程度中文")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="事件描述")
    trigger_condition: Mapped[Optional[str]] = mapped_column(String(200), comment="觸發條件")
    
    # 統計資訊
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1, comment="發生次數")
    confidence_level: Mapped[Optional[float]] = mapped_column(Float, comment="事件信心度")
    
    # 額外資料
    additional_data: Mapped[Optional[dict]] = mapped_column(JSON, comment="額外事件資料")
