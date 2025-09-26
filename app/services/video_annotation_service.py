"""
影片標註服務 - 生成帶有檢測資訊的標註影片
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime
import colorsys
import math

try:
    from app.core.logger import main_logger as logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    from app.core.paths import resolve_model_path
except ImportError:
    logger.error("YOLO import failed")
    YOLO = None


class VideoAnnotationService:
    """影片標註服務 - 在影片上標註檢測結果"""
    
    def __init__(self, model_path: str = "yolo11n.pt"):
        self.colors = {}  # 物件ID對應的顏色
        self.trail_history = {}  # 移動軌跡歷史
        self.max_trail_length = 30  # 軌跡最大長度
        
        # 初始化YOLO模型
        try:
            if YOLO is None:
                raise Exception("YOLO not available")
            
            # 檢查模型檔案
            # 解析模型路徑 (允許傳入簡單檔名)
            model_path = resolve_model_path(model_path)
            model_file = Path(model_path)
            if not model_file.exists():
                # 嘗試在當前目錄查找
                current_dir_model = Path.cwd() / model_path
                if current_dir_model.exists():
                    model_path = str(current_dir_model)
                else:
                    logger.warning(f"Model file not found: {model_path}, will download automatically")
            
            logger.info(f"Loading YOLO model: {model_path}")
            self.model = YOLO(model_path)
            logger.info(f"YOLO model loaded successfully: {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise Exception(f"YOLO model initialization failed: {e}")
        
        logger.info("VideoAnnotationService initialized successfully")
        
    def generate_annotated_video(self, input_video_path: str, output_video_path: str = None) -> Dict:
        """
        生成標註後的影片
        
        Args:
            input_video_path: 輸入影片路徑
            output_video_path: 輸出影片路徑，如果為None則自動生成
            
        Returns:
            包含處理結果的字典
        """
        try:
            input_path = Path(input_video_path)
            if not input_path.exists():
                raise FileNotFoundError(f"輸入影片不存在: {input_video_path}")
            
            # 自動生成輸出路徑
            if output_video_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_dir = Path("annotated_videos")
                output_dir.mkdir(exist_ok=True)
                output_video_path = output_dir / f"annotated_{input_path.stem}_{timestamp}.mp4"
            else:
                output_video_path = Path(output_video_path)
                output_video_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"開始生成標註影片: {input_video_path} -> {output_video_path}")
            print(f"🎬 開始處理影片: {input_path.name}")
            print(f"📁 輸出位置: {output_video_path}")
            
            # 開啟輸入影片
            cap = cv2.VideoCapture(str(input_video_path))
            if not cap.isOpened():
                raise Exception(f"無法開啟影片: {input_video_path}")
            
            # 獲取影片資訊
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 設定輸出影片
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))
            
            if not out.isOpened():
                # 嘗試不同的編解碼器
                print("⚠️  嘗試使用 XVID 編解碼器")
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                output_video_path = output_video_path.with_suffix('.avi')
                out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))
                
                if not out.isOpened():
                    raise Exception(f"無法建立輸出影片: {output_video_path}")
            
            frame_count = 0
            processed_frames = 0
            
            logger.info(f"影片資訊: {width}x{height}, {fps}FPS, {total_frames}幀")
            logger.info(f"YOLO模型狀態: {self.model}")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.info("影片讀取完畢")
                    break
                
                try:
                    # 進行物件檢測 (不使用tracking避免lap問題)
                    results = self.model(frame, verbose=False)
                    
                    # 標註影片幀
                    annotated_frame = self._annotate_frame(frame, results, frame_count)
                    
                    # 寫入輸出影片
                    out.write(annotated_frame)
                    
                except Exception as frame_error:
                    logger.warning(f"處理幀 {frame_count} 時發生錯誤: {frame_error}")
                    # 如果處理失敗，直接寫入原始幀
                    out.write(frame)
                
                frame_count += 1
                processed_frames += 1
                
                # 每處理50幀輸出一次進度
                if processed_frames % 50 == 0:
                    progress = (processed_frames / total_frames) * 100 if total_frames > 0 else 0
                    print(f"📈 處理進度: {processed_frames}/{total_frames} ({progress:.1f}%)")
                    logger.info(f"處理進度: {processed_frames}/{total_frames} ({progress:.1f}%)")
            
            # 釋放資源
            cap.release()
            out.release()
            cv2.destroyAllWindows()  # 清理所有OpenCV窗口
            
            # 確認檔案是否成功生成
            output_path = Path(output_video_path)
            if not output_path.exists():
                raise Exception(f"輸出影片檔案未生成: {output_video_path}")
            
            file_size = output_path.stat().st_size
            if file_size == 0:
                raise Exception(f"輸出影片檔案為空: {output_video_path}")
            
            print(f"✅ 標註影片生成成功!")
            print(f"📁 檔案位置: {output_video_path}")
            print(f"📊 檔案大小: {file_size / 1024 / 1024:.2f} MB")
            
            result = {
                "status": "success",
                "input_video": str(input_video_path),
                "output_video": str(output_video_path),
                "total_frames": total_frames,
                "processed_frames": processed_frames,
                "video_info": {
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "duration": total_frames / fps if fps > 0 else 0
                }
            }
            
            logger.info(f"標註影片生成完成: {output_video_path}")
            return result
            
        except Exception as e:
            logger.error(f"生成標註影片失敗: {e}")
            raise
        finally:
            if 'cap' in locals():
                cap.release()
            if 'out' in locals():
                out.release()
    
    def _annotate_frame(self, frame: np.ndarray, results, frame_number: int) -> np.ndarray:
        """標註單一幀"""
        annotated_frame = frame.copy()
        
        if not results or len(results) == 0:
            return self._add_frame_info(annotated_frame, frame_number, 0)
        
        detections = []
        
        # 解析檢測結果
        for result in results:
            if result.boxes is not None:
                boxes = result.boxes
                for i in range(len(boxes)):
                    detection = {
                        'bbox': boxes.xyxy[i].cpu().numpy(),
                        'confidence': float(boxes.conf[i].cpu().numpy()),
                        'class_id': int(boxes.cls[i].cpu().numpy()),
                        'class_name': result.names[int(boxes.cls[i].cpu().numpy())],
                        'track_id': int(boxes.id[i].cpu().numpy()) if boxes.id is not None else None
                    }
                    detections.append(detection)
        
        # 標註每個檢測物件
        for detection in detections:
            annotated_frame = self._draw_detection(annotated_frame, detection, frame_number)
        
        # 添加整體資訊
        annotated_frame = self._add_frame_info(annotated_frame, frame_number, len(detections))
        
        return annotated_frame
    
    def _draw_detection(self, frame: np.ndarray, detection: Dict, frame_number: int) -> np.ndarray:
        """繪製單個檢測物件的標註"""
        bbox = detection['bbox']
        track_id = detection.get('track_id')
        class_name = detection['class_name']
        confidence = detection['confidence']
        
        x1, y1, x2, y2 = map(int, bbox)
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        # 獲取物件顏色
        color = self._get_object_color(track_id if track_id else detection['class_id'])
        
        # 繪製邊界框
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # 更新移動軌跡
        if track_id is not None:
            self._update_trail(track_id, (center_x, center_y))
            # 繪製移動軌跡
            self._draw_trail(frame, track_id, color)
            # 計算和繪製移動方向
            direction = self._calculate_direction(track_id)
            if direction:
                self._draw_direction_arrow(frame, (center_x, center_y), direction, color)
        
        # 準備標籤文字
        if track_id is not None:
            label = f"ID:{track_id} {class_name}"
        else:
            label = f"{class_name}"
        
        label += f" {confidence:.2f}"
        
        # 計算文字尺寸
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
        
        # 繪製文字背景
        cv2.rectangle(frame, (x1, y1 - text_h - baseline - 10), 
                     (x1 + text_w, y1), color, -1)
        
        # 繪製文字
        cv2.putText(frame, label, (x1, y1 - baseline - 5),
                   font, font_scale, (255, 255, 255), thickness)
        
        # 繪製中心點
        cv2.circle(frame, (center_x, center_y), 4, color, -1)
        cv2.circle(frame, (center_x, center_y), 4, (255, 255, 255), 1)
        
        # 添加速度資訊（如果有移動軌跡）
        if track_id is not None and len(self.trail_history.get(track_id, [])) > 1:
            speed = self._calculate_speed(track_id)
            if speed is not None:
                speed_text = f"Speed: {speed:.1f}"
                cv2.putText(frame, speed_text, (x1, y2 + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return frame
    
    def _get_object_color(self, obj_id: int) -> Tuple[int, int, int]:
        """獲取物件的固定顏色"""
        if obj_id not in self.colors:
            # 使用HSV色彩空間生成不同的顏色
            hue = (obj_id * 137.508) % 360  # 黃金角度分佈
            saturation = 0.7 + (obj_id % 3) * 0.1  # 0.7-1.0
            value = 0.8 + (obj_id % 2) * 0.2  # 0.8-1.0
            
            # 轉換為BGR
            rgb = colorsys.hsv_to_rgb(hue/360, saturation, value)
            bgr = tuple(int(c * 255) for c in rgb[::-1])  # RGB to BGR
            self.colors[obj_id] = bgr
        
        return self.colors[obj_id]
    
    def _update_trail(self, track_id: int, position: Tuple[int, int]):
        """更新移動軌跡"""
        if track_id not in self.trail_history:
            self.trail_history[track_id] = []
        
        self.trail_history[track_id].append(position)
        
        # 限制軌跡長度
        if len(self.trail_history[track_id]) > self.max_trail_length:
            self.trail_history[track_id].pop(0)
    
    def _draw_trail(self, frame: np.ndarray, track_id: int, color: Tuple[int, int, int]):
        """繪製移動軌跡"""
        if track_id not in self.trail_history:
            return
        
        points = self.trail_history[track_id]
        if len(points) < 2:
            return
        
        # 繪製軌跡線
        for i in range(1, len(points)):
            # 根據時間遠近調整透明度
            alpha = i / len(points)
            thickness = max(1, int(alpha * 3))
            
            # 調整顏色亮度
            trail_color = tuple(int(c * alpha) for c in color)
            
            cv2.line(frame, points[i-1], points[i], trail_color, thickness)
        
        # 繪製軌跡點
        for i, point in enumerate(points):
            alpha = (i + 1) / len(points)
            radius = max(1, int(alpha * 3))
            trail_color = tuple(int(c * alpha) for c in color)
            cv2.circle(frame, point, radius, trail_color, -1)
    
    def _calculate_direction(self, track_id: int) -> Optional[float]:
        """計算移動方向（角度）"""
        if track_id not in self.trail_history:
            return None
        
        points = self.trail_history[track_id]
        if len(points) < 2:
            return None
        
        # 使用最近的幾個點計算方向
        recent_points = points[-min(5, len(points)):]
        if len(recent_points) < 2:
            return None
        
        # 計算平均移動方向
        dx_total, dy_total = 0, 0
        for i in range(1, len(recent_points)):
            dx = recent_points[i][0] - recent_points[i-1][0]
            dy = recent_points[i][1] - recent_points[i-1][1]
            dx_total += dx
            dy_total += dy
        
        if dx_total == 0 and dy_total == 0:
            return None
        
        # 計算角度（弧度轉度）
        angle = math.atan2(dy_total, dx_total) * 180 / math.pi
        return angle
    
    def _draw_direction_arrow(self, frame: np.ndarray, center: Tuple[int, int], 
                             angle: float, color: Tuple[int, int, int]):
        """繪製方向箭頭"""
        cx, cy = center
        
        # 箭頭長度
        arrow_length = 30
        
        # 計算箭頭終點
        end_x = int(cx + arrow_length * math.cos(math.radians(angle)))
        end_y = int(cy + arrow_length * math.sin(math.radians(angle)))
        
        # 繪製主線
        cv2.arrowedLine(frame, (cx, cy), (end_x, end_y), color, 3, tipLength=0.3)
        
        # 添加方向文字
        direction_text = self._angle_to_direction_text(angle)
        text_x = end_x + 5
        text_y = end_y - 5
        
        cv2.putText(frame, direction_text, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    def _angle_to_direction_text(self, angle: float) -> str:
        """將角度轉換為方向文字"""
        # 正規化角度到0-360度
        angle = angle % 360
        if angle < 0:
            angle += 360
        
        if 337.5 <= angle or angle < 22.5:
            return "→"  # 右
        elif 22.5 <= angle < 67.5:
            return "↘"  # 右下
        elif 67.5 <= angle < 112.5:
            return "↓"  # 下
        elif 112.5 <= angle < 157.5:
            return "↙"  # 左下
        elif 157.5 <= angle < 202.5:
            return "←"  # 左
        elif 202.5 <= angle < 247.5:
            return "↖"  # 左上
        elif 247.5 <= angle < 292.5:
            return "↑"  # 上
        elif 292.5 <= angle < 337.5:
            return "↗"  # 右上
        else:
            return "?"
    
    def _calculate_speed(self, track_id: int) -> Optional[float]:
        """計算移動速度（像素/幀）"""
        if track_id not in self.trail_history:
            return None
        
        points = self.trail_history[track_id]
        if len(points) < 2:
            return None
        
        # 計算最近幾個點的平均速度
        recent_points = points[-min(10, len(points)):]
        if len(recent_points) < 2:
            return None
        
        total_distance = 0
        for i in range(1, len(recent_points)):
            dx = recent_points[i][0] - recent_points[i-1][0]
            dy = recent_points[i][1] - recent_points[i-1][1]
            distance = math.sqrt(dx*dx + dy*dy)
            total_distance += distance
        
        # 平均速度（像素/幀）
        avg_speed = total_distance / (len(recent_points) - 1)
        return avg_speed
    
    def _add_frame_info(self, frame: np.ndarray, frame_number: int, object_count: int) -> np.ndarray:
        """添加幀資訊"""
        height, width = frame.shape[:2]
        
        # 添加半透明背景
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # 添加文字資訊
        info_text = [
            f"Frame: {frame_number}",
            f"Objects: {object_count}",
            f"Resolution: {width}x{height}"
        ]
        
        for i, text in enumerate(info_text):
            cv2.putText(frame, text, (15, 30 + i * 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame


# 全域服務實例
# 延遲初始化的全域服務實例  
_video_annotation_service = None

def get_video_annotation_service():
    """獲取影片標註服務實例（延遲初始化）"""
    global _video_annotation_service
    if _video_annotation_service is None:
        _video_annotation_service = VideoAnnotationService()
    return _video_annotation_service

# 向後相容性別名
def video_annotation_service():
    return get_video_annotation_service()
