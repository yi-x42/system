#!/usr/bin/env python3
"""
網路使用率運作機制解析與測試
詳細說明系統如何計算和回傳網路使用率數據
"""
import psutil
import time
import json

def explain_network_usage():
    """詳細解釋網路使用率的運作原理"""
    
    print("🌐 網路使用率運作機制解析")
    print("=" * 80)
    
    print("\n📋 1. 資料來源：psutil.net_io_counters()")
    print("   - 使用 Python psutil 庫獲取系統網路 I/O 統計")
    print("   - 這是系統層級的網路統計，包含所有網路介面")
    print("   - 數據來源：作業系統的網路統計資訊")
    
    print("\n🔍 2. 當前實作方式分析：")
    print("   ⚠️  問題：目前的實作有概念性錯誤")
    print("   📊 當前計算：total_bytes = bytes_sent + bytes_recv")
    print("   📈 轉換公式：network_usage = total_bytes / (1024^3) GB")
    print("   ❌ 錯誤：這是累積總量，不是使用率或速度")
    
    try:
        # 獲取目前的網路統計
        net_io = psutil.net_io_counters()
        
        print("\n📊 3. 當前網路統計數據：")
        print(f"   📤 總傳送位元組: {net_io.bytes_sent:,} bytes ({net_io.bytes_sent/(1024**3):.2f} GB)")
        print(f"   📥 總接收位元組: {net_io.bytes_recv:,} bytes ({net_io.bytes_recv/(1024**3):.2f} GB)")
        print(f"   📦 總封包傳送: {net_io.packets_sent:,}")
        print(f"   📦 總封包接收: {net_io.packets_recv:,}")
        
        # 目前系統的計算方式
        total_bytes = net_io.bytes_sent + net_io.bytes_recv
        current_calculation = round((total_bytes / (1024 * 1024 * 1024)), 2)
        
        print(f"\n🧮 4. 目前系統計算結果：")
        print(f"   總流量: {total_bytes:,} bytes")
        print(f"   API 回傳值: {current_calculation} GB")
        print("   ⚠️  這個數字代表自系統啟動以來的累積總流量")
        
    except Exception as e:
        print(f"❌ 無法獲取網路統計: {e}")

def demonstrate_network_speed_calculation():
    """示範正確的網路速度計算方式"""
    
    print("\n" + "=" * 80)
    print("🚀 正確的網路速度計算示範")
    print("=" * 80)
    
    print("\n📝 正確的網路使用率應該測量：")
    print("   1. 即時網路速度 (MB/s 或 Mbps)")
    print("   2. 需要時間間隔來計算速度差")
    print("   3. 公式：速度 = (新數據 - 舊數據) / 時間間隔")
    
    try:
        print(f"\n⏱️  開始 2 秒間隔測量...")
        
        # 第一次測量
        net1 = psutil.net_io_counters()
        time1 = time.time()
        print(f"   時間 1: {net1.bytes_sent + net1.bytes_recv:,} bytes")
        
        # 等待 2 秒
        time.sleep(2)
        
        # 第二次測量
        net2 = psutil.net_io_counters()
        time2 = time.time()
        print(f"   時間 2: {net2.bytes_sent + net2.bytes_recv:,} bytes")
        
        # 計算速度
        bytes_diff = (net2.bytes_sent + net2.bytes_recv) - (net1.bytes_sent + net1.bytes_recv)
        time_diff = time2 - time1
        speed_bps = bytes_diff / time_diff  # bytes per second
        speed_mbps = speed_bps / (1024 * 1024)  # MB per second
        
        print(f"\n📈 計算結果：")
        print(f"   時間間隔: {time_diff:.2f} 秒")
        print(f"   流量差異: {bytes_diff:,} bytes")
        print(f"   網路速度: {speed_bps:.2f} bytes/s")
        print(f"   網路速度: {speed_mbps:.4f} MB/s")
        print(f"   網路速度: {speed_mbps * 8:.4f} Mbps")
        
        if speed_mbps > 0.1:
            print("   🟢 有明顯的網路活動")
        else:
            print("   🟡 網路活動較少（可能是背景流量）")
            
    except Exception as e:
        print(f"❌ 速度計算失敗: {e}")

def show_network_interfaces():
    """顯示所有網路介面的詳細資訊"""
    
    print("\n" + "=" * 80)
    print("🔌 網路介面詳細資訊")
    print("=" * 80)
    
    try:
        # 獲取每個介面的統計
        net_io_per_nic = psutil.net_io_counters(pernic=True)
        
        print(f"\n📡 發現 {len(net_io_per_nic)} 個網路介面：")
        
        for interface, stats in net_io_per_nic.items():
            print(f"\n🔸 介面: {interface}")
            print(f"   📤 傳送: {stats.bytes_sent:,} bytes ({stats.bytes_sent/(1024**2):.1f} MB)")
            print(f"   📥 接收: {stats.bytes_recv:,} bytes ({stats.bytes_recv/(1024**2):.1f} MB)")
            print(f"   📦 封包傳送: {stats.packets_sent:,}")
            print(f"   📦 封包接收: {stats.packets_recv:,}")
            
            if stats.dropin > 0 or stats.dropout > 0:
                print(f"   ⚠️  丟包: 輸入 {stats.dropin}, 輸出 {stats.dropout}")
            if stats.errin > 0 or stats.errout > 0:
                print(f"   ❌ 錯誤: 輸入 {stats.errin}, 輸出 {stats.errout}")
                
    except Exception as e:
        print(f"❌ 無法獲取介面資訊: {e}")

def suggest_improvements():
    """建議改進方案"""
    
    print("\n" + "=" * 80)
    print("💡 改進建議")
    print("=" * 80)
    
    print("""
🔧 目前問題：
   - API 回傳的是累積總流量（GB），不是即時使用率
   - 欄位描述為 "網路使用率 (MB/s)" 但實際是總流量
   - 對使用者來說，這個數字意義不大

✅ 建議改進方案：

1. 【選項 A】真正的網路速度監控：
   - 實作時間間隔測量
   - 回傳即時 MB/s 或 Mbps
   - 需要在記憶體中儲存前次測量值

2. 【選項 B】簡化為總流量顯示：
   - 修改欄位描述為 "累積網路流量 (GB)"
   - 保持目前實作，但正確標示含義

3. 【選項 C】移除網路監控：
   - 如同磁碟使用率一樣移除
   - 專注於 CPU、記憶體、GPU 等更重要的指標

4. 【選項 D】增強版網路監控：
   - 分別顯示上傳/下載速度
   - 顯示活躍的網路介面
   - 提供歷史趨勢資料
""")

def main():
    print("🌐 網路使用率深度分析工具")
    print("=" * 80)
    print("📅 分析時間:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # 1. 解釋目前的運作機制
    explain_network_usage()
    
    # 2. 示範正確的速度計算
    demonstrate_network_speed_calculation()
    
    # 3. 顯示網路介面資訊
    show_network_interfaces()
    
    # 4. 提供改進建議
    suggest_improvements()
    
    print("\n" + "=" * 80)
    print("🎯 結論：目前的網路使用率實作需要改進以提供更有意義的資訊")
    print("=" * 80)

if __name__ == "__main__":
    main()