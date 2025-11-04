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
from pathlib import Path
from typing import Iterable, TextIO

import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO

CSV_FIELDNAMES = [
    "timestamp",
    "frame",
    "tracker_id",
    "confidence",
    "object_type",
    "x_min",
    "y_min",
    "x_max",
    "y_max",
    "corner_on",
    "blur_on",
    "trace_on",
    "heatmap_on",
]


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


def resolve_labels(detections: sv.Detections) -> list[str]:
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

    labels = []
    for tracker_id, confidence in zip(tracker_ids, confidences):
        id_part = f"#{int(tracker_id)} " if tracker_id is not None else ""
        if confidence is None:
            labels.append(f"{id_part}person")
        else:
            labels.append(f"{id_part}person {confidence:.2f}")
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


def draw_hud(frame: np.ndarray, toggles: dict[str, bool]) -> None:
    status = " | ".join(
        f"{name.upper()}: {'ON' if enabled else 'OFF'}"
        for name, enabled in toggles.items()
    )
    text = (
        f"[c]Corner  [b]Blur  [t]Trace  [h]Heatmap  [r]Reset heatmap  [q]Quit\n{status}"
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


def _prepare_csv_writer(
    path: str,
    append: bool,
) -> tuple[TextIO, csv.DictWriter[str]]:
    csv_path = Path(path)
    if not csv_path.parent.exists():
        csv_path.parent.mkdir(parents=True, exist_ok=True)

    write_header = True
    if append and csv_path.exists() and csv_path.stat().st_size > 0:
        write_header = False

    mode = "a" if append else "w"
    csv_file = csv_path.open(mode, newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDNAMES)
    if write_header:
        writer.writeheader()
    return csv_file, writer


def _log_detections(
    writer: csv.DictWriter[str],
    timestamp: float,
    frame_index: int,
    detections: sv.Detections,
    toggles: dict[str, bool],
    object_types: Iterable[str] | None = None,
) -> None:
    if len(detections) == 0:
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

        writer.writerow(
            {
                "timestamp": f"{timestamp:.6f}",
                "frame": frame_index,
                "tracker_id": int(tracker_id) if tracker_id is not None else "",
                "confidence": (
                    round(float(confidence), 4) if confidence is not None else ""
                ),
                "object_type": object_type,
                "x_min": round(x_min, 2),
                "y_min": round(y_min, 2),
                "x_max": round(x_max, 2),
                "y_max": round(y_max, 2),
                "corner_on": toggles.get("corner", False),
                "blur_on": toggles.get("blur", False),
                "trace_on": toggles.get("trace", False),
                "heatmap_on": toggles.get("heatmap", False),
            }
        )


def main() -> None:
    args = parse_args()
    source = _to_camera_source(args.source)

    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open video source: {args.source}")

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

    cv2.namedWindow(args.window_name, cv2.WINDOW_NORMAL)

    csv_file: TextIO | None = None
    csv_writer: csv.DictWriter[str] | None = None
    if args.csv_path:
        csv_file, csv_writer = _prepare_csv_writer(args.csv_path, args.csv_append)
        print(f"[INFO] Logging detections to {args.csv_path}")

    frame_index = 0

    try:
        while True:
            success, frame = capture.read()
            if not success:
                print("[WARN] Failed to read frame from source; stopping.")
                break

            current_frame_index = frame_index
            frame_index += 1

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

            if toggles["heatmap"]:
                annotated = heatmap_annotator.annotate(
                    scene=annotated, detections=detections
                )

            if toggles["blur"] and len(detections):
                annotated = blur_annotator.annotate(
                    scene=annotated, detections=detections
                )

            if toggles["corner"] and len(detections):
                annotated = box_annotator.annotate(
                    scene=annotated, detections=detections
                )
                annotated = label_annotator.annotate(
                    scene=annotated,
                    detections=detections,
                    labels=resolve_labels(detections),
                )

            if toggles["trace"] and len(detections):
                annotated = trace_annotator.annotate(
                    scene=annotated, detections=detections
                )

            if args.show_hud:
                draw_hud(annotated, toggles)

            if csv_writer is not None and csv_file is not None:
                object_types = resolve_object_types(
                    detections,
                    names=getattr(result, "names", None),
                )
                _log_detections(
                    csv_writer,
                    timestamp=time.time(),
                    frame_index=current_frame_index,
                    detections=detections,
                    toggles=toggles,
                    object_types=object_types,
                )
                csv_file.flush()

            cv2.imshow(args.window_name, annotated)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            if key == ord("r"):
                heatmap_annotator.heat_mask = None
                print("[INFO] Heatmap reset.")
                continue
            if key in key_map:
                name = key_map[key]
                toggles[name] = not toggles[name]
                state = "enabled" if toggles[name] else "disabled"
                print(f"[INFO] {name} annotator {state}.")
    finally:
        capture.release()
        cv2.destroyAllWindows()
        if csv_file is not None:
            csv_file.close()


if __name__ == "__main__":
    main()
