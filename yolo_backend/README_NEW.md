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
