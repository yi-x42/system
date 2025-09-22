"""
測試模型清單 API
"""
import requests
import json

def test_model_list_api():
    try:
        url = "http://localhost:8001/api/v1/frontend/models/list"
        print(f"正在測試 API: {url}")
        
        response = requests.get(url)
        print(f"HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print(f"成功獲取 {len(models)} 個模型:")
            for model in models:
                print(f"  - 名稱: {model['name']}")
                print(f"    大小: {model['size'] / (1024*1024):.2f} MB")
                print(f"    路徑: {model['path']}")
                print()
        else:
            print(f"錯誤: {response.text}")
            
    except Exception as e:
        print(f"測試失敗: {str(e)}")

if __name__ == "__main__":
    test_model_list_api()
