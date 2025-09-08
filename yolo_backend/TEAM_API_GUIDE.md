# 🌐 團隊資料存取 API 使用指南

## 📋 概述

本文件說明如何透過 API 存取 YOLOv11 數位雙生分析系統的資料庫內容，讓團隊成員可以從不同電腦/網路環境存取分析結果。

## 🔌 連接資訊

### 本地測試環境
- **API 基礎網址**: `http://localhost:8001/api/v1/data`
- **文件頁面**: `http://localhost:8001/docs`

### 網路環境設定 (待設定)
```
# 替換 YOUR_SERVER_IP 為實際伺服器 IP
API 基礎網址: http://YOUR_SERVER_IP:8001/api/v1/data
文件頁面: http://YOUR_SERVER_IP:8001/docs
```

## 🛠 API 端點說明

### 1. 📊 資料庫概覽 
```
GET /api/v1/data/summary
```
**功能**: 取得資料庫整體統計資訊
**回應範例**:
```json
{
  "analysis_count": 25,
  "detection_count": 1520,
  "behavior_count": 89,
  "object_types": ["person", "car", "bicycle", "dog"],
  "last_analysis": "2025-01-20T10:30:00",
  "database_size": "15.2MB"
}
```

### 2. 📝 分析記錄清單
```
GET /api/v1/data/analyses?page=1&limit=20&status=completed
```
**功能**: 取得影片分析記錄清單
**參數**:
- `page`: 頁碼 (預設: 1)
- `limit`: 每頁筆數 (預設: 20，最大: 100)
- `status`: 狀態篩選 (completed, processing, error)

**回應範例**:
```json
{
  "analyses": [
    {
      "analysis_id": "a123456",
      "video_filename": "test_video.mp4", 
      "status": "completed",
      "start_time": "2025-01-20T10:00:00",
      "end_time": "2025-01-20T10:05:30",
      "detection_count": 45,
      "behavior_count": 3
    }
  ],
  "total": 25,
  "page": 1,
  "total_pages": 2
}
```

### 3. 🎯 檢測結果詳情
```
GET /api/v1/data/analyses/{analysis_id}/detections?page=1&limit=50
```
**功能**: 取得特定分析的檢測結果
**路徑參數**: `analysis_id` - 分析記錄 ID

**回應範例**:
```json
{
  "detections": [
    {
      "detection_id": "d789012",
      "class_name": "person",
      "confidence": 0.87,
      "bbox_x": 150,
      "bbox_y": 200, 
      "bbox_width": 80,
      "bbox_height": 180,
      "frame_number": 120,
      "timestamp": "2025-01-20T10:02:15"
    }
  ],
  "total": 45
}
```

### 4. 📈 檢測統計
```
GET /api/v1/data/detections/stats?days=30
```
**功能**: 取得檢測結果統計資訊
**參數**:
- `days`: 統計天數 (預設: 30)

**回應範例**:
```json
{
  "total_detections": 1520,
  "avg_confidence": 0.82,
  "top_detected_objects": [
    {"class_name": "person", "count": 680},
    {"class_name": "car", "count": 320},
    {"class_name": "bicycle", "count": 180}
  ],
  "detections_by_day": [...]
}
```

### 5. 🔄 行為事件
```
GET /api/v1/data/events?event_type=crowding&limit=10
```
**功能**: 取得行為事件記錄
**參數**:
- `event_type`: 事件類型篩選
- `limit`: 限制筆數

### 6. 🔍 搜尋功能
```
GET /api/v1/data/search?query=person&confidence_min=0.8&limit=20
```
**功能**: 搜尋檢測結果
**參數**:
- `query`: 搜尋關鍵字 (物件類型)
- `confidence_min`: 最小信心度
- `limit`: 限制筆數

