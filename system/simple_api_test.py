#!/usr/bin/env python3
"""
簡單API測試腳本
"""
import requests
import json

def test_api():
    try:
        print("🔍 測試攝影機掃描API...")
        
        # 測試基本連接
        print("1. 測試基本連接...")
        response = requests.get('http://localhost:8001/api/v1/health/', timeout=10)
        print(f"   健康檢查: {response.status_code}")
        
        # 測試攝影機掃描 - 使用快速模式
        print("2. 測試攝影機掃描（快速模式）...")
        response = requests.get('http://localhost:8001/api/v1/cameras/scan', timeout=15)  # 使用新的快速預設值
        print(f"   掃描狀態: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   📊 API回應:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 如果需要詳細掃描，可以解除註解
        # print("3. 測試詳細掃描...")
        # response = requests.get('http://localhost:8001/api/v1/cameras/scan?force_probe=true&retries=3&warmup_frames=5', timeout=30)
        # print(f"   詳細掃描狀態: {response.status_code}")
            
            available_count = len(data.get('available_indices', []))
            devices = data.get('devices', [])
            
            print(f"\n   ✅ 掃描結果: 找到 {available_count} 個可用攝影機")
            for device in devices:
                if device.get('frame_ok'):
                    print(f"      📹 攝影機 {device['index']}: {device['width']}x{device['height']} ({device['backend']})")
        else:
            print(f"   ❌ API錯誤: {response.text}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    test_api()
