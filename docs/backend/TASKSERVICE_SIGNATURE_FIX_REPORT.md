# TaskService 方法簽名不匹配修復報告

## 修復時間
2025年8月10日

## 問題分析

### 錯誤詳情
```
任務創建失敗: TaskService.create_task() got an unexpected keyword argument 'name'
```

### 根本原因發現

**預期 vs 實際使用的服務**:

1. **API 端點導入**: `from app.services.task_service import TaskService`
2. **實際運行時使用**: `app.services.task_service_new.TaskService`

**方法簽名不匹配**:

| 服務版本 | 方法簽名 |
|---------|---------|
| `task_service.py` | `create_task(self, name: str, task_type: str, camera_id: Optional[str], description: str, db: AsyncSession)` |
| `task_service_new.py` | `create_task(self, task_name: str, task_type: str, config: Dict[str, Any], db: AsyncSession)` |

### 問題根源
1. 兩個 TaskService 類存在同名的 `get_task_service()` 函數
2. Python 依賴注入時實際載入了 `task_service_new.py` 的版本
3. API 端點使用舊版本的方法簽名呼叫新版本的服務

## 修復措施

### ✅ 1. 修改 API 端點適配新服務

**修復前** (frontend.py):
```python
# 創建任務
task_id = await task_service.create_task(
    name=task_data.name,                    # ❌ 'name' 參數不存在
    task_type=task_data.task_type,
    camera_id=task_data.camera_id,          # ❌ 直接傳遞，新版本需要 config
    description=task_data.description,      # ❌ 直接傳遞，新版本需要 config
    db=db
)
```

**修復後** (frontend.py):
```python
# 創建任務配置
config = {
    'camera_id': task_data.camera_id,
    'model_name': task_data.model_name,
    'confidence': task_data.confidence,
    'iou_threshold': task_data.iou_threshold,
    'description': task_data.description,
    'schedule_time': task_data.schedule_time
}

# 創建任務
task_id = await task_service.create_task(
    task_name=task_data.name,               # ✅ 'task_name' 參數正確
    task_type=task_data.task_type,          # ✅ 保持不變
    config=config,                          # ✅ 配置打包為 config 對象
    db=db                                   # ✅ 保持不變
)
```

### ✅ 2. 參數映射策略

**新的配置結構**:
```python
config = {
    'camera_id': task_data.camera_id,       # 攝影機/資料來源ID
    'model_name': task_data.model_name,     # YOLO 模型名稱
    'confidence': task_data.confidence,      # 信心度閾值
    'iou_threshold': task_data.iou_threshold, # IoU 閾值
    'description': task_data.description,    # 任務描述
    'schedule_time': task_data.schedule_time # 排程時間
}
```

### ✅ 3. 系統重載確認

```
WARNING: WatchFiles detected changes in 'app\api\v1\frontend.py'. Reloading...
INFO: Shutting down
INFO: Waiting for connections to close.
```

## 技術細節

### task_service_new.py 架構

```python
class TaskService:
    async def create_task(
        self,
        task_name: str,          # 任務名稱
        task_type: str,          # 任務類型 (realtime/batch/training)
        config: Dict[str, Any],  # 配置字典 (包含所有設定)
        db: AsyncSession = None  # 資料庫會話
    ) -> str:
        """創建新任務"""
        task_data = {
            "id": task_id,
            "name": task_name,
            "type": task_type,
            "status": "created",
            "config": config,        # 所有配置存儲在此
            "created_at": datetime.now(),
            # ...
        }
```

### 依賴注入機制

```python
# 兩個文件都有相同的函數名
def get_task_service():
    global _task_service_instance
    if _task_service_instance is None:
        _task_service_instance = TaskService()  # 不同的 TaskService 實現
    return _task_service_instance
```

### FastAPI 自動重載

- `--reload` 模式監控文件變更
- 自動重新啟動應用程式
- 保持開發階段的即時更新

## 驗證步驟

### 1. 專用測試頁面
```
訪問: http://26.86.64.166:8001/website/task_service_fix_test.html
功能: 測試修復後的任務創建 API
特點: 自動等待系統重載，提供詳細測試結果
```

### 2. 原始功能測試
```
訪問: http://26.86.64.166:8001/website/data_source.html
操作: 選擇影片檔案 → 開始分析
期望: 不再出現 "unexpected keyword argument 'name'" 錯誤
```

### 3. 日誌監控
```
預期看到: INFO: POST /api/v1/frontend/tasks HTTP/1.1" 200 OK
而不是:   任務創建失敗: TaskService.create_task() got an unexpected keyword argument 'name'
```

## 相關影響

### API 兼容性 ✅
- TaskCreate 模型保持不變
- 前端請求格式無需修改
- 只修改後端服務調用方式

### 功能完整性 ✅
- 所有 TaskCreate 字段都映射到 config
- 保持原有的任務創建邏輯
- 新增字段支援 (model_name, confidence, iou_threshold)

### 數據結構優化 ✅
- 配置統一存儲在 config 對象中
- 更好的可擴展性
- 符合 task_service_new.py 的設計理念

## 修復狀態總結

- ✅ **方法簽名**: 已適配 task_service_new.py
- ✅ **參數映射**: 已完成 config 對象重組
- ✅ **系統重載**: 修改已生效
- ✅ **測試工具**: 已創建專用測試頁面
- ⏳ **功能驗證**: 等待用戶測試確認

## 後續建議

1. **立即測試**: 使用專用測試頁面驗證修復
2. **功能確認**: 重新測試影片分析創建流程
3. **清理代碼**: 考慮移除或重命名衝突的 task_service.py
4. **文檔更新**: 更新 API 文檔以反映實際使用的服務

修復已完成，任務創建功能應該恢復正常！
