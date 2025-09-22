"""
YOLOv11 配置管理模組
處理系統配置的讀取、更新和驗證
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class YOLOConfig(BaseModel):
    """YOLO 配置數據模型"""
    model_path: str = Field(default="yolo11n.pt", description="模型檔案路徑")
    device: str = Field(default="auto", description="運算設備")
    confidence_threshold: float = Field(default=0.25, ge=0.0, le=1.0, description="信心度閾值")
    iou_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="IoU 閾值")
    max_file_size: str = Field(default="50MB", description="最大檔案大小")
    allowed_extensions: str = Field(default="jpg,jpeg,png,bmp,mp4,avi,mov,mkv", description="允許的檔案格式")

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = ".env"):
        self.config_file = Path(config_file)
        self.config_cache = {}
        
    def load_config(self) -> Dict[str, Any]:
        """載入配置"""
        config = {}
        
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
        
        self.config_cache = config
        return config
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """儲存配置"""
        try:
            # 生成配置檔案內容
            config_content = self._generate_config_content(config)
            
            # 寫入檔案
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(config_content)
            
            # 更新快取
            self.config_cache = config
            return True
            
        except Exception as e:
            print(f"儲存配置失敗: {e}")
            return False
    
    def get_yolo_config(self) -> YOLOConfig:
        """獲取 YOLO 配置"""
        config = self.load_config()
        
        return YOLOConfig(
            model_path=config.get("MODEL_PATH", "yolo11n.pt"),
            device=config.get("DEVICE", "auto"),
            confidence_threshold=float(config.get("CONFIDENCE_THRESHOLD", "0.25")),
            iou_threshold=float(config.get("IOU_THRESHOLD", "0.7")),
            max_file_size=config.get("MAX_FILE_SIZE", "50MB"),
            allowed_extensions=config.get("ALLOWED_EXTENSIONS", "jpg,jpeg,png,bmp,mp4,avi,mov,mkv")
        )
    
    def update_yolo_config(self, yolo_config: YOLOConfig) -> bool:
        """更新 YOLO 配置"""
        config = self.load_config()
        
        # 更新 YOLO 相關配置
        config.update({
            "MODEL_PATH": yolo_config.model_path,
            "DEVICE": yolo_config.device,
            "CONFIDENCE_THRESHOLD": str(yolo_config.confidence_threshold),
            "IOU_THRESHOLD": str(yolo_config.iou_threshold),
            "MAX_FILE_SIZE": yolo_config.max_file_size,
            "ALLOWED_EXTENSIONS": yolo_config.allowed_extensions
        })
        
        return self.save_config(config)
    
    def _generate_config_content(self, config: Dict[str, Any]) -> str:
        """生成配置檔案內容"""
        # 保持原有的配置結構和註釋
        base_config = {
            "HOST": "0.0.0.0",
            "PORT": "8001",
            "DEBUG": "true",
            "LOG_LEVEL": "INFO",
            "LOG_FILE": "logs/app.log"
        }
        
        # 合併配置
        final_config = {**base_config, **config}
        
        config_content = """# YOLOv11 數位雙生分析系統配置

# API 設定
HOST={HOST}
PORT={PORT}
DEBUG={DEBUG}

# YOLO 模型設定
MODEL_PATH={MODEL_PATH}
DEVICE={DEVICE}
CONFIDENCE_THRESHOLD={CONFIDENCE_THRESHOLD}
IOU_THRESHOLD={IOU_THRESHOLD}

# 檔案上傳設定
MAX_FILE_SIZE={MAX_FILE_SIZE}
ALLOWED_EXTENSIONS={ALLOWED_EXTENSIONS}

# 日誌設定
LOG_LEVEL={LOG_LEVEL}
LOG_FILE={LOG_FILE}

# 資料庫設定 (可選)
# DATABASE_URL=postgresql://user:password@localhost:5432/yolo_db
# REDIS_URL=redis://localhost:6379/0

# 安全設定
# SECRET_KEY=your-secret-key-here
# CORS_ORIGINS=["http://localhost:3000"]
""".format(**final_config)
        
        return config_content
    
    def validate_config(self) -> Dict[str, bool]:
        """驗證配置"""
        config = self.load_config()
        validation_result = {}
        
        # 檢查模型檔案是否存在
        model_path = config.get("MODEL_PATH", "yolo11n.pt")
        validation_result["model_exists"] = Path(model_path).exists()
        
        # 檢查設備配置
        device = config.get("DEVICE", "auto")
        validation_result["device_valid"] = device in ["auto", "cpu", "cuda"]
        
        # 檢查閾值範圍
        try:
            conf_threshold = float(config.get("CONFIDENCE_THRESHOLD", "0.25"))
            validation_result["confidence_valid"] = 0.0 <= conf_threshold <= 1.0
        except ValueError:
            validation_result["confidence_valid"] = False
        
        try:
            iou_threshold = float(config.get("IOU_THRESHOLD", "0.7"))
            validation_result["iou_valid"] = 0.0 <= iou_threshold <= 1.0
        except ValueError:
            validation_result["iou_valid"] = False
        
        # 檢查日誌目錄
        log_file = config.get("LOG_FILE", "logs/app.log")
        log_dir = Path(log_file).parent
        validation_result["log_dir_exists"] = log_dir.exists()
        
        return validation_result
    
    def backup_config(self) -> bool:
        """備份配置檔案"""
        try:
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix(f".env.backup")
                backup_file.write_text(self.config_file.read_text(encoding="utf-8"), encoding="utf-8")
                return True
            return False
        except Exception:
            return False
    
    def restore_config(self) -> bool:
        """還原配置檔案"""
        try:
            backup_file = self.config_file.with_suffix(f".env.backup")
            if backup_file.exists():
                self.config_file.write_text(backup_file.read_text(encoding="utf-8"), encoding="utf-8")
                return True
            return False
        except Exception:
            return False

# 全域配置管理器實例
config_manager = ConfigManager()
