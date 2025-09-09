#!/usr/bin/env python3
"""
測試前端API調用路徑
"""

import requests
import json

def test_frontend_api_calls():
    """測試前端實際使用的API路徑"""
    base_url = "http://localhost:8001"
    
    # 前端實際調用的API路徑
    frontend_apis = [
        # react-query-hooks.ts 中定義的路徑
        "/api/v1/frontend/models/list",      # fetchYoloModelList
        "/api/v1/frontend/models/active",    # fetchActiveModels  
        "/api/v1/frontend/models",           # 測試發現的實際API
    ]
    
    print("=== 測試前端API調用路徑 ===\n")
    
    for api_path in frontend_apis:
        print(f"測試: {api_path}")
        try:
            url = f"{base_url}{api_path}"
            response = requests.get(url, timeout=5)
            print(f"  狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  數據類型: {type(data)}")
                
                if isinstance(data, list):
                    print(f"  模型數量: {len(data)}")
                    if data:
                        print(f"  第一個模型: {data[0]}")
                elif isinstance(data, dict):
                    if 'value' in data:
                        print(f"  格式: {{value: [], Count: {data.get('Count', 'N/A')}}}")
                        print(f"  模型數量: {len(data['value']) if data['value'] else 0}")
                    elif 'models' in data:
                        print(f"  格式: {{models: [], current_model: '{data.get('current_model', 'N/A')}'}}")
                        print(f"  模型數量: {len(data['models']) if data['models'] else 0}")
                    else:
                        print(f"  格式: 未知字典格式 - {list(data.keys())[:3]}...")
                
                # 檢查是否有可用的活躍模型
                active_models = []
                if isinstance(data, list):
                    active_models = [m for m in data if m.get('status') == 'active']
                elif isinstance(data, dict):
                    if 'value' in data and isinstance(data['value'], list):
                        active_models = [m for m in data['value'] if m.get('status') == 'active']
                    elif 'models' in data and isinstance(data['models'], list):
                        active_models = [m for m in data['models'] if m.get('status') in ['active', 'loaded']]
                
                if active_models:
                    print(f"  活躍模型: {[m.get('name', m.get('id', 'Unknown')) for m in active_models]}")
                else:
                    print(f"  活躍模型: 無")
                    
            else:
                print(f"  錯誤: {response.text}")
                
        except Exception as e:
            print(f"  異常: {e}")
        
        print()

if __name__ == "__main__":
    test_frontend_api_calls()
    
    print("=== 解決方案建議 ===")
    print("1. 如果 /api/v1/frontend/models/active 返回數據，檢查前端是否正確解析")
    print("2. 如果返回404，可能需要修復API路由或使用其他端點")
    print("3. 檢查數據格式是否與前端TypeScript接口匹配")
    print("4. 確認是否有活躍的模型供前端選擇")
