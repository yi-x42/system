#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接檢測結果保存功能測試
"""

import requests
import time
import json

def test_detection_api():
    """測試檢測 API 和保存功能"""
    base_url = "http://localhost:8001"
    
    print("🧪 檢測結果保存功能測試開始")
    print("=" * 50)
    
    # 1. 檢查健康狀態
    print("🔍 檢查系統健康狀態...")
    try:
        health_response = requests.get(f"{base_url}/api/v1/health")
        if health_response.status_code == 200:
            print("✅ 系統健康狀態正常")
        else:
            print(f"❌ 系統健康檢查失敗: {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ 無法連接到系統: {e}")
        return
    
    # 2. 啟動即時檢測
    print("\n🚀 啟動攝影機檢測...")
    try:
        start_response = requests.post(f"{base_url}/api/v1/realtime/start/0")
        print(f"📡 啟動回應狀態碼: {start_response.status_code}")
        if start_response.status_code == 200:
            print("✅ 攝影機檢測啟動成功")
            if start_response.content:
                print(f"📄 回應內容: {start_response.text}")
        else:
            print(f"❌ 攝影機檢測啟動失敗: {start_response.status_code}")
            if start_response.content:
                print(f"📄 錯誤內容: {start_response.text}")
            return
    except Exception as e:
        print(f"❌ 啟動攝影機檢測時發生錯誤: {e}")
        return
    
    # 3. 等待一段時間讓系統處理
    print("\n⏳ 等待 8 秒讓系統處理檢測和保存...")
    time.sleep(8)
    
    # 4. 獲取系統統計
    print("\n📊 獲取系統統計資訊...")
    try:
        stats_response = requests.get(f"{base_url}/api/v1/frontend/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print("✅ 系統統計獲取成功:")
            print(f"   🔍 總檢測結果數: {stats.get('total_detections', 0)}")
            print(f"   📋 總分析任務數: {stats.get('total_analysis_tasks', 0)}")
            print(f"   🎯 活躍檢測: {stats.get('active_detections', 0)}")
            print(f"   📈 系統狀態: {stats.get('system_status', '未知')}")
        else:
            print(f"❌ 系統統計獲取失敗: {stats_response.status_code}")
    except Exception as e:
        print(f"❌ 獲取系統統計時發生錯誤: {e}")
    
    # 5. 停止檢測
    print("\n🛑 停止攝影機檢測...")
    try:
        stop_response = requests.post(f"{base_url}/api/v1/realtime/stop/0")
        if stop_response.status_code == 200:
            print("✅ 攝影機檢測停止成功")
        else:
            print(f"❌ 攝影機檢測停止失敗: {stop_response.status_code}")
    except Exception as e:
        print(f"❌ 停止攝影機檢測時發生錯誤: {e}")
    
    print("\n🎯 測試完成")
    print("💡 請查看系統終端輸出確認是否還有保存錯誤")

if __name__ == "__main__":
    test_detection_api()
