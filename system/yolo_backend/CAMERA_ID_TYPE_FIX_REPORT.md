# camera_id 類型錯誤修復報告

## 修復時間
2025年8月10日

## 問題詳情

### 錯誤信息分析
```
📥 API 錯誤回應: {"detail":[{"type":"string_type","loc":["body","camera_id"],"msg":"Input should be a valid string","input":10}]}

執行分析失敗: Error: 分析任務創建失敗: body.camera_id: Input should be a valid string
```

### 根本原因
- **期望類型**: `camera_id: Optional[str]` (字符串或 null)
- **實際發送**: `camera_id: 10` (數字類型)
- **Pydantic 驗證**: 嚴格類型檢查失敗

### 資料流追蹤
1. 資料來源 API 返回 `source.id` 為數字類型
2. 前端直接使用 `camera_id: source.id` 
3. 後端 TaskCreate 模型期望字符串
4. Pydantic 驗證拒絕數字輸入

## 修復措施

### ✅ 1. 修正前端類型轉換

**修復前**:
```javascript
const analysisConfig = {
    camera_id: source.id,  // 可能是數字
    // ...
};
```

**修復後**:
```javascript
const analysisConfig = {
    camera_id: String(source.id),  // 強制轉換為字符串
    // ...
};
```

### ✅ 2. 更新測試工具

**task_test.html** 也已同步修復:
```javascript
camera_id: String(document.getElementById('cameraId').value),
```

### ✅ 3. 加入類型安全檢查

前端現在包含防護措施，確保所有字符串欄位都正確轉換。

## 驗證步驟

### 測試計劃
1. **主要功能測試**
   - 訪問: http://26.86.64.166:8001/website/data_source.html
   - 選擇影片檔案並開始分析
   - 檢查是否成功創建任務

2. **測試工具驗證**
   - 訪問: http://26.86.64.166:8001/website/task_test.html
   - 測試不同的 camera_id 值
   - 確認 API 回應正常

3. **日誌監控**
   ```
   預期看到: INFO: POST /api/v1/frontend/tasks HTTP/1.1" 200 OK
   而不是:   INFO: POST /api/v1/frontend/tasks HTTP/1.1" 422 Unprocessable Content
   ```

## 技術細節

### Pydantic 類型系統
```python
class TaskCreate(BaseModel):
    camera_id: Optional[str] = Field(None, description="攝影機ID")
    # 接受: "10", "camera-001", None
    # 拒絕: 10, 10.5, True
```

### JavaScript 類型轉換
```javascript
// 安全的類型轉換方法
String(source.id)      // "10" (推薦)
source.id.toString()   // "10" (如果 id 不是 null/undefined)
`${source.id}`        // "10" (模板字符串)
```

## 相關修復

### 其他可能的類型問題
檢查其他 API 端點是否有類似問題:
- `model_name`: 應為字符串 ✅
- `task_type`: 應為字符串 ✅
- `confidence`: 應為浮點數 ✅
- `iou_threshold`: 應為浮點數 ✅

### 防護性編程
```javascript
// 建議的完整類型檢查
const analysisConfig = {
    name: String(source.name || '未命名分析'),
    task_type: String('batch'),
    camera_id: String(source.id),
    model_name: String('yolov11s'),
    confidence: Number(options.confidence) || 0.5,
    iou_threshold: Number(options.iou) || 0.45,
    description: String(description)
};
```

## 修復狀態

- ✅ **前端類型轉換**: 已修復
- ✅ **測試工具更新**: 已完成
- ✅ **錯誤處理增強**: 已實現
- ⏳ **用戶驗證**: 等待測試

## 下一步行動

1. **立即測試**: 訪問資料來源管理頁面測試影片分析功能
2. **監控日誌**: 檢查是否還有 422 錯誤
3. **功能驗證**: 確認任務創建和執行流程正常

## 預期結果

修復後應該看到:
- ✅ 任務創建成功通知
- ✅ 日誌顯示 200 OK 回應
- ✅ 任務ID 正確返回
- ✅ 分析流程正常啟動
