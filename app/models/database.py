# 資料庫 ORM 模型 (SQLAlchemy)
# 與 deployment/db/init.sql 保持同步

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


def _safe_iso(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    source_width = Column(Integer)
    source_height = Column(Integer)
    source_fps = Column(Float)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    task_name = Column(String(200))
    camera_id = Column(String(100))
    camera_name = Column(String(200))
    camera_type = Column(String(50))
    device_index = Column(Integer)
    model_path = Column(String(255))
    model_id = Column(String(100))
    confidence_threshold = Column(Float, default=0.5)
    iou_threshold = Column(Float, default=0.4)

    data_source = relationship("DataSource", back_populates="analysis_tasks")
    detection_results = relationship(
        "DetectionResult", back_populates="task", cascade="all, delete-orphan"
    )
    line_events = relationship(
        "LineCrossingEvent", back_populates="task", cascade="all, delete-orphan"
    )
    zone_events = relationship(
        "ZoneDwellEvent", back_populates="task", cascade="all, delete-orphan"
    )
    speed_events = relationship(
        "SpeedEvent", back_populates="task", cascade="all, delete-orphan"
    )
    statistics = relationship(
        "TaskStatistics",
        uselist=False,
        back_populates="task",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "task_type": self.task_type,
            "status": self.status,
            "source_id": self.source_id,
            "source_width": self.source_width,
            "source_height": self.source_height,
            "source_fps": self.source_fps,
            "start_time": _safe_iso(self.start_time),
            "end_time": _safe_iso(self.end_time),
            "created_at": _safe_iso(self.created_at),
            "task_name": self.task_name,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "camera_type": self.camera_type,
            "device_index": self.device_index,
            "model_path": self.model_path,
            "model_id": self.model_id,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
        }


class DetectionResult(Base):
    __tablename__ = "detection_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(
        Integer, ForeignKey("analysis_tasks.id", ondelete="CASCADE"), nullable=False
    )
    tracker_id = Column(Integer)
    object_speed = Column(Float)
    zones = Column(JSON)
    frame_number = Column(Integer)
    frame_timestamp = Column(DateTime, default=datetime.utcnow)
    object_type = Column(String(50))
    confidence = Column(Float)
    bbox_x1 = Column(Float)
    bbox_y1 = Column(Float)
    bbox_x2 = Column(Float)
    bbox_y2 = Column(Float)
    center_x = Column(Float)
    center_y = Column(Float)

    task = relationship("AnalysisTask", back_populates="detection_results")

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "tracker_id": self.tracker_id,
            "object_speed": self.object_speed,
            "zones": self.zones,
            "frame_number": self.frame_number,
            "frame_timestamp": _safe_iso(self.frame_timestamp),
            "object_type": self.object_type,
            "confidence": self.confidence,
            "bbox_x1": self.bbox_x1,
            "bbox_y1": self.bbox_y1,
            "bbox_x2": self.bbox_x2,
            "bbox_y2": self.bbox_y2,
            "center_x": self.center_x,
            "center_y": self.center_y,
        }


class LineCrossingEvent(Base):
    __tablename__ = "line_crossing_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    is_enabled = Column(Boolean, default=True)
    task_id = Column(
        Integer, ForeignKey("analysis_tasks.id", ondelete="CASCADE"), nullable=False
    )
    tracker_id = Column(Integer)
    line_id = Column(String(50), nullable=False)
    direction = Column(String(20))
    frame_number = Column(Integer)
    frame_timestamp = Column(DateTime, default=datetime.utcnow)
    extra = Column(JSON)

    task = relationship("AnalysisTask", back_populates="line_events")


class ZoneDwellEvent(Base):
    __tablename__ = "zone_dwell_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    is_enabled = Column(Boolean, default=True)
    task_id = Column(
        Integer, ForeignKey("analysis_tasks.id", ondelete="CASCADE"), nullable=False
    )
    tracker_id = Column(Integer)
    zone_id = Column(String(50), nullable=False)
    entered_at = Column(DateTime)
    exited_at = Column(DateTime)
    dwell_seconds = Column(Float)
    frame_number = Column(Integer)
    event_timestamp = Column(DateTime, default=datetime.utcnow)
    extra = Column(JSON)

    task = relationship("AnalysisTask", back_populates="zone_events")


class SpeedEvent(Base):
    __tablename__ = "speed_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    is_enabled = Column(Boolean, default=True)
    task_id = Column(
        Integer, ForeignKey("analysis_tasks.id", ondelete="CASCADE"), nullable=False
    )
    tracker_id = Column(Integer)
    speed_avg = Column(Float)
    speed_max = Column(Float)
    threshold = Column(Float)
    frame_number = Column(Integer)
    event_timestamp = Column(DateTime, default=datetime.utcnow)
    extra = Column(JSON)

    task = relationship("AnalysisTask", back_populates="speed_events")


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    config = Column(JSON)
    status = Column(String(20), nullable=False, default="active")
    last_check = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    analysis_tasks = relationship("AnalysisTask", back_populates="data_source")

    def to_dict(self):
        return {
            "id": self.id,
            "source_type": self.source_type,
            "name": self.name,
            "config": self.config,
            "status": self.status,
            "last_check": _safe_iso(self.last_check),
            "created_at": _safe_iso(self.created_at),
        }


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TaskStatistics(Base):
    __tablename__ = "task_statistics"

    task_id = Column(
        Integer, ForeignKey("analysis_tasks.id", ondelete="CASCADE"), primary_key=True
    )
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    fps = Column(Float)
    person_count = Column(Integer)
    avg_confidence = Column(Float)
    line_stats = Column(JSON)
    zone_stats = Column(JSON)
    speed_stats = Column(JSON)
    extra = Column(JSON)

    task = relationship("AnalysisTask", back_populates="statistics")


# 索引
Index("idx_analysis_tasks_status", AnalysisTask.status)
Index("idx_analysis_tasks_type", AnalysisTask.task_type)
Index("idx_analysis_tasks_created", AnalysisTask.created_at)
Index("idx_analysis_tasks_source", AnalysisTask.source_id)

Index("idx_detection_results_task", DetectionResult.task_id)
Index("idx_detection_results_tracker", DetectionResult.tracker_id)
Index("idx_detection_results_timestamp", DetectionResult.frame_timestamp)

Index("idx_line_events_task_line", LineCrossingEvent.task_id, LineCrossingEvent.line_id)
Index("idx_line_events_tracker", LineCrossingEvent.tracker_id)

Index("idx_zone_events_task_zone", ZoneDwellEvent.task_id, ZoneDwellEvent.zone_id)
Index("idx_zone_events_tracker", ZoneDwellEvent.tracker_id)

Index("idx_speed_events_task", SpeedEvent.task_id)
Index("idx_speed_events_tracker", SpeedEvent.tracker_id)

Index("idx_data_sources_status", DataSource.status)
Index("idx_data_sources_type", DataSource.source_type)

Index("idx_system_config_key", SystemConfig.config_key)

Index("idx_task_statistics_updated", TaskStatistics.updated_at)
