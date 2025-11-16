# 🚀 YOLOv11 數位雙生分析系統

一個結合即時攝影機串流與影片離線分析的多模態物件辨識平台。系統整合 YOLOv11 模型、統計監控、資料來源管理、任務調度、檢測結果儲存與前端展示，適合作為智慧監控 / 行為分析 / 教學實驗的基礎框架。

## ✨ 系統亮點

- ✅ 同時支援「即時攝影機」與「影片檔案」兩種來源
- ✅ 自動抽取影片解析度 / FPS / 幀數並紀錄
- ✅ 統一資料來源（`data_sources`）與任務（`analysis_tasks`）關聯
- ✅ 上傳影片即自動建構來源並可直接建立分析任務
- ✅ 系統狀態 / 效能（CPU / 記憶體 / GPU / 網路）前端即時輪詢
- ✅ 模組化服務層（YOLO 推論、影片分析、即時檢測、資料庫操作）
- ✅ 提供乾淨的 REST API，可被 Unity / Web 前端 / 腳本整合
- ✅ 具備遠端「安全停用系統」API（`POST /api/v1/frontend/system/shutdown`）
- ✅ 前端（React + Vite）＋ 傳統管理原型（HTML Prototype）雙模式

## 🏗️ 架構概觀

```
         ┌──────────────────────────┐
         │         前端層           │
         │  React Dashboard / 設定  │
         │  傳統管理原型 (website/) │
         └───────────┬────────────┘
                     │ REST / WebSocket（未來）
             ┌───────▼──────────────────────┐
             │          FastAPI              │
             │  /api/v1/frontend/*           │
             │  /api/v1/new_analysis/*       │
             │  /api/v1/realtime_routes/*    │
             │  /api/v1/video-list/*         │
             └───────┬───────────┬──────────┘
                     │           │
          ┌──────────▼───┐   ┌──▼────────────────┐
          │  服務層 services │ │  資料模型 models   │
          │  YOLOService     │ │  DataSource       │
          │  RealtimeService │ │  AnalysisTask     │
          │  VideoAnalysis   │ │  DetectionResult  │
          └──────────┬─────┘ │  SystemConfig ...  │
                     │        └───────────┬────────┘
               ┌─────▼────────┐           │
               │  PostgreSQL   │           │
               │ (async SQLAlchemy)        │
               └───────────────────────────┘
```

## �️ 資料庫核心表

| 表 | 角色 | 說明 |
|----|------|------|
| `data_sources` | 資料來源 | 攝影機或影片 (`source_type = camera | video_file`) |
| `analysis_tasks` | 分析任務 | 與來源關聯，追蹤解析度/FPS/時長 |
| `detection_results` | 檢測結果 | 逐幀物件辨識輸出 |
| `system_config` | 系統設定/警報規則 | 同時儲存傳統 KV 配置與警報/線段/區域等 JSON 設定 |

任務狀態流：`pending → running ↔ paused → completed / failed`

## 🎥 資料來源類型

- `camera`：以 `config.device_id` 或 `config.url` 標記裝置
- `video_file`：上傳即建立來源，`config` 保存：
  - `path`、`original_name`、`duration`、`fps`、`resolution`、`frame_count`、`upload_time`

## 📦 上傳與儲存路徑

統一路徑（已改為固定絕對路徑）：
```
D:/project/system/uploads/
└── videos/
```
集中常數：`app/core/paths.py`
- `PROJECT_ROOT`
- `UPLOADS_DIR`
- `VIDEOS_DIR`
- `DETECTIONS_DIR`（GUI / 即時任務縮圖：`uploads/detections/<task_id>/*.jpg`）

上傳 API：
- `POST /api/v1/frontend/data-sources/upload/video`
  - 回傳 `source_id` 與解析度資訊
影片列表 API（多版本並存）：
- `GET /api/v1/frontend/video-list`
- `GET /api/v1/frontend/videos`（簡化）
- `GET /api/v1/video-list/`
- `GET /api/v1/video-list/simple`

## 🤖 推論與分析流程

