"""
Live Person Camera Service - 後端服務版本

將 live_person_camera copy.py 的邏輯封裝為後端服務，
支援即時人體檢測、註解器切換、線交叉計數等功能。
"""

import asyncio
import base64
import csv
import queue
import threading
import time
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import cv2
import numpy as np
import supervision as sv
import torch
from supervision.detection.utils.converters import polygon_to_mask
from ultralytics import YOLO
from starlette.websockets import WebSocket
import av

from app.core.config import settings
from app.core.logger import detection_logger
from app.services.camera_stream_manager import camera_stream_manager, FrameData, StreamConsumer


@dataclass
class TrackerDwell:
    total_time: float = 0.0
    is_inside: bool = False
    last_seen: float = 0.0
    entered_at: float | None = None


@dataclass
class LineTrackerState:
    last_side: int = 0
    last_cross_time: float = 0.0
    last_seen: float = 0.0


@dataclass
class ManualLineCounter:
    start: sv.Point
    end: sv.Point
    in_count: int = 0
    out_count: int = 0


@dataclass
class LivePersonCameraConfig:
    """服務配置"""
    source: str | int = 0
    model_path: str = "yolo11n.pt"
    imgsz: int = 640
    conf_threshold: float = 0.35
    device: str | None = settings.device
    trace_length: int = 30
    heatmap_radius: int = 40
    heatmap_opacity: float = 0.5
    blur_kernel: int = 25
    csv_path: str | None = None
    csv_append: bool = False

    # 註解器開關
    corner_enabled: bool = True
    blur_enabled: bool = False
    trace_enabled: bool = False
    heatmap_enabled: bool = False
    line_enabled: bool = False
    zone_enabled: bool = False

    # 線配置（可選，如果不提供則使用預設中間垂直線）
    line_start_x: int | None = None
    line_start_y: int | None = None
    line_end_x: int | None = None
    line_end_y: int | None = None

    # 區域配置（可選，如果不提供則使用預設右上角矩形）
    zone_polygon: np.ndarray | None = None


