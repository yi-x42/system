"""Live camera person detection with toggleable annotators.

This script connects to a webcam (or any OpenCV-compatible video source), runs a
YOLO model via Supervision to detect persons, and lets you toggle different
annotators on the fly:
- BoxCornerAnnotator: draw rounded-corner boxes around people.
- BlurAnnotator: blur the regions containing detected people.
- TraceAnnotator: render motion traces for tracked people.
- HeatMapAnnotator: accumulate a heatmap of person positions over time.

Keyboard shortcuts in the preview window:
    q -> quit
    c -> toggle corner boxes
    b -> toggle blur
    t -> toggle traces
    h -> toggle heatmap
    r -> reset heatmap accumulation

Requirements: supervision, ultralytics, opencv-python, numpy.
"""

from __future__ import annotations

import argparse
import csv
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TextIO

import cv2
import numpy as np
import supervision as sv
from supervision.detection.utils.converters import polygon_to_mask
from ultralytics import YOLO
import sys
from pathlib import Path as _Path

# Ensure repository root is on sys.path so `import app` works when running this file directly.
# This makes the script runnable as: python app/services/live_person_camera\ copy.py
repo_root = _Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

CSV_FIELDNAMES = [
    "timestamp",
    "frame",
    "tracker_id",
    "confidence",
    "object_type",
    "dwell_seconds",
    "x_min",
    "y_min",
    "x_max",
    "y_max",
    "corner_on",
    "blur_on",
    "trace_on",
    "heatmap_on",
    "person_count",
    "avg_confidence",
    "fps",
    "line_in_total",
    "line_out_total",
    "zone_current_count",
    "zone_average_dwell",
    "zone_max_dwell",
]


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

    @property
    def vector(self) -> sv.Vector:
        return _LineVector(start=self.start, end=self.end)


@dataclass
class _LineVector:
    start: sv.Point
    end: sv.Point


def _current_dwell_seconds(state: TrackerDwell, now: float) -> float:
    if state.is_inside and state.entered_at is not None:
        return state.total_time + (now - state.entered_at)
    return state.total_time


def _point_side_against_line(
    point: tuple[float, float], start: sv.Point, end: sv.Point
) -> int:
    """Return side of point relative to directed line (start -> end).

    Positive -> point lies on left side of the line direction, negative -> right side,
    zero -> on the line (within tolerance).
    """

    cross = (end.x - start.x) * (point[1] - start.y) - (end.y - start.y) * (
        point[0] - start.x
    )
    if abs(cross) < 1e-6:
        return 0
    return 1 if cross > 0 else -1


def _resolve_line_cross_direction(previous_side: int, new_side: int) -> str | None:
    """Determine in/out direction when the sign changes."""

    if previous_side > 0 and new_side < 0:
        return "in"
    if previous_side < 0 and new_side > 0:
        return "out"
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Live person detection with toggleable Supervision annotators."
    )
    parser.add_argument(
        "--source",
        type=str,
        default="0",
        help="Camera index or video stream path (default: 0).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Ultralytics model checkpoint for inference (default: yolov8n.pt).",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Inference resolution passed to the model (default: 640).",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.35,
        help="Confidence threshold for detections (default: 0.35).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device string forwarded to Ultralytics (e.g., 'cpu', 'cuda:0').",
    )
    parser.add_argument(
        "--trace-length",
        type=int,
        default=30,
        help="Number of historical positions to keep in traces (default: 30).",
    )
    parser.add_argument(
        "--heatmap-radius",
        type=int,
        default=40,
        help="Radius of points accumulated in the heatmap (default: 40).",
    )
    parser.add_argument(
        "--heatmap-opacity",
        type=float,
        default=0.5,
        help="Opacity of the heatmap overlay between 0 and 1 (default: 0.5).",
    )
    parser.add_argument(
        "--blur-kernel",
        type=int,
        default=25,
        help="Kernel size used by BlurAnnotator (default: 25).",
    )
    parser.add_argument(
        "--window-name",
        type=str,
        default="Supervision Live",
        help="Name of the OpenCV preview window.",
    )
    parser.add_argument(
        "--show-hud",
        action="store_true",
        help="Overlay toggle status text in the preview window.",
    )
    parser.add_argument(
        "--csv-path",
        type=str,
        default=None,
        help="Optional path to a CSV file for logging detections.",
    )
    parser.add_argument(
        "--csv-append",
        action="store_true",
        help="Append to the CSV file instead of overwriting it if it exists.",
    )
    return parser.parse_args()


