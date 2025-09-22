# 🚀 YOLOv11 數位雙生分析系統

基於 YOLOv11 的高效能物件辨識與分析系統，提供完整的 REST API 服務。

## ✨ 核心功能

### 🎯 **物件辨識**
- **即時物件檢測**：支援 80 種 COCO 類別物件
- **多種格式支援**：JPG、PNG、BMP 圖片格式
- **高精度檢測**：可調整信心閾值和 IoU 閾值
- **詳細結果**：包含物件類別、位置、信心度

### 🔍 **系統監控**
- **健康檢查**：即時系統狀態監控
- **資源監控**：CPU、記憶體、磁碟使用率
- **模型狀態**：載入狀態、設備資訊
- **服務狀態**：各個服務運行狀況

### 🌐 **API 服務**
- **RESTful API**：標準 HTTP API 接口
- **自動文檔**：Swagger UI 互動式文檔
- **非同步處理**：高效能異步架構
- **錯誤處理**：完整的錯誤回應機制

## 🛠️ 快速開始

### 1. 啟動系統
```bash
python start.py
```

### 2. 檢查系統狀態
```bash
python monitor.py
```

### 3. 診斷系統
```bash
python diagnose.py
```

## 📡 API 端點

### 🏥 健康檢查
- `GET /api/v1/health` - 主要健康檢查
- `GET /api/v1/health/basic` - 基本健康檢查
- `GET /api/v1/health/model` - 模型狀態檢查
- `GET /api/v1/health/system` - 系統資源檢查
- `GET /api/v1/health/services` - 服務狀態檢查

### 🤖 物件檢測
- `POST /api/v1/detection/detect` - 檢測圖片中的物件
- `GET /api/v1/detection/objects` - 獲取支援的物件類別

## 🔗 重要連結

- **API 文檔**: http://localhost:8001/docs
- **健康檢查**: http://localhost:8001/api/v1/health
- **模型狀態**: http://localhost:8001/api/v1/health/model
- **系統狀態**: http://localhost:8001/api/v1/health/system

## 📁 檔案結構

```
yolo_backend/
├── app/                    # 主應用程式
│   ├── api/v1/endpoints/   # API 端點
│   ├── core/              # 核心配置
│   ├── models/            # 資料模型
│   ├── services/          # 業務服務
│   └── utils/             # 工具函數
├── start.py              # 🚀 主啟動腳本
├── monitor.py            # 📊 系統監控腳本
├── diagnose.py           # 🩺 系統診斷腳本
├── requirements.txt      # 📦 依賴套件
├── .env                  # ⚙️ 環境配置
└── yolo11n.pt           # 🤖 YOLO 模型檔案
```

## 🎮 使用範例

### 檢測圖片物件
```bash
curl -X POST "http://localhost:8001/api/v1/detection/detect" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_image.jpg"
```

### 檢查系統狀態
```bash
curl -X GET "http://localhost:8001/api/v1/health"
```

## 📋 支援的物件類別

系統支援 80 種 COCO 標準物件類別，包括：
- 人物：person
- 交通工具：car, truck, bus, motorcycle, bicycle
- 動物：cat, dog, bird, horse, cow, sheep
- 家具：chair, sofa, bed, dining table
- 電子設備：tv, laptop, mouse, keyboard, cell phone
- 還有更多...

## ⚙️ 系統需求

- **Python**: 3.9+
- **記憶體**: 最少 4GB RAM
- **磁碟**: 最少 2GB 可用空間
- **作業系統**: Windows, macOS, Linux

## 🎯 效能特點

- **快速啟動**：2-3 秒完成模型載入
- **高精度**：YOLOv11 最新架構
- **低延遲**：優化的推論引擎
- **高並發**：支援多用戶同時使用

---

**🎉 現在您的 YOLOv11 數位雙生分析系統已經準備就緒！**

## 🚢 部署教學

以下示範在本機與團隊成員電腦上快速部署（開發用）。若需正式上線，請搭配系統服務與反向代理（例如 Nginx）進一步強化。

- 先決條件
  - Python 3.13+
  - Node.js 18+（含 npm）
  - Docker Desktop（可選，用於啟動相依服務）

- 準備環境變數
  - 複製 `.env.example` 為 `.env` 並依需求調整（特別是資料庫密碼）：
    ```bash
    cp .env.example .env
    # 編輯 .env 後保存
    ```

- 啟動相依服務（PostgreSQL/Redis/MinIO，皆可按需取捨）
  - 使用內建開發用 Compose：
    ```bash
    docker compose -f docker-compose.dev.yml up -d postgres redis minio pgadmin
    ```
  - 預設對外連接：
    - PostgreSQL: localhost:5432（帳號 `postgres`）
    - Redis: localhost:6379
    - MinIO Console: http://localhost:9001（預設帳密 `minioadmin/minioadmin`）

- 安裝後端依賴
  ```bash
    uv sync --group dev
  ```

- 啟動後端 API
  - 使用 uv + poe（pyproject 已內建任務）：
    ```bash
    uv run poe dev-api   # 於 http://localhost:8001 提供 API（含自動重載）
    ```
  - 或直接使用 uvicorn：
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8001 --reload
    ```

- 啟動前端（Vite + React）
  ```bash
  cd client
  npm install
  npm run dev  # 於 http://localhost:3000 啟動
  ```

- 驗證服務
  - API Docs: http://localhost:8001/docs
  - 健康檢查: http://localhost:8001/api/v1/health
  - 前端開發伺服器: http://localhost:3000

提示：若使用 `.env` 將 `PORT` 設為 `8001`，且以 `uv run main.py`啟動，實際 API 端口也會一致。

### 常見問題（FAQ）
- 端口衝突：
  - 變更 `uvicorn` 的 `--port` 或調整前端 `vite.config.ts` 中的 `server.port`。
- 無法連線資料庫：
  - 確認 Docker 服務 `postgres` 正在運作，並比對 `.env` 的 `POSTGRES_*` 與 `docker-compose.dev.yml` 設定是否一致。
- 首次模型下載較慢：
  - 首次使用 YOLO 權重會下載，請保持網路暢通；或先行放置 `yolo11n.pt` 至指定路徑並在 `.env` 以 `MODEL_PATH` 指定。

## 💻 開發教學

面向開發者的日常流程與專案啟動方式如下：

- 專案結構要點（節錄）
  - 後端 FastAPI 入口：`main.py`
  - API 路由：`app/api/v1/*`
  - 資料庫與 ORM：`app/core/database.py`, `app/models/*`
  - 設定：`app/core/config.py`（自動讀取專案根目錄 `.env`）
  - 前端：`client/`（Vite + React + TypeScript）

- 推薦工作流
  1) 啟動相依服務（見「部署教學」）。
  2) 後端開發：
     - 使用 uv：`uv run poe dev-api`
     - 或使用 uvicorn：`uvicorn main:app --reload --port 8001`
  3) 前端開發：
     - `cd client && npm run dev`
  4) 介面測試：
     - 以瀏覽器開啟 `http://localhost:3000` 與 `http://localhost:8001/docs`

- 測試與排錯建議
  - 使用 `curl`/`HTTPie` 驗證 API 端點；留意回應中的錯誤訊息與 `app/core/logger.py` 輸出。
  - 若資料表未建立，後端啟動時會透過 SQLAlchemy 自動 `create_all`（位於 `main.py` 的 lifespan 中）。
  - 需要跳過模型初始化時，可在環境變數設定 `SKIP_YOLO_INIT=true`。

---