class LivePersonCameraService:
    """即時人體檢測服務"""

    def __init__(self, config: LivePersonCameraConfig):
        self.config = config
        self.running = False
        self.consumer_id: Optional[str] = None

        # 模型和檢測器
        self.model: Optional[YOLO] = None
        self.tracker: Optional[sv.ByteTrack] = None

        # 註解器
        self.heatmap_annotator: Optional[sv.HeatMapAnnotator] = None
        self.blur_annotator: Optional[sv.BlurAnnotator] = None
        self.trace_annotator: Optional[sv.TraceAnnotator] = None
        self.box_annotator: Optional[sv.BoxCornerAnnotator] = None
        self.label_annotator: Optional[sv.LabelAnnotator] = None

        # 線和區域
        self.line_counter: Optional[ManualLineCounter] = None
        self.line_annotator: Optional[sv.LineZoneAnnotator] = None
        self.polygon_zone: Optional[sv.PolygonZone] = None
        self.polygon_zone_annotator: Optional[sv.PolygonZoneAnnotator] = None

        # 狀態追蹤
        self.line_tracker_states: Dict[int, LineTrackerState] = {}
        self.dwell_states: Dict[int, TrackerDwell] = {}

        # CSV 日誌
        self.csv_writer: Optional[csv.DictWriter] = None
        self.csv_file: Optional[Any] = None

        # 統計
        self.frame_index = 0
        self.last_frame_time = time.perf_counter()
        self.fps_value = 0.0
        self.camera_id: Optional[str] = None
        self.websocket_clients: Set[WebSocket] = set()
        self._ws_lock: Optional[asyncio.Lock] = None
        self.broadcast_queue: Optional[asyncio.Queue] = None
        self.broadcast_task: Optional[asyncio.Task] = None
        self.latest_frame_payload: Optional[Dict[str, Any]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.frame_queue: Optional["queue.Queue[FrameData]"] = None
        self.worker_thread: Optional[threading.Thread] = None
        self.worker_stop_event = threading.Event()
        self.last_broadcast_time = 0.0
        self.broadcast_interval = 1.0 / 20.0  # 20 FPS 上限
        self.latest_frame: Optional[np.ndarray] = None
        self.latest_frame_timestamp: float = 0.0
        self._latest_frame_lock = threading.Lock()
        self.webrtc_sinks: Set[asyncio.Queue] = set()
        self._webrtc_lock: Optional[asyncio.Lock] = None
        self.webrtc_pts: int = 0
        self.webrtc_time_base: Fraction = Fraction(1, 30)
        self.webrtc_peers: Set[Any] = set()
        self._peer_lock: Optional[asyncio.Lock] = None
        self.latest_video_frame: Optional[av.VideoFrame] = None
        self._inference_device: Optional[str] = None

    def _initialize_components(self, frame_width: int, frame_height: int) -> None:
        """初始化模型和註解器"""
        detection_logger.info("初始化 Live Person Camera 組件")

        # 初始化模型
        self.model = YOLO(self.config.model_path)
        self._inference_device = self._resolve_device()
        detection_logger.info(f"Live Person Camera 使用裝置: {self._inference_device}")
        self.model.to(self._inference_device)

        # 初始化 tracker
        self.tracker = sv.ByteTrack()

        # 初始化註解器
        self.heatmap_annotator = sv.HeatMapAnnotator(
            radius=self.config.heatmap_radius,
            opacity=self.config.heatmap_opacity,
        )
        self.blur_annotator = sv.BlurAnnotator(kernel_size=self.config.blur_kernel)
        self.trace_annotator = sv.TraceAnnotator(trace_length=self.config.trace_length)
        self.box_annotator = sv.BoxCornerAnnotator()
        self.label_annotator = sv.LabelAnnotator()

        # 初始化線
        line_start = sv.Point(
            x=self.config.line_start_x if self.config.line_start_x is not None else frame_width // 2,
            y=self.config.line_start_y if self.config.line_start_y is not None else 0
        )
        line_end = sv.Point(
            x=self.config.line_end_x if self.config.line_end_x is not None else frame_width // 2,
            y=self.config.line_end_y if self.config.line_end_y is not None else frame_height
        )
        self.line_counter = ManualLineCounter(start=line_start, end=line_end)
        self.line_annotator = sv.LineZoneAnnotator(text_orient_to_line=True, thickness=3)

        # 初始化區域
        if self.config.zone_polygon is not None:
            zone_polygon = self.config.zone_polygon
        else:
            # 預設右上角矩形
            zone_polygon = np.array([
                [int(frame_width * 0.6), int(frame_height * 0.2)],
                [int(frame_width * 0.9), int(frame_height * 0.2)],
                [int(frame_width * 0.9), int(frame_height * 0.8)],
                [int(frame_width * 0.6), int(frame_height * 0.8)],
            ], dtype=np.int32)

        self.polygon_zone = sv.PolygonZone(
            polygon=zone_polygon,
            triggering_anchors=(sv.Position.CENTER,),
        )
        full_resolution = (frame_width + 2, frame_height + 2)
        self.polygon_zone.frame_resolution_wh = full_resolution
        self.polygon_zone.mask = polygon_to_mask(
            polygon=zone_polygon, resolution_wh=full_resolution
        )

        zone_color = sv.ColorPalette.DEFAULT.by_idx(0)
        self.polygon_zone_annotator = sv.PolygonZoneAnnotator(
            zone=self.polygon_zone,
            color=zone_color,
            thickness=2,
            text_color=sv.Color.from_hex("#000000"),
            text_scale=0.6,
            text_thickness=1,
            opacity=0.2,
        )

        # 初始化 CSV
        if self.config.csv_path:
            self._setup_csv_logging()

    def _resolve_device(self) -> str:
        """解析最終使用的推論裝置"""
        requested = (self.config.device or settings.device or "auto").strip()
        if not requested:
            requested = "auto"

        if requested.lower() == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"

        return requested

    def _setup_csv_logging(self) -> None:
        """設置 CSV 日誌"""
        try:
            csv_path = Path(self.config.csv_path)
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            mode = 'a' if self.config.csv_append else 'w'
            self.csv_file = open(csv_path, mode, newline='', encoding='utf-8')
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=[
                "timestamp", "frame", "tracker_id", "confidence", "object_type",
                "dwell_seconds", "x_min", "y_min", "x_max", "y_max",
                "corner_on", "blur_on", "trace_on", "heatmap_on",
                "person_count", "avg_confidence", "fps",
                "line_in_total", "line_out_total",
                "zone_current_count", "zone_average_dwell", "zone_max_dwell"
            ])

            if not self.config.csv_append:
                self.csv_writer.writeheader()

            detection_logger.info(f"CSV 日誌設置完成: {csv_path}")
        except Exception as e:
            detection_logger.error(f"設置 CSV 日誌失敗: {e}")
            self.csv_file = None
            self.csv_writer = None

    def _process_frame(self, frame_data: FrameData) -> None:
        """處理單一幀"""
        try:
            if not self.running:
                return

            frame = np.ascontiguousarray(frame_data.frame, dtype=np.uint8)
            current_time = time.time()
            now_perf = time.perf_counter()

            # 計算 FPS
            if self.frame_index > 0:
                elapsed = now_perf - self.last_frame_time
                self.fps_value = 1.0 / elapsed if elapsed > 0 else 0.0
            self.last_frame_time = now_perf

            # YOLO 檢測
            result = self.model(
                frame,
                imgsz=self.config.imgsz,
                conf=self.config.conf_threshold,
                device=self._inference_device,
                verbose=False,
            )[0]

            detections = sv.Detections.from_ultralytics(result)
            detections = self._filter_person_detections(detections, result)
            detections = self.tracker.update_with_detections(detections)

            # 統計資訊
            person_count = len(detections)
            avg_confidence = 0.0
            if person_count and detections.confidence is not None:
                confidence_values = [float(conf) for conf in detections.confidence if conf is not None]
                if confidence_values:
                    avg_confidence = sum(confidence_values) / len(confidence_values)

            object_types = self._resolve_object_types(detections, getattr(result, "names", None))

            # 處理線交叉計數
            self._process_line_crossing(detections, current_time)

            # 處理區域停留時間
            zone_stats = self._process_zone_dwell(detections, current_time)

            # 應用註解器
            annotated = self._apply_annotators(frame, detections, object_types, zone_stats)
            contiguous_bgr = np.ascontiguousarray(annotated, dtype=np.uint8)

            height, width = contiguous_bgr.shape[:2]
            if width % 2 != 0:
                contiguous_bgr = contiguous_bgr[:, :-1, :]
            if height % 2 != 0:
                contiguous_bgr = contiguous_bgr[:-1, :, :]

            # CSV 日誌
            if self.csv_writer:
                self._log_to_csv(detections, object_types, zone_stats, person_count, avg_confidence, current_time)

            # 更新最新影像供前端預覽
            with self._latest_frame_lock:
                self.latest_frame = contiguous_bgr.copy()
                self.latest_frame_timestamp = current_time

            # 建立廣播訊息（使用標註後影像）
            should_broadcast = current_time - self.last_broadcast_time >= self.broadcast_interval
            if should_broadcast:
                try:
                    ok, buffer = cv2.imencode(".jpg", contiguous_bgr)
                    if ok:
                        detections_payload = self._build_detections_payload(detections, object_types)
                        payload = {
                            "type": "frame",
                            "timestamp": current_time,
                            "width": contiguous_bgr.shape[1],
                            "height": contiguous_bgr.shape[0],
                            "image": base64.b64encode(buffer).decode("ascii"),
                            "detections": detections_payload,
                        }
                        self.latest_frame_payload = payload
                        self.last_broadcast_time = current_time
                        if self._loop and self.broadcast_queue:
                            try:
                                asyncio.run_coroutine_threadsafe(self._enqueue_frame(payload), self._loop)
                            except RuntimeError as enqueue_error:
                                detection_logger.error(f"排入影像佇列失敗: {enqueue_error}")
                except Exception as encode_error:
                    detection_logger.error(f"影像編碼失敗: {encode_error}")

            try:
                video_frame = av.VideoFrame.from_ndarray(contiguous_bgr, format="bgr24")
                video_frame = video_frame.reformat(
                    width=video_frame.width,
                    height=video_frame.height,
                    format="yuv420p"
                )
                video_frame.pts = self.webrtc_pts
                video_frame.time_base = self.webrtc_time_base
                self.latest_video_frame = video_frame

                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._push_webrtc_frame(video_frame),
                        self._loop
                    )
                self.webrtc_pts += 1
            except Exception as webrtc_error:
                detection_logger.error(f"WebRTC frame 推送失敗: {webrtc_error}")

            self.frame_index += 1

        except Exception as e:
            detection_logger.error(f"處理幀失敗: {e}")

    def _filter_person_detections(self, detections: sv.Detections, result) -> sv.Detections:
        """過濾只保留人體檢測"""
        if len(detections) == 0:
            return detections

        mask = None
        names = getattr(result, "names", {})
        person_class_ids = [
            int(class_id)
            for class_id, class_name in names.items()
            if isinstance(class_name, str) and class_name.lower() == "person"
        ]

        if detections.class_id is not None and person_class_ids:
            mask = np.isin(detections.class_id, person_class_ids)

        class_name_data = detections.data.get("class_name")
        if class_name_data is not None:
            class_names = np.asarray(class_name_data).astype(str)
            name_mask = np.char.lower(class_names) == "person"
            mask = name_mask if mask is None else mask | name_mask

        if mask is None:
            return detections

        return detections[mask]

    def _resolve_object_types(self, detections: sv.Detections, names: Dict[int, str] | None = None) -> List[str]:
        """解析物件類型"""
        if len(detections) == 0:
            return []

        class_name_data = detections.data.get("class_name")
        if class_name_data is not None:
            return [str(name) for name in class_name_data]

        labels = []
        if detections.class_id is not None:
            for class_id in detections.class_id:
                label = ""
                if names is not None:
                    try:
                        label = str(names[int(class_id)])
                    except (KeyError, TypeError, ValueError):
                        label = ""
                if not label and class_id is not None:
                    try:
                        label = str(int(class_id))
                    except (TypeError, ValueError):
                        label = str(class_id)
                labels.append(label or "person")
        else:
            labels = ["person"] * len(detections)

        return [label or "person" for label in labels]

    def _point_side_against_line(self, point: Tuple[float, float], start: sv.Point, end: sv.Point) -> int:
        """計算點相對於線的位置"""
        cross = (end.x - start.x) * (point[1] - start.y) - (end.y - start.y) * (point[0] - start.x)
        if abs(cross) < 1e-6:
            return 0
        return 1 if cross > 0 else -1

    def _resolve_line_cross_direction(self, previous_side: int, new_side: int) -> str | None:
        """解析線交叉方向"""
        if previous_side > 0 and new_side < 0:
            return "in"
        if previous_side < 0 and new_side > 0:
            return "out"
        return None

    def _process_line_crossing(self, detections: sv.Detections, current_time: float) -> None:
        """處理線交叉計數"""
        if not self.config.line_enabled or not self.line_counter or detections.tracker_id is None or len(detections) == 0 or detections.xyxy is None:
            return

        for det_idx, tracker_id in enumerate(detections.tracker_id):
            if tracker_id is None:
                continue

            tracker_int = int(tracker_id)
            state = self.line_tracker_states.setdefault(tracker_int, LineTrackerState())
            state.last_seen = current_time

            bbox = detections.xyxy[det_idx]
            center_x = float((bbox[0] + bbox[2]) / 2)
            center_y = float((bbox[1] + bbox[3]) / 2)
            side = self._point_side_against_line((center_x, center_y), self.line_counter.start, self.line_counter.end)

            if side == 0:
                continue

            if state.last_side == 0:
                state.last_side = side
                continue

            if state.last_side != side:
                if current_time - state.last_cross_time > 0.3:
                    direction = self._resolve_line_cross_direction(state.last_side, side)
                    if direction == "in":
                        self.line_counter.in_count += 1
                    elif direction == "out":
                        self.line_counter.out_count += 1
                    if direction is not None:
                        state.last_cross_time = current_time
                state.last_side = side
            else:
                detection_logger.debug("PeerConnection already registered, skipping")
                detection_logger.debug("PeerConnection already registered, skipping")

                detection_logger.debug("PeerConnection already registered, skipping")


                detection_logger.debug("PeerConnection already registered, skipping")

                state.last_side = side

        # 清理過期的 tracker 狀態
        for tracker_id, tracker_state in list(self.line_tracker_states.items()):
            if current_time - tracker_state.last_seen > 5.0:
                self.line_tracker_states.pop(tracker_id, None)

    def _process_zone_dwell(self, detections: sv.Detections, current_time: float) -> Dict[str, float | int]:
        """處理區域停留時間"""
        if not self.config.zone_enabled or not self.polygon_zone:
            return {
                "current": 0,
                "average": 0.0,
                "max": 0.0,
            }

        zone_mask = self.polygon_zone.trigger(detections=detections)

        current_inside_ids = set()
        current_detection_ids = set()

        if detections.tracker_id is not None and len(detections.tracker_id):
            for detection_idx, tracker_id in enumerate(detections.tracker_id):
                if tracker_id is None:
                    continue

                tracker_int = int(tracker_id)
                current_detection_ids.add(tracker_int)
                state = self.dwell_states.setdefault(tracker_int, TrackerDwell())
                state.last_seen = current_time

                in_zone = bool(zone_mask.shape[0] > detection_idx and zone_mask[detection_idx])
                if in_zone:
                    current_inside_ids.add(tracker_int)
                    if not state.is_inside:
                        state.entered_at = current_time
                    state.is_inside = True
                else:
                    if state.is_inside and state.entered_at is not None:
                        state.total_time += current_time - state.entered_at
                        state.entered_at = None
                    state.is_inside = False

        # 處理離開區域的物件
        for tracker_id, state in list(self.dwell_states.items()):
            if tracker_id not in current_detection_ids and state.is_inside:
                if state.entered_at is not None:
                    state.total_time += current_time - state.entered_at
                    state.entered_at = None
                state.is_inside = False
            if not state.is_inside and current_time - state.last_seen > 30.0:
                del self.dwell_states[tracker_id]

        # 計算統計
        inside_durations = [
            self._current_dwell_seconds(self.dwell_states[tracker_id], current_time)
            for tracker_id in current_inside_ids
            if tracker_id in self.dwell_states
        ]

        zone_current_count = len(current_inside_ids)
        zone_average_dwell = sum(inside_durations) / len(inside_durations) if inside_durations else 0.0
        zone_max_dwell = max(inside_durations, default=0.0)

        return {
            "current": zone_current_count,
            "average": zone_average_dwell,
            "max": zone_max_dwell,
        }

    def _current_dwell_seconds(self, state: TrackerDwell, now: float) -> float:
        """計算當前停留時間"""
        if state.is_inside and state.entered_at is not None:
            return state.total_time + (now - state.entered_at)
        return state.total_time

    def _apply_annotators(self, frame: np.ndarray, detections: sv.Detections, object_types: List[str], zone_stats: Dict[str, float | int]) -> np.ndarray:
        """應用註解器"""
        annotated = frame.copy()

        # 熱力圖
        if self.config.heatmap_enabled:
            annotated = self.heatmap_annotator.annotate(scene=annotated, detections=detections)

        # 模糊
        if self.config.blur_enabled and len(detections):
            annotated = self.blur_annotator.annotate(scene=annotated, detections=detections)

        # 軌跡
        if self.config.trace_enabled and len(detections):
            annotated = self.trace_annotator.annotate(scene=annotated, detections=detections)

        # 區域註解
        if self.config.zone_enabled and self.polygon_zone_annotator:
            annotated = self.polygon_zone_annotator.annotate(scene=annotated)

        # 線註解
        if self.config.line_enabled and self.line_annotator and self.line_counter:
            annotated = self.line_annotator.annotate(frame=annotated, line_counter=self.line_counter)

        # 停留時間查詢
        dwell_lookup = {}
        if detections.tracker_id is not None and len(detections.tracker_id):
            current_time = time.time()
            for tracker_id in detections.tracker_id:
                if tracker_id is None:
                    continue
                tracker_int = int(tracker_id)
                state = self.dwell_states.get(tracker_int)
                if state is not None:
                    dwell_lookup[tracker_int] = self._current_dwell_seconds(state, current_time)

        # 邊框和標籤
        if self.config.corner_enabled and len(detections):
            annotated = self.box_annotator.annotate(scene=annotated, detections=detections)
            labels = self._resolve_labels(detections, object_types, dwell_lookup)
            annotated = self.label_annotator.annotate(scene=annotated, detections=detections, labels=labels)

        return annotated

    def _resolve_labels(self, detections: sv.Detections, object_types: List[str] | None = None, dwell_lookup: Dict[int, float] | None = None) -> List[str]:
        """解析標籤"""
        if len(detections) == 0:
            return []

        confidences = detections.confidence if detections.confidence is not None else [None] * len(detections)
        tracker_ids = detections.tracker_id if detections.tracker_id is not None else [None] * len(detections)

        object_type_list = list(object_types) if object_types is not None else ["person"] * len(detections)
        if len(object_type_list) < len(detections):
            object_type_list.extend(["person"] * (len(detections) - len(object_type_list)))

        labels = []
        for tracker_id, confidence, object_type in zip(tracker_ids, confidences, object_type_list):
            id_part = f"#{int(tracker_id)} " if tracker_id is not None else ""
            dwell_suffix = ""
            if tracker_id is not None and dwell_lookup is not None:
                dwell_value = dwell_lookup.get(int(tracker_id))
                if dwell_value is not None:
                    dwell_suffix = f" {dwell_value:.1f}s"
            if confidence is None:
                labels.append(f"{id_part}{object_type}{dwell_suffix}")
            else:
                labels.append(f"{id_part}{object_type} {confidence:.2f}{dwell_suffix}")
        return labels

    def _log_to_csv(self, detections: sv.Detections, object_types: List[str], zone_stats: Dict[str, float | int], person_count: int, avg_confidence: float, current_time: float) -> None:
        """記錄到 CSV"""
        if not self.csv_writer or not self.csv_file:
            return

        try:
            tracker_dwell_times = {
                tracker_id: self._current_dwell_seconds(state, current_time)
                for tracker_id, state in self.dwell_states.items()
            }

            # 為每個檢測記錄一行
            for i in range(len(detections)):
                tracker_id = detections.tracker_id[i] if detections.tracker_id is not None else None
                confidence = detections.confidence[i] if detections.confidence is not None else None
                bbox = detections.xyxy[i] if detections.xyxy is not None else [0, 0, 0, 0]
                object_type = object_types[i] if i < len(object_types) else "person"
                dwell_seconds = tracker_dwell_times.get(int(tracker_id), 0.0) if tracker_id is not None else 0.0

                row = {
                    "timestamp": current_time,
                    "frame": self.frame_index,
                    "tracker_id": tracker_id,
                    "confidence": confidence,
                    "object_type": object_type,
                    "dwell_seconds": dwell_seconds,
                    "x_min": bbox[0],
                    "y_min": bbox[1],
                    "x_max": bbox[2],
                    "y_max": bbox[3],
                    "corner_on": self.config.corner_enabled,
                    "blur_on": self.config.blur_enabled,
                    "trace_on": self.config.trace_enabled,
                    "heatmap_on": self.config.heatmap_enabled,
                    "person_count": person_count,
                    "avg_confidence": avg_confidence,
                    "fps": self.fps_value,
                    "line_in_total": self.line_counter.in_count if self.line_counter else 0,
                    "line_out_total": self.line_counter.out_count if self.line_counter else 0,
                    "zone_current_count": zone_stats.get("current", 0),
                    "zone_average_dwell": zone_stats.get("average", 0.0),
                    "zone_max_dwell": zone_stats.get("max", 0.0),
                }

                self.csv_writer.writerow(row)

            self.csv_file.flush()

        except Exception as e:
            detection_logger.error(f"CSV 日誌記錄失敗: {e}")

    def _build_detections_payload(self, detections: sv.Detections, object_types: List[str]) -> List[Dict[str, Any]]:
        """建立廣播用的檢測資訊"""
        payload: List[Dict[str, Any]] = []

        if detections.xyxy is None or len(detections.xyxy) == 0:
            return payload

        tracker_ids = detections.tracker_id if detections.tracker_id is not None else [None] * len(detections.xyxy)
        confidences = detections.confidence if detections.confidence is not None else [None] * len(detections.xyxy)

        for idx, bbox in enumerate(detections.xyxy):
            entry: Dict[str, Any] = {
                "bbox": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
                "label": object_types[idx] if idx < len(object_types) else "person",
            }

            confidence = confidences[idx]
            if confidence is not None:
                entry["confidence"] = float(confidence)

            tracker = tracker_ids[idx]
            if tracker is not None:
                try:
                    entry["tracker_id"] = int(tracker)
                except (ValueError, TypeError):
                    entry["tracker_id"] = tracker

            payload.append(entry)

        return payload

    async def start_service(self, camera_id: str, device_index: int = 0) -> bool:
        """啟動服務"""
        try:
            detection_logger.info(f"啟動 Live Person Camera 服務: camera_id={camera_id}, device_index={device_index}")

            # 確保攝影機流正在運行
            if not camera_stream_manager.is_stream_running(camera_id):
                detection_logger.info(f"啟動攝影機流: {camera_id}")
                success = camera_stream_manager.start_stream(camera_id, device_index)
                if not success:
                    detection_logger.error(f"攝影機流啟動失敗: {camera_id}")
                    return False

            # 等待攝影機提供第一幀
            frame_data = None
            max_wait_seconds = 5.0
            poll_interval = 0.1
            elapsed = 0.0
            while elapsed < max_wait_seconds:
                frame_data = camera_stream_manager.get_latest_frame(camera_id)
                if frame_data:
                    break
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

            if not frame_data:
                detection_logger.error(f"無法獲取初始幀 (camera_id={camera_id})，請確認攝影機是否正常輸出畫面")
                return False

            frame_height, frame_width = frame_data.frame.shape[:2]
            self._initialize_components(frame_width, frame_height)

            self._loop = asyncio.get_running_loop()
            self._ws_lock = asyncio.Lock()
            self.broadcast_queue = asyncio.Queue(maxsize=2)
            self.latest_frame_payload = None
            self.webrtc_pts = 0
            self.latest_video_frame = None
            self.webrtc_sinks = set()
            self._webrtc_lock = asyncio.Lock()
            self.webrtc_peers = set()
            self._peer_lock = asyncio.Lock()

            self.frame_queue = queue.Queue(maxsize=1)
            self.worker_stop_event.clear()
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()

            # 創建消費者
            self.consumer_id = f"live_person_camera_{camera_id}_{time.time()}"
            consumer = StreamConsumer(
                consumer_id=self.consumer_id,
                callback=self._create_frame_callback()
            )

            success = camera_stream_manager.add_consumer(camera_id, consumer)
            if not success:
                detection_logger.error(f"無法添加消費者到攝影機流 {camera_id}")
                self.consumer_id = None
                self.broadcast_queue = None
                self._ws_lock = None
                self._loop = None
                self.worker_stop_event.set()
                if self.frame_queue is not None:
                    try:
                        self.frame_queue.put_nowait(None)
                    except queue.Full:
                        pass
                if self.worker_thread and self.worker_thread.is_alive():
                    self.worker_thread.join(timeout=1.0)
                self.frame_queue = None
                self.worker_thread = None
                await self._shutdown_webrtc()
                return False

            self.camera_id = camera_id
            self.running = True
            self.broadcast_task = asyncio.create_task(self._broadcast_loop())
            detection_logger.info(f"Live Person Camera 服務啟動成功: {camera_id}")
            return True

        except Exception as e:
            detection_logger.error(f"啟動 Live Person Camera 服務失敗: {e}")
            return False

    def _create_frame_callback(self):
        """創建幀處理回調"""
        def frame_callback(frame_data: FrameData):
            try:
                if not self.running or not self.frame_queue:
                    return

                try:
                    self.frame_queue.put_nowait(frame_data)
                except queue.Full:
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                    try:
                        self.frame_queue.put_nowait(frame_data)
                    except queue.Full:
                        pass
            except Exception as e:
                detection_logger.error(f"幀處理回調失敗: {e}")
        return frame_callback

    def _worker_loop(self) -> None:
        """背景工作線程：處理幀與推論"""
        detection_logger.info("Live Person Camera 工作線程啟動")
        while not self.worker_stop_event.is_set():
            try:
                if not self.frame_queue:
                    time.sleep(0.05)
                    continue

                try:
                    frame_data = self.frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if frame_data is None:
                    break

                self._process_frame(frame_data)
            except Exception as e:
                detection_logger.error(f"背景工作線程處理幀失敗: {e}")

        detection_logger.info("Live Person Camera 工作線程結束")

    async def stop_service(self, camera_id: str) -> bool:
        """停止服務"""
        try:
            detection_logger.info(f"停止 Live Person Camera 服務: {camera_id}")

            self.running = False

            self.worker_stop_event.set()
            if self.frame_queue is not None:
                try:
                    self.frame_queue.put_nowait(None)
                except queue.Full:
                    pass
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join(timeout=1.5)
            self.worker_thread = None
            self.frame_queue = None

            await self._shutdown_broadcast()
            await self._shutdown_webrtc()

            # 移除消費者
            if self.consumer_id:
                camera_stream_manager.remove_consumer(camera_id, self.consumer_id)
                self.consumer_id = None

            # 關閉 CSV 文件
            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None
                self.csv_writer = None

            # 清理狀態
            self.line_tracker_states.clear()
            self.dwell_states.clear()
            self.camera_id = None
            with self._latest_frame_lock:
                self.latest_frame = None
                self.latest_frame_timestamp = 0.0

            detection_logger.info(f"Live Person Camera 服務已停止: {camera_id}")
            return True

        except Exception as e:
            detection_logger.error(f"停止 Live Person Camera 服務失敗: {e}")
            return False

    def get_latest_frame(self) -> Optional[Tuple[np.ndarray, float]]:
        """取得最新註解後影像"""
        with self._latest_frame_lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame.copy(), self.latest_frame_timestamp

    def get_stats(self) -> Dict[str, Any]:
        """獲取服務統計"""
        return {
            "running": self.running,
            "frame_count": self.frame_index,
            "fps": self.fps_value,
            "line_in_count": self.line_counter.in_count if self.line_counter else 0,
            "line_out_count": self.line_counter.out_count if self.line_counter else 0,
            "active_trackers": len(self.dwell_states),
            "annotators": {
                "corner": self.config.corner_enabled,
                "blur": self.config.blur_enabled,
                "trace": self.config.trace_enabled,
                "heatmap": self.config.heatmap_enabled,
                "line": self.config.line_enabled,
                "zone": self.config.zone_enabled,
            }
        }

    async def _enqueue_frame(self, payload: Dict[str, Any]) -> None:
        """排入待廣播的影像訊息"""
        if not self.broadcast_queue:
            return

        try:
            if self.broadcast_queue.full():
                try:
                    self.broadcast_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            await self.broadcast_queue.put(payload)
        except Exception as e:
            detection_logger.error(f"排入廣播隊列失敗: {e}")

    async def register_webrtc_consumer(self) -> asyncio.Queue:
        """註冊 WebRTC 影像消費者"""
        if not self._webrtc_lock:
            self._webrtc_lock = asyncio.Lock()

        queue_instance: asyncio.Queue = asyncio.Queue(maxsize=1)
        async with self._webrtc_lock:
            self.webrtc_sinks.add(queue_instance)

        if self.latest_video_frame is not None:
            frame = self.latest_video_frame
            try:
                queue_instance.put_nowait(frame)
            except asyncio.QueueFull:
                try:
                    queue_instance.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue_instance.put_nowait(frame)
                except asyncio.QueueFull:
                    pass

        return queue_instance

    async def unregister_webrtc_consumer(self, queue_instance: asyncio.Queue) -> None:
        """移除 WebRTC 消費者"""
        if not self._webrtc_lock:
            return

        async with self._webrtc_lock:
            self.webrtc_sinks.discard(queue_instance)

        try:
            queue_instance.put_nowait(None)
        except asyncio.QueueFull:
            pass

    async def register_peer_connection(self, pc: Any) -> None:
        """登記 WebRTC PeerConnection"""
        if not self._peer_lock:
            self._peer_lock = asyncio.Lock()

        async with self._peer_lock:
            if pc not in self.webrtc_peers:
                self.webrtc_peers.add(pc)
            else:
                detection_logger.debug("PeerConnection already registered, skipping")
    async def unregister_peer_connection(self, pc: Any) -> None:
        """移除 WebRTC PeerConnection"""
        if self._peer_lock:
            async with self._peer_lock:
                self.webrtc_peers.discard(pc)

        try:
            await pc.close()
        except Exception:
            pass

    async def update_annotator(self, name: str, value: bool) -> None:
        """更新註解器開關"""
        if not hasattr(self.config, name):
            detection_logger.warning(f"未知的註解器設定: {name}")
            return

        setattr(self.config, name, bool(value))

        if name == "heatmap_enabled" and not value and self.heatmap_annotator:
            try:
                self.heatmap_annotator.heat_mask = None
            except Exception:
                pass

    async def _push_webrtc_frame(self, frame: av.VideoFrame) -> None:
        """向所有 WebRTC 消費者推送影像"""
        if not self._webrtc_lock:
            return

        async with self._webrtc_lock:
            sinks = list(self.webrtc_sinks)

        if not sinks:
            return

        for sink in sinks:
            try:
                if sink.full():
                    try:
                        sink.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                # 為多個消費者建立獨立影格
                if len(sinks) > 1:
                    clone = frame.reformat(
                        width=frame.width,
                        height=frame.height,
                        format=frame.format.name
                    )
                    clone.pts = frame.pts
                    clone.time_base = frame.time_base
                    target = clone
                else:
                    target = frame

                await asyncio.wait_for(sink.put(target), timeout=0.02)
            except asyncio.TimeoutError:
                detection_logger.debug("WebRTC queue put timeout, dropping frame")
                continue
            except Exception as e:
                detection_logger.debug(f"推送 WebRTC 影像給消費者失敗: {e}")
                continue


    async def _broadcast_loop(self) -> None:
        """處理 WebSocket 廣播佇列"""
        if not self.broadcast_queue:
            return

        try:
            while True:
                payload = await self.broadcast_queue.get()
                if payload is None:
                    break
                await self._broadcast_payload(payload)
        except asyncio.CancelledError:
            detection_logger.info("廣播任務被取消")
        except Exception as e:
            detection_logger.error(f"廣播任務發生錯誤: {e}")

    async def _shutdown_webrtc(self) -> None:
        """關閉所有 WebRTC 相關資源"""
        if self._webrtc_lock:
            async with self._webrtc_lock:
                sinks = list(self.webrtc_sinks)
                self.webrtc_sinks.clear()
        else:
            sinks = []

        for sink in sinks:
            try:
                sink.put_nowait(None)
            except asyncio.QueueFull:
                try:
                    sink.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    sink.put_nowait(None)
                except Exception:
                    pass

        if self._peer_lock:
            async with self._peer_lock:
                peers = list(self.webrtc_peers)
                self.webrtc_peers.clear()
        else:
            peers = []

        for pc in peers:
            try:
                await pc.close()
            except Exception:
                pass

        self.latest_video_frame = None
        self.webrtc_pts = 0
        self.webrtc_sinks = set()
        self._webrtc_lock = None
        self.webrtc_peers = set()
        self._peer_lock = None

    async def _broadcast_payload(self, payload: Dict[str, Any]) -> None:
        """向所有 WebSocket 客戶端推送資料"""
        if not self._ws_lock:
            return

        to_remove: List[WebSocket] = []
        async with self._ws_lock:
            clients = list(self.websocket_clients)

        for websocket in clients:
            try:
                await websocket.send_json(payload)
            except Exception:
                to_remove.append(websocket)

        for websocket in to_remove:
            await self.unregister_client(websocket)

    async def register_client(self, websocket: WebSocket) -> None:
        """註冊 WebSocket 客戶端"""
        await websocket.accept()

        if not self.running:
            await websocket.send_json({"type": "error", "message": "服務尚未運行"})
            await websocket.close()
            return

        if not self._ws_lock:
            self._ws_lock = asyncio.Lock()

        async with self._ws_lock:
            self.websocket_clients.add(websocket)

        if self.latest_frame_payload:
            try:
                await websocket.send_json(self.latest_frame_payload)
            except Exception:
                await self.unregister_client(websocket)

    async def unregister_client(self, websocket: WebSocket) -> None:
        """移除 WebSocket 客戶端"""
        if not self._ws_lock:
            return

        async with self._ws_lock:
            if websocket in self.websocket_clients:
                self.websocket_clients.remove(websocket)

        try:
            await websocket.close()
        except Exception:
            pass

    async def _shutdown_broadcast(self) -> None:
        """停止廣播任務並關閉客戶端"""
        if self.broadcast_queue:
            try:
                while True:
                    self.broadcast_queue.put_nowait(None)
                    break
            except asyncio.QueueFull:
                try:
                    self.broadcast_queue.get_nowait()
                    self.broadcast_queue.put_nowait(None)
                except asyncio.QueueEmpty:
                    pass

        if self.broadcast_task:
            try:
                await self.broadcast_task
            except Exception as e:
                detection_logger.error(f"等待廣播任務結束時出錯: {e}")

        if self._ws_lock:
            async with self._ws_lock:
                clients = list(self.websocket_clients)
                self.websocket_clients.clear()
        else:
            clients = []

        for websocket in clients:
            try:
                await websocket.close()
            except Exception:
                pass

        self.broadcast_queue = None
        self.broadcast_task = None
        self.latest_frame_payload = None
        self._loop = None
        self._ws_lock = None


