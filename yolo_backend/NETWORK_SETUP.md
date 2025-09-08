# 🌐 網路配置說明 - 讓團隊成員遠端存取

## 🎯 目標
讓團隊成員從不同電腦/網路存取 YOLOv11 分析系統的資料庫內容

## 📍 目前狀態
✅ **已完成**:
- API 服務已啟動在 `http://localhost:8001`
- 資料查詢 API 端點已建立 (7 個主要功能)
- API 文檔可在 `http://localhost:8001/docs` 查看
- 完整團隊使用指南已建立 (`TEAM_API_GUIDE.md`)

📊 **網路資訊**:
- **內部 IP**: 192.168.211.157 (手機熱點分享)
- **IPv6 位址**: 2402:7500:901:f5d9:905:3c8f:672d:143b
- **VPN IP**: 26.86.64.166 (Radmin VPN)

## 🔧 外網存取配置步驟

### 🚀 **方案 1: 手機熱點分享 (推薦)**

您目前透過手機熱點上網，這是最簡單的外網分享方式：

#### 步驟 1: 設定防火牆規則
```cmd
# 以管理員權限執行
netsh advfirewall firewall add rule name="YOLO API External Access" dir=in action=allow protocol=TCP localport=8001
```

#### 步驟 2: 手機熱點設定
1. 在手機熱點設定中找到「端口轉發」或「DMZ」設定
2. 設定端口轉發: `8001 → 192.168.211.157:8001`
3. 或啟用 DMZ 模式指向您的電腦

#### 步驟 3: 取得外部存取位址
您的 IPv6 位址: `2402:7500:901:f5d9:905:3c8f:672d:143b`

團隊成員可以使用:
```
http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/docs
http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/api/v1/data/summary
```

### 🌐 **方案 2: Radmin VPN (適合團隊)**

您已安裝 Radmin VPN，這是企業級的解決方案：

#### VPN 設定步驟:
1. **建立 VPN 網路**:
   - 在 Radmin VPN 中建立新網路
   - 記下網路名稱和密碼

2. **邀請團隊成員**:
   - 分享網路名稱和密碼給團隊成員
   - 成員下載並安裝 Radmin VPN
   - 加入您建立的 VPN 網路

3. **使用 VPN IP 存取**:
   ```
   VPN 內部存取: http://26.86.64.166:8001/docs
   資料 API: http://26.86.64.166:8001/api/v1/data/summary
   ```

### 🏠 **方案 3: 傳統路由器設定**

如果使用固定寬頻網路:

#### 步驟 1: 取得內部 IP
```cmd
ipconfig
```
找到您的內部 IP (如: 192.168.1.100)

#### 步驟 2: 路由器端口轉發
1. 登入路由器管理介面 (通常是 192.168.1.1)
2. 找到「端口轉發」或「虛擬伺服器」設定
3. 新增規則:
   - **內部 IP**: 您的電腦 IP
   - **內部端口**: 8001
   - **外部端口**: 8001
   - **協議**: TCP

#### 步驟 3: 取得外部 IP
```powershell
Invoke-RestMethod -Uri "https://ifconfig.me/ip"
```

### 步驟 2: 設定防火牆規則 (Windows)
```cmd
# 以管理員權限執行
netsh advfirewall firewall add rule name="YOLO API Access" dir=in action=allow protocol=TCP localport=8001
```

### 步驟 3: 測試內網連接
團隊成員可以測試:
```
# 替換 192.168.1.100 為實際 IP
http://192.168.1.100:8001/docs
http://192.168.1.100:8001/api/v1/data/summary
```

### 步驟 4: 路由器設定 (跨網路存取)
如需外網存取，在路由器設定:
- 端口轉發: 外部 8001 → 內部 192.168.1.100:8001
- 取得外部 IP 提供給團隊成員

## 📋 團隊連接檢查清單

### 🌐 外網存取測試

#### 方案 1: IPv6 直接存取
- [ ] 防火牆已開放端口 8001
- [ ] 手機熱點已設定端口轉發
- [ ] 團隊成員可以存取 `http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/docs`
- [ ] 可以取得資料 `http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/api/v1/data/summary`

