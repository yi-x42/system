"""
測試座標 API - 用於驗證 Unity 座標系統
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_async_db
from app.models.analysis import DetectionResult, AnalysisRecord, BehaviorEvent
from typing import List, Dict, Any
import json

router = APIRouter()

@router.get("/coordinates/test", summary="測試座標資料", description="取得簡化的座標資訊用於測試")
async def test_coordinates(
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db)
):
    """
    測試座標 API - 只回傳座標相關資訊
    
    - **limit**: 限制回傳筆數 (預設: 10)
    - 回傳格式: Unity 螢幕座標 (左下角原點，Y軸向上)
    """
    
    try:
        # 查詢檢測結果的座標資訊
        query = select(
            DetectionResult.id,
            DetectionResult.object_type,
            DetectionResult.confidence,
            DetectionResult.center_x,
            DetectionResult.center_y,
            DetectionResult.bbox_x1,
            DetectionResult.bbox_y1,
            DetectionResult.bbox_x2,
            DetectionResult.bbox_y2,
            DetectionResult.created_at
        ).limit(limit)
        
        result = await db.execute(query)
        detections = result.fetchall()
        
        # 格式化座標資料 - 以邊界框為主
        coordinates_data = []
        for detection in detections:
            coord_info = {
                "id": detection.id,
                "object_type": detection.object_type,
                "confidence": round(detection.confidence, 3),
                "bounding_box": {
                    "x1": detection.bbox_x1,  # 左下角 X
                    "y1": detection.bbox_y1,  # 左下角 Y
                    "x2": detection.bbox_x2,  # 右上角 X
                    "y2": detection.bbox_y2,  # 右上角 Y
                    "width": detection.bbox_x2 - detection.bbox_x1,
                    "height": detection.bbox_y2 - detection.bbox_y1
                },
                "center_point": {
                    "x": detection.center_x,
                    "y": detection.center_y
                },
                "timestamp": detection.created_at.isoformat() if detection.created_at else None
            }
            coordinates_data.append(coord_info)
        
        return {
            "status": "success",
            "coordinate_system": "Unity Screen Space - Bounding Box Format",
            "description": "左下角為原點(0,0)，Y軸向上為正，邊界框格式 (x1,y1) -> (x2,y2)",
            "unit": "像素",
            "bbox_format": "x1,y1 = 左下角座標, x2,y2 = 右上角座標",
            "total_found": len(coordinates_data),
            "coordinates": coordinates_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查詢座標資料失敗: {str(e)}"
        )

@router.get("/coordinates/sample", summary="座標格式範例", description="顯示 Unity 座標格式範例")
async def coordinates_sample():
    """
    Unity 座標格式範例
    
    展示標準的 Unity 螢幕座標格式
    """
    
    sample_data = {
        "coordinate_system_info": {
            "name": "Unity Screen Space - Bounding Box Format",
            "origin": "左下角 (0, 0)",
            "y_axis": "向上為正",
            "unit": "像素",
            "screen_resolution": "1920x1080",
            "bbox_format": "x1,y1 = 左下角, x2,y2 = 右上角"
        },
        "sample_coordinates": [
            {
                "id": 1,
                "object_type": "person",
                "confidence": 0.856,
                "bounding_box": {
                    "x1": 280.0,    # 左下角 X
                    "y1": 780.0,    # 左下角 Y (Unity: Y軸向上)
                    "x2": 360.0,    # 右上角 X
                    "y2": 900.0,    # 右上角 Y (Unity: Y軸向上)
                    "width": 80.0,  # 寬度
                    "height": 120.0 # 高度
                },
                "center_point": {
                    "x": 320.0,     # 中心點 X
                    "y": 840.0      # 中心點 Y
                }
            },
            {
                "id": 2,
                "object_type": "car",
                "confidence": 0.923,
                "bounding_box": {
                    "x1": 900.0,    # 左下角 X
                    "y1": 480.0,    # 左下角 Y
                    "x2": 1020.0,   # 右上角 X
                    "y2": 600.0,    # 右上角 Y
                    "width": 120.0,
                    "height": 120.0
                },
                "center_point": {
                    "x": 960.0,     # 螢幕中央
                    "y": 540.0      # 螢幕中央
                }
            },
            {
                "id": 3,
                "object_type": "bicycle",
                "confidence": 0.734,
                "bounding_box": {
                    "x1": 1550.0,   # 左下角 X
                    "y1": 200.0,    # 左下角 Y (螢幕下方)
                    "x2": 1650.0,   # 右上角 X
                    "y2": 280.0,    # 右上角 Y
                    "width": 100.0,
                    "height": 80.0
                },
                "center_point": {
                    "x": 1600.0,    # 螢幕右側
                    "y": 240.0      # 螢幕下方
                }
            }
        ],
        "unity_usage_note": {
            "description": "邊界框座標可以直接在 Unity 中使用",
            "coordinate_conversion": "已完成，無需額外轉換",
            "bounding_box_usage": {
                "rect_creation": "new Rect(x1, y1, width, height)",
                "position_mapping": "左下角對應 Unity 的 (x1, y1)",
                "size_calculation": "width = x2 - x1, height = y2 - y1"
            },
            "screen_mapping": {
                "bottom": "y1, y2 接近 0 (螢幕底部)",
                "top": "y1, y2 接近 1080 (螢幕頂部)",
                "left": "x1, x2 接近 0 (螢幕左側)", 
                "right": "x1, x2 接近 1920 (螢幕右側)"
            }
        }
    }
    
    return sample_data

@router.get("/coordinates/count", summary="座標資料統計", description="顯示資料庫中座標資料的統計資訊")
async def coordinates_count(db: AsyncSession = Depends(get_async_db)):
    """
    座標資料統計
    
    顯示資料庫中各種物件的座標資料統計
    """
    
    try:
        # 統計各類型物件數量
        stats_query = text("""
            SELECT 
                object_type,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence,
                MIN(center_x) as min_x,
                MAX(center_x) as max_x,
                MIN(center_y) as min_y,
                MAX(center_y) as max_y
            FROM detection_results 
            GROUP BY object_type 
            ORDER BY count DESC
        """)
        
        result = await db.execute(stats_query)
        stats = result.fetchall()
        
        # 總計查詢
        total_query = select(DetectionResult).count()
        total_count = await db.scalar(select(total_query))
        
        object_stats = []
        for stat in stats:
            object_stats.append({
                "object_type": stat.object_type,
                "count": stat.count,
                "avg_confidence": round(stat.avg_confidence, 3),
                "coordinate_range": {
                    "x_range": {"min": stat.min_x, "max": stat.max_x},
                    "y_range": {"min": stat.min_y, "max": stat.max_y}
                }
            })
        
        return {
            "status": "success",
            "coordinate_system": "Unity Screen Space - Bounding Box (左下角原點，Y軸向上)",
            "bbox_format": "x1,y1 = 左下角, x2,y2 = 右上角",
            "total_detections": total_count or 0,
            "object_statistics": object_stats,
            "database_status": "資料使用 Unity 邊界框座標格式" if total_count > 0 else "資料庫為空，等待新檢測資料"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"統計查詢失敗: {str(e)}",
            "coordinate_system": "Unity Screen Space - Bounding Box (左下角原點，Y軸向上)",
            "bbox_format": "x1,y1 = 左下角, x2,y2 = 右上角",
            "total_detections": 0,
            "object_statistics": [],
            "database_status": "查詢錯誤或資料庫為空"
        }
