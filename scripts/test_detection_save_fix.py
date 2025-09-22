#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢測結果保存功能測試腳本
測試 save_detection_results 方法的參數修復
"""

import asyncio
import requests
import time
import json

async def test_detection_save():
    """測試檢測結果保存功能"""
    print("🧪 [測試] 開始檢測結果保存功能測試")
    
    # 1. 啟動即時檢測
    print("🔧 [測試] 正在啟動攝影機檢測...")
    start_response = requests.post("http://localhost:8001/api/v1/realtime/start/0")
    if start_response.status_code == 200:
        print("✅ [測試] 攝影機檢測啟動成功")
    else:
        print(f"❌ [測試] 攝影機檢測啟動失敗: {start_response.status_code}")
        return
    
    # 2. 等待幾秒鐘讓系統處理一些幀
    print("⏳ [測試] 等待 5 秒讓系統處理檢測...")
    await asyncio.sleep(5)
    
    # 3. 停止檢測
    print("🛑 [測試] 正在停止攝影機檢測...")
    stop_response = requests.post("http://localhost:8001/api/v1/realtime/stop/0")
    if stop_response.status_code == 200:
        print("✅ [測試] 攝影機檢測停止成功")
    else:
        print(f"❌ [測試] 攝影機檢測停止失敗: {stop_response.status_code}")
    
    # 4. 檢查系統狀態
    print("📊 [測試] 檢查系統狀態...")
    stats_response = requests.get("http://localhost:8001/api/v1/frontend/stats")
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"✅ [測試] 系統狀態獲取成功")
        print(f"   📈 檢測結果數量: {stats.get('total_detections', '未知')}")
        print(f"   📊 分析任務數量: {stats.get('total_analysis_tasks', '未知')}")
    else:
        print(f"❌ [測試] 系統狀態獲取失敗: {stats_response.status_code}")
    
    print("🎯 [測試] 檢測結果保存功能測試完成")
    print("💡 [提示] 請檢查終端輸出中是否還有 'missing 1 required positional argument' 錯誤")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 檢測結果保存功能驗證測試")
    print("=" * 60)
    
    try:
        asyncio.run(test_detection_save())
    except Exception as e:
        print(f"❌ [錯誤] 測試執行失敗: {e}")
    
    print("=" * 60)
    print("測試結束")
