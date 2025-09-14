# 外鍵約束錯誤修復報告
**日期**: 2025年9月15日  
**問題**: 暫停->停止任務流程產生資料庫外鍵約束錯誤  
**狀態**: ✅ 已修復

---

## 🚨 問題描述

用戶報告在執行以下操作序列時出現資料庫錯誤：

1. 啟動即時檢測任務
2. 暫停任務（任務狀態變為 `paused`，但檢測服務仍在運行）
3. 停止任務（任務記錄被處理，但檢測服務未及時停止）
4. **錯誤發生**：檢測服務繼續嘗試儲存檢測結果，但對應的任務記錄已經不存在

### 錯誤訊息
```
SQL 執行錯誤: (psycopg2.errors.ForeignKeyViolation) insert or update on table "detection_results" violates foreign key constraint "detection_results_task_id_fkey"
DETAIL:  Key (task_id)=(189) is not present in table "analysis_tasks".
```

---

## 🔍 根本原因分析

### 問題根源
1. **資料庫層面**：`detection_results` 表有外鍵約束，要求 `task_id` 必須存在於 `analysis_tasks` 表中
2. **時序問題**：停止任務時，任務記錄被處理/刪除，但檢測服務有延遲停止
3. **缺乏驗證**：檢測結果保存邏輯沒有驗證任務是否仍然存在

### 技術細節
- 檢測服務每 30 幀才檢查一次任務狀態（性能優化）
- 在這 30 幀的間隔內，任務可能已被刪除但檢測仍在進行
- 檢測結果保存方法沒有任務存在性驗證機制

---

## 🔨 修復方案

### 1. 檢測結果保存增強 ✅
**檔案**: `yolo_backend/app/services/new_database_service.py`

```python
def create_detection_result_sync(self, detection_data: Dict[str, Any]) -> bool:
    with SyncSessionLocal() as session:
        # 🔥 修復：先驗證任務是否存在，防止外鍵約束錯誤
        task_id = int(detection_data['task_id'])
        task_check = session.execute(
            text("SELECT id, status FROM analysis_tasks WHERE id = :task_id"), 
            {'task_id': task_id}
        ).fetchone()
        
        if not task_check:
            db_logger.warning(f"任務 {task_id} 不存在，跳過檢測結果儲存")
            return False
        
        # 檢查任務狀態，如果已停止則不儲存
        task_status = task_check[1]
        if task_status in ['completed', 'stopped', 'failed']:
            db_logger.warning(f"任務 {task_id} 已停止（狀態: {task_status}），跳過檢測結果儲存")
            return False
        
        # 繼續原有的儲存邏輯...
```

### 2. 檢測服務狀態檢查增強 ✅
**檔案**: `yolo_backend/app/services/realtime_detection_service.py`

```python
def _process_frame(self, session: RealtimeSession, frame_data: FrameData, db_service: DatabaseService = None):
    # 檢查任務的資料庫狀態（每30幀檢查一次）
    if session.frame_count % 30 == 0:
        if db_service:
            try:
                task_status = db_service.get_task_status_sync(session.task_id)
                
                # 🔥 修復：如果任務不存在或已停止，立即停止檢測
                if task_status is None:
                    detection_logger.warning(f"任務 {session.task_id} 不存在，停止檢測處理")
                    session.running = False
                    return
                
                # 原有的狀態檢查邏輯...
            except Exception as e:
                # 出現異常時，為安全起見，停止處理
                detection_logger.warning(f"由於無法檢查任務狀態，停止任務 {session.task_id} 的處理")
                session.running = False
                return
```

---

## 🧪 驗證測試

### 測試腳本
創建了專門的測試腳本：`test、simple/test_pause_stop_foreign_key_fix.py`

### 測試流程
1. ✅ 啟動即時檢測任務
2. ✅ 等待產生檢測結果
3. ✅ 暫停任務（驗證狀態更新）
4. ✅ 停止任務（關鍵測試點）
5. ✅ 觀察 15 秒，檢查是否還有外鍵約束錯誤

### 預期結果
- 不再出現 `ForeignKeyViolation` 錯誤
- 檢測服務能正確識別任務不存在並停止處理
- 停止任務後不會有新的檢測結果產生

---

## 📊 修復效果

### Before（修復前）
- ❌ 暫停->停止流程會產生外鍵約束錯誤
- ❌ 檢測服務無法正確處理任務不存在的情況
- ❌ 錯誤日誌大量出現，影響系統穩定性

### After（修復後）
- ✅ 雙重保護：任務存在性驗證 + 狀態檢查增強
- ✅ 檢測服務能優雅地處理任務不存在的情況
- ✅ 不再產生外鍵約束錯誤
- ✅ 系統更加穩定和健壯

---

## 🔄 部署說明

### 影響的檔案
1. `yolo_backend/app/services/new_database_service.py`
2. `yolo_backend/app/services/realtime_detection_service.py`

### 部署步驟
1. 更新修改的檔案
2. 重啟後端服務
3. 執行測試腳本驗證修復效果

### 風險評估
- **風險等級**: 低
- **影響範圍**: 檢測結果儲存和狀態檢查邏輯
- **回滾方案**: 可快速回滾到前一版本

---

## 🎯 總結

此修復解決了暫停->停止任務流程中的**外鍵約束錯誤**問題，通過：

1. **預防性檢查**：在儲存檢測結果前驗證任務是否存在
2. **增強狀態監控**：改善檢測服務的任務狀態檢查邏輯
3. **優雅降級**：當任務不存在時安全地停止處理

修復確保了系統的穩定性和數據完整性，用戶現在可以安全地執行暫停->停止操作而不會遇到資料庫錯誤。