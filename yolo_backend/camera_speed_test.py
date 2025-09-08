#!/usr/bin/env python3
"""
攝影機掃描性能測試腳本
測試新的快速掃描 vs 舊的慢速掃描的差異
"""

import time
import requests
import json

def test_camera_scan_speed():
    """測試攝影機掃描速度"""
    base_url = "http://localhost:8001"
    
    print("🚀 攝影機掃描性能測試")
    print("=" * 50)
    
    # 測試1: 快速掃描（新預設值）
    print("\n1. 快速掃描模式（新預設值）:")
    print("   - warmup_frames=3")
    print("   - retries=1") 
    print("   - force_probe=false")
    
    start_time = time.time()
    try:
        response = requests.get(f'{base_url}/api/v1/cameras/scan', timeout=15)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   ⏱️  耗時: {duration:.2f}秒")
        print(f"   📊 狀態: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            camera_count = data.get('count', 0)
            print(f"   📷 找到攝影機: {camera_count}個")
            if camera_count > 0:
                print(f"   🎯 可用索引: {data.get('available_indices', [])}")
        
    except Exception as e:
        print(f"   ❌ 錯誤: {str(e)}")
    
    # 測試2: 詳細掃描（舊設定模擬）
    print("\n2. 詳細掃描模式（舊設定模擬）:")
    print("   - warmup_frames=15")
    print("   - retries=3")
    print("   - force_probe=true")
    
    start_time = time.time()
    try:
        response = requests.get(
            f'{base_url}/api/v1/cameras/scan?force_probe=true&retries=3&warmup_frames=15', 
            timeout=60
        )
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   ⏱️  耗時: {duration:.2f}秒")
        print(f"   📊 狀態: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            camera_count = data.get('count', 0)
            print(f"   📷 找到攝影機: {camera_count}個")
            if camera_count > 0:
                print(f"   🎯 可用索引: {data.get('available_indices', [])}")
                
    except Exception as e:
        print(f"   ❌ 錯誤: {str(e)}")
    
    # 測試3: 極速掃描
    print("\n3. 極速掃描模式:")
    print("   - warmup_frames=1")
    print("   - retries=1")
    print("   - force_probe=false")
    
    start_time = time.time()
    try:
        response = requests.get(
            f'{base_url}/api/v1/cameras/scan?warmup_frames=1&retries=1', 
            timeout=10
        )
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   ⏱️  耗時: {duration:.2f}秒")
        print(f"   📊 狀態: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            camera_count = data.get('count', 0)
            print(f"   📷 找到攝影機: {camera_count}個")
            if camera_count > 0:
                print(f"   🎯 可用索引: {data.get('available_indices', [])}")
                
    except Exception as e:
        print(f"   ❌ 錯誤: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ 性能測試完成")
    print("\n建議:")
    print("- 一般使用: 快速掃描模式（預設）")
    print("- 問題排除: 詳細掃描模式")
    print("- 即時應用: 極速掃描模式")

if __name__ == "__main__":
    test_camera_scan_speed()
