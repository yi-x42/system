# YOLOv11 數位雙生分析系統 - 資料庫優化建議

## 📊 當前資料庫結構分析

### 現有資料表概覽
1. **analysis_records** - 影片分析記錄表
2. **detection_results** - 物件檢測結果表  
3. **behavior_events** - 行為事件記錄表

---

## 🎯 優化目標

### 核心目標
- 提升查詢效能
- 優化儲存空間使用
- 增強資料完整性
- 支援大量資料處理
- 改善資料分析能力

---

## 🔧 建議的資料表結構優化

### 1. 系統管理相關表 (新增)

#### 1.1 系統用戶表 (users)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

#### 1.2 系統配置表 (system_configs)
```sql
CREATE TABLE system_configs (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_system_configs_key ON system_configs(config_key);
```

### 2. YOLO 模型管理表 (新增)

#### 2.1 模型版本表 (model_versions)
```sql
CREATE TABLE model_versions (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    model_path VARCHAR(500) NOT NULL,
    model_size BIGINT,
    model_type VARCHAR(50) DEFAULT 'YOLOv11',
    accuracy_metrics JSONB,
    is_active BOOLEAN DEFAULT false,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_model_versions_name ON model_versions(model_name);
CREATE INDEX idx_model_versions_active ON model_versions(is_active);
CREATE UNIQUE INDEX idx_model_name_version ON model_versions(model_name, version);
```

#### 2.2 物件類型定義表 (object_types)
```sql
CREATE TABLE object_types (
    id SERIAL PRIMARY KEY,
    type_code VARCHAR(50) UNIQUE NOT NULL,
    type_name VARCHAR(100) NOT NULL,
    type_name_chinese VARCHAR(100),
    description TEXT,
    color_hex VARCHAR(7) DEFAULT '#FF0000',
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_object_types_code ON object_types(type_code);
CREATE INDEX idx_object_types_active ON object_types(is_active);
```

### 3. 優化現有核心表

#### 3.1 分析記錄表 (analysis_records) - 優化版
```sql
-- 新增欄位和優化
ALTER TABLE analysis_records ADD COLUMN IF NOT EXISTS model_version_id INTEGER REFERENCES model_versions(id);
ALTER TABLE analysis_records ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);
ALTER TABLE analysis_records ADD COLUMN IF NOT EXISTS session_id VARCHAR(100);
ALTER TABLE analysis_records ADD COLUMN IF NOT EXISTS processing_server VARCHAR(100);
ALTER TABLE analysis_records ADD COLUMN IF NOT EXISTS input_source VARCHAR(50) DEFAULT 'file'; -- file/camera/stream
ALTER TABLE analysis_records ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 5;
ALTER TABLE analysis_records ADD COLUMN IF NOT EXISTS tags TEXT[];

-- 性能優化索引
CREATE INDEX IF NOT EXISTS idx_analysis_records_status ON analysis_records(status);
CREATE INDEX IF NOT EXISTS idx_analysis_records_analysis_type ON analysis_records(analysis_type);
CREATE INDEX IF NOT EXISTS idx_analysis_records_created_date ON analysis_records(DATE(created_at));
CREATE INDEX IF NOT EXISTS idx_analysis_records_session ON analysis_records(session_id);
CREATE INDEX IF NOT EXISTS idx_analysis_records_user ON analysis_records(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_records_model ON analysis_records(model_version_id);

-- 複合索引提升查詢效能
CREATE INDEX IF NOT EXISTS idx_analysis_records_status_type ON analysis_records(status, analysis_type);
CREATE INDEX IF NOT EXISTS idx_analysis_records_date_status ON analysis_records(DATE(created_at), status);
```