### 7. 💾 CSV 匯出
```
GET /api/v1/data/export/csv?table=detections&limit=1000
```
**功能**: 匯出資料為 CSV 格式
**參數**:
- `table`: 資料表 (analyses, detections, events)
- `limit`: 限制筆數

## 💻 使用範例

### Python 範例
```python
import requests

# 設定 API 基礎網址
BASE_URL = "http://localhost:8001/api/v1/data"

# 1. 取得資料庫概覽
response = requests.get(f"{BASE_URL}/summary")
summary = response.json()
print(f"總分析數: {summary['analysis_count']}")

# 2. 取得最新 10 筆分析記錄
response = requests.get(f"{BASE_URL}/analyses?limit=10")
analyses = response.json()['analyses']

# 3. 取得特定分析的檢測結果
if analyses:
    analysis_id = analyses[0]['analysis_id']
    response = requests.get(f"{BASE_URL}/analyses/{analysis_id}/detections")
    detections = response.json()['detections']
    print(f"檢測結果數: {len(detections)}")

# 4. 搜尋人員檢測
response = requests.get(f"{BASE_URL}/search?query=person&confidence_min=0.8")
persons = response.json()['detections']

# 5. 匯出檢測資料為 CSV
response = requests.get(f"{BASE_URL}/export/csv?table=detections&limit=500")
with open("detections.csv", "wb") as f:
    f.write(response.content)
```

### JavaScript 範例
```javascript
const BASE_URL = "http://localhost:8001/api/v1/data";

// 取得資料庫概覽
fetch(`${BASE_URL}/summary`)
  .then(response => response.json())
  .then(data => {
    console.log('分析記錄數:', data.analysis_count);
    console.log('檢測結果數:', data.detection_count);
  });

// 取得分析記錄並顯示
fetch(`${BASE_URL}/analyses?limit=5`)
  .then(response => response.json()) 
  .then(data => {
    data.analyses.forEach(analysis => {
      console.log(`${analysis.video_filename} - ${analysis.status}`);
    });
  });
```

### cURL 範例
```bash
# 取得資料庫概覽
curl "http://localhost:8001/api/v1/data/summary"

# 取得分析記錄
curl "http://localhost:8001/api/v1/data/analyses?limit=10"

# 搜尋人員檢測
curl "http://localhost:8001/api/v1/data/search?query=person&confidence_min=0.8"

# 匯出 CSV
curl "http://localhost:8001/api/v1/data/export/csv?table=detections&limit=100" -o detections.csv
```

## 🔧 設定網路存取

### 1. 修改 FastAPI 主機設定
```python
# 在 start_server.py 或啟動腳本中
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0",  # 允許所有 IP 存取
        port=8001,
        reload=True
    )
```

### 2. 防火牆設定 (Windows)
```cmd
# 允許端口 8001
netsh advfirewall firewall add rule name="YOLO API" dir=in action=allow protocol=TCP localport=8001
```

### 3. 路由器設定
- 設定端口轉發: 外部 8001 → 內部伺服器 8001
- 取得外部 IP 位址給團隊成員使用

## 📞 支援與說明

### 常見問題

**Q: API 無法連接？**
A: 檢查：
1. FastAPI 服務是否正在運行 (`http://localhost:8001/docs`)
2. 防火牆是否允許端口 8001
3. IP 位址是否正確

**Q: 回應速度很慢？**
A: 
1. 使用 `limit` 參數限制資料筆數
2. 檢查資料庫連接狀況
3. 使用分頁功能避免一次載入過多資料

**Q: 需要更多欄位？**
A: API 回應包含主要欄位，如需完整欄位請聯繫開發者

### 聯絡資訊
- 開發者: [您的聯絡方式]
- 技術支援: [支援管道]
- API 文件: `http://服務器IP:8001/docs`

## 📅 更新記錄

- **2025-01-20**: 初始版本，包含 7 個主要 API 端點
- **待更新**: 增加身份驗證、資料篩選增強功能

---
*本文件最後更新: 2025-01-20*
