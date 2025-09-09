#!/usr/bin/env python3
"""
調試前端按鈕狀態 - 檢查 selectedModel 和按鈕狀態
"""

import requests
import json
import time

def check_model_apis():
    """檢查所有模型相關的API"""
    base_url = "http://localhost:8001"
    
    apis = [
        "/api/v1/models/active",
        "/api/v1/models/yolo",
        "/api/v1/frontend/models"
    ]
    
    print("=== 檢查模型API狀態 ===")
    for api in apis:
        try:
            url = f"{base_url}{api}"
            response = requests.get(url, timeout=5)
            print(f"\n{api}:")
            print(f"狀態碼: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"原始回應: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # 檢查數據結構
                if isinstance(data, dict) and 'value' in data:
                    print(f"模型列表 (data.value): {data['value']}")
                    print(f"模型數量: {data.get('Count', 'N/A')}")
                elif isinstance(data, list):
                    print(f"模型列表 (直接數組): {data}")
                    print(f"模型數量: {len(data)}")
                else:
                    print(f"未知格式: {type(data)}")
            else:
                print(f"錯誤: {response.text}")
        except Exception as e:
            print(f"{api} 錯誤: {e}")

def check_frontend_console():
    """創建測試頁面來檢查前端狀態"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>前端按鈕狀態調試</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .debug-info { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .error { background: #ffe6e6; color: red; }
        .success { background: #e6ffe6; color: green; }
    </style>
</head>
<body>
    <h1>前端按鈕狀態調試</h1>
    
    <div id="api-status" class="debug-info">
        <h3>API 狀態檢查中...</h3>
        <div id="api-results"></div>
    </div>
    
    <div id="react-status" class="debug-info">
        <h3>React 狀態檢查</h3>
        <div id="react-results">
            <p>請在瀏覽器控制台中檢查以下項目:</p>
            <ol>
                <li>打開開發者工具 (F12)</li>
                <li>切換到 Console 頁面</li>
                <li>查看是否有錯誤訊息</li>
                <li>執行以下指令檢查狀態:</li>
            </ol>
            <pre style="background: #333; color: white; padding: 10px;">
// 檢查模型狀態
window.reactDevTools = true;
console.log('檢查 React Query 快取...');

// 如果使用 React Query DevTools，可以執行:
// window.__REACT_QUERY_STATE__ 

console.log('檢查 selectedModel 狀態...');
// 在 React 組件中添加 console.log 來查看狀態
            </pre>
        </div>
    </div>
    
    <script>
        // 檢查 API
        async function checkAPIs() {
            const apis = [
                '/api/v1/models/active',
                '/api/v1/models/yolo', 
                '/api/v1/frontend/models'
            ];
            
            const results = document.getElementById('api-results');
            results.innerHTML = '';
            
            for (const api of apis) {
                try {
                    const response = await fetch(`http://localhost:8001${api}`);
                    const data = await response.json();
                    
                    const div = document.createElement('div');
                    div.className = response.ok ? 'success' : 'error';
                    
                    let modelsInfo = '';
                    if (data.value && Array.isArray(data.value)) {
                        modelsInfo = `模型: [${data.value.map(m => m.name || m).join(', ')}]`;
                    } else if (Array.isArray(data)) {
                        modelsInfo = `模型: [${data.map(m => m.name || m).join(', ')}]`;
                    }
                    
                    div.innerHTML = `
                        <strong>${api}</strong>: ${response.status} 
                        ${modelsInfo}
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    `;
                    results.appendChild(div);
                } catch (error) {
                    const div = document.createElement('div');
                    div.className = 'error';
                    div.innerHTML = `<strong>${api}</strong>: 錯誤 - ${error.message}`;
                    results.appendChild(div);
                }
            }
        }
        
        // 頁面載入時檢查 API
        checkAPIs();
        
        // 每5秒重新檢查
        setInterval(checkAPIs, 5000);
        
        console.log('=== 前端調試信息 ===');
        console.log('1. 檢查 React 應用是否載入');
        console.log('2. 檢查 selectedModel 狀態');
        console.log('3. 檢查模型選擇器選項');
    </script>
</body>
</html>
"""
    
    with open("debug_frontend.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("\n=== 前端調試頁面已生成 ===")
    print("請在瀏覽器中打開: debug_frontend.html")
    print("或運行: start http://localhost:8001/debug_frontend.html")

if __name__ == "__main__":
    print("開始調試前端按鈕狀態...")
    
    # 1. 檢查API狀態
    check_model_apis()
    
    # 2. 生成前端調試頁面
    check_frontend_console()
    
    print("\n=== 調試建議 ===")
    print("1. 確認瀏覽器已刷新 (Ctrl+Shift+R 硬刷新)")
    print("2. 檢查瀏覽器控制台是否有錯誤")
    print("3. 確認模型選擇器是否顯示 'yolo11n.pt' 選項")
    print("4. 檢查是否已選擇模型")
    print("5. 檢查 React Query 是否正確獲取數據")