#### 3.2 檢測結果表 (detection_results) - 優化版
```sql
-- 新增欄位優化
ALTER TABLE detection_results ADD COLUMN IF NOT EXISTS object_type_id INTEGER REFERENCES object_types(id);
ALTER TABLE detection_results ADD COLUMN IF NOT EXISTS tracking_id VARCHAR(100);
ALTER TABLE detection_results ADD COLUMN IF NOT EXISTS frame_hash VARCHAR(64);
ALTER TABLE detection_results ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false;
ALTER TABLE detection_results ADD COLUMN IF NOT EXISTS verified_by INTEGER REFERENCES users(id);

-- 關鍵性能索引
CREATE INDEX IF NOT EXISTS idx_detection_results_analysis_id ON detection_results(analysis_id);
CREATE INDEX IF NOT EXISTS idx_detection_results_frame_number ON detection_results(frame_number);
CREATE INDEX IF NOT EXISTS idx_detection_results_timestamp ON detection_results(timestamp);
CREATE INDEX IF NOT EXISTS idx_detection_results_object_type ON detection_results(object_type);
CREATE INDEX IF NOT EXISTS idx_detection_results_confidence ON detection_results(confidence);
CREATE INDEX IF NOT EXISTS idx_detection_results_tracking_id ON detection_results(tracking_id);

-- 複合索引優化查詢
CREATE INDEX IF NOT EXISTS idx_detection_results_analysis_frame ON detection_results(analysis_id, frame_number);
CREATE INDEX IF NOT EXISTS idx_detection_results_analysis_object ON detection_results(analysis_id, object_type);
CREATE INDEX IF NOT EXISTS idx_detection_results_confidence_type ON detection_results(confidence, object_type);

-- 空間索引 (PostgreSQL GiST)
CREATE INDEX IF NOT EXISTS idx_detection_results_center_point ON detection_results USING GIST(point(center_x, center_y));
```

#### 3.3 行為事件表 (behavior_events) - 優化版
```sql
-- 新增欄位
ALTER TABLE behavior_events ADD COLUMN IF NOT EXISTS event_category VARCHAR(50);
ALTER TABLE behavior_events ADD COLUMN IF NOT EXISTS alert_level INTEGER DEFAULT 1; -- 1-5 級別
ALTER TABLE behavior_events ADD COLUMN IF NOT EXISTS is_false_positive BOOLEAN DEFAULT false;
ALTER TABLE behavior_events ADD COLUMN IF NOT EXISTS reviewed_by INTEGER REFERENCES users(id);
ALTER TABLE behavior_events ADD COLUMN IF NOT EXISTS review_notes TEXT;

-- 索引優化
CREATE INDEX IF NOT EXISTS idx_behavior_events_analysis_id ON behavior_events(analysis_id);
CREATE INDEX IF NOT EXISTS idx_behavior_events_timestamp ON behavior_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_behavior_events_event_type ON behavior_events(event_type);
CREATE INDEX IF NOT EXISTS idx_behavior_events_alert_level ON behavior_events(alert_level);
CREATE INDEX IF NOT EXISTS idx_behavior_events_category ON behavior_events(event_category);

-- 複合索引
CREATE INDEX IF NOT EXISTS idx_behavior_events_analysis_type ON behavior_events(analysis_id, event_type);
CREATE INDEX IF NOT EXISTS idx_behavior_events_date_type ON behavior_events(DATE(timestamp), event_type);
```

### 4. 新增輔助功能表

#### 4.1 區域定義表 (zones)
```sql
CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    zone_code VARCHAR(50) UNIQUE NOT NULL,
    zone_name VARCHAR(100) NOT NULL,
    zone_name_chinese VARCHAR(100),
    zone_type VARCHAR(50), -- rectangle/polygon/circle
    coordinates JSONB NOT NULL, -- 座標定義
    is_active BOOLEAN DEFAULT true,
    alert_enabled BOOLEAN DEFAULT false,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_zones_code ON zones(zone_code);
CREATE INDEX idx_zones_active ON zones(is_active);
```

#### 4.2 系統日誌表 (system_logs)
```sql
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    log_level VARCHAR(20) NOT NULL, -- DEBUG/INFO/WARNING/ERROR/CRITICAL
    module VARCHAR(100),
    message TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    additional_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_system_logs_level ON system_logs(log_level);
CREATE INDEX idx_system_logs_module ON system_logs(module);
CREATE INDEX idx_system_logs_created_date ON system_logs(DATE(created_at));
CREATE INDEX idx_system_logs_user ON system_logs(user_id);

-- 複合索引
CREATE INDEX idx_system_logs_level_date ON system_logs(log_level, DATE(created_at));
```

