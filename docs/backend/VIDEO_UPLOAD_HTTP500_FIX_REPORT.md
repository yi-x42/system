# 影片上傳 HTTP 500 錯誤修復報告

## 問題描述
用戶在上傳影片檔案時遇到 HTTP 500 內部服務器錯誤：
```
:8001/api/v1/frontend/data-sources/upload/video:1  Failed to load resource: the server responded with a status of 500 (Internal Server Error)
data_source_manager.js:307 檔案上傳失敗: Error: 上傳失敗: HTTP 500
```

## 根本原因分析

### 1. 資料庫約束違反
錯誤詳情顯示：
```
new row for relation "data_sources" violates check constraint "data_sources_source_type_check"
DETAIL: Failing row contains (7, video, 1338590-hd_1920_1080_30fps.mp4, ...)
```

### 2. 資料類型不匹配
- **資料庫約束允許的值**: `'camera'`, `'video_file'`
- **API 嘗試插入的值**: `'video'`
- **結果**: 違反檢查約束，拋出 IntegrityError

### 3. 配置欄位不一致
- **模型期望的欄位**: `config.path`
- **API 提供的欄位**: `config.file_path`
- **結果**: 資料不一致，影響後續功能

## 錯誤日誌分析
```
sqlalchemy.dialects.postgresql.asyncpg.IntegrityError: 
<class 'asyncpg.exceptions.CheckViolationError'>: 
new row for relation "data_sources" violates check constraint "data_sources_source_type_check"

[SQL: INSERT INTO data_sources (source_type, name, config, status, last_check, created_at) 
VALUES ($1::VARCHAR, $2::VARCHAR, $3::JSON, $4::VARCHAR, $5::TIMESTAMP WITHOUT TIME ZONE, $6::TIMESTAMP WITHOUT TIME ZONE)]
[parameters: ('video', '1338590-hd_1920_1080_30fps.mp4', ...)]
```

## 修復策略

### 修復 1: 更正資料類型
```python
# 修復前 (錯誤)
source_data = {
    "source_type": "video",  # ❌ 不符合資料庫約束
    ...
}

# 修復後 (正確)
source_data = {
    "source_type": "video_file",  # ✅ 符合資料庫約束
    ...
}
```

### 修復 2: 統一配置欄位
```python
# 修復前 (不完整)
video_config = {
    "file_path": file_path,  # 只有 file_path
    ...
}

# 修復後 (完整)
video_config = {
    "path": file_path,       # ✅ 模型期望的欄位
    "file_path": file_path,  # ✅ 向後相容性
    ...
}
```

## 修復實施

### 修復的檔案
`/yolo_backend/app/api/v1/frontend.py` - 影片上傳 API

### 具體修改
```python
# 在 upload_video_file 函數中
async def upload_video_file(file: UploadFile = File(...)):
    # ... 檔案處理邏輯 ...
    
    # 修復：使用正確的資料類型和配置欄位
    video_config = {
        "path": file_path,          # 新增：模型期望的欄位
        "file_path": file_path,     # 保留：向後相容性
        "original_name": file.filename,
        "file_size": os.path.getsize(file_path),
        "duration": round(duration, 2),
        "fps": round(fps, 2),
        "resolution": f"{width}x{height}",
        "frame_count": frame_count,
        "upload_time": datetime.now().isoformat()
    }
    
    source_data = {
        "source_type": "video_file",  # 修復：使用正確的類型
        "name": file.filename,
        "config": video_config,
        "status": "active"
    }
```

## 測試驗證

### 服務器日誌確認修復成功
```
INFO: 127.0.0.1:52471 - "POST /api/v1/frontend/data-sources/upload/video HTTP/1.1" 200 OK
```

### Before (修復前)
- ❌ HTTP 500 Internal Server Error
- ❌ IntegrityError: 檢查約束違反
- ❌ 無法創建資料來源記錄
- ❌ 上傳功能完全失效

### After (修復後)
- ✅ HTTP 200 OK
- ✅ 成功創建資料來源記錄
- ✅ 正確的資料類型 (`video_file`)
- ✅ 完整的配置欄位 (`path` + `file_path`)
- ✅ 上傳功能完全恢復

## 相關系統一致性

### 前端過濾邏輯 (已修復)
前端已經修改為同時支援 `video` 和 `video_file` 類型：
```javascript
const videos = this.dataSources.filter(source => 
    source.source_type === 'video' || source.source_type === 'video_file');
```

### 資料庫模型一致性
確保模型期望與 API 提供的資料一致：
- `config.path` - 主要路徑欄位
- `config.file_path` - 備用路徑欄位（向後相容）

## 預防措施

### 1. 加強類型驗證
建議在 API 層添加類型驗證，確保只使用允許的 `source_type` 值。

### 2. 配置欄位標準化
統一所有相關 API 使用相同的配置欄位命名慣例。

### 3. 錯誤處理改進
添加更清晰的錯誤訊息，當約束違反時提供有用的診斷資訊。

### 4. 測試覆蓋
添加自動化測試來驗證上傳功能和資料庫約束。

## 後續工作

### 1. 資料庫架構檢視 (可選)
考慮是否需要修改資料庫約束以支援更多資料來源類型，或者保持現有約束並確保 API 一致性。

### 2. API 文檔更新
更新 API 文檔以反映正確的 `source_type` 值和配置欄位。

---

**修復狀態**: ✅ 完成  
**測試狀態**: ✅ 通過  
**部署狀態**: ✅ 已應用  

現在用戶可以正常上傳影片檔案，不會再遇到 HTTP 500 錯誤，且影片會正確顯示在前端介面中。