1. 建立資料來源（攝影機掃描或影片上傳）
2. 建立分析任務（即時 / 影片）
3. 實際處理服務：
   - 即時：`realtime_detection_service.py`
   - 影片：`video_analysis_service.py` / `enhanced_video_analysis_service.py`
4. YOLO 推論：`yolo_service.py`
5. 結果寫入 `detection_results`
6. 前端透過儀表板 / 任務列表顯示

## 📊 系統統計

`GET /api/v1/frontend/stats` 回傳（常見字段）：
- `cpu_usage`, `memory_usage`, `gpu_usage`, `network_usage`
- `total_cameras`, `online_cameras`
- `active_tasks`
- `system_uptime_seconds`
- `last_updated`

React 前端使用 React Query 定時輪詢顯示。

## 🗄️ 資料庫查詢 API（Unity / 協作者專用）

所有「讀資料」的 REST API 已統一掛在 `GET /api/v1/database/*`，每張表各對應一支端點，回傳格式固定為：

```jsonc
{
  "success": true,
  "data": [...],        // 查到的資料列
  "pagination": {...},  // limit / offset / total / has_next / has_prev
  "filters": {...},     // 實際生效的查詢條件
  "timestamp": "ISO8601"
}
```

| 資料表 | 端點 | 常用查詢參數 | 說明 |
|--------|------|--------------|------|
| `data_sources` | `GET /api/v1/database/data-sources` | `source_type`, `status`, `keyword`, `limit`, `offset` | 來源清單，提供名稱模糊搜尋 |
| `analysis_tasks` | `GET /api/v1/database/tasks` | `task_type`, `status`, `start_date`, `end_date`, `limit`, `offset` | 任務主檔（既有端點，保留） |
| `detection_results` | `GET /api/v1/database/detection-results` | `task_id`, `object_type`, `min_confidence`, `start_date`, `end_date`, `limit`, `offset` | 任務逐幀結果（既有端點，保留） |
| `line_crossing_events` | `GET /api/v1/database/line-events` | `task_id`, `line_id`, `start_time`, `end_time`, `limit`, `offset` | 穿越線事件 |
| `zone_dwell_events` | `GET /api/v1/database/zone-events` | `task_id`, `zone_id`, `start_time`, `end_time`, `limit`, `offset` | 區域停留事件 |
| `speed_events` | `GET /api/v1/database/speed-events` | `task_id`, `min_speed`, `start_time`, `end_time`, `limit`, `offset` | 速度異常事件 |
| `task_statistics` | `GET /api/v1/database/task-statistics` | `task_id`, `limit`, `offset` | 最新任務統計（fps、人數、分區統計等） |
| `system_config` | `GET /api/v1/database/system-config` | `key`, `config_type`, `limit`, `offset` | 取得指定類型 (如 `kv`, `alert_rule`) 的配置 |
| `users` | `GET /api/v1/database/users` | `role`, `is_active`, `limit`, `offset` | 只回傳公開欄位（不包含 `password_hash`） |

> 時間參數同時支援 `YYYY-MM-DD` 與完整 ISO 8601，適合 Unity 端直接帶 `DateTime.ToString("o")`。

## 🔐 系統控制

- `POST /api/v1/frontend/system/shutdown`
  - 延遲背景執行（回應先返回）
  - Windows：`GenerateConsoleCtrlEvent` → fallback `taskkill`
  - Linux/macOS：`SIGINT`

## � 主要 API 分類速覽

| 類別 | 範例端點 |
|------|----------|
| 健康檢查 | `/api/v1/health` `/api/v1/health/system` |
| 系統統計 | `/api/v1/frontend/stats` |
| 資料來源 | `GET/POST/PUT/DELETE /api/v1/frontend/data-sources/*` |
| 影片上傳 | `POST /api/v1/frontend/data-sources/upload/video` |
| 影片列表 | `GET /api/v1/frontend/video-list` |
| 任務管理 | `/api/v1/new-analysis/*`, `/api/v1/frontend/tasks` |
| 即時攝影機 | `/api/v1/realtime/*`（依實作狀態） |
| 系統控制 | `POST /api/v1/frontend/system/shutdown` |

