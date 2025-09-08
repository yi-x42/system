"""
座標系統轉換工具 - 在資料處理階段直接轉換為 Unity 座標
"""

from typing import Tuple, Dict, Any

class CoordinateConverter:
    """座標系統轉換器"""
    
    def __init__(self, image_width: int = 1920, image_height: int = 1080):
        self.image_width = image_width
        self.image_height = image_height
    
    def convert_pixel_to_unity(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """
        將像素座標轉換為 Unity 螢幕座標
        
        Args:
            pixel_x: 像素座標 X (左上角原點)
            pixel_y: 像素座標 Y (左上角原點)
            
        Returns:
            (unity_x, unity_y): Unity 螢幕座標 (左下角原點，Y軸向上為正)
        """
        unity_x = pixel_x
        unity_y = self.image_height - pixel_y
        return unity_x, unity_y
    
    def convert_bbox_to_unity(self, x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float, float, float]:
        """
        將邊界框座標轉換為 Unity 螢幕座標
        
        Args:
            x1, y1: 左上角座標 (像素)
            x2, y2: 右下角座標 (像素)
            
        Returns:
            (unity_x1, unity_y1, unity_x2, unity_y2): Unity 座標系的邊界框
            - unity_x1, unity_y1: 左下角
            - unity_x2, unity_y2: 右上角
        """
        # 轉換為 Unity 座標
        unity_x1 = x1
        unity_y1 = self.image_height - y2  # 原來的 y2 (下方) 變成 Unity 的 y1 (下方)
        unity_x2 = x2
        unity_y2 = self.image_height - y1  # 原來的 y1 (上方) 變成 Unity 的 y2 (上方)
        
        return unity_x1, unity_y1, unity_x2, unity_y2
    
    def convert_detection_to_unity(self, detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        將整個檢測結果轉換為 Unity 座標系統
        """
        # 取得原始座標 - 支援兩種格式
        if 'bbox' in detection:
            x1, y1, x2, y2 = detection['bbox']
        else:
            # 使用分別的欄位
            x1 = detection.get('bbox_x1', detection.get('x1', 0))
            y1 = detection.get('bbox_y1', detection.get('y1', 0)) 
            x2 = detection.get('bbox_x2', detection.get('x2', 0))
            y2 = detection.get('bbox_y2', detection.get('y2', 0))
        
        # 轉換邊界框
        unity_x1, unity_y1, unity_x2, unity_y2 = self.convert_bbox_to_unity(x1, y1, x2, y2)
        
        # 轉換中心點
        if 'center_x' in detection and 'center_y' in detection:
            unity_center_x, unity_center_y = self.convert_pixel_to_unity(
                detection['center_x'], detection['center_y']
            )
        else:
            # 從邊界框計算中心點
            unity_center_x = (unity_x1 + unity_x2) / 2
            unity_center_y = (unity_y1 + unity_y2) / 2
        
        # 計算寬高（在 Unity 座標系中保持不變）
        width = unity_x2 - unity_x1
        height = unity_y2 - unity_y1
        area = width * height
        
        # 創建新的檢測結果
        unity_detection = detection.copy()
        unity_detection.update({
            'bbox_x1': unity_x1,
            'bbox_y1': unity_y1,
            'bbox_x2': unity_x2,
            'bbox_y2': unity_y2,
            'center_x': unity_center_x,
            'center_y': unity_center_y,
            'width': width,
            'height': height,
            'area': area
        })
        
        return unity_detection
    
    def convert_velocity_to_unity(self, velocity_x: float, velocity_y: float) -> Tuple[float, float]:
        """
        將速度向量轉換為 Unity 座標系統
        
        Args:
            velocity_x: X 方向速度 (像素/秒)
            velocity_y: Y 方向速度 (像素/秒，向下為正)
            
        Returns:
            (unity_vx, unity_vy): Unity 座標系的速度向量 (Y軸向上為正)
        """
        unity_vx = velocity_x
        unity_vy = -velocity_y  # Y軸翻轉
        return unity_vx, unity_vy

# 全域轉換器實例
_global_converter = None

def get_coordinate_converter(image_width: int = 1920, image_height: int = 1080) -> CoordinateConverter:
    """取得座標轉換器實例"""
    global _global_converter
    if _global_converter is None or _global_converter.image_width != image_width or _global_converter.image_height != image_height:
        _global_converter = CoordinateConverter(image_width, image_height)
    return _global_converter
