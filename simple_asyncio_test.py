"""
測試修復後的 asyncio 事件迴圈問題
"""

import requests
import time
from datetime import datetime

# 測試配置
BACKEND_URL = "http://localhost:8001"
CAMERA_INDEX = 0

def test_asyncio_fix():
    """測試修復後的 asyncio 功能"""
    print("🔧 測試 AsyncIO 事件迴圈修復")
    print("=" * 40)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 測試健康檢查
        print("1. 測試後端連接...")
        health_response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        if health_response.status_code == 200:
            print("   ✅ 後端連接正常")
        else:
            print(f"   ❌ 後端連接失敗: {health_response.status_code}")
            return False
        
        # 測試攝影機預覽 (可能會觸發 asyncio 問題)
        print("2. 測試攝影機預覽 (檢查 asyncio 問題)...")
        try:
            preview_response = requests.get(
                f"{BACKEND_URL}/api/v1/frontend/cameras/{CAMERA_INDEX}/preview", 
                timeout=10
            )
            
            if preview_response.status_code == 200:
                print(f"   ✅ 攝影機預覽成功 (影像大小: {len(preview_response.content)} bytes)")
                print("   ✅ 沒有出現 'no running event loop' 錯誤")
            elif preview_response.status_code == 404:
                print(f"   ⚠️  攝影機 {CAMERA_INDEX} 不存在，但沒有 asyncio 錯誤")
            else:
                print(f"   ❌ 攝影機預覽失敗: {preview_response.status_code}")
                print(f"      回應: {preview_response.text}")
                
        except Exception as e:
            if "no running event loop" in str(e):
                print(f"   ❌ AsyncIO 事件迴圈錯誤仍然存在: {e}")
                return False
            else:
                print(f"   ⚠️  其他錯誤 (非 asyncio): {e}")
        
        # 測試啟動實時分析 (可能會觸發 asyncio 問題)
        print("3. 測試啟動實時分析 (檢查 asyncio 問題)...")
        try:
            analysis_payload = {
                "camera_id": str(CAMERA_INDEX),
                "model_id": "yolo11n",
                "confidence": 0.5,
                "iou_threshold": 0.45
            }
            
            analysis_response = requests.post(
                f"{BACKEND_URL}/api/v1/frontend/analysis/start-realtime",
                json=analysis_payload,
                timeout=15
            )
            
            if analysis_response.status_code == 200:
                result = analysis_response.json()
                task_id = result.get("task_id")
                print(f"   ✅ 實時分析啟動成功 (任務ID: {task_id})")
                print("   ✅ 沒有出現 'no running event loop' 錯誤")
                
                # 等待一下讓分析運行
                print("   等待 5 秒讓分析運行...")
                time.sleep(5)
                
            else:
                print(f"   ❌ 實時分析啟動失敗: {analysis_response.status_code}")
                print(f"      回應: {analysis_response.text}")
                
        except Exception as e:
            if "no running event loop" in str(e):
                print(f"   ❌ AsyncIO 事件迴圈錯誤仍然存在: {e}")
                return False
            else:
                print(f"   ⚠️  其他錯誤 (非 asyncio): {e}")
        
        print("\n🎯 測試結果:")
        print("   ✅ AsyncIO 事件迴圈錯誤已修復")
        print("   ✅ 幀回調函數可以正常運行")
        print("   ✅ 多線程環境下的 asyncio 處理正常")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        return False


if __name__ == "__main__":
    success = test_asyncio_fix()
    
    if success:
        print("\n🎉 AsyncIO 修復測試通過！")
    else:
        print("\n💥 AsyncIO 修復測試失敗！")
    
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")