#### 4.3 檔案管理表 (file_records)
```sql
CREATE TABLE file_records (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50), -- video/image/csv/json
    file_size BIGINT,
    file_hash VARCHAR(64),
    mime_type VARCHAR(100),
    analysis_id INTEGER REFERENCES analysis_records(id),
    uploaded_by INTEGER REFERENCES users(id),
    is_temporary BOOLEAN DEFAULT false,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_file_records_hash ON file_records(file_hash);
CREATE INDEX idx_file_records_analysis ON file_records(analysis_id);
CREATE INDEX idx_file_records_type ON file_records(file_type);
CREATE INDEX idx_file_records_temporary ON file_records(is_temporary);
```

#### 4.4 即時攝影機狀態表 (camera_status)
```sql
CREATE TABLE camera_status (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(100) UNIQUE NOT NULL,
    camera_name VARCHAR(255),
    ip_address INET,
    status VARCHAR(20) DEFAULT 'offline', -- online/offline/error
    fps FLOAT,
    resolution VARCHAR(20),
    last_frame_time TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_camera_status_id ON camera_status(camera_id);
CREATE INDEX idx_camera_status_status ON camera_status(status);
```

---

## 📈 資料分割策略

### 1. 時間分割 (Partitioning)
```sql
-- detection_results 按月分割
CREATE TABLE detection_results_y2025m01 PARTITION OF detection_results
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE detection_results_y2025m02 PARTITION OF detection_results
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- 自動建立未來分割
CREATE OR REPLACE FUNCTION create_monthly_partitions()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    table_name text;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE + interval '1 month');
    end_date := start_date + interval '1 month';
    table_name := 'detection_results_y' || to_char(start_date, 'YYYY') || 'm' || to_char(start_date, 'MM');
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF detection_results FOR VALUES FROM (%L) TO (%L)',
                   table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

### 2. 資料歸檔策略
```sql
-- 建立歷史資料表
CREATE TABLE detection_results_archive (
    LIKE detection_results INCLUDING ALL
);

-- 歸檔程序
CREATE OR REPLACE FUNCTION archive_old_detections(days_old INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    rows_moved INTEGER;
BEGIN
    WITH moved_rows AS (
        DELETE FROM detection_results 
        WHERE created_at < NOW() - INTERVAL '%s days' 
        RETURNING *
    )
    INSERT INTO detection_results_archive SELECT * FROM moved_rows;
    
    GET DIAGNOSTICS rows_moved = ROW_COUNT;
    RETURN rows_moved;
END;
$$ LANGUAGE plpgsql;
```

---

## ⚡ 性能優化建議

### 1. 查詢優化
```sql
-- 建立物化視圖加速統計查詢
CREATE MATERIALIZED VIEW daily_detection_stats AS
SELECT 
    DATE(timestamp) as detection_date,
    object_type,
    COUNT(*) as detection_count,
    AVG(confidence) as avg_confidence,
    MIN(confidence) as min_confidence,
    MAX(confidence) as max_confidence
FROM detection_results
GROUP BY DATE(timestamp), object_type;

-- 建立唯一索引支援 REFRESH CONCURRENTLY
CREATE UNIQUE INDEX idx_daily_detection_stats_unique 
ON daily_detection_stats(detection_date, object_type);
```

### 2. 連接池優化
```python
# database.py 優化建議
async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,          # 增加連接池大小
    max_overflow=30,       # 增加溢出連接
    pool_timeout=30,       # 連接超時
    pool_recycle=3600,     # 連接回收時間
    pool_pre_ping=True,    # 連接前測試
    echo=False             # 生產環境關閉SQL日誌
)
```

### 3. 批量操作優化
```python
# 批量插入檢測結果
async def bulk_insert_detections(session: AsyncSession, detections: List[dict]):
    """批量插入檢測結果，提升性能"""
    await session.execute(
        insert(DetectionResult),
        detections
    )
    await session.commit()
```

---

## 🔒 資料完整性約束

### 1. 外鍵約束
```sql
-- 確保資料一致性
ALTER TABLE detection_results 
ADD CONSTRAINT fk_detection_analysis 
FOREIGN KEY (analysis_id) REFERENCES analysis_records(id) ON DELETE CASCADE;

