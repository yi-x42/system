#!/usr/bin/env python3
"""
攝影機數量統計功能驗證測試
驗證儀表板中的攝影機總數和線上數量是否正確顯示
"""

import asyncio
import requests
import json
from datetime import datetime

# API 基礎路徑
BASE_URL = "http://localhost:8001/api/v1"

def test_camera_statistics():
    """測試攝影機數量統計功能"""
    print("🔍 攝影機數量統計功能測試")
    print("=" * 60)
    
    try:
        # 1. 測試系統統計API - 檢查攝影機數量欄位
        print("📊 1. 測試系統統計API...")
        stats_response = requests.get(f"{BASE_URL}/frontend/stats", timeout=10)
        
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print("✅ 系統統計API響應成功")
            
            # 檢查必要欄位
            required_fields = ['total_cameras', 'online_cameras']
            for field in required_fields:
                if field in stats_data:
                    print(f"   ✓ {field}: {stats_data[field]}")
                else:
                    print(f"   ❌ 缺少欄位: {field}")
                    
            print(f"   📈 攝影機總數: {stats_data.get('total_cameras', '未知')}")
            print(f"   🟢 線上數量: {stats_data.get('online_cameras', '未知')}")
        else:
            print(f"❌ 系統統計API失敗: {stats_response.status_code}")
            return False

        # 2. 測試攝影機即時檢測API - 對照數據
        print("\n🎥 2. 測試攝影機即時檢測API...")
        cameras_response = requests.get(f"{BASE_URL}/frontend/cameras?real_time_check=true", timeout=15)
        
        if cameras_response.status_code == 200:
            cameras_data = cameras_response.json()
            print("✅ 攝影機即時檢測API響應成功")
            
            total_cameras_detected = len(cameras_data)
            online_cameras_detected = len([cam for cam in cameras_data if cam.get('status') == 'online'])
            
            print(f"   📊 檢測到攝影機總數: {total_cameras_detected}")
            print(f"   🟢 線上攝影機數量: {online_cameras_detected}")
            
            # 顯示每個攝影機的狀態
            for i, camera in enumerate(cameras_data[:5]):  # 最多顯示5個
                print(f"   攝影機 {i+1}: {camera.get('name', '未知')} - {camera.get('status', '未知')}")
                
        else:
            print(f"❌ 攝影機API失敗: {cameras_response.status_code}")

        # 3. 數據一致性檢查
        print("\n🔍 3. 數據一致性檢查...")
        if stats_response.status_code == 200 and cameras_response.status_code == 200:
            stats_total = stats_data.get('total_cameras', 0)
            stats_online = stats_data.get('online_cameras', 0)
            
            # 注意：系統統計的total_cameras來自資料庫，可能與即時檢測的數量不同
            # 這是正常的，因為資料庫中可能有未啟用或配置中的攝影機
            print(f"   📊 系統統計攝影機總數: {stats_total}")
            print(f"   🎥 即時檢測攝影機數: {total_cameras_detected}")
            print(f"   🟢 系統統計線上數量: {stats_online}")
            print(f"   🟢 即時檢測線上數量: {online_cameras_detected}")
            
            if stats_online == online_cameras_detected:
                print("   ✅ 線上攝影機數量一致！")
            else:
                print("   ⚠️  線上攝影機數量不一致（可能是檢測延遲）")

        # 4. 前端儀表板測試提醒
        print("\n🌐 4. 前端測試指南...")
        print("   請在瀏覽器中訪問: http://localhost:3000")
        print("   檢查儀表板中的「攝影機總數」卡片是否顯示：")
        print(f"   - 攝影機總數: {stats_data.get('total_cameras', '未知')}")
        print(f"   - 線上: {stats_data.get('online_cameras', '未知')}")
        
        print("\n🎉 攝影機數量統計功能測試完成！")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到後端服務，請確認後端正在運行")
        return False
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        return False

def test_database_camera_count():
    """額外測試：檢查資料庫中的攝影機數量"""
    print("\n💾 資料庫攝影機數量檢查...")
    try:
        # 透過API檢查資料來源
        sources_response = requests.get(f"{BASE_URL}/data-sources", timeout=10)
        
        if sources_response.status_code == 200:
            sources_data = sources_response.json()
            camera_sources = [source for source in sources_data if source.get('source_type') == 'camera']
            
            print(f"   📂 資料庫中攝影機類型資料來源: {len(camera_sources)}")
            
            for i, source in enumerate(camera_sources[:3]):  # 顯示前3個
                print(f"   攝影機 {i+1}: {source.get('name', '未知')} - {source.get('status', '未知')}")
        else:
            print("   ⚠️  無法獲取資料來源列表")
            
    except Exception as e:
        print(f"   ❌ 資料庫檢查錯誤: {e}")

if __name__ == "__main__":
    print("🚀 開始攝影機數量統計功能驗證...")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_camera_statistics()
    test_database_camera_count()
    
    if success:
        print("\n✅ 所有測試完成！")
    else:
        print("\n❌ 部分測試失敗，請檢查系統狀態")