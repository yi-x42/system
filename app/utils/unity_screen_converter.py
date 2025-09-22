"""
Unity 螢幕座標轉換器
將像素座標轉換為 Unity 螢幕座標格式
"""

from typing import Dict, List, Union

class UnityScreenConverter:
    """Unity 螢幕座標轉換器"""
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        self.screen_width = screen_width
        self.screen_height = screen_height
    
    def convert_to_unity_screen(self, pixel_x: float, pixel_y: float) -> Dict[str, float]:
        """
        將像素座標轉換為 Unity 螢幕座標
        
        Args:
            pixel_x: 像素座標 X (左上角原點)
            pixel_y: 像素座標 Y (左上角原點)
            
        Returns:
            Unity 螢幕座標 (左下角原點，Y軸向上為正)
        """
        # Unity 螢幕座標：左下角為原點(0,0)，Y軸向上為正
        unity_screen_x = pixel_x
        unity_screen_y = self.screen_height - pixel_y
        
        return {
            "screen_x": unity_screen_x,
            "screen_y": unity_screen_y
        }
    
    def convert_bbox_to_unity_screen(self, 
                                   center_x: float, 
                                   center_y: float,
                                   bbox_x1: float, 
                                   bbox_y1: float,
                                   bbox_x2: float, 
                                   bbox_y2: float) -> Dict[str, Union[float, Dict]]:
        """
        將邊界框座標轉換為 Unity 螢幕座標
        """
        # 轉換中心點
        center_unity = self.convert_to_unity_screen(center_x, center_y)
        
        # 轉換邊界框四個角
        bbox_unity = {
            "x1": bbox_x1,
            "y1": self.screen_height - bbox_y2,  # 左下角
            "x2": bbox_x2,
            "y2": self.screen_height - bbox_y1   # 右上角
        }
        
        # 計算寬高（在 Unity 座標系中保持不變）
        width = bbox_x2 - bbox_x1
        height = bbox_y2 - bbox_y1
        
        return {
            "center": {
                "screen_x": center_unity["screen_x"],
                "screen_y": center_unity["screen_y"]
            },
            "bbox": {
                "screen_x1": bbox_unity["x1"],  # 左下角 X
                "screen_y1": bbox_unity["y1"],  # 左下角 Y
                "screen_x2": bbox_unity["x2"],  # 右上角 X
                "screen_y2": bbox_unity["y2"]   # 右上角 Y
            },
            "size": {
                "width": width,
                "height": height
            },
            "coordinate_system": "Unity Screen Space (pixels, bottom-left origin, Y-up)"
        }
    
    def convert_detection_list(self, detections: List[Dict]) -> List[Dict]:
        """
        批量轉換檢測結果為 Unity 螢幕座標
        """
        converted_detections = []
        
        for detection in detections:
            # 取得原始座標
            center_x = detection.get('center_x', 0)
            center_y = detection.get('center_y', 0)
            bbox_x1 = detection.get('bbox_x1', 0)
            bbox_y1 = detection.get('bbox_y1', 0)
            bbox_x2 = detection.get('bbox_x2', 0)
            bbox_y2 = detection.get('bbox_y2', 0)
            
            # 轉換座標
            unity_coords = self.convert_bbox_to_unity_screen(
                center_x, center_y, bbox_x1, bbox_y1, bbox_x2, bbox_y2
            )
            
            # 建立新的檢測結果
            unity_detection = {
                # 基本資訊保持不變
                "id": detection.get('id'),
                "analysis_id": detection.get('analysis_id'),
                "timestamp": detection.get('timestamp'),
                "frame_number": detection.get('frame_number'),
                "object_type": detection.get('object_type'),
                "object_chinese": detection.get('object_chinese'),
                "confidence": detection.get('confidence'),
                
                # Unity 螢幕座標（主要使用）
                "screen_x": unity_coords["center"]["screen_x"],
                "screen_y": unity_coords["center"]["screen_y"],
                
                # Unity 邊界框座標
                "bbox_screen_x1": unity_coords["bbox"]["screen_x1"],
                "bbox_screen_y1": unity_coords["bbox"]["screen_y1"],
                "bbox_screen_x2": unity_coords["bbox"]["screen_x2"],
                "bbox_screen_y2": unity_coords["bbox"]["screen_y2"],
                
                # 尺寸資訊
                "width": unity_coords["size"]["width"],
                "height": unity_coords["size"]["height"],
                
                # 追蹤和分析資料
                "track_id": detection.get('track_id'),
                "zone": detection.get('zone'),
                "zone_chinese": detection.get('zone_chinese'),
                
                # 速度資訊（需要轉換 Y 軸）
                "velocity_x": detection.get('velocity_x', 0.0),
                "velocity_y": -detection.get('velocity_y', 0.0),  # Y軸翻轉
                "velocity_magnitude": detection.get('velocity_magnitude', 0.0),
                
                # 座標系統資訊
                "coordinate_system": unity_coords["coordinate_system"],
                
                # 原始像素座標（參考用）
                "original_pixel": {
                    "center_x": center_x,
                    "center_y": center_y,
                    "bbox_x1": bbox_x1,
                    "bbox_y1": bbox_y1,
                    "bbox_x2": bbox_x2,
                    "bbox_y2": bbox_y2
                },
                
                # 其他欄位
                "created_at": detection.get('created_at')
            }
            
            converted_detections.append(unity_detection)
        
        return converted_detections

def convert_to_unity_screen_format(detections: List[Dict], 
                                 screen_width: int = 1920, 
                                 screen_height: int = 1080) -> Dict:
    """
    快速轉換函數 - 將檢測結果轉換為 Unity 螢幕座標格式
    """
    converter = UnityScreenConverter(screen_width, screen_height)
    unity_detections = converter.convert_detection_list(detections)
    
    return {
        "detections": unity_detections,
        "total_count": len(unity_detections),
        "coordinate_system": "Unity Screen Space",
        "coordinate_info": {
            "origin": "Bottom-left corner (0, 0)",
            "y_axis": "Upward positive",
            "unit": "Pixels",
            "screen_resolution": {
                "width": screen_width,
                "height": screen_height
            }
        }
    }

# 使用範例
if __name__ == "__main__":
    # 測試轉換
    test_detection = {
        "id": 1,
        "center_x": 320,
        "center_y": 240,
        "bbox_x1": 280,
        "bbox_y1": 180,
        "bbox_x2": 360,
        "bbox_y2": 300,
        "object_type": "person",
        "confidence": 0.85
    }
    
    result = convert_to_unity_screen_format([test_detection])
    
    print("🎮 Unity 螢幕座標轉換結果:")
    print(f"原始像素座標: center_x={test_detection['center_x']}, center_y={test_detection['center_y']}")
    
    unity_detection = result["detections"][0]
    print(f"Unity 螢幕座標: screen_x={unity_detection['screen_x']}, screen_y={unity_detection['screen_y']}")
    print(f"座標系統: {result['coordinate_info']['origin']}, {result['coordinate_info']['y_axis']}")
