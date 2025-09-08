# YOLOv11 系統啟動腳本使用說明

## 🚀 啟動系統

運行啟動腳本：
```bash
python start.py
```

## 🎛️ 控制命令

啟動後，您可以使用以下命令控制系統：

### 停止服務
- `quit` - 優雅地停止服務
- `exit` - 同上
- `stop` - 同上  
- `q` - 同上
- `Ctrl+C` - 強制停止服務

### 檢查狀態
- `status` - 檢查服務運行狀態
- `s` - 同上

## 📋 功能特點

### ✅ 優雅停止
- 自動清理進程
- 安全關閉服務
- 跨平台支援（Windows/Linux/Mac）

### 📊 狀態監控
- 實時檢查 API 連通性
- 顯示進程狀態
- 服務健康度檢查

### 🔄 自動重載
- 開發模式自動重載
- 程式碼變更即時生效
- 不需手動重啟

## 🌐 訪問地址

啟動成功後，您可以訪問：

- **API 文件**: http://localhost:8001/docs
- **後台管理**: http://localhost:8001/admin
- **現代化界面**: http://localhost:8001/website/
- **影片測試頁面**: http://localhost:8001/video-test
- **健康檢查**: http://localhost:8001/api/v1/health

### Radmin 網絡訪問
- **API 文件**: http://26.86.64.166:8001/docs
- **後台管理**: http://26.86.64.166:8001/admin
- **現代化界面**: http://26.86.64.166:8001/website/

## 🛠️ 故障排除

### 常見問題

1. **端口被佔用**
   ```bash
   netstat -ano | findstr :8001
   ```

2. **套件缺失**
   - 腳本會自動檢測並嘗試安裝缺失套件

3. **權限問題**
   - 使用管理員權限運行 PowerShell

4. **防火牆阻擋**
   - 檢查 Windows 防火牆設定
   - 允許 Python 程式通過防火牆

### 手動安裝套件
```bash
pip install fastapi uvicorn jinja2 psutil opencv-python
```

## 💡 使用技巧

1. **背景運行**: 啟動後可以在同一個終端繼續輸入命令
2. **快速停止**: 輸入 `q` 是最快的停止方式
3. **狀態檢查**: 使用 `status` 確認服務是否正常
4. **多種停止方式**: 支援命令輸入和 Ctrl+C 兩種方式

## 🔧 技術細節

- 使用 `subprocess.Popen` 進行進程管理
- 背景執行輸入監聽
- 跨平台進程終止處理
- 自動進程清理機制
- 異常處理和資源清理
