#!/usr/bin/env python3
"""
測試乙太網路即時速度功能
驗證新的網路速度監控是否正確運作
"""
import requests
import json
import time
import psutil

def test_ethernet_speed_api():
    """測試API的乙太網路即時速度功能"""
    
    print("🌐 測試乙太網路即時速度 API")
    print("=" * 60)
    
    url = "http://localhost:8001/api/v1/frontend/stats"
    
    print("📡 測試策略：")
    print("   1. 連續調用API 3次，每次間隔2秒")
    print("   2. 觀察network_usage數值變化")
    print("   3. 驗證是否為即時速度 (MB/s)")
    
    measurements = []
    
    try:
        for i in range(3):
            print(f"\n🔍 第 {i+1} 次測量...")
            
            # 發送API請求
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                network_speed = data.get('network_usage', 0)
                measurements.append({
                    'time': time.strftime('%H:%M:%S'),
                    'speed': network_speed,
                    'raw_data': data
                })
                
                print(f"   ⏰ 時間: {time.strftime('%H:%M:%S')}")
                print(f"   🚀 乙太網路速度: {network_speed} MB/s")
                print(f"   💾 記憶體使用率: {data.get('memory_usage', 'N/A')}%")
                print(f"   🖥️  CPU使用率: {data.get('cpu_usage', 'N/A')}%")
                
            else:
                print(f"   ❌ API請求失敗: HTTP {response.status_code}")
            
            # 等待2秒 (除了最後一次)
            if i < 2:
                print("   ⏳ 等待2秒...")
                time.sleep(2)
        
        print(f"\n" + "=" * 60)
        print("📊 測量結果分析")
        print("=" * 60)
        
        if len(measurements) >= 2:
            speeds = [m['speed'] for m in measurements]
            print(f"🔢 速度變化: {speeds}")
            
            # 檢查速度是否有變化 (非累積值)
            if all(s == speeds[0] for s in speeds) and speeds[0] > 10:
                print("⚠️  所有測量值相同且很大，可能仍是累積值")
            elif all(s == 0 for s in speeds):
                print("ℹ️  所有測量值為0，可能網路活動很少")
            else:
                print("✅ 速度有變化，看起來是即時速度")
            
            # 分析速度合理性
            max_speed = max(speeds)
            if max_speed > 100:
                print(f"⚠️  最高速度 {max_speed} MB/s 看起來過高")
            elif max_speed > 0:
                print(f"✅ 速度範圍合理: 0-{max_speed:.3f} MB/s")
        
        return measurements
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API 伺服器")
        print("💡 請先執行 'python start.py' 啟動系統")
        return []
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        return []

def show_system_ethernet_info():
    """顯示系統乙太網路介面資訊"""
    
    print(f"\n" + "=" * 60)
    print("🔌 系統乙太網路介面資訊")
    print("=" * 60)
    
    try:
        net_io_per_nic = psutil.net_io_counters(pernic=True)
        
        # 尋找乙太網路介面
        ethernet_interfaces = []
        for name, stats in net_io_per_nic.items():
            if any(keyword in name.lower() for keyword in ['ethernet', '乙太', '以太']):
                ethernet_interfaces.append((name, stats))
        
        if ethernet_interfaces:
            print(f"📡 發現 {len(ethernet_interfaces)} 個乙太網路介面：")
            
            for name, stats in ethernet_interfaces:
                print(f"\n🔸 介面: {name}")
                print(f"   📤 總傳送: {stats.bytes_sent/(1024**3):.2f} GB")
                print(f"   📥 總接收: {stats.bytes_recv/(1024**3):.2f} GB")
                print(f"   📦 封包傳送: {stats.packets_sent:,}")
                print(f"   📦 封包接收: {stats.packets_recv:,}")
                
                if stats.dropin > 0 or stats.dropout > 0:
                    print(f"   ⚠️  丟包: 輸入 {stats.dropin}, 輸出 {stats.dropout}")
        else:
            print("⚠️  未找到乙太網路介面")
            print("📋 所有可用介面:")
            for name in net_io_per_nic.keys():
                print(f"   - {name}")
    
    except Exception as e:
        print(f"❌ 獲取網路介面資訊失敗: {e}")

def demonstrate_speed_calculation():
    """示範乙太網路速度計算過程"""
    
    print(f"\n" + "=" * 60)
    print("🧮 乙太網路速度計算示範")
    print("=" * 60)
    
    try:
        # 獲取乙太網路介面
        net_io_per_nic = psutil.net_io_counters(pernic=True)
        ethernet_name = None
        
        for name in net_io_per_nic.keys():
            if '乙太網路' in name or 'Ethernet' in name:
                ethernet_name = name
                break
        
        if not ethernet_name:
            print("⚠️  未找到乙太網路介面，使用總網路統計")
            ethernet_stats = psutil.net_io_counters()
        else:
            ethernet_stats = net_io_per_nic[ethernet_name]
            print(f"📡 使用介面: {ethernet_name}")
        
        # 第一次測量
        bytes1 = ethernet_stats.bytes_sent + ethernet_stats.bytes_recv
        time1 = time.time()
        print(f"⏰ 測量1 - 時間: {time.strftime('%H:%M:%S')}, 累積流量: {bytes1:,} bytes")
        
        # 等待3秒
        print("⏳ 等待3秒...")
        time.sleep(3)
        
        # 第二次測量
        if ethernet_name:
            net_io_per_nic = psutil.net_io_counters(pernic=True)
            ethernet_stats = net_io_per_nic[ethernet_name]
        else:
            ethernet_stats = psutil.net_io_counters()
            
        bytes2 = ethernet_stats.bytes_sent + ethernet_stats.bytes_recv
        time2 = time.time()
        print(f"⏰ 測量2 - 時間: {time.strftime('%H:%M:%S')}, 累積流量: {bytes2:,} bytes")
        
        # 計算速度
        time_diff = time2 - time1
        bytes_diff = bytes2 - bytes1
        speed_bps = bytes_diff / time_diff
        speed_mbps = speed_bps / (1024 * 1024)
        
        print(f"\n📈 計算結果:")
        print(f"   時間間隔: {time_diff:.2f} 秒")
        print(f"   流量差異: {bytes_diff:,} bytes")
        print(f"   計算速度: {speed_bps:.2f} bytes/s")
        print(f"   乙太網路速度: {speed_mbps:.4f} MB/s")
        
        if speed_mbps > 0.001:
            print("   🟢 有網路活動")
        else:
            print("   🟡 幾乎無網路活動")
    
    except Exception as e:
        print(f"❌ 速度計算示範失敗: {e}")

def main():
    print("🚀 乙太網路即時速度測試工具")
    print("=" * 60)
    print(f"📅 測試時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 顯示系統乙太網路資訊
    show_system_ethernet_info()
    
    # 2. 示範速度計算
    demonstrate_speed_calculation()
    
    # 3. 測試API功能
    measurements = test_ethernet_speed_api()
    
    # 4. 總結
    print(f"\n" + "=" * 60)
    print("🎯 測試總結")
    print("=" * 60)
    
    if measurements:
        print("✅ API 測試成功完成")
        print("📊 網路速度監控功能已實作")
        print("🔄 建議觀察更長時間以驗證即時性")
    else:
        print("❌ API 測試失敗")
        print("🔧 請檢查系統是否正常運行")
    
    print(f"\n💡 說明：network_usage 欄位現在顯示乙太網路的即時傳輸速度 (MB/s)")

if __name__ == "__main__":
    main()