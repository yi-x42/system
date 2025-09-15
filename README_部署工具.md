# 🚀 YOLOv11數位雙生分析系統 - 組員部署工具包

## 📦 工具包內容

這個工具包包含了幫助組員快速部署YOLOv11系統的所有必要工具：

### 🎯 主要腳本

| 檔案 | 功能 | 推薦使用場景 |
|------|------|-------------|
| `組員部署工具.bat` | **一鍵部署工具** (Windows) | ⭐ **最推薦** - 所有Windows用戶 |
| `deploy.py` | 完整自動部署腳本 | 新環境首次部署 |
| `quick_database_setup.py` | 快速資料庫設置 | 只需要設置資料庫時 |
| `verify_deployment.py` | 部署結果驗證 | 檢查系統是否正確部署 |

### 📚 說明文檔

| 檔案 | 內容 |
|------|------|
| `組員部署指南.md` | 詳細的部署步驟和故障排除 |
| `部署說明.md` | 系統使用說明 (部署後生成) |
| `README_部署工具.md` | 本檔案 - 工具包總覽 |

## 🎮 快速開始

### Windows用戶 (推薦)
```cmd
# 雙擊運行
組員部署工具.bat
```

### 所有平台用戶
```bash
# 完整部署
python deploy.py

# 或僅設置資料庫
python quick_database_setup.py

# 驗證部署結果
python verify_deployment.py
```

## 📋 部署前準備

確保您的電腦已安裝：
- ✅ **Python 3.8+** (推薦 3.10+)
- ✅ **Node.js 16+** (包含 npm)
- ✅ **PostgreSQL 12+** (必須已安裝並運行)
- ✅ **網路連接** (下載依賴和YOLO模型)

## 🗄️ 資料庫設置

### 預設配置
- **主機**: localhost
- **端口**: 5432
- **用戶**: postgres
- **密碼**: 49679904 ⚠️ **請根據您的實際密碼修改**
- **資料庫名**: yolo_analysis

### 修改密碼方法
1. 編輯 `deploy.py` 或 `quick_database_setup.py`
2. 找到 `"password": "49679904"`
3. 改為您的實際PostgreSQL密碼

## 🛠️ 工具功能詳解

### 1. 組員部署工具.bat (Windows一鍵工具)
- ✨ 圖形化選單界面
- 🚀 一鍵完整部署
- 🗄️ 快速資料庫設置
- 🔍 系統狀態檢查
- 📊 部署結果驗證
- 📚 說明文檔快速訪問

### 2. deploy.py (完整部署腳本)
- 🔍 環境檢查 (Python, Node.js, PostgreSQL)
- 📦 自動安裝所有依賴套件
- 🗄️ 創建和初始化資料庫
- ⚙️ 生成配置檔案
- 🤖 下載YOLO模型
- 🧪 系統功能測試
- 📝 創建啟動腳本

### 3. quick_database_setup.py (資料庫專用)
- 🔗 PostgreSQL連接測試
- 🏗️ 自動創建資料庫
- 📋 創建所有必要資料表
- 🔗 設置外鍵約束
- 📝 插入範例資料
- ✅ 資料庫設置驗證

### 4. verify_deployment.py (驗證工具)
- 📁 檢查檔案結構完整性
- 🗄️ 測試資料庫連接
- 🔧 驗證後端功能  
- ⚛️ 檢查前端檔案
- 🐍 確認Python依賴
- ⚙️ 驗證配置檔案
- 🤖 測試YOLO模型
- 🌐 檢查網路端口

## 📊 部署流程圖

```
開始
  ↓
環境檢查 → Python 3.8+ ✓
  ↓         Node.js 16+ ✓
  ↓         PostgreSQL ✓
依賴安裝 → pip install -r requirements.txt
  ↓         npm install
資料庫設置 → 創建 yolo_analysis 資料庫
  ↓          創建 6 個資料表
  ↓          插入範例資料
配置生成 → .env 檔案
  ↓         database_info.json
  ↓         攝影機配置檔案
模型準備 → 下載 YOLO11n 模型
  ↓
系統測試 → 後端API測試
  ↓         資料庫連接測試
完成部署 → 生成啟動腳本
  ↓         創建說明文檔
啟動系統 → python start.py
```

## 🌐 部署完成後

### 系統訪問地址
- **前端界面**: http://localhost:3000
- **API文檔**: http://localhost:8001/docs
- **健康檢查**: http://localhost:8001/api/v1/health
- **系統狀態**: http://localhost:8001/api/v1/frontend/stats

### 啟動系統
```bash
# 使用部署工具生成的腳本
python start.py

# Windows: 雙擊
啟動系統.bat

# Linux/Mac: 執行
./start_system.sh
```

## 🔧 常見問題解決

### Q: PostgreSQL連接失敗
**A:** 檢查以下項目：
1. PostgreSQL服務是否運行
2. 用戶名密碼是否正確
3. 防火牆設定
4. 端口5432是否被占用

### Q: Python套件安裝失敗
**A:** 嘗試以下解決方案：
```bash
# 升級pip
python -m pip install --upgrade pip

# 清除快取
python -m pip cache purge

# 重新安裝
python -m pip install -r requirements.txt
```

### Q: Node.js套件安裝失敗
**A:** 嘗試以下解決方案：
```bash
# 清除npm快取
npm cache clean --force

# 刪除node_modules重新安裝
cd "react web"
rm -rf node_modules
npm install
```

### Q: 端口被占用
**A:** 檢查並關閉占用端口的程序：
```bash
# Windows
netstat -ano | findstr :8001
netstat -ano | findstr :3000

# Linux/Mac
lsof -i :8001
lsof -i :3000
```

## 📞 技術支援

### 日誌檔案位置
- 系統日誌: `logs/system.log`
- 資料庫日誌: `logs/database.log`
- API日誌: `logs/api.log`

### 配置檔案
- 環境變數: `.env`
- 資料庫資訊: `database_info.json`
- 攝影機配置: `camera*.json`

### 獲取幫助
1. 查看 `組員部署指南.md` 詳細說明
2. 運行 `python verify_deployment.py` 檢查問題
3. 檢查系統日誌檔案
4. 聯繫開發團隊技術支援

## 🎯 部署檢查清單

部署完成後，請確認以下項目：

- [ ] Python 3.8+ 已安裝
- [ ] Node.js 16+ 已安裝
- [ ] PostgreSQL 已安裝並運行
- [ ] 執行部署腳本成功
- [ ] 資料庫和表格創建完成
- [ ] 環境配置檔案已生成
- [ ] Python和npm依賴已安裝
- [ ] YOLO模型已準備
- [ ] 系統可以成功啟動
- [ ] 前端可訪問 (localhost:3000)
- [ ] API可訪問 (localhost:8001/docs)
- [ ] 驗證腳本通過所有測試

## 🚀 下一步

部署完成後，您可以：

1. **啟動系統**: `python start.py`
2. **訪問前端**: http://localhost:3000
3. **查看API**: http://localhost:8001/docs
4. **配置攝影機**: 編輯 `camera*.json` 檔案
5. **上傳影片**: 使用前端界面上傳測試影片
6. **創建分析任務**: 在前端建立新的檢測任務
7. **查看結果**: 在儀表板查看檢測統計

---

## 🎉 恭喜！

如果您看到這裡，表示您已經成功了解了YOLOv11系統的部署工具包。現在開始您的AI檢測之旅吧！

**YOLOv11數位雙生分析系統 v2.0**  
*讓AI為您的安全監控賦能* 🤖✨