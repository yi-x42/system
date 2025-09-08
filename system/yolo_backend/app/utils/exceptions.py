"""
YOLOv11 數位雙生分析系統 - 自訂例外類別
"""

from typing import Optional, Dict, Any


class YOLOBackendException(Exception):
    """基礎例外類別"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ModelNotLoadedException(YOLOBackendException):
    """模型未載入例外"""
    pass


class InferenceException(YOLOBackendException):
    """推論失敗例外"""
    pass


class TrackingException(YOLOBackendException):
    """追蹤失敗例外"""
    pass


class DatabaseException(YOLOBackendException):
    """資料庫例外"""
    pass


class CacheException(YOLOBackendException):
    """快取例外"""
    pass


class ValidationException(YOLOBackendException):
    """驗證例外"""
    pass


class FileProcessingException(YOLOBackendException):
    """檔案處理例外"""
    pass


class AlertException(YOLOBackendException):
    """異常事件例外"""
    pass


class UnityIntegrationException(YOLOBackendException):
    """Unity 整合例外"""
    pass


class HeatmapException(YOLOBackendException):
    """熱點圖產生例外"""
    pass


class AuthenticationException(YOLOBackendException):
    """身份驗證例外"""
    pass


class AuthorizationException(YOLOBackendException):
    """授權例外"""
    pass
