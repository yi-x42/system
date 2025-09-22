# YOLOv11 數位雙生分析系統 - AI 編程助手指導

## 🏗️ 系統架構概覽

這是一個基於 **YOLOv11** 的物件辨識與分析系統，專為 **Radmin 網絡環境** 優化，支援團隊協作。

### 核心組件
- **FastAPI 後端**: `app/main.py` 為應用程式入口點
- **YOLOv11 模型**: 使用 `ultralytics` 套件，模型檔案為 `yolo11n.pt`
- **PostgreSQL 資料庫**: 儲存分析記錄、檢測結果、行為事件
- **Radmin VPN**: 支援 IPv4/IPv6 團隊網絡存取

### 專案結構重點
```
app/
├── api/v1/endpoints/      # API 端點實作
├── core/                  # 配置、資料庫、日誌
├── models/               # Pydantic 資料模型
├── services/             # 業務邏輯服務
└── utils/                # 工具函數
```

## 🔧 關鍵開發工作流程

### 啟動系統
```bash
python start.py           # 自動檢查依賴並啟動服務
python monitor.py         # 系統監控
python diagnose.py        # 問題診斷
```

### 資料庫操作
```bash
python create_database.py     # 建立資料庫結構
python clear_database.py      # 清除資料庫
python init_database.py       # 初始化資料庫
```

### 測試與除錯
```bash
python test_api.py            # API 功能測試
python test_unity_coordinates.py  # Unity 座標轉換測試
python test_simple.py        # 基本功能測試
```

## 🎯 專案特有模式與慣例

### 1. 網絡配置模式
- **主要服務**: `0.0.0.0:8001` (允許 Radmin 網絡存取)
- **固定 Radmin IP**: `26.86.64.166` (硬編碼在啟動訊息中)
- **雙協議支援**: IPv4 + IPv6 存取

### 2. 座標系統規範
- **Unity 整合**: 使用 Unity 螢幕座標系統 (左下角為原點，Y軸向上)
- **邊界框格式**: `(x1,y1) -> (x2,y2)` 像素單位
- **座標轉換**: 參考 `test_unity_coordinates.py` 和 `UNITY_SCREEN_COORDINATE_GUIDE.md`

### 3. 依賴檢查機制
系統具備自動依賴檢查功能 (`start.py`):
```python
critical_packages = {
    'fastapi': 'FastAPI 框架',
    'ultralytics': 'YOLOv11 模型',
    'sqlalchemy': 'SQLAlchemy ORM',
    'asyncpg': 'PostgreSQL 異步驅動',
    # ...
}
```

### 4. 資料庫設計模式
- **分析記錄表**: `analysis_records` - 影片分析基本資訊
- **檢測結果表**: `detection_results` - 物件檢測詳細資訊  
- **行為事件表**: `behavior_events` - 行為分析結果
- **關聯設計**: 使用 SQLAlchemy ORM 進行關聯管理

## 🚨 常見問題與解決方案

### 1. 缺少 psycopg2 套件
**錯誤訊息**: `ModuleNotFoundError: No module named 'psycopg2'`
**解決方案**:
```bash
pip install psycopg2-binary
# 或使用 Python 環境工具
install_python_packages(["psycopg2-binary"])
```
**根本原因**: PostgreSQL 需要同步和異步兩種驅動程式 (`psycopg2` + `asyncpg`)

### 2. YOLO 模型載入失敗
設定環境變數跳過初始載入:
```bash
export SKIP_YOLO_INIT=true
```

### 3. 網絡連接問題
- 檢查防火牆設定: `setup_firewall.bat`
- IPv6 存取問題: 參考 `TROUBLESHOOTING_IPv6.md`
- Radmin 連接: 參考 `RADMIN_CONNECTION_GUIDE.txt`

### 4. 資料庫連接問題
檢查 `.env` 檔案中的資料庫配置:
```properties
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/yolo_analysis
POSTGRES_PASSWORD=your_actual_password
```

## 📝 重要配置檔案

- **`.env`**: 環境配置 (自動生成)
- **`requirements.txt`**: Python 依賴套件
- **各種指南文件**: `*_GUIDE.md` 和 `*_GUIDE.txt`

## 🔗 API 存取模式

### 本地開發
- API 文檔: `http://localhost:8001/docs`
- 健康檢查: `http://localhost:8001/api/v1/health`

### 團隊存取 (透過 Radmin)
- API 文檔: `http://26.86.64.166:8001/docs`
- 資料總覽: `http://26.86.64.166:8001/api/v1/data/summary`
- 物件搜尋: `http://26.86.64.166:8001/api/v1/data/search?keyword=person`

## 💡 開發建議

1. **啟動前檢查**: 總是使用 `python start.py` 而非直接執行 uvicorn
2. **資料庫變更**: 修改模型後執行相應的 `test_` 檔案驗證
3. **網絡測試**: 修改網絡相關功能後檢查 IPv4/IPv6 雙協議存取
4. **Unity 整合**: 座標相關修改需執行 `test_unity_coordinates.py`