def _to_camera_source(value: str) -> int | str:
    if value.isdigit():
        return int(value)
    if cv2.haveImageReader(value):
        return value
    return value


def filter_person_detections(
    detections: sv.Detections, result
) -> sv.Detections:
    if len(detections) == 0:
        return detections

    mask: np.ndarray | None = None
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


def resolve_labels(
    detections: sv.Detections,
    object_types: Iterable[str] | None = None,
    dwell_lookup: dict[int, float] | None = None,
) -> list[str]:
    if len(detections) == 0:
        return []

    confidences: Iterable[float | None]
    if detections.confidence is None:
        confidences = [None] * len(detections)
    else:
        confidences = detections.confidence

    tracker_ids = (
        detections.tracker_id
        if detections.tracker_id is not None
        else [None] * len(detections)
    )

    object_type_list = (
        list(object_types) if object_types is not None else ["person"] * len(detections)
    )
    if len(object_type_list) < len(detections):
        object_type_list.extend(["person"] * (len(detections) - len(object_type_list)))

    labels = []
    for tracker_id, confidence, object_type in zip(
        tracker_ids, confidences, object_type_list
    ):
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


def resolve_object_types(
    detections: sv.Detections,
    names: dict[int, str] | None = None,
    default: str = "person",
) -> list[str]:
    if len(detections) == 0:
        return []

    class_name_data = detections.data.get("class_name")
    if class_name_data is not None:
        return [str(name) for name in class_name_data]

    labels: list[str] = []
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
            labels.append(label or default)
    else:
        labels = [default] * len(detections)

    return [label or default for label in labels]


