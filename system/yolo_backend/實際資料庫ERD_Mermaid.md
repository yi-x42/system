# YOLOv11 資料庫實際內容 - Mermaid ERD

基於 2025-08-03 的實際 PostgreSQL 資料庫分析結果

## 📊 資料庫統計摘要
- **資料庫類型**: PostgreSQL  
- **表單總數**: 3 個
- **總記錄數**: 2,114 筆
- **最大表**: detection_results (1,249 筆記錄)

## 🎯 Mermaid ERD 程式碼

```mermaid
erDiagram
    %% YOLOv11 數位雙生分析系統 - 實際資料庫 ERD
    %% 基於 PostgreSQL 實際結構和內容 (2025-08-03)
    
    ANALYSIS_RECORDS {
        integer id PK "主鍵 (自增) 🔑"
        varchar video_path "影片檔案路徑 (500字元)"
        varchar video_name "影片檔案名稱 (255字元)"
        varchar analysis_type "分析類型 detection/annotation (50字元)"
        varchar status "處理狀態 (50字元)"
        double duration "影片長度(秒)"
        double fps "幀率"
        integer total_frames "總幀數"
        varchar resolution "解析度 (50字元)"
        integer total_detections "總檢測數量"
        integer unique_objects "唯一物件數量"
        double analysis_duration "分析耗時(秒)"
        varchar csv_file_path "CSV結果檔案路徑 (500字元)"
        varchar annotated_video_path "標註影片檔案路徑 (500字元)"
        json extra_data "額外元數據"
        text error_message "錯誤訊息"
        timestamp created_at "建立時間 (預設now())"
        timestamp updated_at "更新時間 (預設now())"
    }
    
    DETECTION_RESULTS {
        integer id PK "主鍵 (自增) 🔑"
        integer analysis_id FK "關聯的分析記錄ID"
        timestamp timestamp "檢測時間"
        integer frame_number "幀編號"
        double frame_time "影片時間點(秒)"
        varchar object_id "物件追蹤ID (100字元)"
        varchar object_type "物件類型 (50字元)"
        varchar object_chinese "物件中文名稱 (50字元)"
        double confidence "信心度 (0.0-1.0)"
        double bbox_x1 "邊界框左下角X (Unity座標)"
        double bbox_y1 "邊界框左下角Y (Unity座標)"
        double bbox_x2 "邊界框右上角X (Unity座標)"
        double bbox_y2 "邊界框右上角Y (Unity座標)"
        double center_x "中心點X (Unity座標)"
        double center_y "中心點Y (Unity座標)"
        double width "寬度"
        double height "高度"
        double area "面積"
        varchar zone "所在區域 (50字元)"
        varchar zone_chinese "區域中文名稱 (50字元)"
        double velocity_x "X方向速度"
        double velocity_y "Y方向速度"
        double speed "移動速度"
        varchar direction "移動方向 (20字元)"
        varchar direction_chinese "移動方向中文 (20字元)"
        varchar detection_quality "檢測品質 (20字元)"
        timestamp created_at "建立時間 (預設now())"
        timestamp updated_at "更新時間 (預設now())"
    }
    
    BEHAVIOR_EVENTS {
        integer id PK "主鍵 (自增) 🔑"
        integer analysis_id FK "關聯的分析記錄ID"
        timestamp timestamp "事件發生時間"
        varchar event_type "事件類型 (50字元)"
        varchar event_chinese "事件中文名稱 (100字元)"
        varchar object_id "相關物件ID (100字元)"
        varchar object_type "物件類型 (50字元)"
        varchar object_chinese "物件中文名稱 (50字元)"
        varchar zone "發生區域 (50字元)"
        varchar zone_chinese "區域中文名稱 (50字元)"
        double position_x "事件X座標"
        double position_y "事件Y座標"
        double duration "持續時間(秒)"
        varchar severity "嚴重程度 (20字元)"
        varchar severity_chinese "嚴重程度中文 (20字元)"
        text description "事件描述"
        varchar trigger_condition "觸發條件 (200字元)"
        integer occurrence_count "發生次數"
        double confidence_level "事件信心度"
        json additional_data "額外事件資料"
        timestamp created_at "建立時間 (預設now())"
        timestamp updated_at "更新時間 (預設now())"
    }
    
    %% 關聯關係
    ANALYSIS_RECORDS ||--o{ DETECTION_RESULTS : "一個分析包含多個檢測結果 (1→1249)"
    ANALYSIS_RECORDS ||--o{ BEHAVIOR_EVENTS : "一個分析包含多個行為事件 (1→864)"
```

## 📈 實際資料統計

### 📊 表單記錄數分布
1. **detection_results** - 1,249 筆 (59.1%)
2. **behavior_events** - 864 筆 (40.9%)  
3. **analysis_records** - 1 筆 (0.0%)

### 🎯 主要特色

#### ANALYSIS_RECORDS (分析記錄主表)
- **記錄數**: 1 筆 (已有實際分析數據)
- **主要用途**: 儲存影片分析的基本資訊和統計結果
- **關鍵欄位**: video_path, analysis_type, status, total_detections

#### DETECTION_RESULTS (檢測結果表)
- **記錄數**: 1,249 筆 (大量檢測數據)
- **主要用途**: 儲存每幀的物件檢測結果
- **座標系統**: Unity 座標系統 (Y軸向上)
- **關鍵欄位**: object_type, confidence, bbox坐標, 運動資訊

#### BEHAVIOR_EVENTS (行為事件表)
- **記錄數**: 864 筆 (豐富的行為數據)
- **主要用途**: 記錄識別到的行為事件
- **事件類型**: crowding(聚集), abnormal_speed(異常速度)
- **空間分區**: left_area(左側區域), center_area(中央區域), right_area(右側區域)

### 🔗 實際關聯狀況
- 1 個分析記錄 → 1,249 個檢測結果
- 1 個分析記錄 → 864 個行為事件
- 平均每個檢測結果觸發 0.69 個行為事件

### 💡 資料品質觀察

#### 檢測品質分布
- **fair** (良好): 主要品質等級
- **poor** (較差): 部分低信心度檢測

#### 物件類型
- **person (人)**: 主要檢測目標
- **中文標記**: 完整的中英文對照

#### 行為事件特點
- **聚集事件**: crowd 在 center_area
- **速度異常**: abnormal_speed 在各區域
- **空間分析**: 完整的區域劃分

## 🚀 使用建議

1. **GitHub 嵌入**: 直接複製 Mermaid 程式碼到 README.md
2. **線上預覽**: 使用 https://mermaid.live/ 即時查看
3. **文檔整合**: 適合技術文檔和系統展示
4. **團隊溝通**: 清楚顯示實際資料結構和關聯

這個 ERD 基於您的實際 PostgreSQL 資料庫內容，真實反映了系統的運行狀況！
