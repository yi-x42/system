#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單API速度測試工具
測試乙太網路即時速度功能
"""
import json
import time
import requests
from datetime import datetime

def test_api_speed():
    """測試乙太網路即時速度API"""
    print("🚀 簡單API速度測試")
    print("=" * 50)
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    api_url = "http://localhost:8001/api/v1/frontend/stats"
    
    print("🔍 連續測量網路速度...")
    print("-" * 50)
    
    for i in range(5):
        try:
            print(f"📊 第 {i+1} 次測量...")
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                network_usage = data.get('network_usage', 0)
                system_uptime = data.get('system_uptime_seconds', 0)
                cpu_percent = data.get('cpu_percent', 0)
                memory_percent = data.get('memory_percent', 0)
                
                print(f"   ✅ 成功! 乙太網路速度: {network_usage:.4f} MB/s")
                print(f"   📈 CPU使用率: {cpu_percent:.1f}%")
                print(f"   🧠 記憶體使用率: {memory_percent:.1f}%")
                print(f"   ⏰ 系統運行時間: {system_uptime}秒")
                print()
            else:
                print(f"   ❌ API返回錯誤: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 無法連接到API伺服器")
            print("   💡 請確保系統已啟動: python start.py")
            break
        except Exception as e:
            print(f"   ❌ 請求失敗: {str(e)}")
            
        if i < 4:  # 不在最後一次測量後等待
            print("⏳ 等待2秒...")
            time.sleep(2)
    
    print("=" * 50)
    print("🎯 測試完成!")
    print("💡 network_usage欄位現在顯示乙太網路即時速度 (MB/s)")

if __name__ == "__main__":
    test_api_speed()