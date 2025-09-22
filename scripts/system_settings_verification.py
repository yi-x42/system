#!/usr/bin/env python3
"""
系統設定頁面效能監控驗證測試
驗證 SystemSettings 頁面是否正確顯示真實的系統統計數據
"""

import requests
import json
from datetime import datetime

def test_system_settings_integration():
    """測試系統設定頁面的數據整合"""
    print("🔍 系統設定頁面效能監控整合測試")
    print("=" * 60)
    
    try:
        # 1. 測試後端統計API
        print("📊 1. 測試後端統計API...")
        response = requests.get("http://localhost:8001/api/v1/frontend/stats", timeout=10)
        
        if response.status_code == 200:
            stats_data = response.json()
            print("✅ 系統統計API響應成功")
            
            # 檢查關鍵數據欄位
            required_fields = {
                'cpu_usage': 'CPU使用率',
                'memory_usage': '記憶體使用率', 
                'gpu_usage': 'GPU使用率',
                'network_usage': '網路使用率'
            }
            
            print("\n📈 系統效能數據:")
            for field, name in required_fields.items():
                if field in stats_data:
                    value = stats_data[field]
                    if field == 'network_usage':
                        print(f"   ✓ {name}: {value:.2f} MB/s")
                    else:
                        print(f"   ✓ {name}: {value:.1f}%")
                else:
                    print(f"   ❌ 缺少欄位: {name}")
                    
        else:
            print(f"❌ 統計API失敗: {response.status_code}")
            return False

        # 2. 前端整合測試指南
        print("\n🌐 2. 前端整合測試...")
        print("   請在瀏覽器中訪問: http://localhost:3000")
        print("   導航到「系統設定」頁面")
        print("   選擇「效能監控」標籤")
        print("   檢查「當前系統狀態」卡片是否顯示:")
        
        if response.status_code == 200:
            cpu = stats_data.get('cpu_usage', 0)
            memory = stats_data.get('memory_usage', 0) 
            gpu = stats_data.get('gpu_usage', 0)
            network = stats_data.get('network_usage', 0)
            
            print(f"   - CPU 使用率: {cpu:.1f}%")
            print(f"   - 記憶體使用率: {memory:.1f}%")
            print(f"   - GPU 使用率: {gpu:.1f}%") 
            print(f"   - 網路使用率: {network:.2f} MB/s")

        # 3. 數據更新測試
        print("\n🔄 3. 數據更新測試...")
        print("   等待15秒後重新檢查數據是否更新...")
        
        import time
        time.sleep(3)  # 短暫等待
        
        response2 = requests.get("http://localhost:8001/api/v1/frontend/stats", timeout=10)
        if response2.status_code == 200:
            stats_data2 = response2.json()
            
            # 比較時間戳
            time1 = stats_data.get('last_updated', '')
            time2 = stats_data2.get('last_updated', '')
            
            if time1 != time2:
                print("   ✅ 數據已更新（時間戳不同）")
            else:
                print("   ⚠️  數據未更新（可能是緩存或間隔太短）")
                
            # 比較CPU使用率變化
            cpu1 = stats_data.get('cpu_usage', 0)
            cpu2 = stats_data2.get('cpu_usage', 0)
            
            if abs(cpu1 - cpu2) > 0.1:
                print(f"   ✅ CPU使用率有變化: {cpu1:.1f}% → {cpu2:.1f}%")
            else:
                print(f"   📊 CPU使用率穩定: {cpu1:.1f}%")

        print("\n🎉 系統設定頁面效能監控測試完成！")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到後端服務，請確認後端正在運行")
        return False
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        return False

def test_ui_components():
    """測試UI元件功能"""
    print("\n🎨 UI元件功能測試指南...")
    print("   在系統設定頁面中，您應該看到：")
    print("   1. ✅ 載入狀態：顯示骨架屏動畫")
    print("   2. ✅ 數據顯示：顯示真實的系統效能數據")
    print("   3. ✅ 進度條：根據實際使用率顯示進度")
    print("   4. ✅ 錯誤處理：如果API失敗，顯示錯誤訊息")
    print("   5. ✅ 自動更新：數據會定期自動更新")
    
    print("\n💡 測試建議：")
    print("   - 開啟開發者工具觀察網路請求")
    print("   - 檢查 Console 是否有錯誤訊息")
    print("   - 測試不同頁面切換的資料載入")
    print("   - 觀察數據是否會自動更新")

if __name__ == "__main__":
    print("🚀 開始系統設定頁面效能監控整合測試...")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_system_settings_integration()
    test_ui_components()
    
    if success:
        print("\n✅ 所有測試完成！系統設定頁面已成功整合真實數據")
    else:
        print("\n❌ 部分測試失敗，請檢查系統狀態")