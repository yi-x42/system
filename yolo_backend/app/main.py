"""
YOLOv11 數位雙生分析系統 - 主應用程式
FastAPI 應用程式入口點 - 整合新資料庫架構
"""

import os
import time
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import get_settings
from app.core.logger import main_logger, api_logger
from app.core.database import engine, get_db
from app.models.database import Base

# 導入新的 API 路由
from app.api.v1.new_analysis import router as new_analysis_router
from app.api.v1.router import api_router
from app.api.v1.data_query import data_router
from app.api.v1.database_query import db_query_router  # 新增資料庫查詢路由
from app.api.v1.frontend import router as frontend_router  # 新增前端API
from app.api.v1.camera_routes import router as camera_router  # 攝影機管理API 新增
from app.api.v1.realtime_routes import router as realtime_router  # 實時檢測API
# WebSocket 路由
from app.websocket.routes import router as websocket_router

# 異步隊列管理器
from app.services.async_queue_manager import AsyncQueueManager

# 導入實時檢測服務設置函數
from app.services.realtime_detection_service import set_queue_manager_for_realtime_service

# 導入服務
from app.services.new_database_service import DatabaseService
# from app.services.yolo_service import get_yolo_service  # 暫時註解
from app.utils.exceptions import YOLOBackendException

# 導入 WebSocket 推送服務
from app.websocket.push_service import realtime_push_service

# （已移除舊管理介面）


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時
    settings = get_settings()
    main_logger.info(f"啟動 {settings.app_name} v{settings.app_version}")
    
    # 初始化全域異步隊列管理器
    app.state.queue_manager = AsyncQueueManager()
    app.state.queue_manager.start()
    main_logger.info("✅ 異步隊列管理器已啟動")
    
    # 為實時檢測服務設置隊列管理器
    set_queue_manager_for_realtime_service(app.state.queue_manager)
    main_logger.info("✅ 實時檢測服務隊列管理器已設置")
    
    # 初始化新的資料庫架構
    main_logger.info("🔄 初始化資料庫架構...")
    try:
        # 創建所有資料表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        main_logger.info("✅ 資料庫初始化完成")
        
        # 啟動 WebSocket 推送服務
        await realtime_push_service.start()
        main_logger.info("🚀 WebSocket 推送服務已啟動")
        
    except Exception as e:
        main_logger.error(f"❌ 資料庫初始化失敗: {e}")
        raise
    
    # 載入 YOLOv11 模型（可選）
    skip_yolo_init = os.getenv("SKIP_YOLO_INIT", "false").lower() in ("true", "1", "yes")
    
    if skip_yolo_init:
        main_logger.info("⚠️ 跳過 YOLO 模型初始化（將在首次使用時載入）")
    else:
        try:
            main_logger.info("開始載入 YOLOv11 模型...")
            # success = await get_yolo_service().load_model(settings.model_path)  # 暫時註解
            success = True  # 模擬成功
            if success:
                main_logger.info("YOLOv11 模型載入成功 (模擬)")
            else:
                main_logger.error("YOLOv11 模型載入失敗")
        except Exception as e:
            main_logger.error(f"YOLOv11 模型載入過程中發生錯誤: {str(e)}")
            main_logger.info("💡 提示：可以設定 SKIP_YOLO_INIT=true 跳過初始載入")
    
    yield
    
    # 關閉時
    main_logger.info("正在關閉應用程式...")
    
    # 停止異步隊列管理器
    if hasattr(app.state, 'queue_manager') and app.state.queue_manager:
        app.state.queue_manager.stop()
        main_logger.info("⏹️ 異步隊列管理器已停止")
    
    # 停止 WebSocket 推送服務
    await realtime_push_service.stop()
    main_logger.info("⏹️ WebSocket 推送服務已停止")


# 建立 FastAPI 應用程式實例
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基於 YOLOv11 的數位雙生物件辨識分析系統",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 請求日誌中間件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """記錄請求日誌"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        api_logger.info(
            f"API - {request.method} {request.url.path} [{response.status_code}] "
            f"{process_time:.3f}s"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        api_logger.error(
            f"API - {request.method} {request.url.path} [ERROR] "
            f"{process_time:.3f}s - {str(e)}"
        )
        raise

# 錯誤處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """處理 HTTP 異常"""
    api_logger.error(f"HTTPException: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(YOLOBackendException)
async def yolo_exception_handler(request: Request, exc: YOLOBackendException):
    """處理 YOLO 後端異常"""
    api_logger.error(f"YOLOBackendException: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_type": exc.error_type,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """處理一般異常"""
    api_logger.error(f"Unexpected error: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "內部伺服器錯誤",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

# 包含 API 路由
app.include_router(api_router, prefix="/api/v1")
app.include_router(frontend_router, prefix="/api/v1")  # 新增前端API路由
app.include_router(camera_router)  # 新增攝影機管理API 路由

# 相容舊前端: /admin/api/cameras/scan -> 導向新邏輯
legacy_router = APIRouter()
@legacy_router.post("/admin/api/cameras/scan")
async def legacy_scan(max_index: int = 6):
    from app.api.v1.camera_routes import _do_scan
    return _do_scan(max_index=max_index)
app.include_router(legacy_router)

# 調試：列出攝影機相關路由
for r in app.router.routes:
    if hasattr(r, 'path') and '/api/v1/cameras' in getattr(r, 'path'):
        main_logger.info(f"CameraRoute loaded: {getattr(r, 'path')} -> {getattr(r, 'name', '')}")

# 暫時禁用WebSocket路由
app.include_router(websocket_router)  # 新增WebSocket路由

# 包含實時檢測 API 路由
app.include_router(realtime_router, prefix="/api/v1", tags=["實時檢測"])

# 包含新的分析 API 路由 (僅使用 v1 避免衝突)
app.include_router(new_analysis_router, prefix="/api/v1", tags=["分析功能與資料庫查看"])

# 包含資料查詢 API 路由
app.include_router(data_router, prefix="/api/v1/data", tags=["資料查詢"])

# 包含新的資料庫查詢 API 路由
app.include_router(db_query_router, tags=["資料庫查詢"])

# 包含測試座標 API 路由
from app.api.v1.test_coordinates import router as test_coord_router
app.include_router(test_coord_router, prefix="/api/v1/test", tags=["座標測試"])

# 靜態檔案服務 - 指向正確的現代化網站
# 您的現代化 YOLO AI v2.0 網站
website_path = Path("website_prototype")
if website_path.exists():
    app.mount("/website", StaticFiles(directory=str(website_path), html=True), name="website")
    print(f"✅ YOLO AI v2.0 網站已掛載: {website_path.absolute()}")
else:
    print(f"❌ 網站目錄不存在: {website_path.absolute()}")

# 管理後台靜態檔案 (保留作為備用)
admin_static_path = Path("app/admin/static")
if admin_static_path.exists():
    app.mount("/admin/static", StaticFiles(directory=str(admin_static_path)), name="admin_static")

# 管理後台模板檔案 (保留作為備用)
admin_templates_path = Path("app/admin/templates")
if admin_templates_path.exists():
    app.mount("/admin", StaticFiles(directory=str(admin_templates_path), html=True), name="admin")

# 前端靜態檔案
frontend_static_path = Path("app/static")
if frontend_static_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_static_path)), name="frontend_static")

# 根路由 - 重定向到您的現代化網站
@app.get("/", include_in_schema=False)
async def root():
    """根路由 - 重定向到現代化 YOLO AI v2.0 系統"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/website/")


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
        log_level="info"
    )
