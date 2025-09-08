# YOLOv11 數位雙生分析系統 - 資料庫整合版

## 🎯 系統概述

這是一個基於 YOLOv11 的智能影片分析系統，整合了 PostgreSQL 資料庫，提供完整的影片分析、物件檢測、行為識別和資料儲存功能。

## 📋 主要功能

### 🔍 核心分析功能
- **物件檢測**: 基於 YOLOv11 的高精度物件識別
- **多目標追蹤**: 物件軌跡追蹤和 ID 管理
- **行為分析**: 智能行為模式識別
- **區域監控**: 可自定義監控區域
- **影片標註**: 生成帶標註的分析影片

### 🗄️ 資料庫功能
- **分析記錄管理**: 完整的分析歷史追蹤
- **檢測結果存儲**: 詳細的物件檢測資料
- **行為事件記錄**: 行為分析結果保存
- **統計報表**: 分析統計和趨勢報告
- **資料查詢**: 靈活的資料檢索介面

### 🌐 API 介面
- **RESTful API**: 標準化的 REST 介面
- **檔案上傳**: 支援多種影片格式上傳
- **本地檔案分析**: 直接分析服務器本地檔案
- **即時狀態**: 分析進度和狀態監控
- **資料匯出**: CSV 格式的結果匯出

## 🛠️ 系統架構

```
YOLOv11 數位雙生分析系統
├── FastAPI 網頁框架
├── YOLOv11 AI 模型
├── PostgreSQL 資料庫
├── SQLAlchemy ORM
└── 非同步處理系統
```

## 📦 安裝要求

### Python 依賴
```bash
pip install -r requirements.txt
```

### 主要套件
- `fastapi`: 網頁框架
- `ultralytics`: YOLOv11 模型
- `sqlalchemy[asyncio]`: 資料庫 ORM  
- `asyncpg`: PostgreSQL 驅動
- `opencv-python`: 影像處理
- `pandas`: 資料處理
- `numpy`: 數值計算

### 資料庫設定
1. 安裝 PostgreSQL
2. 創建資料庫: `yolo_analysis`
3. 設定連接參數:
   ```
   Host: localhost
   Port: 5432
   Database: yolo_analysis
   Username: postgres
   Password: 49679904
   ```

## 🚀 快速開始

### 1. 初始化資料庫
```bash
python init_database.py
```

### 2. 檢查系統狀態
```bash
python test_complete_system.py
```

### 3. 啟動服務
```bash
python start_server.py
```
或
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 訪問 API 文檔
瀏覽器開啟: `http://localhost:8000/docs`

## 📚 API 端點

### 🔄 傳統分析端點
- `POST /api/v1/analysis/upload` - 上傳影片分析
- `POST /api/v1/analysis/local` - 本地檔案分析
- `POST /api/v1/analysis/annotate` - 影片標註分析

### 🗄️ 資料庫整合端點
- `POST /api/v1/analysis/upload-with-database` - 上傳並保存到資料庫
- `POST /api/v1/analysis/local-with-database` - 本地分析並保存到資料庫
- `GET /api/v1/analysis/history` - 獲取分析歷史
- `GET /api/v1/analysis/details/{id}` - 獲取分析詳情
- `GET /api/v1/analysis/statistics` - 獲取統計資訊
- `GET /api/v1/analysis/detections/{id}` - 獲取檢測結果

### 📊 系統管理端點
- `GET /api/v1/analysis/status` - 系統狀態
- `GET /api/v1/analysis/supported-formats` - 支援格式
- `POST /api/v1/analysis/stop` - 停止分析

## 💾 資料庫結構

### 分析記錄表 (analysis_records)
```sql
- id: 主鍵
- video_path: 影片路徑
- video_name: 影片名稱  
- analysis_type: 分析類型
- status: 處理狀態
- total_detections: 總檢測數
- analysis_duration: 分析耗時
- created_at: 創建時間
```

### 檢測結果表 (detection_results)  
```sql
- id: 主鍵
- analysis_id: 關聯分析記錄
- frame_number: 幀編號
- object_type: 物件類型
- confidence: 信心度
- bbox_x1, y1, x2, y2: 邊界框座標
- zone: 所在區域
- speed: 移動速度
```