def draw_hud(
    frame: np.ndarray,
    toggles: dict[str, bool],
    line_counts: tuple[int, int],
    zone_stats: dict[str, float | int],
    person_count: int,
    avg_confidence: float,
    fps: float,
) -> None:
    status = " | ".join(
        f"{name.upper()}: {'ON' if enabled else 'OFF'}"
        for name, enabled in toggles.items()
    )
    text = (
        f"[c]Corner  [b]Blur  [t]Trace  [h]Heatmap  [l]Set line  [z]Set zone\n"
        f"[r]Reset heatmap  [q]Quit\n"
        f"{status}\n"
        f"LINE  IN: {line_counts[0]}  OUT: {line_counts[1]}\n"
        f"ZONE  Count: {zone_stats.get('current', 0)}  Avg: {zone_stats.get('average', 0.0):.1f}s  "
        f"Max: {zone_stats.get('max', 0.0):.1f}s\n"
        f"PERSONS: {person_count}  AVG CONF: {avg_confidence:.2f}  FPS: {fps:.1f}"
    )
    y0 = 24
    for i, line in enumerate(text.split("\n")):
        cv2.putText(
            frame,
            line,
            (10, y0 + i * 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )


def _configure_line(frame: np.ndarray) -> tuple[sv.Point, sv.Point] | None:
    window_name = "Configure Line"
    points: list[tuple[int, int]] = []

    def on_mouse(event: int, x: int, y: int, flags: int, param: object) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) < 2:
                points.append((x, y))
            else:
                points[-1] = (x, y)

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, on_mouse)

    try:
        while True:
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                points = []
                break

            preview = frame.copy()
            cv2.putText(
                preview,
                "Left click: set points | C: clear | Enter: confirm | Esc: cancel",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            for idx, (px, py) in enumerate(points):
                cv2.circle(preview, (px, py), 6, (0, 255, 0), -1, cv2.LINE_AA)
                cv2.putText(
                    preview,
                    f"P{idx+1}",
                    (px + 8, py - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                    cv2.LINE_AA,
                )

            if len(points) == 2:
                cv2.line(preview, points[0], points[1], (0, 255, 0), 2, cv2.LINE_AA)

            cv2.imshow(window_name, preview)
            key = cv2.waitKey(16) & 0xFF

            if key in (27, ord("q")):
                points = []
                break
            if key == ord("c"):
                points.clear()
            if key in (13, ord("\r"), ord("\n")) and len(points) == 2:
                return (sv.Point(x=points[0][0], y=points[0][1]), sv.Point(x=points[1][0], y=points[1][1]))
    finally:
        cv2.setMouseCallback(window_name, lambda *args: None)
        cv2.destroyWindow(window_name)

    return None


def _configure_zone(frame: np.ndarray) -> np.ndarray | None:
    window_name = "Configure Zone"
    points: list[tuple[int, int]] = []

    def on_mouse(event: int, x: int, y: int, flags: int, param: object) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
        elif event == cv2.EVENT_RBUTTONDOWN and points:
            points.pop()

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, on_mouse)

    try:
        while True:
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                points = []
                break

            preview = frame.copy()
            message = "Left click: add vertex | Right click: undo | C: clear | Enter: confirm | Esc: cancel"
            cv2.putText(
                preview,
                message,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            if len(points) > 0:
                cv2.polylines(
                    preview,
                    [np.array(points, dtype=np.int32)],
                    False,
                    (255, 200, 0),
                    2,
                    cv2.LINE_AA,
                )
            if len(points) >= 3:
                cv2.polylines(
                    preview,
                    [np.array(points, dtype=np.int32)],
                    True,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

            for idx, (px, py) in enumerate(points):
                cv2.circle(preview, (px, py), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.putText(
                    preview,
                    str(idx + 1),
                    (px + 8, py - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

            cv2.imshow(window_name, preview)
            key = cv2.waitKey(16) & 0xFF

            if key in (27, ord("q")):
                points = []
                break
            if key == ord("c"):
                points.clear()
            if key in (13, ord("\r"), ord("\n")) and len(points) >= 3:
                return np.array(points, dtype=np.int32)
    finally:
        cv2.setMouseCallback(window_name, lambda *args: None)
        cv2.destroyWindow(window_name)

    return None


def _prepare_csv_writer(
    path: str,
    append: bool,
) -> tuple[Path, TextIO, csv.DictWriter[str]]:
    csv_path = Path(path)
    if not csv_path.parent.exists():
        csv_path.parent.mkdir(parents=True, exist_ok=True)

    write_header = True
    if append and csv_path.exists() and csv_path.stat().st_size > 0:
        write_header = False

    mode = "a" if append else "w"
    try:
        csv_file = csv_path.open(mode, newline="", encoding="utf-8")
    except PermissionError:
        timestamp_suffix = time.strftime("%Y%m%d-%H%M%S")
        fallback_name = f"{csv_path.stem}_{timestamp_suffix}{csv_path.suffix}"
        csv_path = csv_path.with_name(fallback_name)
        csv_file = csv_path.open(mode, newline="", encoding="utf-8")
        write_header = True
        print(
            f"[WARN] Could not access requested CSV file. Logging to fallback: {csv_path}"
        )
    writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDNAMES)
    if write_header:
        writer.writeheader()
    return csv_path, csv_file, writer


def _log_detections(
    writer: csv.DictWriter[str],
    timestamp: float,
    frame_index: int,
    detections: sv.Detections,
    toggles: dict[str, bool],
    object_types: Iterable[str] | None = None,
    dwell_times: dict[int, float] | None = None,
    line_counts: tuple[int, int] | None = None,
    zone_stats: dict[str, float | int] | None = None,
    person_count: int = 0,
    avg_confidence: float = 0.0,
    fps: float = 0.0,
) -> None:
    line_in, line_out = line_counts if line_counts is not None else (0, 0)
    zone_current = int(zone_stats.get("current", 0)) if zone_stats else 0
    zone_average = float(zone_stats.get("average", 0.0)) if zone_stats else 0.0
    zone_max = float(zone_stats.get("max", 0.0)) if zone_stats else 0.0

    if len(detections) == 0:
        writer.writerow(
            {
                "timestamp": f"{timestamp:.6f}",
                "frame": frame_index,
                "tracker_id": "",
                "confidence": "",
                "object_type": "",
                "dwell_seconds": "",
                "x_min": "",
                "y_min": "",
                "x_max": "",
                "y_max": "",
                "corner_on": toggles.get("corner", False),
                "blur_on": toggles.get("blur", False),
                "trace_on": toggles.get("trace", False),
                "heatmap_on": toggles.get("heatmap", False),
                "person_count": person_count,
                "avg_confidence": round(avg_confidence, 4),
                "fps": round(fps, 2),
                "line_in_total": line_in,
                "line_out_total": line_out,
                "zone_current_count": zone_current,
                "zone_average_dwell": round(zone_average, 2),
                "zone_max_dwell": round(zone_max, 2),
            }
        )
        return

    xyxy = detections.xyxy
    confidences: Iterable[float | None]
    if detections.confidence is None:
        confidences = [None] * len(detections)
    else:
        confidences = detections.confidence

    tracker_ids = (
        detections.tracker_id
        if detections.tracker_id is not None
        else [None] * len(detections)
    )

    object_types_list = (
        list(object_types) if object_types is not None else ["person"] * len(detections)
    )

    if len(object_types_list) < len(detections):
        object_types_list.extend(["person"] * (len(detections) - len(object_types_list)))

    for i in range(len(detections)):
        x_min, y_min, x_max, y_max = map(float, xyxy[i])
        tracker_id = tracker_ids[i]
        confidence = confidences[i]
        object_type = object_types_list[i] if i < len(object_types_list) else "person"
        tracker_int = int(tracker_id) if tracker_id is not None else None
        dwell_value = 0.0
        if dwell_times is not None and tracker_int is not None:
            dwell_value = float(dwell_times.get(tracker_int, 0.0))

        writer.writerow(
            {
                "timestamp": f"{timestamp:.6f}",
                "frame": frame_index,
                "tracker_id": int(tracker_id) if tracker_id is not None else "",
                "confidence": (
                    round(float(confidence), 4) if confidence is not None else ""
                ),
                "object_type": object_type,
                "dwell_seconds": round(dwell_value, 2) if dwell_value else 0,
                "x_min": round(x_min, 2),
                "y_min": round(y_min, 2),
                "x_max": round(x_max, 2),
                "y_max": round(y_max, 2),
                "corner_on": toggles.get("corner", False),
                "blur_on": toggles.get("blur", False),
                "trace_on": toggles.get("trace", False),
                "heatmap_on": toggles.get("heatmap", False),
                "person_count": person_count,
                "avg_confidence": round(avg_confidence, 4),
                "fps": round(fps, 2),
                "line_in_total": line_in,
                "line_out_total": line_out,
                "zone_current_count": zone_current,
                "zone_average_dwell": round(zone_average, 2),
                "zone_max_dwell": round(zone_max, 2),
            }
        )


def main() -> None:
    args = parse_args()
    source = _to_camera_source(args.source)

    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open video source: {args.source}")

    success, frame = capture.read()
    if not success:
        raise RuntimeError("Unable to read initial frame from source")

    model = YOLO(args.model)
    tracker = sv.ByteTrack()

    heatmap_annotator = sv.HeatMapAnnotator(
        radius=args.heatmap_radius,
        opacity=args.heatmap_opacity,
    )
    blur_annotator = sv.BlurAnnotator(kernel_size=args.blur_kernel)
    trace_annotator = sv.TraceAnnotator(trace_length=args.trace_length)
    box_annotator = sv.BoxCornerAnnotator()
    label_annotator = sv.LabelAnnotator()

    frame_height, frame_width = frame.shape[:2]
    line_start = sv.Point(x=frame_width // 2, y=0)
    line_end = sv.Point(x=frame_width // 2, y=frame_height)
    line_counter = ManualLineCounter(start=line_start, end=line_end)
    line_annotator = sv.LineZoneAnnotator(text_orient_to_line=True, thickness=3)

    zone_polygon = np.array(
        [
            [int(frame_width * 0.6), int(frame_height * 0.2)],
            [int(frame_width * 0.9), int(frame_height * 0.2)],
            [int(frame_width * 0.9), int(frame_height * 0.8)],
            [int(frame_width * 0.6), int(frame_height * 0.8)],
        ],
        dtype=np.int32,
    )
    polygon_zone = sv.PolygonZone(
        polygon=zone_polygon,
        triggering_anchors=(sv.Position.CENTER,),
    )
    full_resolution = (frame_width + 2, frame_height + 2)
    polygon_zone.frame_resolution_wh = full_resolution
    polygon_zone.mask = polygon_to_mask(
        polygon=zone_polygon, resolution_wh=full_resolution
    )
    zone_color = sv.ColorPalette.DEFAULT.by_idx(0)
    polygon_zone_annotator = sv.PolygonZoneAnnotator(
        zone=polygon_zone,
        color=zone_color,
        thickness=2,
        text_color=sv.Color.from_hex("#000000"),
        text_scale=0.6,
        text_thickness=1,
        opacity=0.2,
    )

    toggles = {
        "corner": True,
        "blur": False,
        "trace": False,
        "heatmap": False,
    }

    key_map = {
        ord("c"): "corner",
        ord("b"): "blur",
        ord("t"): "trace",
        ord("h"): "heatmap",
    }

    line_tracker_states: dict[int, LineTrackerState] = {}

    cv2.namedWindow(args.window_name, cv2.WINDOW_NORMAL)

    csv_file_path: Path | None = None
    csv_file: TextIO | None = None
    csv_writer: csv.DictWriter[str] | None = None
    if args.csv_path:
        csv_file_path, csv_file, csv_writer = _prepare_csv_writer(
            args.csv_path, args.csv_append
        )
        if csv_file_path is not None:
            print(f"[INFO] Logging detections to {csv_file_path}")

    frame_index = 0
    dwell_states: dict[int, TrackerDwell] = {}
    last_frame_time = time.perf_counter()
    fps_value = 0.0

    try:
        while True:
            current_frame_index = frame_index
            frame_index += 1

            current_time = time.time()
            now_perf = time.perf_counter()
            if frame_index > 1:
                elapsed = now_perf - last_frame_time
                fps_value = 1.0 / elapsed if elapsed > 0 else 0.0
            else:
                fps_value = 0.0
            last_frame_time = now_perf

            result = model(
                frame,
                imgsz=args.imgsz,
                conf=args.conf,
                device=args.device,
                verbose=False,
            )[0]
            detections = sv.Detections.from_ultralytics(result)
            detections = filter_person_detections(detections, result)
            detections = tracker.update_with_detections(detections)

            annotated = frame.copy()

            object_types = resolve_object_types(
                detections,
                names=getattr(result, "names", None),
            )

            person_count = len(detections)
            avg_confidence = 0.0
            if person_count and detections.confidence is not None:
                confidence_values = [
                    float(conf)
                    for conf in detections.confidence
                    if conf is not None
                ]
                if confidence_values:
                    avg_confidence = sum(confidence_values) / len(confidence_values)

            if toggles["heatmap"]:
                annotated = heatmap_annotator.annotate(
                    scene=annotated, detections=detections
                )

            if toggles["blur"] and len(detections):
                annotated = blur_annotator.annotate(
                    scene=annotated, detections=detections
                )

            if toggles["trace"] and len(detections):
                annotated = trace_annotator.annotate(
                    scene=annotated, detections=detections
                )

            zone_mask = polygon_zone.trigger(detections=detections)

            if (
                detections.tracker_id is not None
                and len(detections)
                and detections.xyxy is not None
            ):
                for det_idx, tracker_id in enumerate(detections.tracker_id):
                    if tracker_id is None:
                        continue
                    tracker_int = int(tracker_id)
                    state = line_tracker_states.setdefault(
                        tracker_int, LineTrackerState()
                    )
                    state.last_seen = current_time

                    bbox = detections.xyxy[det_idx]
                    center_x = float((bbox[0] + bbox[2]) / 2)
                    center_y = float((bbox[1] + bbox[3]) / 2)
                    side = _point_side_against_line(
                        (center_x, center_y),
                        line_counter.start,
                        line_counter.end,
                    )

                    if side == 0:
                        continue

                    if state.last_side == 0:
                        state.last_side = side
                        continue

                    if state.last_side != side:
                        if current_time - state.last_cross_time > 0.3:
                            direction = _resolve_line_cross_direction(
                                state.last_side, side
                            )
                            if direction == "in":
                                line_counter.in_count += 1
                            elif direction == "out":
                                line_counter.out_count += 1
                            if direction is not None:
                                state.last_cross_time = current_time
                        state.last_side = side
                    else:
                        state.last_side = side

            for tracker_id, tracker_state in list(line_tracker_states.items()):
                if current_time - tracker_state.last_seen > 5.0:
                    line_tracker_states.pop(tracker_id, None)

            current_inside_ids: set[int] = set()
            current_detection_ids: set[int] = set()
            if detections.tracker_id is not None and len(detections.tracker_id):
                for detection_idx, tracker_id in enumerate(detections.tracker_id):
                    if tracker_id is None:
                        continue
                    tracker_int = int(tracker_id)
                    current_detection_ids.add(tracker_int)
                    state = dwell_states.setdefault(tracker_int, TrackerDwell())
                    state.last_seen = current_time

                    in_zone = bool(
                        zone_mask.shape[0] > detection_idx and zone_mask[detection_idx]
                    )
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

            for tracker_id, state in list(dwell_states.items()):
                if tracker_id not in current_detection_ids and state.is_inside:
                    if state.entered_at is not None:
                        state.total_time += current_time - state.entered_at
                        state.entered_at = None
                    state.is_inside = False
                if (not state.is_inside) and (current_time - state.last_seen > 30.0):
                    del dwell_states[tracker_id]

            inside_durations = [
                _current_dwell_seconds(dwell_states[tracker_id], current_time)
                for tracker_id in current_inside_ids
                if tracker_id in dwell_states
            ]
            zone_current_count = len(current_inside_ids)
            zone_average_dwell = (
                sum(inside_durations) / len(inside_durations)
                if inside_durations
                else 0.0
            )
            zone_max_dwell = max(inside_durations, default=0.0)

            annotated = polygon_zone_annotator.annotate(scene=annotated)
            annotated = line_annotator.annotate(
                frame=annotated, line_counter=line_counter
            )

            dwell_lookup: dict[int, float] = {}
            if (
                detections.tracker_id is not None
                and len(detections.tracker_id)
            ):
                for tracker_id in detections.tracker_id:
                    if tracker_id is None:
                        continue
                    tracker_int = int(tracker_id)
                    state = dwell_states.get(tracker_int)
                    if state is not None:
                        dwell_lookup[tracker_int] = _current_dwell_seconds(
                            state, current_time
                        )

            if toggles["corner"] and len(detections):
                annotated = box_annotator.annotate(
                    scene=annotated, detections=detections
                )
                annotated = label_annotator.annotate(
                    scene=annotated,
                    detections=detections,
                    labels=resolve_labels(
                        detections,
                        object_types=object_types,
                        dwell_lookup=dwell_lookup,
                    ),
                )

            if args.show_hud:
                draw_hud(
                    annotated,
                    toggles,
                    (line_counter.in_count, line_counter.out_count),
                    # ... but replaced later ??? need to ensure double patch
                    {
                        "current": zone_current_count,
                        "average": zone_average_dwell,
                        "max": zone_max_dwell,
                    },
                    person_count,
                    avg_confidence,
                    fps_value,
                )

            if csv_writer is not None and csv_file is not None:
                tracker_dwell_times = {
                    tracker_id: _current_dwell_seconds(state, current_time)
                    for tracker_id, state in dwell_states.items()
                }
                _log_detections(
                    csv_writer,
                    timestamp=current_time,
                    frame_index=current_frame_index,
                    detections=detections,
                    toggles=toggles,
                    object_types=object_types,
                    dwell_times=tracker_dwell_times,
                    line_counts=(line_counter.in_count, line_counter.out_count),
                    zone_stats={
                        "current": zone_current_count,
                        "average": zone_average_dwell,
                        "max": zone_max_dwell,
                    },
                    person_count=person_count,
                    avg_confidence=avg_confidence,
                    fps=fps_value,
                )
                csv_file.flush()

            cv2.imshow(args.window_name, annotated)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            if key == ord("r"):
                heatmap_annotator.heat_mask = None
                print("[INFO] Heatmap reset.")
            if key in key_map:
                name = key_map[key]
                toggles[name] = not toggles[name]
                state = "enabled" if toggles[name] else "disabled"
                print(f"[INFO] {name} annotator {state}.")

            if key == ord("l"):
                new_line = _configure_line(frame)
                if new_line is not None:
                    line_start_point, line_end_point = new_line
                    line_start = line_start_point
                    line_end = line_end_point
                    line_counter.start = line_start_point
                    line_counter.end = line_end_point
                    line_counter.in_count = 0
                    line_counter.out_count = 0
                    line_tracker_states.clear()
                    line_annotator = sv.LineZoneAnnotator(
                        text_orient_to_line=True,
                        thickness=3,
                    )
                    print(
                        f"[INFO] Line updated: start={line_start_point.as_xy_int_tuple()} end={line_end_point.as_xy_int_tuple()}"
                    )

            if key == ord("z"):
                new_polygon = _configure_zone(frame)
                if new_polygon is not None and len(new_polygon) >= 3:
                    frame_height, frame_width = frame.shape[:2]
                    polygon_zone = sv.PolygonZone(
                        polygon=new_polygon,
                        triggering_anchors=(sv.Position.CENTER,),
                    )
                    full_resolution = (frame_width + 2, frame_height + 2)
                    polygon_zone.frame_resolution_wh = full_resolution
                    polygon_zone.mask = polygon_to_mask(
                        polygon=new_polygon, resolution_wh=full_resolution
                    )
                    polygon_zone_annotator = sv.PolygonZoneAnnotator(
                        zone=polygon_zone,
                        color=zone_color,
                        thickness=2,
                        text_color=sv.Color.from_hex("#000000"),
                        text_scale=0.6,
                        text_thickness=1,
                        opacity=0.2,
                    )
                    dwell_states.clear()
                    print(
                        f"[INFO] Zone updated with {len(new_polygon)} vertices; dwell timers reset."
                    )

            success, frame = capture.read()
            if not success:
                print("[WARN] Failed to read frame from source; stopping.")
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()
        if csv_file is not None:
            csv_file.close()


if __name__ == "__main__":
    main()
