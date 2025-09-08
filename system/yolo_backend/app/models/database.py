# 新的資料庫模型定義
# 根據重新設計的資料庫架構

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class AnalysisTask(Base):
    """分析任務表 - 統一管理即時攝影機和影片檔案分析"""
    __tablename__ = "analysis_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(20), nullable=False)  # 'realtime_camera' | 'video_file'
    status = Column(String(20), nullable=False, default='pending')  # 'pending' | 'running' | 'completed' | 'failed'
    source_info = Column(JSON)  # 攝影機配置或影片檔案路徑（不含解析度）
    source_width = Column(Integer)  # 來源影像寬度
    source_height = Column(Integer)  # 來源影像高度
    source_fps = Column(Float)  # 來源影片幀率
    start_time = Column(DateTime)  # 任務開始時間
    end_time = Column(DateTime)    # 任務結束時間
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 關聯關係
    detection_results = relationship("DetectionResult", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnalysisTask(id={self.id}, type={self.task_type}, status={self.status})>"
    
    def to_dict(self):
        # 安全處理日期時間字段
        def safe_isoformat(dt_value):
            if dt_value is None:
                return None
            if isinstance(dt_value, str):
                return dt_value  # 如果已經是字串，直接返回
            if hasattr(dt_value, 'isoformat'):
                return dt_value.isoformat()
            return str(dt_value)  # 最後的備用方案
        
        return {
            'id': self.id,
            'task_type': self.task_type,
            'status': self.status,
            'source_info': self.source_info,
            'source_width': self.source_width,
            'source_height': self.source_height,
            'source_fps': self.source_fps,
            'start_time': safe_isoformat(self.start_time),
            'end_time': safe_isoformat(self.end_time),
            'created_at': safe_isoformat(self.created_at)
        }

class DetectionResult(Base):
    """檢測結果表 - 儲存物件檢測的原始結果"""
    __tablename__ = "detection_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('analysis_tasks.id', ondelete='CASCADE'), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    object_type = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    center_x = Column(Float, nullable=False)
    center_y = Column(Float, nullable=False)
    
    # 關聯關係
    task = relationship("AnalysisTask", back_populates="detection_results")
    
    def __repr__(self):
        return f"<DetectionResult(id={self.id}, task_id={self.task_id}, object_type={self.object_type})>"
    
    def to_dict(self):
        # 安全處理日期時間字段
        def safe_isoformat(dt_value):
            if dt_value is None:
                return None
            if isinstance(dt_value, str):
                return dt_value  # 如果已經是字串，直接返回
            if hasattr(dt_value, 'isoformat'):
                return dt_value.isoformat()
            return str(dt_value)  # 最後的備用方案
        
        return {
            'id': self.id,
            'task_id': self.task_id,
            'frame_number': self.frame_number,
            'timestamp': safe_isoformat(self.timestamp),
            'object_type': self.object_type,
            'confidence': self.confidence,
            'bbox_x1': self.bbox_x1,
            'bbox_y1': self.bbox_y1,
            'bbox_x2': self.bbox_x2,
            'bbox_y2': self.bbox_y2,
            'center_x': self.center_x,
            'center_y': self.center_y
        }

class DataSource(Base):
    """資料來源表 - 管理攝影機和影片檔案資訊"""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(20), nullable=False)  # 'camera' | 'video_file'
    name = Column(String(100), nullable=False)
    config = Column(JSON)  # 配置資訊（IP、檔案路徑等）
    status = Column(String(20), nullable=False, default='active')  # 'active' | 'inactive' | 'error'
    last_check = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<DataSource(id={self.id}, name={self.name}, type={self.source_type})>"
    
    def to_dict(self):
        # 安全處理日期時間字段
        def safe_isoformat(dt_value):
            if dt_value is None:
                return None
            if isinstance(dt_value, str):
                return dt_value  # 如果已經是字串，直接返回
            if hasattr(dt_value, 'isoformat'):
                return dt_value.isoformat()
            return str(dt_value)  # 最後的備用方案
        
        # 從 config 中提取路徑資訊
        source_path = ""
        if self.config:
            if self.source_type == "camera" and "ip" in self.config:
                source_path = f"http://{self.config.get('ip')}:{self.config.get('port', 8080)}"
            elif self.source_type == "video_file" and "path" in self.config:
                source_path = self.config.get('path', '')
        
        return {
            'id': self.id,
            'source_type': self.source_type,
            'name': self.name,
            'config': self.config,
            'status': self.status,
            'source_path': source_path,  # 添加便於模板使用的路徑字段
            'last_check': safe_isoformat(self.last_check),
            'created_at': safe_isoformat(self.created_at)
        }

class SystemConfig(Base):
    """系統配置表 - 系統參數和設定"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SystemConfig(key={self.config_key}, value={self.config_value})>"
    
    def to_dict(self):
        # 安全處理日期時間字段
        def safe_isoformat(dt_value):
            if dt_value is None:
                return None
            if isinstance(dt_value, str):
                return dt_value  # 如果已經是字串，直接返回
            if hasattr(dt_value, 'isoformat'):
                return dt_value.isoformat()
            return str(dt_value)  # 最後的備用方案
        
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'description': self.description,
            'updated_at': safe_isoformat(self.updated_at)
        }

# 建立索引
Index('idx_analysis_tasks_task_type', AnalysisTask.task_type)
Index('idx_analysis_tasks_status', AnalysisTask.status)
Index('idx_analysis_tasks_created_at', AnalysisTask.created_at)

Index('idx_detection_results_task_id', DetectionResult.task_id)
Index('idx_detection_results_timestamp', DetectionResult.timestamp)
Index('idx_detection_results_object_type', DetectionResult.object_type)

Index('idx_data_sources_source_type', DataSource.source_type)
Index('idx_data_sources_status', DataSource.status)

Index('idx_system_config_key', SystemConfig.config_key)
