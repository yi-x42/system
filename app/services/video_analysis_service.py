"""
影片分析服務 - 核心分析功能
支援攝影機輸入、影片分析、行為檢測、CSV輸出
"""

import cv2
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import threading
import queue
import json
import uuid
from ultralytics import YOLO
from app.core.paths import resolve_model_path

from app.core.logger import main_logger as logger
from app.utils.coordinate_system import get_coordinate_converter


def safe_strftime(dt_value, format_str='%Y-%m-%d %H:%M:%S.%f'):
    """安全地將日期時間對象格式化為字串"""
    if dt_value is None:
        return None
    if isinstance(dt_value, str):
        return dt_value  # 如果已經是字串，直接返回
    if hasattr(dt_value, 'strftime'):
        return dt_value.strftime(format_str)
    return str(dt_value)  # 最後的備用方案


@dataclass
class DetectionRecord:
    """檢測記錄資料結構 - 使用 Unity 螢幕座標系統"""
    timestamp: str
    frame_number: int
    object_id: int
    object_type: str
    confidence: float
    bbox_x1: float  # Unity 座標：左下角 X
    bbox_y1: float  # Unity 座標：左下角 Y  
    bbox_x2: float  # Unity 座標：右上角 X
    bbox_y2: float  # Unity 座標：右上角 Y
    center_x: float # Unity 座標：中心 X
    center_y: float # Unity 座標：中心 Y (Y軸向上為正)
    width: float
    height: float
    area: float
    zone: Optional[str] = None
    speed: Optional[float] = None
    direction: Optional[float] = None
    source: str = "unknown"


@dataclass
class BehaviorEvent:
    """行為事件資料結構"""
    event_id: str
    timestamp: str
    object_id: int
    object_type: str
    behavior: str
    zone: str
    position_x: float
    position_y: float
    duration: Optional[float] = None
    confidence: float = 1.0
    metadata: str = "{}"
    source: str = "unknown"


