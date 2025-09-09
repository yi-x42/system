# AI 程式設計助理指南：YOLOv11 全端分析系統

歡迎！本指南旨在幫助您快速理解此專案的架構和工作流程。

## 🏗️ 系統架構概覽

本專案是一個全端應用程式，包含一個 React 前端和一個 Python FastAPI 後端。

-   **React 前端 (`/react web`)**: 使用 Vite、TypeScript 和 `shadcn/ui` 元件庫建構的現代化使用者介面。
    -   **狀態管理**: 使用 `@tanstack/react-query` 處理伺服器狀態（資料獲取、快取）。設定檔在 `react web/src/main.tsx`，自訂 hooks 在 `react web/src/hooks/react-query-hooks.ts`。
    -   **API 客戶端**: 在 `react web/src/lib/api.ts` 中設定，與後端 `http://localhost:8001` 通信。

-   **FastAPI 後端 (`/yolo_backend`)**: 提供物件辨識、資料庫操作和 API 端點。
    -   **應用程式入口**: `yolo_backend/app/main.py`。
    -   **核心模型**: 使用 `ultralytics` 搭配 `yolo11n.pt` 模型。
    -   **資料庫**: 使用 PostgreSQL
    ## 1. analysis_tasks (分析任務表)
id               INTEGER      主鍵
task_type        VARCHAR(20)  'realtime_camera' | 'video_file'
status           VARCHAR(20)  'pending' | 'running' | 'completed' | 'failed'
source_info      JSON         攝影機配置或影片檔案路徑（不再包含解析度資訊）
source_width     INTEGER      來源影像寬度（專用欄位）
source_height    INTEGER      來源影像高度（專用欄位）
source_fps       FLOAT        來源影像幀率（專用欄位）
start_time       TIMESTAMP    任務開始時間
end_time         TIMESTAMP    任務結束時間
created_at       TIMESTAMP    建立時間

## 2. detection_results (檢測結果表)
id               INTEGER      主鍵
task_id          INTEGER      關聯 analysis_tasks.id
frame_number     INTEGER      幀編號
timestamp        TIMESTAMP    檢測時間
object_type      VARCHAR(50)  物件類型 (person, car, bike...)
confidence       FLOAT        信心度 (0.0-1.0)
bbox_x1          FLOAT        邊界框左上角X
bbox_y1          FLOAT        邊界框左上角Y
bbox_x2          FLOAT        邊界框右下角X
bbox_y2          FLOAT        邊界框右下角Y
center_x         FLOAT        中心點X座標
center_y         FLOAT        中心點Y座標

## 3. behavior_events (行為事件表)   (程式先不要做這部分)
id               INTEGER      主鍵
task_id          INTEGER      關聯 analysis_tasks.id
event_type       VARCHAR(50)  'crowding' | 'abnormal_speed' | 'zone_intrusion'
severity         VARCHAR(20)  'low' | 'medium' | 'high'
description      TEXT         事件描述
confidence_level FLOAT        事件信心度
timestamp        TIMESTAMP    事件發生時間
additional_data  JSON         額外事件資料

## 4. data_sources (資料來源表)
id               INTEGER      主鍵
source_type      VARCHAR(20)  'camera' | 'video_file'
name             VARCHAR(100) 來源名稱
config           JSON         配置資訊（IP、檔案路徑等）
status           VARCHAR(20)  'active' | 'inactive' | 'error'
last_check       TIMESTAMP    最後檢查時間
created_at       TIMESTAMP    建立時間

## 5. users (使用者表)  (程式先不要做這部分)
id               INTEGER      主鍵
username         VARCHAR(50)  使用者名稱
password_hash    VARCHAR(255) 密碼雜湊
role             VARCHAR(20)  'admin' | 'operator' | 'viewer'
is_active        BOOLEAN      是否啟用
last_login       TIMESTAMP    最後登入時間
created_at       TIMESTAMP    建立時間

## 6. system_config (系統配置表)
id               INTEGER      主鍵
config_key       VARCHAR(100) 配置鍵值
config_value     TEXT         配置值
description      TEXT         說明
updated_at       TIMESTAMP    更新時間

==========================================================
📊 關聯關係說明
==========================================================

1. data_sources → analysis_tasks (1:N)
關係: 一個資料來源可以被多個分析任務使用
實現: analysis_tasks.source_info (JSON) 包含 source_id

範例:
data_sources.id = 1 (大廳攝影機A)
  ├── analysis_tasks.id = 10 (今天上午的監控)
  ├── analysis_tasks.id = 11 (今天下午的監控)
  └── analysis_tasks.id = 12 (昨天晚上的監控)

