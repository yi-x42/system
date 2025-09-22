# YOLOv11 後台管理系統使用指南

## 🎛️ 系統概覽

YOLOv11 後台管理系統是一個基於 Web 的管理介面，提供完整的系統監控、配置管理和檔案操作功能，專為 Radmin 網絡環境優化。

## 🚀 快速開始

### 1. 啟動系統
```bash
# 在專案根目錄執行
python start.py
```

### 2. 訪問後台管理
- **本機訪問**: http://localhost:8001/admin
- **Radmin 網絡**: http://26.86.64.166:8001/admin

### 3. 測試系統功能
```bash
# 執行測試腳本
python test_admin_system.py
```

## 📊 功能模組

### 1. 系統監控 (Dashboard)
- **實時系統指標**: CPU、記憶體、GPU、磁碟使用率
- **資源趨勢圖表**: 系統性能歷史數據可視化
- **網絡流量監控**: 實時網絡傳輸統計
- **自動更新**: 每 5 秒自動刷新系統狀態

**API 端點**:
- `GET /admin/api/system/status` - 獲取系統狀態

### 2. YOLO 配置管理
- **模型設定**: 模型路徑、運算設備選擇
- **檢測參數**: 信心度閾值、IoU 閾值調整
- **檔案限制**: 上傳檔案大小和格式設定
- **即時儲存**: 配置修改即時生效

**支援的設備**:
- `auto` - 自動選擇最佳設備
- `cpu` - 強制使用 CPU 運算
- `cuda` - 使用 GPU 加速（需支援 CUDA）

**API 端點**:
- `GET /admin/api/yolo/config` - 獲取配置
- `POST /admin/api/yolo/config` - 更新配置

### 3. 檔案管理
- **目錄瀏覽**: 安全的檔案系統瀏覽
- **檔案上傳**: 支援多種格式檔案上傳
- **檔案分類**: 自動識別檔案類型（圖片、影片、文件等）
- **安全限制**: 防止訪問系統關鍵檔案

**支援的檔案類型**:
- 圖片: jpg, jpeg, png, bmp, gif, tiff
- 影片: mp4, avi, mov, mkv, wmv, flv
- 文件: txt, pdf, doc, docx, md
- 配置: json, yaml, yml, ini, cfg, env
- 模型: pt, pth, onnx, pb

**API 端點**:
- `GET /admin/api/files/list` - 列出檔案
- `POST /admin/api/files/upload` - 上傳檔案

### 4. 資料分析
- **檢測統計**: YOLO 檢測結果統計分析
- **趨勢分析**: 檢測數據時間序列分析
- **效能指標**: 系統處理效能評估
- **報告匯出**: 分析結果匯出功能

### 5. 網絡狀態監控
- **Radmin 連接狀態**: 實時監控 Radmin VPN 連接
- **網絡介面資訊**: 顯示所有網絡介面和 IP 地址
- **連接測試**: 自動ping測試網絡連通性
- **介面統計**: 網絡流量和錯誤統計

**Radmin 網絡配置**:
- IP 地址: 26.86.64.166
- 端口: 8001
- 協議: HTTP/HTTPS

**API 端點**:
- `GET /admin/api/radmin/status` - 獲取網絡狀態

### 6. 系統日誌
- **即時日誌**: 系統運行日誌即時顯示
- **日誌篩選**: 按時間、級別篩選日誌
- **錯誤追蹤**: 錯誤和異常日誌高亮顯示
- **終端樣式**: 類似終端的日誌顯示界面

**API 端點**:
- `GET /admin/api/logs/list` - 獲取日誌列表

## 🔧 配置說明

