# YOLOv11 影片分析系統 使用指南

## 🚀 快速開始

### 1. 啟動系統
```bash
python start.py
```

### 2. 測試系統功能
```bash
python test_analysis.py
```

### 3. 訪問 API 文檔
- 主要文檔：http://localhost:8001/docs
- 替代文檔：http://localhost:8001/redoc

## 🎯 主要功能

### 攝影機輸入分析
- **端點**：`POST /api/v1/analysis/camera/{camera_id}`
- **參數**：
  - `camera_id`: 攝影機ID (通常 0 是預設攝影機)
  - `duration`: 分析持續時間(秒，預設60秒)

### 影片檔案分析
- **上傳分析**：`POST /api/v1/analysis/video/upload`
  - 支援格式：mp4, avi, mov, mkv, wmv, flv, webm
  - 檔案大小限制：100MB
  
- **本地檔案分析**：`POST /api/v1/analysis/video/local`
  - 分析伺服器上的影片檔案

### 影片標註功能 🆕
- **上傳影片標註**：`POST /api/v1/analysis/video/annotate/upload`
  - 生成帶有物件ID、類型、移動方向標註的影片
  - 檔案大小限制：200MB
  
- **本地檔案標註**：`POST /api/v1/analysis/video/annotate/local`
  - 標註伺服器上的影片檔案

- **列出標註影片**：`GET /api/v1/analysis/annotated-videos/list`
  - 查看所有已生成的標註影片

### 分析狀態監控
- **即時狀態**：`GET /api/v1/analysis/status`
- **最新結果**：`GET /api/v1/analysis/results/latest`
- **停止分析**：`POST /api/v1/analysis/stop`

## 📊 輸出資料格式

### CSV 分析資料
系統會自動生成兩個 CSV 檔案：

#### 檢測記錄 (detections_YYYYMMDD_HHMMSS.csv)
記錄每個檢測到的物件詳細資訊，包含：
- 時間戳、幀編號、物件ID、類型
- 邊界框座標、中心點、尺寸、面積
- 區域標籤、速度、移動方向等

#### 行為事件 (behaviors_YYYYMMDD_HHMMSS.csv)  
記錄檢測到的行為事件，包含：
- 停留時間、異常行為、區域進入事件
- 擁擠檢測、位置資訊、持續時間等

### 標註影片 🆕
系統會生成帶有視覺標註的影片檔案：
- **物件追蹤**：每個物件都有固定顏色的邊界框和唯一ID
- **移動軌跡**：顯示物件的移動路徑
- **方向指示**：箭頭顯示移動方向（↑↓←→↗↘↙↖）
- **速度資訊**：顯示物件的移動速度
- **統計資訊**：幀數、物件數量、解析度等

標註影片會儲存在 `annotated_videos/` 目錄中，檔名格式為：
`annotated_{原檔名}_{時間戳}.mp4`

## 🔍 支援的行為類型

### 1. 停留檢測 (loitering)
- **觸發條件**：物件在同一區域停留超過10秒且移動緩慢
- **輸出資訊**：停留時間、位置、區域

### 2. 異常速度 (abnormal_speed)  
- **觸發條件**：物件移動速度超過100 pixels/sec
- **輸出資訊**：速度值、移動方向

### 3. 區域進入 (zone_entry)
- **觸發條件**：物件進入新的檢測區域
- **輸出資訊**：來源區域、目標區域

### 4. 擁擠檢測 (crowding)
- **觸發條件**：單一區域內物件數量≥5個
- **輸出資訊**：物件數量、區域

## 🗺️ 預設檢測區域

系統自動建立以下區域：
- **entrance**: 畫面上方1/4區域
- **center_area**: 畫面中央區域  
- **exit**: 畫面下方1/4區域
- **left_area**: 畫面左側區域
- **right_area**: 畫面右側區域

## 🎬 測試影片

運行 `python test_analysis.py` 會自動生成：
1. **basic_movement_test.mp4** - 基礎移動物件測試
2. **crowding_scenario_test.mp4** - 擁擠場景測試

## 📝 使用範例

### Python 客戶端範例
```python
import requests
import json

# 1. 攝影機分析
response = requests.post(
    "http://localhost:8001/api/v1/analysis/camera/0",
    data={"duration": 30}
)
result = response.json()

# 2. 上傳影片分析
with open("test_video.mp4", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:8001/api/v1/analysis/video/upload",
        files=files
    )
    result = response.json()

# 3. 檢查分析狀態
response = requests.get("http://localhost:8001/api/v1/analysis/status")
status = response.json()
```

### curl 範例
```bash
# 攝影機分析
curl -X POST "http://localhost:8001/api/v1/analysis/camera/0" \
     -F "duration=60"

# 上傳影片分析
curl -X POST "http://localhost:8001/api/v1/analysis/video/upload" \
     -F "file=@test_video.mp4"

# 上傳影片標註 🆕
curl -X POST "http://localhost:8001/api/v1/analysis/video/annotate/upload" \
     -F "file=@test_video.mp4"

# 列出標註影片
curl "http://localhost:8001/api/v1/analysis/annotated-videos/list"

# 檢查狀態
curl "http://localhost:8001/api/v1/analysis/status"
```

## 🔧 進階設定

### 調整檢測參數
編輯 `app/services/video_analysis_service.py`:
```python
# 行為分析參數
self.loitering_threshold = 10.0  # 停留時間門檻(秒)
self.speed_threshold = 100.0     # 異常速度門檻
self.crowd_threshold = 5         # 擁擠門檻
```

### 自訂檢測區域
```python
# 新增自訂區域
zone_manager.add_zone("custom_area", [
    (100, 100), (400, 100), 
    (400, 300), (100, 300)
])
```

## 📊 資料庫整合建議

生成的 CSV 檔案可以直接匯入各種資料庫：

### PostgreSQL
```sql
CREATE TABLE detections (
    timestamp TIMESTAMP,
    frame_number INTEGER,
    object_id INTEGER,
    object_type VARCHAR(50),
    confidence REAL,
    bbox_x1 REAL, bbox_y1 REAL, bbox_x2 REAL, bbox_y2 REAL,
    center_x REAL, center_y REAL,
    width REAL, height REAL, area REAL,
    zone VARCHAR(50),
    speed REAL,
    direction REAL,
    source VARCHAR(100)
);

COPY detections FROM '/path/to/detections.csv' DELIMITER ',' CSV HEADER;
```

### MySQL  
```sql
LOAD DATA INFILE '/path/to/detections.csv'
INTO TABLE detections
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
```

## 🚨 故障排除

### 常見問題
1. **攝影機無法開啟**：檢查攝影機ID，嘗試其他數字(0,1,2...)
2. **影片分析失敗**：確認影片格式和檔案完整性
3. **CSV檔案為空**：檢查YOLO模型是否正確載入
4. **記憶體不足**：降低影片解析度或縮短處理時間

### 日誌檢查
```bash
# 查看系統日誌
tail -f logs/app.log
```

## 📈 效能優化

- **GPU加速**：安裝CUDA版本的PyTorch
- **多執行緒**：調整ThreadPoolExecutor的max_workers
- **幀採樣**：修改幀處理間隔(目前每3幀處理1幀)
- **模型選擇**：使用更輕量的模型(yolo11n.pt vs yolo11x.pt)