class LivePersonCameraManager:
    """管理多個 Live Person Camera 服務實例"""

    def __init__(self) -> None:
        self._services: Dict[str, LivePersonCameraService] = {}
        self._task_to_camera: Dict[str, str] = {}
        self._camera_to_task: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def start_service(
        self,
        task_id: str,
        camera_id: str,
        device_index: int,
        config: LivePersonCameraConfig,
    ) -> bool:
        """啟動指定任務的服務"""
        await self.stop_by_camera(camera_id)

        service = LivePersonCameraService(config)
        success = await service.start_service(camera_id, device_index)
        if not success:
            return False

        async with self._lock:
            self._services[task_id] = service
            self._task_to_camera[task_id] = camera_id
            self._camera_to_task[camera_id] = task_id
        return True

    async def stop_service(self, task_id: str) -> bool:
        """根據任務 ID 停止服務"""
        async with self._lock:
            service = self._services.pop(task_id, None)
            camera_id = self._task_to_camera.pop(task_id, None)
            if camera_id:
                self._camera_to_task.pop(camera_id, None)

        if service and camera_id:
            return await service.stop_service(camera_id)
        return False

    async def stop_by_camera(self, camera_id: str) -> bool:
        """根據攝影機 ID 停止服務"""
        async with self._lock:
            task_id = self._camera_to_task.get(camera_id)

        if not task_id:
            return False
        return await self.stop_service(task_id)

    def get_task_by_camera(self, camera_id: str) -> Optional[str]:
        """查詢攝影機目前綁定的任務"""
        return self._camera_to_task.get(camera_id)

    def get_service(self, task_id: str) -> Optional[LivePersonCameraService]:
        """取得指定任務的服務實例"""
        return self._services.get(task_id)


# 全域管理器實例
live_person_camera_manager = LivePersonCameraManager()
