"""
YOLOv11 數位雙生分析系統 - 核心配置模組 (簡化版)
"""

import os
from typing import Optional, List
from functools import lru_cache

class Settings:
    """應用程式設定類別 - 簡化版本"""
    
    def __init__(self):
        # 基本應用設定
        self.app_name = os.getenv("APP_NAME", "YOLOv11 數位雙生分析系統")
        self.app_version = "1.0.0"
        self.debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        
        # API 設定
        self.api_v1_str = "/api/v1"
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.workers = int(os.getenv("WORKERS", "4"))
        
        # YOLOv11 模型設定
        self.model_path = os.getenv("MODEL_PATH", "yolo11n.pt")
        self.YOLO_MODEL_PATH = self.model_path  # 別名支援
        self.device = os.getenv("DEVICE", "auto")
        self.DEVICE = self.device  # 別名支援
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))
        self.CONFIDENCE_THRESHOLD = self.confidence_threshold  # 別名支援
        self.iou_threshold = float(os.getenv("IOU_THRESHOLD", "0.45"))
        self.IOU_THRESHOLD = self.iou_threshold  # 別名支援
        self.max_detections = int(os.getenv("MAX_DETECTIONS", "100"))
        self.MAX_DETECTIONS = self.max_detections  # 別名支援
        
        # 追蹤器設定
        self.tracker = os.getenv("TRACKER", "bytetrack.yaml")
        self.track_high_thresh = float(os.getenv("TRACK_HIGH_THRESH", "0.6"))
        self.track_low_thresh = float(os.getenv("TRACK_LOW_THRESH", "0.1"))
        self.new_track_thresh = float(os.getenv("NEW_TRACK_THRESH", "0.7"))
        
        # 檔案上傳設定
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.MAX_FILE_SIZE = self.max_file_size  # 別名支援
        self.allowed_extensions = ["jpg", "jpeg", "png", "bmp", "gif", "mp4", "avi", "mov", "mkv"]
        self.ALLOWED_EXTENSIONS = self.allowed_extensions  # 別名支援
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        
        # 日誌設定
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "logs/app.log")
        self.log_format = os.getenv("LOG_FORMAT", "text")  # text 或 json
        self.log_rotation = "1 day"
        self.log_retention = "30 days"
        
        # 資料庫設定
        self.postgres_server = os.getenv("POSTGRES_SERVER", "localhost")
        self.postgres_user = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", "49679904")
        self.postgres_db = os.getenv("POSTGRES_DB", "yolo_analysis")
        self.postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
        
        # 資料庫連接 URL
        self.DATABASE_URL = f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        self.DATABASE_POOL_SIZE = 5
        self.DATABASE_MAX_OVERFLOW = 10
        self.DATABASE_ECHO = self.debug
        
        # Redis 設定
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD")
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        
        # 安全設定
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
        # CORS 設定
        cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
        self.cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
        
        # MinIO 設定
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.minio_bucket = os.getenv("MINIO_BUCKET", "yolo-data")
        self.minio_secure = os.getenv("MINIO_SECURE", "false").lower() in ("true", "1", "yes")
        
        # 載入 .env 檔案 (如果存在)
        self._load_env_file()
    
    def _load_env_file(self):
        """載入 .env 檔案"""
        try:
            if os.path.exists(".env"):
                with open(".env", "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
        except Exception as e:
            print(f"⚠️  載入 .env 檔案時發生錯誤: {e}")
    
    @property
    def database_url(self) -> str:
        """建構資料庫連線 URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """建構 Redis 連線 URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

@lru_cache()
def get_settings() -> Settings:
    """取得設定實例（單例模式）"""
    return Settings()

# YOLO 類別名稱對應表 (COCO 資料集)
YOLO_CLASSES = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane",
    5: "bus", 6: "train", 7: "truck", 8: "boat", 9: "traffic light",
    10: "fire hydrant", 11: "stop sign", 12: "parking meter", 13: "bench", 14: "bird",
    15: "cat", 16: "dog", 17: "horse", 18: "sheep", 19: "cow",
    20: "elephant", 21: "bear", 22: "zebra", 23: "giraffe", 24: "backpack",
    25: "umbrella", 26: "handbag", 27: "tie", 28: "suitcase", 29: "frisbee",
    30: "skis", 31: "snowboard", 32: "sports ball", 33: "kite", 34: "baseball bat",
    35: "baseball glove", 36: "skateboard", 37: "surfboard", 38: "tennis racket", 39: "bottle",
    40: "wine glass", 41: "cup", 42: "fork", 43: "knife", 44: "spoon",
    45: "bowl", 46: "banana", 47: "apple", 48: "sandwich", 49: "orange",
    50: "broccoli", 51: "carrot", 52: "hot dog", 53: "pizza", 54: "donut",
    55: "cake", 56: "chair", 57: "couch", 58: "potted plant", 59: "bed",
    60: "dining table", 61: "toilet", 62: "tv", 63: "laptop", 64: "mouse",
    65: "remote", 66: "keyboard", 67: "cell phone", 68: "microwave", 69: "oven",
    70: "toaster", 71: "sink", 72: "refrigerator", 73: "book", 74: "clock",
    75: "vase", 76: "scissors", 77: "teddy bear", 78: "hair drier", 79: "toothbrush"
}

# 設定實例
settings = get_settings()
