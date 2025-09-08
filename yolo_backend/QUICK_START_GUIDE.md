# 🚀 團隊成員快速連接指南

## 🎯 目標
讓團隊成員從任何地點存取 YOLOv11 分析系統的資料

---

## 📱 方案 1: 手機/瀏覽器直接存取 (最簡單)

### 🌐 IPv6 網址 (推薦先試這個):
```
API 文檔: http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/docs
資料概覽: http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/api/v1/data/summary
```

**如何使用**:
1. 直接複製網址到瀏覽器
2. 如果能打開 Swagger API 文檔，表示連接成功！
3. 點擊 `/summary` 端點測試資料存取

---

## 🔐 方案 2: VPN 連接 (最穩定)

### 步驟:
1. **下載 Radmin VPN**: https://www.radmin-vpn.com/
2. **安裝並建立帳號**
3. **聯繫管理員**取得 VPN 網路資訊:
   - 網路名稱: `[請向管理員索取]`
   - 網路密碼: `[請向管理員索取]`
4. **加入網路並連接**
5. **使用以下網址**:
   ```
   API 文檔: http://26.86.64.166:8001/docs
   資料概覽: http://26.86.64.166:8001/api/v1/data/summary
   ```

---

## 💻 程式碼範例

### Python 存取範例:
```python
import requests

# 方案 1: IPv6 直接存取
base_url = "http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/api/v1/data"

# 方案 2: VPN 存取
# base_url = "http://26.86.64.166:8001/api/v1/data"

# 取得資料庫概覽
try:
    response = requests.get(f"{base_url}/summary")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 連接成功！")
        print(f"📊 分析記錄: {data['analysis_count']} 筆")
        print(f"🎯 檢測結果: {data['detection_count']} 筆")
    else:
        print(f"❌ 連接失敗: {response.status_code}")
except Exception as e:
    print(f"❌ 連接錯誤: {e}")
```

### JavaScript 存取範例:
```javascript
// 設定 API 網址
const baseUrl = "http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/api/v1/data";

// 取得資料概覽
fetch(`${baseUrl}/summary`)
  .then(response => response.json())
  .then(data => {
    console.log('✅ 連接成功！');
    console.log('📊 分析記錄:', data.analysis_count);
    console.log('🎯 檢測結果:', data.detection_count);
  })
  .catch(error => {
    console.log('❌ 連接錯誤:', error);
  });
```

---

## 🧪 快速測試

### 瀏覽器測試:
1. 複製這個網址到瀏覽器: `http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/docs`
2. 如果看到 Swagger API 文檔 = 成功！
3. 點擊 `GET /summary` → `Try it out` → `Execute` 測試資料存取

### 命令列測試:
```bash
# Windows PowerShell
Invoke-RestMethod -Uri "http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/api/v1/data/summary"

# Linux/Mac
curl "http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/api/v1/data/summary"
```

---

## 📋 可用的 API 端點

| 功能 | 網址 | 說明 |
|------|------|------|
| 📊 資料庫概覽 | `/summary` | 總體統計資訊 |
| 📝 分析記錄 | `/analyses` | 影片分析清單 |
| 🎯 檢測結果 | `/analyses/{id}/detections` | 特定分析的檢測結果 |
| 📈 檢測統計 | `/detections/stats` | 統計報表 |
| 🔍 搜尋功能 | `/search?query=person` | 搜尋檢測結果 |
| 💾 匯出 CSV | `/export/csv?table=detections` | 資料匯出 |

---

## ❓ 常見問題

**Q: 無法連接到 IPv6 網址？**
A: 您的網路可能不支援 IPv6，請使用 Radmin VPN 方案

**Q: VPN 連接後還是無法存取？**
A: 請確認:
1. VPN 已成功連接
2. 使用正確的 IP: `26.86.64.166:8001`
3. 聯繫管理員檢查服務狀態

**Q: API 回應很慢？**
A: 使用 `limit` 參數限制資料量，例如: `/analyses?limit=10`

**Q: 需要更多功能？**
A: 參考完整的 `TEAM_API_GUIDE.md` 文檔

---

## 📞 技術支援

- **管理員**: [聯繫資訊]
- **完整文檔**: TEAM_API_GUIDE.md
- **網路設定**: NETWORK_SETUP.md

---

**🎯 記住**: 如果 IPv6 網址能直接使用，這是最簡單的方式！
