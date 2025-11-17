"""
日誌系統配置
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging():
    """設置日誌系統"""
    # 確保日誌目錄存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 創建日誌檔案名稱
    log_file = log_dir / f"yolo_system_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 配置日誌格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 配置根日誌記錄器
    logging.basicConfig(
        level=logging.DEBUG,  # 改為DEBUG級別
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """獲取日誌記錄器"""
    return logging.getLogger(name)

# 為向後兼容性保留的類別
class StructuredLogger:
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def info(self, message: str, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)
    
    def log_error(self, error, context=None):
        self.logger.error(f"Error: {str(error)} | Context: {context}")
    
    def log_detection(self, image_id, detections, inference_time, model_version):
        """記錄檢測事件"""
        self.logger.info(f"Detection - Image ID: {image_id}, Objects: {len(detections)}, "
                        f"Time: {inference_time:.3f}s, Model: {model_version}")

# 系統日誌記錄器 - 使用 StructuredLogger 包裝
system_logger = StructuredLogger("yolo_system")
api_logger = StructuredLogger("yolo_system.api") 
detection_logger = StructuredLogger("yolo_system.detection")
main_logger = StructuredLogger("yolo_system")
performance_logger = get_logger("yolo_system.performance")

def log_performance(func_name):
    """性能日誌裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            performance_logger.info(f"{func_name} executed in {end_time - start_time:.3f}s")
            return result
        return wrapper
    return decorator
