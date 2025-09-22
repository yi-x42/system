"""
YOLOv11 數位雙生分析系統 - Pydantic 資料模型
定義 API 請求/回應與內部資料結構
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


# === 基礎資料模型 ===

class BoundingBox(BaseModel):
    """邊界框模型"""
    x1: float = Field(..., description="左上角 X 座標")
    y1: float = Field(..., description="左上角 Y 座標") 
    x2: float = Field(..., description="右下角 X 座標")
    y2: float = Field(..., description="右下角 Y 座標")
    
    @validator('x2')
    def x2_must_be_greater_than_x1(cls, v, values):
        if 'x1' in values and v <= values['x1']:
            raise ValueError('x2 必須大於 x1')
        return v
    
    @validator('y2') 
    def y2_must_be_greater_than_y1(cls, v, values):
        if 'y1' in values and v <= values['y1']:
            raise ValueError('y2 必須大於 y1')
        return v


class Point2D(BaseModel):
    """2D 座標點"""
    x: float = Field(..., description="X 座標")
    y: float = Field(..., description="Y 座標")


class Detection(BaseModel):
    """偵測結果模型"""
    class_id: int = Field(..., description="類別 ID")
    class_name: str = Field(..., description="類別名稱")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心值 (0-1)")
    bbox: BoundingBox = Field(..., description="邊界框")
    center: Point2D = Field(..., description="中心點座標")
    area: float = Field(..., ge=0.0, description="邊界框面積")
    track_id: Optional[int] = Field(None, description="追蹤 ID")


class Track(BaseModel):
    """追蹤目標模型"""
    track_id: int = Field(..., description="追蹤 ID")
    class_id: int = Field(..., description="類別 ID")
    class_name: str = Field(..., description="類別名稱")
    bbox: BoundingBox = Field(..., description="當前邊界框")
    center: Point2D = Field(..., description="當前中心點")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心值")
    first_seen: datetime = Field(..., description="首次出現時間")
    last_seen: datetime = Field(..., description="最後出現時間")
    velocity: Optional[Point2D] = Field(None, description="速度向量")
    trajectory: List[Point2D] = Field(default_factory=list, description="軌跡點")


# === API 請求模型 ===

class DetectionRequest(BaseModel):
    """偵測請求模型"""
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="信心值閾值")
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0, description="IOU 閾值")
    max_detections: int = Field(default=100, ge=1, le=1000, description="最大偵測數量")
    
    class Config:
        schema_extra = {
            "example": {
                "confidence_threshold": 0.5,
                "iou_threshold": 0.45,
                "max_detections": 100
            }
        }


class TrackingRequest(BaseModel):
    """追蹤請求模型"""
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="信心值閾值")
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0, description="IOU 閾值")
    tracker: str = Field(default="bytetrack.yaml", description="追蹤器類型")
    
    class Config:
        schema_extra = {
            "example": {
                "confidence_threshold": 0.5,
                "iou_threshold": 0.45,
                "tracker": "bytetrack.yaml"
            }
        }


class HeatmapRequest(BaseModel):
    """熱點圖請求模型"""
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    grid_size: int = Field(default=1024, ge=64, le=2048, description="網格大小")
    gaussian_sigma: float = Field(default=2.0, ge=0.1, le=10.0, description="高斯核標準差")
    roi_id: Optional[str] = Field(None, description="感興趣區域 ID")


# === API 回應模型 ===

class DetectionResponse(BaseModel):
    """偵測回應模型"""
    image_id: str = Field(..., description="圖片 ID")
    detections: List[Detection] = Field(..., description="偵測結果列表")
    inference_time: float = Field(..., ge=0.0, description="推論時間 (秒)")
    image_shape: tuple = Field(..., description="圖片尺寸 (height, width, channels)")
    detection_count: int = Field(..., ge=0, description="偵測數量")
    timestamp: float = Field(..., description="時間戳記")
    
    class Config:
        schema_extra = {
            "example": {
                "image_id": "123e4567-e89b-12d3-a456-426614174000",
                "detections": [
                    {
                        "class_id": 0,
                        "class_name": "person",
                        "confidence": 0.95,
                        "bbox": {"x1": 100, "y1": 200, "x2": 300, "y2": 500},
                        "center": {"x": 200, "y": 350},
                        "area": 60000,
                        "track_id": 1
                    }
                ],
                "inference_time": 0.023,
                "image_shape": [720, 1280, 3],
                "detection_count": 1,
                "timestamp": 1640995200.0
            }
        }


class TrackingResponse(BaseModel):
    """追蹤回應模型"""
    image_id: str = Field(..., description="圖片 ID")
    detections: List[Detection] = Field(..., description="偵測結果列表")
    tracks: List[Track] = Field(..., description="追蹤結果列表")
    inference_time: float = Field(..., ge=0.0, description="推論時間 (秒)")
    image_shape: tuple = Field(..., description="圖片尺寸")
    detection_count: int = Field(..., ge=0, description="偵測數量")
    track_count: int = Field(..., ge=0, description="追蹤數量")
    timestamp: float = Field(..., description="時間戳記")


class HeatmapResponse(BaseModel):
    """熱點圖回應模型"""
    heatmap_data: str = Field(..., description="Base64 編碼的熱點圖 PNG")
    grid_size: int = Field(..., description="網格大小")
    max_intensity: float = Field(..., description="最大熱度值")
    min_intensity: float = Field(..., description="最小熱度值")
    generation_time: float = Field(..., description="生成時間 (秒)")
    data_points: int = Field(..., description="資料點數量")
    time_range: Dict[str, datetime] = Field(..., description="時間範圍")


# === 異常事件相關模型 ===

class AlertType(str, Enum):
    """異常事件類型枚舉"""
    DWELL_TIME_EXCEEDED = "dwell_time_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    REVERSE_DIRECTION = "reverse_direction"
    ABANDONED_OBJECT = "abandoned_object"
    CROWD_DENSITY = "crowd_density"
    SPEED_VIOLATION = "speed_violation"


class AlertSeverity(str, Enum):
    """事件嚴重性等級枚舉"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(BaseModel):
    """異常事件模型"""
    alert_id: str = Field(..., description="事件 ID")
    alert_type: AlertType = Field(..., description="事件類型")
    severity: AlertSeverity = Field(..., description="嚴重性等級")
    track_id: Optional[int] = Field(None, description="相關追蹤 ID")
    description: str = Field(..., description="事件描述")
    location: Point2D = Field(..., description="事件位置")
    roi_id: Optional[str] = Field(None, description="相關 ROI ID")
    payload: Dict[str, Any] = Field(default_factory=dict, description="額外資料")
    created_at: datetime = Field(..., description="建立時間")
    resolved_at: Optional[datetime] = Field(None, description="解決時間")
    is_active: bool = Field(default=True, description="是否為活躍事件")


