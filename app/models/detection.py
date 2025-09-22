"""
偵測相關的資料模型
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class BBox(BaseModel):
    """邊界框座標"""
    x1: float = Field(..., description="左上角 X 座標")
    y1: float = Field(..., description="左上角 Y 座標") 
    x2: float = Field(..., description="右下角 X 座標")
    y2: float = Field(..., description="右下角 Y 座標")
    
    class Config:
        json_schema_extra = {  # 修復 Pydantic v2 警告
            "example": {
                "x1": 100.0,
                "y1": 150.0,
                "x2": 200.0,
                "y2": 250.0
            }
        }

class Detection(BaseModel):
    """單個偵測結果"""
    class_id: int = Field(..., description="類別 ID")
    class_name: str = Field(..., description="類別名稱")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心值")
    bbox: BBox = Field(..., description="邊界框")
    
    class Config:
        json_schema_extra = {
            "example": {
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.85,
                "bbox": {
                    "x1": 100.0,
                    "y1": 150.0, 
                    "x2": 200.0,
                    "y2": 250.0
                }
            }
        }

class DetectionResponse(BaseModel):
    """偵測回應"""
    success: bool = Field(..., description="偵測是否成功")
    detections: List[Detection] = Field(..., description="偵測結果列表")
    processing_time: float = Field(..., description="處理時間（秒）")
    image_info: Dict[str, Any] = Field(..., description="圖片資訊")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "detections": [
                    {
                        "class_id": 0,
                        "class_name": "person",
                        "confidence": 0.85,
                        "bbox": {
                            "x1": 100.0,
                            "y1": 150.0,
                            "x2": 200.0, 
                            "y2": 250.0
                        }
                    }
                ],
                "processing_time": 0.156,
                "image_info": {
                    "width": 640,
                    "height": 480,
                    "format": "JPEG"
                },
                "timestamp": "2025-01-19T00:20:26"
            }
        }