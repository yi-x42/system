"""
YOLOv11 數位雙生分析系統 - API 路由器
"""

from fastapi import APIRouter

from app.api.v1.endpoints import detection, health
# 使用簡化版 analysis
from app.api.v1.endpoints import analysis_simple
from app.core.config import get_settings

api_router = APIRouter()

# 包含各個端點路由器
api_router.include_router(
    detection.router,
    prefix="/detection",
    tags=["物件偵測"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["健康檢查"]
)

# 包含影片分析端點 (簡化版)
api_router.include_router(
    analysis_simple.router
)

# 根路徑端點
@api_router.get("/")
async def root():
    """API 根端點"""
    settings = get_settings()
    return {
        "message": f"歡迎使用 {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": f"{settings.api_v1_str}/health",
        "analysis": f"{settings.api_v1_str}/analysis"
    }
