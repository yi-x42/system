"""
測試多模型啟用邏輯
"""
import requests
import json

def test_multi_model_logic():
    base_url = "http://localhost:8001/api/v1/frontend"
    
    print("=== 測試多模型啟用邏輯 ===\n")
    
    try:
        # 1. 取得所有模型清單
        print("1. 取得所有模型清單:")
        response = requests.get(f"{base_url}/models/list")
        if response.status_code == 200:
            all_models = response.json()
            print(f"   找到 {len(all_models)} 個模型")
            for model in all_models:
                print(f"   - {model['name']}: {model['status']}")
        else:
            print(f"   錯誤: {response.status_code}")
            return
        
        print()
        
        # 2. 取得已啟用模型
        print("2. 取得已啟用的模型:")
        response = requests.get(f"{base_url}/models/active")
        if response.status_code == 200:
            active_models = response.json()
            print(f"   已啟用 {len(active_models)} 個模型:")
            for model in active_models:
                print(f"   - {model['name']}")
        else:
            print(f"   錯誤: {response.status_code}")
        
        print()
        
        # 3. 測試啟用第二個模型
        if len(all_models) >= 2:
            second_model = all_models[1]
            model_id = second_model['id']
            print(f"3. 嘗試啟用第二個模型 ({second_model['name']}):")
            
            response = requests.post(f"{base_url}/models/{model_id}/toggle")
            if response.status_code == 200:
                result = response.json()
                print(f"   成功: {result['message']}")
            else:
                print(f"   錯誤: {response.status_code}")
            
            print()
            
            # 4. 再次檢查已啟用模型
            print("4. 切換後的已啟用模型:")
            response = requests.get(f"{base_url}/models/active")
            if response.status_code == 200:
                active_models = response.json()
                print(f"   現在已啟用 {len(active_models)} 個模型:")
                for model in active_models:
                    print(f"   - {model['name']}")
            else:
                print(f"   錯誤: {response.status_code}")
        
    except Exception as e:
        print(f"測試失敗: {str(e)}")

if __name__ == "__main__":
    test_multi_model_logic()