#### 方案 2: Radmin VPN 存取
- [ ] VPN 網路已建立並分享給團隊
- [ ] 團隊成員已加入 VPN 網路
- [ ] 可以存取 `http://26.86.64.166:8001/docs`
- [ ] 可以取得資料 `http://26.86.64.166:8001/api/v1/data/summary`

### 內網連接測試
- [ ] 伺服器防火牆已開放端口 8001
- [ ] 團隊成員可以 ping 到伺服器 IP
- [ ] 可以開啟 `http://內網IP:8001/docs`
- [ ] 可以存取 `http://內網IP:8001/api/v1/data/summary`

### 跨網路連接測試  
- [ ] 路由器端口轉發已設定
- [ ] 外部 IP 已取得並分享給團隊
- [ ] 可以開啟 `http://外部IP:8001/docs`

## 🔒 安全建議

1. **限制存取來源**
   - 只允許特定 IP 範圍存取
   - 考慮使用 VPN 連線

2. **API 認證** (可選增強功能)
   - 添加 API Key 驗證
   - 設定使用者權限管理

3. **資料保護**
   - 定期備份資料庫
   - 監控 API 使用情況

## 🎯 快速連接範例

### 🌐 **外網存取方式**

#### 方案 1: IPv6 直接連接
```python
# IPv6 位址存取 (需要團隊成員支援 IPv6)
SERVER_IP = "2402:7500:901:f5d9:905:3c8f:672d:143b"
BASE_URL = f"http://[{SERVER_IP}]:8001/api/v1/data"

# 測試連接
import requests
response = requests.get(f"{BASE_URL}/summary")
print(response.json())
```

#### 方案 2: Radmin VPN 連接 (推薦)
```python
# VPN 內部 IP 存取
SERVER_IP = "26.86.64.166"  # Radmin VPN IP
BASE_URL = f"http://{SERVER_IP}:8001/api/v1/data"

# 團隊成員需先連接 VPN，然後使用此 IP
response = requests.get(f"{BASE_URL}/summary")
print(response.json())
```

### 團隊成員連接步驟

#### 使用 Radmin VPN (推薦方式):
1. 下載並安裝 Radmin VPN
2. 加入您提供的 VPN 網路
3. 連接後使用: `http://26.86.64.166:8001/docs`

#### 使用 IPv6 位址:
1. 確認網路支援 IPv6
2. 直接存取: `http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/docs`

### Python 完整連接範例
```python
import requests
import json

# 多種連接方式測試
connection_options = [
    {
        "name": "Radmin VPN",
        "url": "http://26.86.64.166:8001/api/v1/data"
    },
    {
        "name": "IPv6 Direct",
        "url": "http://[2402:7500:901:f5d9:905:3c8f:672d:143b]:8001/api/v1/data"
    },
    {
        "name": "Local Network",
        "url": "http://192.168.211.157:8001/api/v1/data"
    }
]

def test_connection(option):
    try:
        response = requests.get(f"{option['url']}/summary", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {option['name']} 連接成功!")
            print(f"   資料庫中有 {data.get('analysis_count', 0)} 筆分析記錄")
            return True
        else:
            print(f"❌ {option['name']} 連接失敗: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ {option['name']} 連接錯誤: {e}")
    return False

# 測試各種連接方式
print("🔍 測試 YOLO API 連接...")
for option in connection_options:
    test_connection(option)
```

## 📞 故障排除

### 常見問題
1. **無法連接到 API**
   - 檢查防火牆設定
   - 確認 IP 位址正確
   - 檢查服務是否正在運行

2. **回應很慢**
   - 檢查網路頻寬
   - 使用 `limit` 參數限制資料量

3. **權限錯誤**
   - 確認防火牆規則已新增
   - 檢查路由器設定

### 聯絡支援
- 技術問題請聯繫系統管理員
- API 使用問題請參考 `TEAM_API_GUIDE.md`

---
⏰ **設定時間**: 2025-01-20  
🚀 **服務端口**: 8001  
📖 **完整文檔**: TEAM_API_GUIDE.md
