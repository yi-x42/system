# YOLOv11 數位雙生分析系統 - 簡化 ERD

## 📊 資料表結構

┌─────────────────────────────────────────────────────────────┐
│                    YOLOv11 資料庫架構                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   USERS         │      │   CAMERAS       │      │  YOLO_MODELS    │
├─────────────────┤      ├─────────────────┤      ├─────────────────┤
│ • id (PK)       │      │ • id (PK)       │      │ • id (PK)       │
│ • username      │      │ • name          │      │ • name          │
│ • email         │      │ • type          │      │ • version       │
│ • role          │      │ • connection    │      │ • file_path     │
│ • is_active     │      │ • location      │      │ • model_type    │
│ • created_at    │      │ • status        │      │ • is_active     │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                        │                        │
         │ creates                │ uses                   │ processed_by
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  ANALYSIS_RECORDS                           │
├─────────────────────────────────────────────────────────────┤
│ • id (PK)                                                   │
│ • camera_id (FK)                                            │
│ • video_path                                                │
│ • status (pending/processing/completed/failed)             │
│ • created_at, updated_at                                    │
│ • start_time, end_time                                      │
│ • total_frames, processed_frames                            │
│ • metadata (JSON)                                           │
│ • error_message                                             │
└─────────────────────────────────────────────────────────────┘
         │                        │
         │ contains               │ generates
         │                        │
         ▼                        ▼
┌─────────────────────┐   ┌─────────────────────┐
│  DETECTION_RESULTS  │   │  BEHAVIOR_EVENTS    │
├─────────────────────┤   ├─────────────────────┤
│ • id (PK)           │   │ • id (PK)           │
│ • analysis_id (FK)  │   │ • analysis_id (FK)  │
│ • frame_number      │   │ • event_type        │
│ • object_class      │   │ • severity          │
│ • confidence        │   │ • description       │
│ • x_min, y_min      │   │ • start_frame       │
│ • x_max, y_max      │   │ • end_frame         │
│ • detected_at       │   │ • event_time        │
│ • additional_data   │   │ • event_data        │
└─────────────────────┘   └─────────────────────┘

┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ FILE_UPLOADS    │      │ SYSTEM_LOGS     │      │ SYS_CONFIG      │
├─────────────────┤      ├─────────────────┤      ├─────────────────┤
│ • id (PK)       │      │ • id (PK)       │      │ • key (PK)      │
│ • original_name │      │ • level         │      │ • category      │
│ • stored_name   │      │ • component     │      │ • value         │
│ • file_path     │      │ • message       │      │ • description   │
│ • mime_type     │      │ • context       │      │ • data_type     │
│ • file_size     │      │ • created_at    │      │ • updated_at    │
│ • upload_type   │      │ • ip_address    │      │ • updated_by    │
│ • uploaded_by   │      │ • user_id (FK)  │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘

## 🔗 關聯關係說明

1. **使用者管理**
   - 一個使用者可以管理多台攝影機
   - 一個使用者可以上傳多個模型
   - 一個使用者可以創建多個分析記錄

2. **分析流程**
   - 一個分析記錄使用一台攝影機
   - 一個分析記錄使用一個 YOLO 模型
   - 一個分析記錄產生多個檢測結果
   - 一個分析記錄產生多個行為事件

3. **資料追蹤**
   - 所有操作都有使用者追蹤
   - 所有變更都有時間戳記
   - 重要操作都有日誌記錄

## 📈 資料流向

使用者 → 上傳影片 → 選擇攝影機/模型 → 開始分析 
  ↓
建立分析記錄 → YOLO 處理 → 產生檢測結果 → 識別行為事件
  ↓
更新分析狀態 → 記錄系統日誌 → 完成分析

## 🎯 主要索引

- analysis_records: status, created_at
- detection_results: analysis_id, frame_number
- behavior_events: analysis_id, event_type
- system_logs: level, created_at
- users: username, email

## 💾 儲存估算

假設每日處理 10 個影片（30分鐘/1080p）：
- analysis_records: ~10 筆/日
- detection_results: ~500,000 筆/日
- behavior_events: ~1,000 筆/日
- system_logs: ~10,000 筆/日

建議定期歸檔超過 30 天的資料以維持效能。

## 🛠️ 建議的資料庫配置

### PostgreSQL 配置
```sql
-- 建立資料庫
CREATE DATABASE yolov11_system;

-- 啟用 UUID 擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 建立用戶和權限
CREATE USER yolo_admin WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE yolov11_system TO yolo_admin;
```

### 效能調優參數
```sql
-- 提升查詢效能
SET shared_buffers = '256MB';
SET effective_cache_size = '1GB';
SET random_page_cost = 1.1;
SET seq_page_cost = 1.0;

-- 批量插入優化
SET wal_buffers = '16MB';
SET checkpoint_segments = 32;
SET checkpoint_completion_target = 0.9;
```

## 🔧 維護建議

1. **定期備份**: 每日全量備份 + 增量備份
2. **索引重建**: 週期性重建索引以維持效能
3. **統計更新**: 定期更新表統計信息
4. **空間清理**: 清理過期資料和日誌
5. **監控查詢**: 識別和優化慢查詢

## 📊 監控指標

- 資料庫連接數
- 查詢響應時間
- 表大小增長率
- 索引使用率
- 磁盤空間使用率
- CPU 和記憶體使用率
