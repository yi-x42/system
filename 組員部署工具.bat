@echo off
chcp 65001 >nul
title YOLOv11數位雙生分析系統 - 組員部署工具

echo.
echo ████████████████████████████████████████████████████████
echo ██                                                    ██
echo ██     YOLOv11數位雙生分析系統 - 組員部署工具        ██
echo ██                                                    ██
echo ████████████████████████████████████████████████████████
echo.
echo 🚀 歡迎使用YOLOv11系統部署工具！
echo.
echo 請選擇您要執行的操作：
echo.
echo [1] 完整系統部署 (推薦新用戶)
echo [2] 僅設置資料庫
echo [3] 驗證部署結果
echo [4] 啟動系統
echo [5] 檢查系統狀態
echo [6] 查看說明文檔
echo [0] 退出
echo.

:menu
set /p choice="請輸入選項 (0-6): "

if "%choice%"=="1" goto full_deploy
if "%choice%"=="2" goto database_only
if "%choice%"=="3" goto verify
if "%choice%"=="4" goto start_system
if "%choice%"=="5" goto check_status
if "%choice%"=="6" goto show_docs
if "%choice%"=="0" goto exit

echo 無效選項，請重新輸入
goto menu

:full_deploy
echo.
echo ════════════════════════════════════════════════════════
echo 🚀 開始完整系統部署...
echo ════════════════════════════════════════════════════════
echo.
echo 這個過程將會：
echo ✓ 檢查系統環境 (Python, Node.js, PostgreSQL)
echo ✓ 安裝所有依賴套件
echo ✓ 創建和初始化資料庫
echo ✓ 配置系統環境
echo ✓ 下載YOLO模型
echo ✓ 驗證系統功能
echo.
pause
python deploy.py
echo.
echo ════════════════════════════════════════════════════════
echo 部署完成！按任意鍵返回主選單...
pause >nul
goto menu

:database_only
echo.
echo ════════════════════════════════════════════════════════
echo 🗄️  開始資料庫快速設置...
echo ════════════════════════════════════════════════════════
echo.
echo 這個過程將會：
echo ✓ 安裝資料庫相關套件
echo ✓ 測試PostgreSQL連接
echo ✓ 創建yolo_analysis資料庫
echo ✓ 創建所有資料表
echo ✓ 插入範例資料
echo ✓ 驗證資料庫設置
echo.
pause
python quick_database_setup.py
echo.
echo ════════════════════════════════════════════════════════
echo 資料庫設置完成！按任意鍵返回主選單...
pause >nul
goto menu

:verify
echo.
echo ════════════════════════════════════════════════════════
echo 🔍 開始驗證部署結果...
echo ════════════════════════════════════════════════════════
echo.
python verify_deployment.py
echo.
echo ════════════════════════════════════════════════════════
echo 驗證完成！按任意鍵返回主選單...
pause >nul
goto menu

:start_system
echo.
echo ════════════════════════════════════════════════════════
echo 🚀 啟動YOLOv11系統...
echo ════════════════════════════════════════════════════════
echo.
echo 系統將在背景啟動，請稍候...
echo.
echo 前端網址: http://localhost:3000
echo API文檔: http://localhost:8001/docs
echo.
echo 按 Ctrl+C 可停止系統
echo.
python start.py
echo.
echo ════════════════════════════════════════════════════════
echo 系統已停止！按任意鍵返回主選單...
pause >nul
goto menu

:check_status
echo.
echo ════════════════════════════════════════════════════════
echo 📊 檢查系統狀態...
echo ════════════════════════════════════════════════════════
echo.

REM 檢查端口8001 (後端)
netstat -an | findstr :8001 >nul
if %errorlevel%==0 (
    echo ✅ 後端服務 (端口8001) - 運行中
    echo    API地址: http://localhost:8001
    echo    健康檢查: http://localhost:8001/api/v1/health
) else (
    echo ❌ 後端服務 (端口8001) - 未運行
)

echo.

REM 檢查端口3000 (前端)
netstat -an | findstr :3000 >nul
if %errorlevel%==0 (
    echo ✅ 前端服務 (端口3000) - 運行中
    echo    前端地址: http://localhost:3000
) else (
    echo ❌ 前端服務 (端口3000) - 未運行
)

echo.

REM 檢查PostgreSQL端口5432
netstat -an | findstr :5432 >nul
if %errorlevel%==0 (
    echo ✅ PostgreSQL資料庫 (端口5432) - 運行中
) else (
    echo ❌ PostgreSQL資料庫 (端口5432) - 未運行
)

echo.

REM 檢查重要檔案
if exist ".env" (
    echo ✅ 環境配置檔案 (.env) - 存在
) else (
    echo ❌ 環境配置檔案 (.env) - 不存在
)

if exist "database_info.json" (
    echo ✅ 資料庫資訊檔案 - 存在
) else (
    echo ❌ 資料庫資訊檔案 - 不存在
)

echo.
echo ════════════════════════════════════════════════════════
echo 狀態檢查完成！按任意鍵返回主選單...
pause >nul
goto menu

:show_docs
echo.
echo ════════════════════════════════════════════════════════
echo 📚 說明文檔
echo ════════════════════════════════════════════════════════
echo.

if exist "組員部署指南.md" (
    echo ✅ 組員部署指南.md - 詳細部署說明
    set /p open_guide="是否要開啟部署指南? (y/n): "
    if /i "%open_guide%"=="y" (
        start "" "組員部署指南.md"
    )
)

echo.

if exist "部署說明.md" (
    echo ✅ 部署說明.md - 系統使用說明
    set /p open_readme="是否要開啟使用說明? (y/n): "
    if /i "%open_readme%"=="y" (
        start "" "部署說明.md"
    )
)

echo.
echo 📋 快速參考:
echo.  
echo 🚀 啟動系統: python start.py
echo 🔍 驗證部署: python verify_deployment.py
echo 🗄️  設置資料庫: python quick_database_setup.py
echo ⚙️  完整部署: python deploy.py
echo.
echo 🌐 系統地址:
echo    前端: http://localhost:3000
echo    API: http://localhost:8001/docs
echo    健康檢查: http://localhost:8001/api/v1/health
echo.
echo ════════════════════════════════════════════════════════
echo 按任意鍵返回主選單...
pause >nul
goto menu

:exit
echo.
echo 👋 感謝使用YOLOv11數位雙生分析系統部署工具！
echo.
echo 如有問題，請查看：
echo   📖 組員部署指南.md
echo   🔍 python verify_deployment.py
echo.
echo 祝您使用愉快！🎉
echo.
pause
exit /b 0