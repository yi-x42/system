"""
YOLOv11 數位雙生分析系統 - 核心配置模組 (簡化版)
"""

import os
from typing import Optional, List
from pathlib import Path
from functools import lru_cache

class Settings:
    """應用程式設定類別 - 簡化版本"""

    def __init__(self):
        # ====== 1. 載入 .env ======
        pre_env_pwd = os.environ.get("POSTGRES_PASSWORD")
        self._load_env_file()
        post_env_pwd = os.environ.get("POSTGRES_PASSWORD")

        # ====== 2. 基本應用設定 ======
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
        self.YOLO_MODEL_PATH = self.model_path
        self.device = os.getenv("DEVICE", "auto")
        self.DEVICE = self.device
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))
        self.CONFIDENCE_THRESHOLD = self.confidence_threshold
        self.iou_threshold = float(os.getenv("IOU_THRESHOLD", "0.45"))
        self.IOU_THRESHOLD = self.iou_threshold
        self.max_detections = int(os.getenv("MAX_DETECTIONS", "100"))
        self.MAX_DETECTIONS = self.max_detections

        # 追蹤器設定
        self.tracker = os.getenv("TRACKER", "bytetrack.yaml")
        self.track_high_thresh = float(os.getenv("TRACK_HIGH_THRESH", "0.6"))
        self.track_low_thresh = float(os.getenv("TRACK_LOW_THRESH", "0.1"))
        self.new_track_thresh = float(os.getenv("NEW_TRACK_THRESH", "0.7"))

        # 上傳設定
        self.max_file_size = 50 * 1024 * 1024
        self.MAX_FILE_SIZE = self.max_file_size
        self.allowed_extensions = ["jpg", "jpeg", "png", "bmp", "gif", "mp4", "avi", "mov", "mkv"]
        self.ALLOWED_EXTENSIONS = self.allowed_extensions
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")

        # 日誌設定
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "logs/app.log")
        self.log_format = os.getenv("LOG_FORMAT", "text")
        self.log_rotation = "1 day"
        self.log_retention = "30 days"

        # ====== 3. 資料庫設定 ======
        self.postgres_server = os.getenv("POSTGRES_SERVER", "localhost")
        self.postgres_user = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", "__DEFAULT_FALLBACK_PASSWORD__")
        self.postgres_db = os.getenv("POSTGRES_DB", "yolo_analysis")
        self.postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))

        self.DATABASE_URL = (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        )

        # ====== 4. Debug 輸出 ======
        print("=" * 50)
        print("🔧 DEBUG: DATABASE CONNECTION SETTINGS")
        if pre_env_pwd is None and post_env_pwd is not None:
            print("  - Load event: loaded from .env (新增)")
        elif pre_env_pwd is not None and post_env_pwd == pre_env_pwd:
            print("  - Load event: pre-existing env var (未被 .env 覆蓋)")
        elif post_env_pwd is None:
            print("  - Load event: POSTGRES_PASSWORD 未定義 (使用 fallback)")
        else:
            print("  - Load event: 狀態不明 (請回報)")
        print(f"  - User: {self.postgres_user}")
        if self.postgres_password == "__DEFAULT_FALLBACK_PASSWORD__":
            print("  - Password: (USING DEFAULT / 未讀到 .env)")
        else:
            print(f"  - Password length: {len(self.postgres_password)} (masked)")
        print(f"  - Host: {self.postgres_server}")
        print(f"  - Port: {self.postgres_port}")
        print(f"  - Database: {self.postgres_db}")
        if self.postgres_password != "__DEFAULT_FALLBACK_PASSWORD__":
            print(
                "  - Connection URL: "
                + self.DATABASE_URL.replace(self.postgres_password, "********")
            )
        else:
            print("  - Connection URL: (masked; using default password)")
        print("=" * 50)

        self.DATABASE_POOL_SIZE = 5
        self.DATABASE_MAX_OVERFLOW = 10
        self.DATABASE_ECHO = self.debug

        # Redis
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD")
        self.redis_db = int(os.getenv("REDIS_DB", "0"))

        # 安全
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

        # CORS
        cors_origins_str = os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
        )
        self.cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

        # MinIO
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.minio_bucket = os.getenv("MINIO_BUCKET", "yolo-data")
        self.minio_secure = (
            os.getenv("MINIO_SECURE", "false").lower() in ("true", "1", "yes")
        )
    
    def _load_env_file(self):
        """僅載入『專案根目錄』的 .env，並在偵測到密碼不一致時強制覆蓋。

        規則：
        1. 專案根目錄判定：向上尋找同層具有 start.py 的資料夾。
        2. 只允許載入根目錄 .env（忽略子資料夾的任何 .env / .env.backup）。
        3. 如果系統環境已有 POSTGRES_PASSWORD 且與根 .env 不同，記錄警告並覆蓋。
        4. 其他變數：若已存在則不覆蓋；若不存在則新增。
        """
        try:
            # 1. 尋找專案根目錄（包含 start.py 且同時包含 yolo_backend 子目錄）
            root_dir = None
            for parent in Path(__file__).resolve().parents:
                start_py = parent / 'start.py'
                yolo_backend_dir = parent / 'yolo_backend'
                if start_py.exists() and yolo_backend_dir.exists() and yolo_backend_dir.is_dir():
                    root_dir = parent
                    break
            if root_dir is None:
                print("⚠️  無法判定專案根目錄 (找不到 start.py)，跳過 .env 載入")
                return

            env_path = root_dir / '.env'
            if not env_path.exists():
                print(f"⚠️  根目錄未找到 .env：{env_path}，使用程式內預設值")
                return

            # 2. 讀取根 .env 內容至暫存 dict
            parsed = {}
            with open(env_path, 'r', encoding='utf-8') as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    parsed[k.strip()] = v.strip()

            existing_pwd = os.environ.get('POSTGRES_PASSWORD')
            file_pwd = parsed.get('POSTGRES_PASSWORD')

            # 3. 密碼處理：若文件有值且 (不存在或不同) 則覆蓋
            if file_pwd:
                if existing_pwd is None:
                    os.environ['POSTGRES_PASSWORD'] = file_pwd
                    print(f"✅ 載入 root .env POSTGRES_PASSWORD (長度 {len(file_pwd)})")
                elif existing_pwd != file_pwd:
                    os.environ['POSTGRES_PASSWORD'] = file_pwd
                    print(
                        "⚠️  偵測到預先存在的 POSTGRES_PASSWORD 與 root .env 不一致 → 已強制覆蓋"
                        f" (原長度 {len(existing_pwd)} -> 新長度 {len(file_pwd)})"
                    )
                else:
                    print("✅ root .env POSTGRES_PASSWORD 與現有環境一致 (無需變更)")
            else:
                print("⚠️  root .env 未定義 POSTGRES_PASSWORD，將使用現有或 fallback")

            # 4. 載入其他變數（不覆蓋既有環境）
            for k, v in parsed.items():
                if k == 'POSTGRES_PASSWORD':
                    continue
                if k not in os.environ:
                    os.environ[k] = v

            print(f"✅ 已處理根目錄 .env：{env_path} (實際根目錄: {root_dir})")
        except Exception as e:
            print(f"❌ 讀取根目錄 .env 失敗: {e}")
    
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