### 行為事件表 (behavior_events)
```sql
- id: 主鍵  
- analysis_id: 關聯分析記錄
- event_type: 事件類型
- timestamp: 發生時間
- position_x, y: 事件位置
- duration: 持續時間
```

## 🎯 使用範例

### 1. 上傳影片並分析
```python
import requests

# 上傳檔案
files = {'file': open('test_video.mp4', 'rb')}
data = {
    'confidence_threshold': 0.5,
    'track_objects': True,
    'detect_behaviors': True,
    'annotate_video': False
}

response = requests.post(
    'http://localhost:8000/api/v1/analysis/upload-with-database',
    files=files,
    data=data
)

result = response.json()
analysis_id = result['analysis_record_id']
```

### 2. 查詢分析結果
```python
# 獲取分析詳情
response = requests.get(f'http://localhost:8000/api/v1/analysis/details/{analysis_id}')
details = response.json()

# 獲取檢測結果
response = requests.get(f'http://localhost:8000/api/v1/analysis/detections/{analysis_id}')
detections = response.json()
```

### 3. 查看統計資訊
```python
response = requests.get('http://localhost:8000/api/v1/analysis/statistics')
stats = response.json()
```

## 🔧 設定檔案

### 環境變數
```bash
# 資料庫設定
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres  
POSTGRES_PASSWORD=49679904
POSTGRES_DB=yolo_analysis
POSTGRES_PORT=5432

# AI 模型設定
MODEL_PATH=yolo11n.pt
DEVICE=auto
CONFIDENCE_THRESHOLD=0.5

# 服務設定  
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 設定類別
系統使用 `app/core/config.py` 中的 `Settings` 類別管理所有設定。

## 📁 專案結構

```
yolo_backend/
├── app/                          # 主應用程式
│   ├── api/v1/endpoints/         # API 端點
│   ├── core/                     # 核心模組 (設定、資料庫、日誌)
│   ├── models/                   # 資料庫模型
│   ├── services/                 # 業務邏輯服務
│   └── utils/                    # 工具函數
├── analysis_results/             # 分析結果輸出
├── annotated_videos/            # 標註影片輸出  
├── logs/                        # 日誌檔案
├── test_videos/                 # 測試影片
├── uploads/                     # 上傳檔案
├── init_database.py            # 資料庫初始化
├── start_server.py             # 服務啟動腳本
└── requirements.txt            # Python 依賴
```

## 🧪 測試

### 系統測試
```bash
python test_complete_system.py
```

### 資料庫測試
```bash
python check_db_structure.py
```

### API 測試
```bash
# 啟動服務後訪問
curl http://localhost:8000/api/v1/analysis/statistics
```

## 🐛 故障排除

### 常見問題

1. **資料庫連接失敗**
   - 檢查 PostgreSQL 是否運行
   - 確認連接參數正確
   - 檢查防火牆設定

2. **YOLO 模型載入失敗**  
   - 確保 `yolo11n.pt` 檔案存在
   - 檢查檔案路徑設定
   - 確認網絡連接 (首次下載)

3. **記憶體不足**
   - 降低 `confidence_threshold`
   - 減少 `max_detections`
   - 使用較小的模型版本

4. **影片處理失敗**
   - 檢查影片格式支援
   - 確認檔案完整性
   - 檢查檔案權限

### 日誌位置
- 應用日誌: `logs/app.log`
- 資料庫日誌: SQLAlchemy 輸出
- 系統日誌: 控制台輸出

## 🔮 未來發展

### 計劃功能
- [ ] 即時串流分析
- [ ] 分布式處理支援  
- [ ] 更多 AI 模型整合
- [ ] 網頁管理介面
- [ ] 自動報表生成
- [ ] 多租戶支援

### 效能優化
- [ ] Redis 快取整合
- [ ] 資料庫連接池優化
- [ ] 異步任務隊列
- [ ] GPU 加速支援

## 📄 授權

此專案採用 MIT 授權條款。

## 🤝 貢獻

歡迎提交 Issues 和 Pull Requests！

---

**YOLOv11 數位雙生分析系統** - 讓 AI 影片分析更智能、更完整！