class AlertResponse(BaseModel):
    """異常事件回應模型"""
    alerts: List[Alert] = Field(..., description="事件列表")
    total_count: int = Field(..., description="總事件數")
    active_count: int = Field(..., description="活躍事件數")
    severity_breakdown: Dict[str, int] = Field(..., description="嚴重性分佈")


# === 統計與分析模型 ===

class CountingStats(BaseModel):
    """計數統計模型"""
    total_count: int = Field(..., description="總計數")
    enter_count: int = Field(..., description="進入數")
    exit_count: int = Field(..., description="離開數")
    current_count: int = Field(..., description="當前數量")
    peak_time: Optional[datetime] = Field(None, description="尖峰時間")
    peak_count: int = Field(..., description="尖峰數量")
    time_range: Dict[str, datetime] = Field(..., description="統計時間範圍")


class DwellTimeStats(BaseModel):
    """停留時間統計模型"""
    track_id: int = Field(..., description="追蹤 ID")
    total_dwell_time: float = Field(..., description="總停留時間 (秒)")
    average_speed: float = Field(..., description="平均速度")
    distance_traveled: float = Field(..., description="移動距離")
    roi_visits: List[str] = Field(default_factory=list, description="造訪的 ROI")


# === Unity 整合模型 ===

class UnityObject(BaseModel):
    """Unity 物件同步模型"""
    object_id: str = Field(..., description="Unity 物件 ID")
    track_id: Optional[int] = Field(None, description="對應的追蹤 ID")
    position: Point2D = Field(..., description="世界座標位置")
    rotation: float = Field(default=0.0, description="旋轉角度 (度)")
    scale: float = Field(default=1.0, description="縮放比例")
    class_name: str = Field(..., description="物件類別")
    is_active: bool = Field(default=True, description="是否活躍")
    last_updated: datetime = Field(..., description="最後更新時間")


class UnitySyncData(BaseModel):
    """Unity 同步資料模型"""
    objects: List[UnityObject] = Field(..., description="物件列表")
    heatmap_url: Optional[str] = Field(None, description="熱點圖 URL")
    alerts: List[Alert] = Field(default_factory=list, description="活躍事件列表")
    stats: Dict[str, Any] = Field(default_factory=dict, description="統計資料")
    timestamp: float = Field(..., description="同步時間戳記")


# === 健康檢查模型 ===

class HealthStatus(BaseModel):
    """健康狀態模型"""
    status: str = Field(..., description="狀態: healthy, unhealthy, degraded")
    timestamp: datetime = Field(..., description="檢查時間")
    services: Dict[str, str] = Field(..., description="各服務狀態")
    system_info: Dict[str, Any] = Field(..., description="系統資訊")
    uptime: float = Field(..., description="運行時間 (秒)")


# === 錯誤回應模型 ===

class ErrorResponse(BaseModel):
    """錯誤回應模型"""
    error: str = Field(..., description="錯誤訊息")
    error_type: str = Field(..., description="錯誤類型")
    details: Dict[str, Any] = Field(default_factory=dict, description="錯誤詳情")
    timestamp: datetime = Field(..., description="錯誤時間")
    request_id: Optional[str] = Field(None, description="請求 ID")


# === 分頁模型 ===

class PaginationParams(BaseModel):
    """分頁參數模型"""
    page: int = Field(default=1, ge=1, description="頁碼")
    size: int = Field(default=20, ge=1, le=100, description="每頁大小")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel):
    """分頁回應基礎模型"""
    page: int = Field(..., description="當前頁碼")
    size: int = Field(..., description="每頁大小")
    total: int = Field(..., description="總數量")
    pages: int = Field(..., description="總頁數")
    has_next: bool = Field(..., description="是否有下一頁")
    has_prev: bool = Field(..., description="是否有上一頁")