## 🧠 YOLO 模型

- 權重檔案：`yolo11n.pt`
- 可透過環境變數指定：`MODEL_PATH`
- 推論封裝：`app/services/yolo_service.py`

## 🧩 服務層（部分）

| 檔案 | 用途 |
|------|------|
| `camera_stream_manager.py` | 攝影機串流資源管理 |
| `realtime_detection_service.py` | 即時辨識核心 |
| `video_analysis_service.py` | 基本影片分析流程 |
| `enhanced_video_analysis_service.py` | 強化版影片分析（效能/穩定性） |
| `analytics_service.py` | 彙總與統計 |
| `database_service.py` / `new_database_service.py` | 資料來源與任務 CRUD |
| `async_queue_manager.py` | 非同步任務排程基礎 |

## 🖥️ 前端（React）

- 技術：Vite + React + TypeScript
- Hooks：`react web/src/hooks/react-query-hooks.ts`
- 已實作：系統統計、影片上傳（建立 data_source）、任務與影片刪除（部分）
- 待擴充：資料來源 CRUD、即時視覺化串流

## 🧪 測試 / 除錯腳本（`scripts/`）

- `test_video_upload.py`：上傳 + 驗證
- `test_video_directory.py`：列出影片
- `test_multiple_upload.py`：批次測試
- `test_delete_video.py`：刪除驗證
- `simple_file_api.py`：最小化影片列出 API

## 🛡️ 刪除策略建議（video_file）

建議刪除條件：
- 無任務引用，或所有引用任務為 `completed` / `failed`

避免刪除：
- 仍有 `running` / `pending` / `paused` 任務引用

## 🚨 常見風險與建議

| 風險 | 建議 |
|------|------|
| 影片大量堆積 | 掛載外部儲存 / 週期清理 |
| 串流卡頓 | 避免重複開啟同一裝置索引 |
| 任務泛濫 | 加入併發限制（待實作） |
| 強制關閉中斷 | 未來可加入任務恢復機制 |

## � 專案節錄結構（更新）

```
project/
├── main.py
├── pyproject.toml
├── yolo11n.pt
├── uploads/
│   └── videos/              # 影片儲存（絕對路徑 D:/project/system/uploads/videos）
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── paths.py         # ← 新增：集中路徑設定
│   ├── api/v1/
│   │   ├── frontend.py
│   │   ├── new_analysis.py
│   │   ├── video_list.py
│   │   └── endpoints/
│   ├── models/
│   ├── services/
│   ├── utils/
│   └── websocket/
├── react web/ (或 client/)
├── docs/
└── scripts/
```

## 🔮 Roadmap（建議）

- WebSocket 推播即時檢測結果
- `behavior_events` 表啟用
- 前端完整化資料來源 CRUD
- 任務恢復 / 暫停續跑
- 模型多版本管理 UI
- HLS / WebRTC 串流預覽
- 影片轉碼 / 快速預覽

---

**🎉 系統已完成核心框架，可持續擴充！**

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
已幫你在專案底下新增一套 Docker 化的資料庫配置，路徑在 deployment/db/：

docker-compose.yml：使用 postgres:16-alpine，自動載入初始化 SQL，並把資料掛在 volume yolo_pgdata。
.env.db：預設帳號 yolo_user、密碼 please_change_me、資料庫 yolo_analysis（記得改成自己要的值）。
init.sql：照你調整後的 schema 產生所有資料表（analysis_tasks、detection_results、line_crossing_events、zone_dwell_events、speed_events、data_sources、users、system_config 等）以及常用索引。
使用方式：

轉到 deployment/db 目錄。
執行 docker compose up -d 就會啟動新的 PostgreSQL。
若要進入資料庫，可用 docker exec -it yolo_analysis_db psql -U yolo_user -d yolo_analysis。
將應用程式的連線字串改成 postgresql://yolo_user:please_change_me@localhost:5432/yolo_analysis（或依你修改 .env.db 的設定）。




docker compose down -v      # 會停止容器並刪除 volume
docker volume ls | findstr yolo_pgdata  # 確認沒有殘留
docker compose up -d --build
