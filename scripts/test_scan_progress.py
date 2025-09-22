#!/usr/bin/env python3
"""
測試攝影機掃描進度條功能
這個腳本會模擬掃描過程來驗證進度條是否正常顯示
"""

import time
import requests
import json

def test_scan_progress():
    """測試掃描進度顯示"""
    print("🔍 測試攝影機掃描進度條...")
    
    base_url = "http://localhost:8001"
    scan_endpoint = f"{base_url}/api/v1/cameras/scan"
    
    print("📡 開始攝影機掃描測試...")
    start_time = time.time()
    
    try:
        # 使用較長的參數來模擬進度
        response = requests.get(scan_endpoint, params={
            "max_index": 6,
            "warmup_frames": 5,  # 增加暖機時間，讓掃描時間更長
            "force_probe": False,
            "retries": 2
        })
        response.raise_for_status()
        
        end_time = time.time()
        scan_duration = end_time - start_time
        
        scan_result = response.json()
        print(f"✅ 掃描完成！")
        print(f"⏱️ 掃描耗時: {scan_duration:.2f} 秒")
        print(f"📊 掃描結果:")
        print(f"   - 找到設備: {scan_result['count']}")
        print(f"   - 可用設備: {scan_result['available_indices']}")
        
        # 建議的進度條測試步驟
        print("\n🎯 前端進度條測試建議:")
        print(f"1. 預期掃描時間約: {scan_duration:.1f} 秒")
        print("2. 進度條應該從 0% 逐漸增長到 90%")
        print("3. API 完成後進度條跳到 100%")
        print("4. 然後顯示掃描結果")
        
        # 計算建議的進度更新間隔
        suggested_interval = scan_duration / 6  # 6個進度步驟 (0, 15, 30, 45, 60, 75, 90)
        print(f"5. 建議進度更新間隔: {suggested_interval:.1f} 秒")
        
        return scan_result, scan_duration
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 掃描測試失敗: {e}")
        return None, None

def suggest_progress_timing(scan_duration):
    """根據實際掃描時間建議進度條參數"""
    if scan_duration is None:
        return
    
    print("\n⚙️ 進度條參數建議:")
    
    # 計算合適的更新間隔
    steps = 6  # 0, 15, 30, 45, 60, 75, 90
    interval = max(100, min(500, scan_duration * 1000 / steps))  # 限制在100-500ms之間
    
    print(f"   setTimeout 間隔: {interval:.0f}ms")
    print(f"   總動畫時間: {steps * interval / 1000:.1f}s (實際掃描: {scan_duration:.1f}s)")
    
    if scan_duration < 1:
        print("   ⚠️ 掃描太快，建議增加 warmup_frames 或使用固定動畫時間")
    elif scan_duration > 3:
        print("   ✅ 掃描時間適中，進度條動畫應該正常")
    else:
        print("   📝 可以調整動畫速度以匹配實際掃描時間")

def test_progress_animation_code():
    """輸出建議的進度條代碼"""
    print("\n💻 建議的進度條動畫代碼:")
    print("```javascript")
    print("const progressAnimation = async () => {")
    print("  const steps = [0, 15, 30, 45, 60, 75, 90];")
    print("  for (const progress of steps) {")
    print("    setScanProgress(progress);")
    print("    await new Promise(resolve => setTimeout(resolve, 300));")
    print("  }")
    print("};")
    print("```")

def main():
    """主測試函數"""
    print("🚀 攝影機掃描進度條測試")
    print("=" * 50)
    
    # 檢查服務是否運行
    try:
        response = requests.get("http://localhost:8001/api/v1/health", timeout=3)
        print("✅ 後端服務正常運行")
    except:
        print("❌ 後端服務未運行，請先啟動 start.py")
        return
    
    try:
        response = requests.get("http://localhost:3001", timeout=3)
        print("✅ 前端服務正常運行")
    except:
        print("❌ 前端服務未運行，請檢查 React 開發伺服器")
    
    # 執行掃描測試
    scan_result, scan_duration = test_scan_progress()
    
    if scan_result:
        suggest_progress_timing(scan_duration)
        test_progress_animation_code()
        
        print("\n🔧 修復步驟:")
        print("1. 確保 setScanProgress() 正確調用")
        print("2. 檢查 Progress 組件的 value 屬性綁定")
        print("3. 驗證進度數字顯示正確")
        print("4. 測試取消按鈕功能")
        
        print("\n🌐 前端測試:")
        print("1. 開啟 http://localhost:3001")
        print("2. 導航到攝影機控制頁面")
        print("3. 點擊「自動掃描」按鈕")
        print("4. 觀察進度條是否從 0% 增長到 100%")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
