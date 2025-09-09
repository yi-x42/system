#!/usr/bin/env python3
"""
攝影機掃描功能整合測試
測試前端與後端的攝影機掃描功能是否正常整合
"""

import requests
import json
import time

def test_camera_scan_api():
    """測試攝影機掃描 API"""
    print("🔍 測試攝影機掃描 API...")
    
    base_url = "http://localhost:8001"
    scan_endpoint = f"{base_url}/api/v1/cameras/scan"
    
    # 測試基本掃描
    print("📡 執行基本掃描...")
    try:
        response = requests.get(scan_endpoint, params={
            "max_index": 3,
            "warmup_frames": 2,
            "force_probe": False,
            "retries": 1
        })
        response.raise_for_status()
        
        scan_result = response.json()
        print(f"✅ 掃描成功！")
        print(f"📊 掃描結果:")
        print(f"   - 總計設備: {scan_result['count']}")
        print(f"   - 可用設備: {scan_result['available_indices']}")
        
        # 顯示詳細設備資訊
        for device in scan_result['devices']:
            if device['frame_ok']:
                print(f"   📹 攝影機 {device['index']}:")
                print(f"      - 後端: {device['backend']}")
                print(f"      - 解析度: {device.get('width', '未知')}x{device.get('height', '未知')}")
                print(f"      - 狀態: ✅ 正常")
            else:
                print(f"   ❌ 攝影機 {device['index']}: 無法讀取影格")
        
        return scan_result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API 測試失敗: {e}")
        return None

def test_frontend_integration():
    """測試前端是否正常運作"""
    print("\n🌐 測試前端整合...")
    
    frontend_url = "http://localhost:3001"
    
    try:
        response = requests.get(frontend_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ 前端服務正常運作 ({frontend_url})")
            return True
        else:
            print(f"⚠️ 前端回應異常: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 無法連接前端: {e}")
        return False

def test_system_stats_api():
    """測試系統統計 API（確認基礎整合正常）"""
    print("\n📊 測試系統統計 API...")
    
    try:
        response = requests.get("http://localhost:8001/api/v1/frontend/stats")
        response.raise_for_status()
        
        stats = response.json()
        print(f"✅ 系統統計 API 正常")
        print(f"   - 系統運行時間: {stats.get('system_uptime_seconds', 0)} 秒")
        print(f"   - 線上攝影機: {stats.get('online_cameras', 0)}")
        print(f"   - 活躍任務: {stats.get('active_tasks', 0)}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 系統統計 API 測試失敗: {e}")
        return False

def main():
    """主要測試函數"""
    print("🚀 攝影機掃描功能整合測試")
    print("=" * 50)
    
    # 測試系統基礎狀態
    stats_ok = test_system_stats_api()
    
    # 測試前端
    frontend_ok = test_frontend_integration()
    
    # 測試攝影機掃描 API
    scan_result = test_camera_scan_api()
    
    print("\n" + "=" * 50)
    print("📋 測試摘要:")
    
    if stats_ok:
        print("✅ 系統統計 API 正常")
    else:
        print("❌ 系統統計 API 異常")
    
    if frontend_ok:
        print("✅ React 前端正常")
    else:
        print("❌ React 前端異常")
    
    if scan_result:
        print("✅ 攝影機掃描 API 正常")
        if scan_result['count'] > 0:
            print(f"✅ 成功掃描到 {scan_result['count']} 台攝影機")
        else:
            print("⚠️ 未掃描到任何攝影機（這可能是正常的）")
    else:
        print("❌ 攝影機掃描 API 異常")
    
    print("\n🎯 後續測試步驟:")
    print("1. 在瀏覽器中開啟 http://localhost:3001")
    print("2. 導航到攝影機控制頁面")
    print("3. 點擊「自動掃描」按鈕")
    print("4. 觀察是否顯示掃描進度和結果")
    print("5. 嘗試新增掃描到的攝影機到系統中")
    
    if scan_result and scan_result['count'] > 0:
        print(f"\n💡 提示：系統已掃描到 {scan_result['count']} 台攝影機，測試新增功能應該可以看到實際結果！")

if __name__ == "__main__":
    main()