class ZoneManager:
    """區域管理器 - 定義和管理檢測區域"""
    
    def __init__(self):
        self.zones = {}
        self.zone_counters = defaultdict(int)
        
    def add_zone(self, zone_name: str, polygon: List[Tuple[int, int]]):
        """新增檢測區域"""
        self.zones[zone_name] = np.array(polygon, dtype=np.int32)
        logger.info(f"新增檢測區域: {zone_name}")
        
    def get_zone(self, point: Tuple[float, float]) -> Optional[str]:
        """檢查點位於哪個區域"""
        for zone_name, polygon in self.zones.items():
            if cv2.pointPolygonTest(polygon, point, False) >= 0:
                return zone_name
        return "unknown_area"
        
    def setup_default_zones(self, frame_width: int, frame_height: int):
        """設置預設區域"""
        # 入口區域 (上方 1/4)
        self.add_zone("entrance", [
            (0, 0), (frame_width, 0), 
            (frame_width, frame_height//4), (0, frame_height//4)
        ])
        
        # 中央活動區域
        self.add_zone("center_area", [
            (frame_width//4, frame_height//4), 
            (3*frame_width//4, frame_height//4),
            (3*frame_width//4, 3*frame_height//4), 
            (frame_width//4, 3*frame_height//4)
        ])
        
        # 出口區域 (下方 1/4)
        self.add_zone("exit", [
            (0, 3*frame_height//4), (frame_width, 3*frame_height//4),
            (frame_width, frame_height), (0, frame_height)
        ])
        
        # 左側區域
        self.add_zone("left_area", [
            (0, frame_height//4), (frame_width//4, frame_height//4),
            (frame_width//4, 3*frame_height//4), (0, 3*frame_height//4)
        ])
        
        # 右側區域
        self.add_zone("right_area", [
            (3*frame_width//4, frame_height//4), (frame_width, frame_height//4),
            (frame_width, 3*frame_height//4), (3*frame_width//4, 3*frame_height//4)
        ])


class ObjectTracker:
    """物件追蹤器 - 處理多目標追蹤"""
    
    def __init__(self):
        self.tracks = {}  # object_id -> track_info
        self.track_history = defaultdict(lambda: deque(maxlen=50))
        self.next_id = 1
        self.disappeared_tracks = {}
        
    def update_tracks(self, detections: List[Dict], frame_number: int, source: str, 
                     image_width: int = 1920, image_height: int = 1080) -> List[DetectionRecord]:
        """更新追蹤資訊並返回檢測記錄 - 使用 Unity 座標系統"""
        current_time = datetime.now()
        records = []
        
        # 取得座標轉換器
        converter = get_coordinate_converter(image_width, image_height)
        
        for det in detections:
            # 使用 YOLO 內建的追蹤 ID
            obj_id = det.get('track_id')
            if obj_id is None:
                obj_id = self.next_id
                self.next_id += 1
                
            # 取得原始像素座標
            pixel_x1, pixel_y1, pixel_x2, pixel_y2 = det['bbox']
            
            # 轉換為 Unity 螢幕座標
            unity_x1, unity_y1, unity_x2, unity_y2 = converter.convert_bbox_to_unity(
                pixel_x1, pixel_y1, pixel_x2, pixel_y2
            )
            
            # 計算 Unity 座標系的中心點和尺寸
            center_x = (unity_x1 + unity_x2) / 2
            center_y = (unity_y1 + unity_y2) / 2
            width = unity_x2 - unity_x1
            height = unity_y2 - unity_y1
            area = width * height
            
            # 更新追蹤歷史（使用 Unity 座標）
            self.track_history[obj_id].append({
                'timestamp': current_time,  # 保持為 datetime 對象以便計算
                'center': (center_x, center_y),
                'bbox': (unity_x1, unity_y1, unity_x2, unity_y2),
                'frame_number': frame_number
            })
            
            # 計算速度和方向（在 Unity 座標系中）
            speed, direction = self._calculate_motion(obj_id)
            
            record = DetectionRecord(
                timestamp=safe_strftime(current_time, '%Y-%m-%d %H:%M:%S.%f'),
                frame_number=frame_number,
                object_id=obj_id,
                object_type=det['class'],
                confidence=det['confidence'],
                bbox_x1=unity_x1,  # Unity 座標：左下角 X
                bbox_y1=unity_y1,  # Unity 座標：左下角 Y
                bbox_x2=unity_x2,  # Unity 座標：右上角 X
                bbox_y2=unity_y2,  # Unity 座標：右上角 Y
                center_x=center_x, # Unity 座標：中心 X
                center_y=center_y, # Unity 座標：中心 Y (Y軸向上)
                width=width,
                height=height,
                area=area,
                speed=speed,
                direction=direction,
                source=source
            )
            
            records.append(record)
            
        return records
        
    def _calculate_motion(self, obj_id: int) -> Tuple[Optional[float], Optional[float]]:
        """計算物件移動速度和方向 - Unity 座標系統"""
        history = self.track_history[obj_id]
        if len(history) < 2:
            return None, None
            
        recent = list(history)[-2:]
        dt = (recent[1]['timestamp'] - recent[0]['timestamp']).total_seconds()
        
        if dt == 0:
            return None, None
            
        # 在 Unity 座標系中計算位移
        dx = recent[1]['center'][0] - recent[0]['center'][0]
        dy = recent[1]['center'][1] - recent[0]['center'][1]  # Y軸向上為正
        
        speed = np.sqrt(dx**2 + dy**2) / dt  # pixels per second
        
        # 計算方向角度（Unity 座標系，Y軸向上）
        direction = np.arctan2(dy, dx) * 180 / np.pi  # degrees
        
        return speed, direction


class BehaviorAnalyzer:
    """行為分析器 - 分析物件行為模式"""
    
    def __init__(self):
        self.loitering_threshold = 10.0  # 停留時間門檻(秒)
        self.speed_threshold = 100.0  # 異常速度門檻
        self.crowd_threshold = 5  # 擁擠門檻
        self.object_states = {}  # object_id -> state info
        self.zone_occupancy = defaultdict(int)
        
    def analyze_behavior(self, records: List[DetectionRecord], 
                        zone_manager: ZoneManager) -> List[BehaviorEvent]:
        """分析行為事件"""
        events = []
        current_time = datetime.now()
        
        # 更新區域佔用統計
        self.zone_occupancy.clear()
        
        for record in records:
            # 更新區域資訊
            record.zone = zone_manager.get_zone((record.center_x, record.center_y))
            self.zone_occupancy[record.zone] += 1
            
            # 檢測各種行為
            events.extend(self._detect_loitering(record, current_time))
            events.extend(self._detect_abnormal_speed(record, current_time))
            events.extend(self._detect_zone_entry(record, current_time))
            
        # 檢測群體行為
        events.extend(self._detect_crowding(current_time))
            
        return events
        
    def _detect_loitering(self, record: DetectionRecord, 
                         current_time: datetime) -> List[BehaviorEvent]:
        """檢測停留行為"""
        obj_id = record.object_id
        events = []
        
        if obj_id not in self.object_states:
            self.object_states[obj_id] = {
                'first_seen': current_time,
                'last_position': (record.center_x, record.center_y),
                'zone_entry_time': current_time,
                'current_zone': record.zone,
                'zone_duration': 0.0,
                'last_loitering_alert': None
            }
            return events
            
        state = self.object_states[obj_id]
        
        # 檢查是否在同一區域停留
        if state['current_zone'] == record.zone:
            state['zone_duration'] = (current_time - state['zone_entry_time']).total_seconds()
            
            # 檢查速度是否很慢（可能在停留）
            if record.speed is not None and record.speed < 10.0:
                if (state['zone_duration'] > self.loitering_threshold and 
                    (state['last_loitering_alert'] is None or 
                     (current_time - state['last_loitering_alert']).total_seconds() > 30)):
                    
                    events.append(BehaviorEvent(
                        event_id=f"loiter_{obj_id}_{int(current_time.timestamp())}",
                        timestamp=safe_strftime(current_time, '%Y-%m-%d %H:%M:%S.%f'),
                        object_id=obj_id,
                        object_type=record.object_type,
                        behavior="loitering",
                        zone=record.zone,
                        position_x=record.center_x,
                        position_y=record.center_y,
                        duration=state['zone_duration'],
                        metadata=json.dumps({"threshold": self.loitering_threshold, "speed": record.speed}),
                        source=record.source
                    ))
                    
                    state['last_loitering_alert'] = current_time
        else:
            # 進入新區域，重置計時
            state['zone_entry_time'] = current_time
            state['current_zone'] = record.zone
            state['zone_duration'] = 0.0
            
        return events
        
    def _detect_abnormal_speed(self, record: DetectionRecord, 
                             current_time: datetime) -> List[BehaviorEvent]:
        """檢測異常速度"""
        events = []
        
        if record.speed is None or record.speed < self.speed_threshold:
            return events
            
        events.append(BehaviorEvent(
            event_id=f"speed_{record.object_id}_{int(current_time.timestamp())}",
            timestamp=safe_strftime(current_time, '%Y-%m-%d %H:%M:%S.%f'),
            object_id=record.object_id,
            object_type=record.object_type,
            behavior="abnormal_speed",
            zone=record.zone,
            position_x=record.center_x,
            position_y=record.center_y,
            metadata=json.dumps({"speed": record.speed, "threshold": self.speed_threshold}),
            source=record.source
        ))
        
        return events
        
    def _detect_zone_entry(self, record: DetectionRecord, 
                          current_time: datetime) -> List[BehaviorEvent]:
        """檢測區域進入事件"""
        obj_id = record.object_id
        events = []
        
        if obj_id not in self.object_states:
            return events
            
        state = self.object_states[obj_id]
        
        # 檢查是否進入新區域
        if state.get('current_zone') != record.zone:
            events.append(BehaviorEvent(
                event_id=f"enter_{record.zone}_{obj_id}_{int(current_time.timestamp())}",
                timestamp=safe_strftime(current_time, '%Y-%m-%d %H:%M:%S.%f'),
                object_id=obj_id,
                object_type=record.object_type,
                behavior="zone_entry",
                zone=record.zone,
                position_x=record.center_x,
                position_y=record.center_y,
                metadata=json.dumps({"from_zone": state.get('current_zone', "unknown")}),
                source=record.source
            ))
            
        return events
        
    def _detect_crowding(self, current_time: datetime) -> List[BehaviorEvent]:
        """檢測擁擠情況"""
        events = []
        
        for zone, count in self.zone_occupancy.items():
            if count >= self.crowd_threshold:
                events.append(BehaviorEvent(
                    event_id=f"crowd_{zone}_{int(current_time.timestamp())}",
                    timestamp=safe_strftime(current_time, '%Y-%m-%d %H:%M:%S.%f'),
                    object_id=-1,  # 群體事件
                    object_type="crowd",
                    behavior="crowding",
                    zone=zone,
                    position_x=0,
                    position_y=0,
                    metadata=json.dumps({"count": count, "threshold": self.crowd_threshold}),
                    source="system"
                ))
                
        return events


class VideoAnalysisService:
    """主要的影片分析服務（支援動態模型載入）"""
    
    def __init__(self, model_path: str | None = None):
        # 延遲載入：首次使用或切換時才載入模型
        self.model: YOLO | None = None
        self.model_path: str | None = None
        if model_path:
            self.set_model(model_path)
        
        self.zone_manager = ZoneManager()
        self.object_tracker = ObjectTracker()
        self.behavior_analyzer = BehaviorAnalyzer()
        
        # 資料儲存
        self.detection_records = []
        self.behavior_events = []
        
        # 影片處理狀態
        self.is_processing = False
        self.current_source = None
        
        logger.info("VideoAnalysisService 初始化完成")

    def set_model(self, model_path: str):
        """設定 / 切換 YOLO 模型 (必要時才重新載入) - 使用集中解析。"""
        resolved = resolve_model_path(model_path)
        try:
            if self.model is not None and self.model_path == resolved:
                logger.debug(f"沿用已載入影片分析模型: {resolved}")
                return
            logger.info(f"載入影片分析模型: {model_path} (resolved={resolved})")
            self.model = YOLO(resolved)
            self.model_path = resolved
        except Exception as e:
            logger.error(f"載入影片分析模型失敗: {model_path} (resolved={resolved}) -> {e}")
            raise
        
    def analyze_camera(self, camera_id: int = 0, duration: int = 60, model_path: str | None = None) -> Dict[str, Any]:
        """分析攝影機輸入"""
        try:
            if model_path:
                self.set_model(model_path)
            elif self.model is None:
                # fallback 預設
                self.set_model("yolo11n.pt")
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                raise Exception(f"無法開啟攝影機 {camera_id}")
                
            # 設定攝影機參數
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.current_source = f"Camera_{camera_id}"
            self._setup_zones(1280, 720)
            
            return self._process_video_stream(cap, duration, self.current_source)
            
        except Exception as e:
            logger.error(f"攝影機分析失敗: {e}")
            raise
        finally:
            if 'cap' in locals():
                cap.release()
                
    def analyze_video_file(self, video_path: str, model_path: str | None = None) -> Dict[str, Any]:
        """分析影片檔案"""
        try:
            if model_path:
                self.set_model(model_path)
            elif self.model is None:
                self.set_model("yolo11n.pt")
            if not Path(video_path).exists():
                raise Exception(f"影片檔案不存在: {video_path}")
                
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"無法開啟影片檔案: {video_path}")
                
            # 獲取影片資訊
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            self.current_source = Path(video_path).name
            self._setup_zones(frame_width, frame_height)
            
            logger.info(f"開始分析影片: {video_path} ({total_frames} 幀, {fps} FPS)")
            
            return self._process_video_stream(cap, total_frames//fps if fps > 0 else 0, self.current_source)
            
        except Exception as e:
            logger.error(f"影片分析失敗: {e}")
            raise
        finally:
            if 'cap' in locals():
                cap.release()
                
    def _setup_zones(self, width: int, height: int):
        """設置檢測區域"""
        self.zone_manager.setup_default_zones(width, height)
        
    def _process_video_stream(self, cap, max_duration: int, source: str) -> Dict[str, Any]:
        """處理影片流"""
        self.is_processing = True
        self.detection_records.clear()
        self.behavior_events.clear()
        
        frame_count = 0
        start_time = datetime.now()
        processed_frames = 0
        
        try:
            while self.is_processing and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    logger.info("影片處理完畢")
                    break
                    
                # 檢查處理時間限制
                if max_duration > 0 and (datetime.now() - start_time).total_seconds() > max_duration:
                    logger.info("達到最大處理時間限制")
                    break
                    
                # 每隔幾幀處理一次（提高效能）
                if frame_count % 3 == 0:
                    self._process_frame(frame, frame_count, source)
                    processed_frames += 1
                    
                frame_count += 1
                
                # 每處理100幀輸出一次進度
                if processed_frames % 100 == 0:
                    logger.info(f"已處理 {processed_frames} 幀")
                    
        except Exception as e:
            logger.error(f"影片流處理錯誤: {e}")
            raise
        finally:
            self.is_processing = False
            
        # 生成分析結果
        result = self._generate_analysis_result(start_time, frame_count, processed_frames)
        
        # 儲存 CSV
        self._save_to_csv()
        
        return result
        
    def _process_frame(self, frame, frame_number: int, source: str):
        """處理單一幀"""
        try:
            # YOLO 檢測
            results = self.model.track(frame, persist=True, verbose=False)
            
            if not results or len(results) == 0:
                return
                
            # 解析檢測結果
            detections = []
            for result in results:
                if result.boxes is not None:
                    boxes = result.boxes
                    for i in range(len(boxes)):
                        detection = {
                            'bbox': boxes.xyxy[i].cpu().numpy().tolist(),
                            'confidence': float(boxes.conf[i].cpu().numpy()),
                            'class': self.model.names[int(boxes.cls[i].cpu().numpy())],
                            'track_id': int(boxes.id[i].cpu().numpy()) if boxes.id is not None else None
                        }
                        detections.append(detection)
                        
            # 更新追蹤
            detection_records = self.object_tracker.update_tracks(detections, frame_number, source)
            self.detection_records.extend(detection_records)
            
            # 分析行為
            behavior_events = self.behavior_analyzer.analyze_behavior(detection_records, self.zone_manager)
            self.behavior_events.extend(behavior_events)
            
        except Exception as e:
            logger.error(f"處理幀 {frame_number} 時發生錯誤: {e}")
            
    def _generate_analysis_result(self, start_time: datetime, total_frames: int, processed_frames: int) -> Dict[str, Any]:
        """生成分析結果摘要"""
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 統計資訊
        object_types = {}
        behavior_types = {}
        zone_activity = {}
        
        for record in self.detection_records:
            object_types[record.object_type] = object_types.get(record.object_type, 0) + 1
            if record.zone:
                zone_activity[record.zone] = zone_activity.get(record.zone, 0) + 1
                
        for event in self.behavior_events:
            behavior_types[event.behavior] = behavior_types.get(event.behavior, 0) + 1
            
        return {
            "source": self.current_source,
            "processing_time": processing_time,
            "total_frames": total_frames,
            "processed_frames": processed_frames,
            "detection_count": len(self.detection_records),
            "behavior_event_count": len(self.behavior_events),
            "object_types": object_types,
            "behavior_types": behavior_types,
            "zone_activity": zone_activity,
            "start_time": safe_strftime(start_time, '%Y-%m-%d %H:%M:%S'),
            "end_time": safe_strftime(end_time, '%Y-%m-%d %H:%M:%S')
        }
        
    def _save_to_csv(self):
        """儲存分析結果到 CSV"""
        timestamp = safe_strftime(datetime.now(), '%Y%m%d_%H%M%S')
        output_dir = Path("analysis_results")
        output_dir.mkdir(exist_ok=True)
        
        # 儲存檢測記錄
        if self.detection_records:
            detection_df = pd.DataFrame([asdict(record) for record in self.detection_records])
            detection_file = output_dir / f"detections_{timestamp}.csv"
            detection_df.to_csv(detection_file, index=False, encoding='utf-8-sig')
            logger.info(f"檢測記錄已儲存至: {detection_file}")
            
        # 儲存行為事件
        if self.behavior_events:
            behavior_df = pd.DataFrame([asdict(event) for event in self.behavior_events])
            behavior_file = output_dir / f"behaviors_{timestamp}.csv"
            behavior_df.to_csv(behavior_file, index=False, encoding='utf-8-sig')
            logger.info(f"行為事件已儲存至: {behavior_file}")
            
    def stop_processing(self):
        """停止處理"""
        self.is_processing = False
        logger.info("影片處理已停止")


# 延遲初始化的全域服務實例
_video_analysis_service = None

def get_video_analysis_service():
    """獲取影片分析服務實例（延遲初始化）"""
    global _video_analysis_service
    if _video_analysis_service is None:
        _video_analysis_service = VideoAnalysisService()
    return _video_analysis_service

# 向後相容性別名
def video_analysis_service():
    return get_video_analysis_service()