### 環境變數配置 (.env)
```bash
# API 設定
HOST=0.0.0.0
PORT=8001
DEBUG=true

# YOLO 模型設定
MODEL_PATH=yolo11n.pt
DEVICE=auto
CONFIDENCE_THRESHOLD=0.25
IOU_THRESHOLD=0.7

# 檔案上傳設定
MAX_FILE_SIZE=50MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,bmp,mp4,avi,mov,mkv

# 日誌設定
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 安全設定
- **路徑限制**: 檔案操作限制在專案目錄內
- **檔案名清理**: 自動清理危險字符
- **系統檔案保護**: 防止刪除重要系統檔案
- **CORS 設定**: 跨域請求安全配置

## 📱 使用介面

### 1. 側邊欄導航
- **系統監控**: 查看系統資源使用狀況
- **YOLO 配置**: 調整模型和檢測參數
- **檔案管理**: 瀏覽和管理系統檔案
- **資料分析**: 查看檢測結果分析
- **網絡狀態**: 監控 Radmin 網絡連接
- **系統日誌**: 查看系統運行日誌

### 2. 主內容區域
- **回應式設計**: 支援電腦、平板、手機訪問
- **即時更新**: 關鍵數據自動刷新
- **互動式圖表**: 支援縮放、篩選的數據圖表
- **通知系統**: 操作結果即時通知

### 3. 快速操作
- **快捷鍵**: 支援鍵盤快捷鍵操作
- **搜尋功能**: 快速搜尋檔案和設定
- **批量操作**: 支援批量檔案操作
- **匯出功能**: 一鍵匯出配置和數據

## 🔍 故障排除

### 常見問題

1. **無法訪問後台管理頁面**
   - 確認服務是否正常啟動
   - 檢查端口 8001 是否被占用
   - 確認防火牆設定允許訪問

2. **系統監控數據顯示異常**
   - 檢查 psutil 套件是否正確安裝
   - 確認權限允許訪問系統資訊
   - 重新啟動服務

3. **檔案上傳失敗**
   - 檢查檔案大小是否超過限制
   - 確認檔案格式是否被允許
   - 檢查磁碟空間是否足夠

4. **YOLO 配置無法儲存**
   - 確認 .env 檔案寫入權限
   - 檢查配置參數格式是否正確
   - 重新啟動服務使配置生效

5. **Radmin 網絡連接問題**
   - 確認 Radmin VPN 連接正常
   - 檢查 IP 地址 26.86.64.166 可訪問性
   - 確認網絡設定和防火牆配置

### 日誌檢查
```bash
# 查看應用程式日誌
tail -f logs/app.log

# 查看系統日誌（Windows）
Get-EventLog -LogName Application -Source Python*

# 檢查網絡連接
ping 26.86.64.166
netstat -ano | findstr :8001
```

## 🚀 進階功能

### 1. API 整合
所有後台管理功能都提供 REST API，可以與其他系統整合：

```python
import httpx

# 獲取系統狀態
async def get_system_status():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8001/admin/api/system/status")
        return response.json()
```

### 2. 自定義配置
可以通過修改配置檔案自定義系統行為：

```python
# app/admin/config.py
ADMIN_CONFIG = {
    "update_interval": 5,  # 系統狀態更新間隔（秒）
    "max_log_lines": 1000,  # 最大日誌行數
    "chart_data_points": 20,  # 圖表數據點數
}
```

### 3. 擴展模組
可以添加自定義管理模組：

```python
# 創建新的管理模組
from fastapi import APIRouter

custom_router = APIRouter(prefix="/admin/custom")

@custom_router.get("/")
async def custom_function():
    return {"message": "自定義功能"}

# 在 main.py 中註冊
app.include_router(custom_router)
```

## 📞 技術支援

如果遇到問題或需要幫助：

1. 查看系統日誌檔案
2. 執行測試腳本診斷問題
3. 檢查網絡連接和防火牆設定
4. 確認所有依賴套件正確安裝

## 🔄 更新和維護

### 定期維護
- 清理日誌檔案：定期清理過舊的日誌
- 更新模型：定期更新 YOLO 模型檔案
- 備份配置：定期備份重要配置檔案
- 監控效能：定期檢查系統效能指標

### 版本更新
- 備份現有配置
- 更新程式檔案
- 執行測試確認功能正常
- 恢復自定義配置

---

**版本**: 1.0.0  
**最後更新**: 2025年8月2日  
**適用於**: YOLOv11 數位雙生分析系統
