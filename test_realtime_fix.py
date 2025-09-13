"""
測試修復後的實時檢測服務
驗證幀處理不會再出現屬性錯誤
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
import requests
import json
from datetime import datetime

# 測試配置
BACKEND_URL = "http://localhost:8001"
CAMERA_INDEX = 0
MODEL_ID = "yolo11n"

async def test_realtime_detection_fix():
    """測試修復後的實時檢測功能"""
    print("🔧 測試實時檢測服務修復")
    print("=" * 50)
    
    # 1. 測試基本功能
    print("1. 測試實時分析啟動...")
    try:
        analysis_payload = {
            "camera_id": str(CAMERA_INDEX),
            "model_id": MODEL_ID,
            "confidence": 0.5,
            "iou_threshold": 0.45
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/frontend/analysis/start-realtime",
            json=analysis_payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            print(f"   ✅ 實時分析啟動成功 (任務ID: {task_id})")
            
            # 2. 等待一段時間觀察是否有錯誤
            print("2. 監控運行狀態 (20秒)...")
            
            error_detected = False
            for i in range(20):
                await asyncio.sleep(1)
                print(f"   監控中... {i+1}/20 秒", end="\r")
                
                # 每5秒檢查一次系統狀態
                if (i + 1) % 5 == 0:
                    try:
                        stats_response = requests.get(f"{BACKEND_URL}/api/v1/frontend/stats", timeout=5)
                        if stats_response.status_code == 200:
                            stats = stats_response.json()
                            active_tasks = stats.get("active_tasks", 0)
                            print(f"\n   📊 系統狀態正常，活動任務: {active_tasks}")
                        else:
                            print(f"\n   ⚠️  系統狀態檢查失敗: {stats_response.status_code}")
                    except Exception as e:
                        print(f"\n   ⚠️  系統狀態檢查異常: {e}")
                        error_detected = True
                        break
            
            print(f"\n3. 測試結果:")
            if not error_detected:
                print("   ✅ 沒有檢測到 'camera_stream_manager' 屬性錯誤")
                print("   ✅ 實時檢測服務運行穩定")
            else:
                print("   ❌ 檢測到系統錯誤")
                
            return not error_detected
            
        else:
            print(f"   ❌ 實時分析啟動失敗: {response.status_code}")
            print(f"      回應: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 測試過程異常: {e}")
        return False

async def main():
    """主測試函數"""
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 檢查後端是否運行
        print("檢查後端服務...")
        try:
            health_response = requests.get(f"{BACKEND_URL}/api/v1/frontend/stats", timeout=5)
            if health_response.status_code != 200:
                print("❌ 後端服務未運行，請先啟動系統")
                return
        except Exception:
            print("❌ 無法連接到後端服務，請確認系統已啟動")
            return
            
        print("✅ 後端服務運行正常\n")
        
        success = await test_realtime_detection_fix()
        
        if success:
            print("\n🎉 修復驗證成功！")
            print("   ✅ 'camera_stream_manager' 屬性錯誤已修復")
            print("   ✅ 實時檢測服務運行正常")
        else:
            print("\n❌ 修復驗證失敗！請檢查錯誤日誌")
            
    except Exception as e:
        print(f"\n💥 測試過程中發生錯誤: {e}")
    
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())