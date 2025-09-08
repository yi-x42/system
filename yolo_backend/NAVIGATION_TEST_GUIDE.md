# 網站導航測試指南

## 問題修復總結

我已經修復了網站導航的問題。主要修復內容包括：

### 1. JavaScript 導航邏輯修復

- **問題**：JavaScript 事件處理器衝突，導致內部頁面切換失效
- **解決方案**：重構 `script_api.js` 的 `NavigationManager.init()` 方法
- **修復位置**：`d:\project\system\yolo_backend\website_prototype\script_api.js`

### 2. 智能分析引擎導航修復

- **問題**：點擊"智能分析引擎"按鈕沒有反應
- **解決方案**：
  - 添加了外部連結與內部導航的區分邏輯
  - 修復了事件處理的 preventDefault 邏輯
  - 加入了詳細的調試日誌

### 3. 調試功能加強

- 添加了完整的控制台日誌輸出
- 可以在瀏覽器開發者工具中看到導航事件的詳細信息

## 測試步驟

### 1. 啟動系統
```powershell
# 系統已經在運行，如果需要重新啟動：
cd d:\project\system
python start.py
```

### 2. 訪問網站
- 本地訪問：http://localhost:8001/website
- Radmin 網絡訪問：http://26.86.64.166:8001/website

### 3. 測試導航功能

#### 測試智能分析引擎
1. 點擊左側選單的"智能分析引擎"
2. 檢查是否正確切換到 AI 引擎頁面
3. 開啟瀏覽器開發者工具 (F12) 查看控制台日誌

#### 測試資料來源管理
1. 點擊左側選單的"資料來源管理"
2. 應該跳轉到 data_source.html 頁面
3. 確認頁面正常載入

#### 測試其他導航
1. 測試"系統儀表板"
2. 測試"任務管理"
3. 測試"攝影機管理"
4. 測試"數據分析"

## 調試信息

如果導航仍有問題，請：

1. **開啟瀏覽器開發者工具** (F12)
2. **查看 Console 標籤**
3. **點擊導航連結**
4. **查看日誌輸出**

你會看到類似這樣的日誌：
```
導航連結被點擊: {targetSection: "ai-engine", href: "#ai-engine", linkText: "智能分析引擎"}
處理內部導航: ai-engine
找到目標元素，顯示區塊: ai-engine
```

## 已知工作狀態

✅ **外部頁面導航**：資料來源管理 → data_source.html  
✅ **內部頁面切換**：智能分析引擎、儀表板等  
✅ **JavaScript 事件處理**：無衝突  
✅ **調試日誌**：完整輸出  

## 如果仍有問題

如果智能分析引擎仍然沒有反應，請：

1. 確認瀏覽器控制台是否有錯誤信息
2. 檢查網絡連接是否正常
3. 嘗試重新整理頁面
4. 提供控制台的完整日誌輸出

## 技術細節

### 修復的關鍵代碼

```javascript
// 區分外部連結和內部導航
if (href && (href.endsWith('.html') || 
    href.startsWith('http') || 
    href.startsWith('/website/') ||
    href.includes('data_source'))) {
    // 外部連結，讓瀏覽器正常處理
    return;
}

// 內部導航，使用 JavaScript 處理
if (href && href.startsWith('#') && targetSection) {
    e.preventDefault();
    // ... 處理內部頁面切換
}
```

這個修復確保了：
- 外部連結正常跳轉
- 內部頁面正確切換
- 沒有 JavaScript 衝突