ALTER TABLE behavior_events 
ADD CONSTRAINT fk_behavior_analysis 
FOREIGN KEY (analysis_id) REFERENCES analysis_records(id) ON DELETE CASCADE;
```

### 2. 檢查約束
```sql
-- 信心度範圍檢查
ALTER TABLE detection_results 
ADD CONSTRAINT chk_confidence_range 
CHECK (confidence >= 0.0 AND confidence <= 1.0);

-- 座標合理性檢查
ALTER TABLE detection_results 
ADD CONSTRAINT chk_bbox_valid 
CHECK (bbox_x1 >= 0 AND bbox_y1 >= 0 AND bbox_x2 > bbox_x1 AND bbox_y2 > bbox_y1);
```

---

## 📊 監控與維護

### 1. 資料庫監控視圖
```sql
-- 資料表大小監控
CREATE VIEW table_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 索引使用率監控
CREATE VIEW index_usage AS
SELECT 
    t.tablename,
    indexname,
    c.reltuples AS num_rows,
    pg_size_pretty(pg_relation_size(quote_ident(t.tablename)::text)) AS table_size,
    pg_size_pretty(pg_relation_size(quote_ident(indexrelname)::text)) AS index_size,
    CASE WHEN indisunique THEN 'Y' ELSE 'N' END AS unique,
    idx_scan as number_of_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_tables t
LEFT OUTER JOIN pg_class c ON c.relname=t.tablename
LEFT OUTER JOIN 
    ( SELECT c.relname AS ctablename, ipg.relname AS indexname, x.indnatts AS number_of_columns, idx_scan, idx_tup_read, idx_tup_fetch, indexrelname, indisunique FROM pg_index x
           JOIN pg_class c ON c.oid = x.indrelid
           JOIN pg_class ipg ON ipg.oid = x.indexrelid  
           JOIN pg_stat_all_indexes psai ON x.indexrelid = psai.indexrelid )
    AS foo
    ON t.tablename = foo.ctablename
WHERE t.schemaname='public'
ORDER BY 1,2;
```

### 2. 自動維護任務
```sql
-- 定期 VACUUM 和 ANALYZE
CREATE OR REPLACE FUNCTION auto_maintenance()
RETURNS void AS $$
BEGIN
    -- 重建統計資訊
    ANALYZE detection_results;
    ANALYZE behavior_events;
    ANALYZE analysis_records;
    
    -- 清理無效資料
    VACUUM (ANALYZE, VERBOSE) detection_results;
    VACUUM (ANALYZE, VERBOSE) behavior_events;
    VACUUM (ANALYZE, VERBOSE) analysis_records;
    
    -- 更新物化視圖
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_detection_stats;
END;
$$ LANGUAGE plpgsql;
```

---

## 🚀 實施建議

### 階段一：基礎優化 (1週)
1. 新增關鍵索引
2. 建立系統配置表
3. 實施基本約束檢查

### 階段二：結構擴展 (2週)
1. 新增用戶管理系統
2. 建立模型版本控制
3. 實施物件類型標準化

### 階段三：性能提升 (2週)
1. 實施資料分割策略
2. 建立物化視圖
3. 優化查詢性能

### 階段四：監控完善 (1週)
1. 建立監控視圖
2. 設定自動維護任務
3. 實施資料歸檔策略

---

## 💾 備份與恢復策略

### 1. 定期備份
```bash
# 每日完整備份
pg_dump -h localhost -U postgres -d yolo_analysis > backup_$(date +%Y%m%d).sql

# 每小時增量備份 (WAL 歸檔)
archive_command = 'cp %p /backup/wal_archive/%f'
```

### 2. 災難恢復計畫
1. **RTO目標**: 30分鐘內恢復服務
2. **RPO目標**: 最多丟失1小時資料
3. **備份保留**: 30天完整備份 + 7天WAL日誌

---

## 📋 檢查清單

### 實施前檢查
- [ ] 評估當前資料量和增長趨勢
- [ ] 確認硬體資源是否充足
- [ ] 備份現有資料庫
- [ ] 制定回滾計畫

### 實施後驗證
- [ ] 執行性能測試
- [ ] 驗證資料完整性
- [ ] 檢查索引使用率
- [ ] 監控系統資源使用

---

**建議優先級**: ⭐⭐⭐⭐⭐ (高度建議立即實施)

這個優化方案將大幅提升您的 YOLOv11 分析系統的資料處理能力和查詢性能！