2. analysis_tasks → detection_results (1:N)
關係: 一個分析任務產生多個檢測結果
實現: detection_results.task_id → analysis_tasks.id (外鍵)

範例:
analysis_tasks.id = 10 (30分鐘的即時監控)
  ├── detection_results (54,000筆記錄) # 30分鐘 × 30fps × 60秒
  └── 每筆記錄包含: 物件類型、座標、信心度等

3. analysis_tasks → behavior_events (1:N)
關係: 一個分析任務可能產生多個行為事件
實現: behavior_events.task_id → analysis_tasks.id (外鍵)

範例:
analysis_tasks.id = 10
  ├── behavior_events.id = 50 (10:15發生聚集事件)
  ├── behavior_events.id = 51 (10:20發生異常速度)
  └── behavior_events.id = 52 (10:25發生區域入侵)

4. users → analysis_tasks (1:N) - 未來擴展
關係: 一個使用者可以建立多個分析任務
可能實現: analysis_tasks 新增 user_id 欄位

範例:
users.id = 1 (管理員張三)
  ├── analysis_tasks.id = 10 (建立的監控任務A)
  ├── analysis_tasks.id = 11 (建立的監控任務B)
  └── analysis_tasks.id = 12 (建立的監控任務C)

5. system_config → 全域設定 (獨立表)
關係: 系統配置影響所有其他功能
使用方式: 其他模組讀取配置參數

-   **根目錄腳本**: 包含用於管理全系統的腳本，例如啟動和測試。

## 🔧 關鍵開發工作流程

### **主要啟動流程 (最重要)**

要同時啟動後端和前端開發伺服器，請務必在 **專案根目錄** 執行單一命令：

```bash
# 此命令會同時啟動 FastAPI 後端 (8001 埠) 和 React 前端 (3000 埠)
python start.py
```

`start.py` 腳本會自動處理 Python 和 Node.js 的依賴檢查與安裝。

### **依賴管理**

-   **後端 (Python)**: 依賴項目定義在 `requirements.txt` 中，使用 `pip` 管理。
-   **前端 (Node.js)**: 依賴項目定義在 `react web/package.json` 中，使用 `npm` 管理。

### **測試**

本專案使用根目錄下的 `quick_*.py` 或 `test_*.py` 腳本進行快速的整合或功能測試，而非使用 `pytest` 等正式框架。
新增的測試用腳本或是快速啟動等腳本，請放在"D:\project\system\test、simple"資料夾中。
功能測試報告請放在這個"D:\project\system\報告"資料夾中。
```bash
# 範例：執行一個簡單的 API 測試
python simple_api_test.py
```

## 🎯 專案特有模式與慣例

### 1. 運行時間計算

系統運行時間由後端計算，以避免前端重新整理時重置計時器。
-   **計時邏輯**: `yolo_backend/app/core/uptime.py` 在後端程序啟動時記錄時間。
-   **API 端點**: `/api/v1/frontend/stats` 會回傳 `system_uptime_seconds` 欄位。
-   **前端格式化**: React 前端在 `Dashboard.tsx` 中使用 `formatUptime` 函式將秒數轉換為「X 天 Y 分鐘」或「Z 分鐘」的格式。

### 2. 網絡配置 (Radmin VPN)

系統針對 Radmin VPN 環境進行了優化，以便團隊協作。
-   **服務監聽**: 後端服務監聽 `0.0.0.0:8001`，允許來自區域網路的存取。
-   **固定 IP**: `26.86.64.166` 是一個常用於團隊測試的 Radmin IP。

### 3. Unity 座標系統

與 Unity 引擎整合時，座標系統有特殊規範。
-   **原點**: 螢幕左下為 `(0, 0)`。

## 💡 開發建議

-   **修改前端**: 當您新增需要與後端互動的功能時，請先在 `react web/src/hooks/react-query-hooks.ts` 中建立一個新的 hook 來獲取資料。
-   **修改後端 API**: 如果您修改了 `yolo_backend` 中的 Pydantic 模型或資料庫結構，請記得更新相關的 API 端點和前端的 TypeScript 型別定義。
-   **啟動方式**: **請務必使用 `python start.py`** 來啟動開發環境，不要單獨執行 `uvicorn` 或 `npm run dev`，否則會導致跨來源 (CORS) 或連線問題。

再把react網站的模擬數據替換為真實功能的時後 不要去改變整體排版 希望照著原有的架構下去做變更
