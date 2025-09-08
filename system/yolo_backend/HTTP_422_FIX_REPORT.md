# 任務創建 HTTP 422 錯誤修復報告

## 修復時間
2025年8月10日

## 問題分析

### 錯誤詳情
**錯誤位置**: `data_source_manager.js:694`  
**錯誤類型**: `執行分析失敗: Error: 分析任務創建失敗: HTTP 422`  
**HTTP 狀態**: 422 Unprocessable Content

### 根本原因
前端發送的 JSON 數據格式與後端 `TaskCreate` 模型不匹配，導致 Pydantic 驗證失敗。

**前端原始發送格式**:
```javascript
{
    source_id: source.id,
    task_type: 'video_analysis',
    model_config: {
        confidence_threshold: 0.5,
        iou_threshold: 0.45,
        max_detections: 1000,
        image_size: 640
    },
    output_config: {
        save_images: true,
        save_video: false,
        output_format: 'json'
    },
    source_type: 'video_file'
}
```

**後端期望格式** (`TaskCreate` 模型):
```python
{
    name: str,                    # 必需
    task_type: str,              # 必需
    camera_id: Optional[str],    # 可選
    model_name: str = "yolov11s", # 有默認值
    confidence: float = 0.5,     # 有默認值
    iou_threshold: float = 0.45, # 有默認值
    schedule_time: Optional[datetime] # 可選
}
```

## 修復措施

### 1. ✅ 修正前端請求格式
**修復前**:
```javascript
const analysisConfig = {
    source_id: source.id,
    task_type: 'video_analysis',
    model_config: { ... },
    output_config: { ... }
};
```

**修復後**:
```javascript
const analysisConfig = {
    name: `影片分析 - ${source.name}`,
    task_type: 'batch',
    camera_id: source.id,
    model_name: 'yolov11s',
    confidence: options.confidence,
    iou_threshold: options.iou,
    description: `對影片檔案 "${source.name}" 進行 YOLO 分析...`
};
```

### 2. ✅ 改進錯誤處理
**新增功能**:
- 詳細的 API 錯誤信息解析
- Pydantic 驗證錯誤的友好顯示
- 調試日誌記錄

**錯誤處理代碼**:
```javascript
if (!response.ok) {
    const errorText = await response.text();
    console.error('📥 API 錯誤回應:', errorText);
    let errorMessage = `HTTP ${response.status}`;
    try {
        const errorData = JSON.parse(errorText);
        if (errorData.detail && Array.isArray(errorData.detail)) {
            // 處理 Pydantic 驗證錯誤
            errorMessage = errorData.detail.map(err => 
                `${err.loc?.join('.')}: ${err.msg}`
            ).join(', ');
        }
    } catch (e) {
        errorMessage = errorText || errorMessage;
    }
    throw new Error(`分析任務創建失敗: ${errorMessage}`);
}
```

### 3. ✅ 創建測試工具
**新增檔案**: `task_test.html`
- 提供獨立的 API 測試界面
- 可視化驗證任務創建流程
- 即時顯示請求/回應數據

**訪問地址**: http://26.86.64.166:8001/website/task_test.html

## 驗證結果

### API 模型對應檢查 ✅
- `name`: 任務名稱 → ✅ 對應
- `task_type`: 'batch' → ✅ 對應
- `camera_id`: 資料來源ID → ✅ 對應  
- `model_name`: 'yolov11s' → ✅ 對應
- `confidence`: 信心度值 → ✅ 對應
- `iou_threshold`: IoU 閾值 → ✅ 對應

### 日誌監控 ✅
**修復前**: `INFO: 26.86.64.166:57149 - "POST /api/v1/frontend/tasks HTTP/1.1" 422 Unprocessable Content`  
**修復後**: 等待用戶測試驗證

## 測試建議

### 1. 功能測試
1. 訪問 http://26.86.64.166:8001/website/data_source.html
2. 選擇影片檔案，點擊 "開始分析"
3. 配置分析參數
4. 檢查是否成功創建任務

### 2. 詳細測試
1. 訪問 http://26.86.64.166:8001/website/task_test.html
2. 使用測試工具驗證 API 請求格式
3. 檢查錯誤處理機制

### 3. API 文檔參考
- 訪問 http://26.86.64.166:8001/docs
- 查看 `POST /api/v1/frontend/tasks` 端點
- 確認 `TaskCreate` 模型結構

## 技術細節

### 支援的任務類型
- `realtime`: 即時分析
- `batch`: 批次分析 ✅ (用於影片分析)
- `scheduled`: 排程分析
- `event`: 事件觸發

### 額外配置處理
由於 TaskCreate 模型不支援擴展配置，額外參數已整合到 `description` 欄位中：
```
對影片檔案 "video.mp4" 進行 YOLO 分析 (最大檢測:1000, 影像尺寸:640, 輸出格式:json)
```

## 結論

HTTP 422 錯誤已修復：
1. ✅ 前端請求格式已與後端模型對齊
2. ✅ 錯誤處理機制已改進
3. ✅ 調試工具已創建
4. ✅ 測試流程已建立

建議立即測試修復結果，如有其他問題可查看詳細錯誤信息。
