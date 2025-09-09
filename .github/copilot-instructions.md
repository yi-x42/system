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
-   **原點**: 螢幕左下角為 `(0, 0)`。
-   **格式**: 邊界框使用像素單位的 `(x1, y1)` 到 `(x2, y2)`。
-   **參考**: `test_unity_coordinates.py` 和 `UNITY_SCREEN_COORDINATE_GUIDE.md`。

## 💡 開發建議

-   **修改前端**: 當您新增需要與後端互動的功能時，請先在 `react web/src/hooks/react-query-hooks.ts` 中建立一個新的 hook 來獲取資料。
-   **修改後端 API**: 如果您修改了 `yolo_backend` 中的 Pydantic 模型或資料庫結構，請記得更新相關的 API 端點和前端的 TypeScript 型別定義。
-   **啟動方式**: **請務必使用 `python start.py`** 來啟動開發環境，不要單獨執行 `uvicorn` 或 `npm run dev`，否則會導致跨來源 (CORS) 或連線問題。

再把react網站的模擬數據替換為真實功能的時後 不要去改變整體排版 希望照著原有的架構下去做變更