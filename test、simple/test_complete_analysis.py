"""
測試完整的分析流程：創建任務 -> 執行分析 -> 檢查結果
"""

import requests
import json
import time
import os

# API 基礎 URL
BASE_URL = "http://localhost:8001/api/v1"

def test_create_and_execute_analysis():
    """測試創建並執行分析任務"""
    
    print("🎬 開始測試完整的影片分析流程...")
    
    # 檢查影片檔案是否存在
    video_path = "D:/project/system/yolo_backend/uploads/videos/20250909_231421_3687560-uhd_2160_3840_30fps.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ 影片檔案不存在: {video_path}")
        return
    
    print(f"✅ 影片檔案存在: {video_path}")
    
    # 準備任務資料
    task_data = {
        "task_type": "video_file",
        "source_info": {
            "file_path": video_path,
            "original_filename": "test_video.mp4",
            "confidence_threshold": 0.5
        },
        "source_width": 2160,
        "source_height": 3840,
        "source_fps": 30.0
    }
    
    try:
        # 1. 創建並執行分析任務
        print("\n📝 步驟 1: 創建並執行分析任務...")
        
        response = requests.post(
            f"{BASE_URL}/tasks/create-and-execute",
            json=task_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ 創建任務失敗: {response.status_code}")
            print(f"錯誤內容: {response.text}")
            return
        
        result = response.json()
        print(f"✅ 任務創建成功!")
        print(f"   任務 ID: {result['task_id']}")
        print(f"   狀態: {result['status']}")
        print(f"   訊息: {result['message']}")
        
        task_id = result['task_id']
        
        # 2. 檢查任務狀態
        print(f"\n🔄 步驟 2: 檢查任務狀態...")
        
        for i in range(30):  # 最多等待30秒
            time.sleep(1)
            
            status_response = requests.get(f"{BASE_URL}/tasks/{task_id}")
            if status_response.status_code == 200:
                task_status = status_response.json()
                current_status = task_status.get('status', 'unknown')
                
                print(f"   檢查 {i+1}/30: 狀態 = {current_status}")
                
                if current_status == 'completed':
                    print("✅ 任務執行完成!")
                    break
                elif current_status == 'failed':
                    print("❌ 任務執行失敗!")
                    return
            else:
                print(f"   無法獲取任務狀態: {status_response.status_code}")
        
        # 3. 獲取檢測結果
        print(f"\n📊 步驟 3: 獲取檢測結果...")
        
        results_response = requests.get(f"{BASE_URL}/tasks/{task_id}/results")
        
        if results_response.status_code == 200:
            detection_results = results_response.json()
            
            print(f"✅ 檢測結果獲取成功!")
            print(f"   檢測到的物件數量: {len(detection_results.get('detections', []))}")
            
            # 顯示前幾個檢測結果
            detections = detection_results.get('detections', [])
            if detections:
                print(f"\n🎯 前5個檢測結果:")
                for i, detection in enumerate(detections[:5]):
                    print(f"   {i+1}. 幀 {detection['frame_number']}: {detection['object_type']} "
                          f"(信心度: {detection['confidence']:.2f}, "
                          f"位置: ({detection['center_x']:.0f}, {detection['center_y']:.0f}))")
            
            # 統計資訊
            object_counts = {}
            for detection in detections:
                obj_type = detection['object_type']
                object_counts[obj_type] = object_counts.get(obj_type, 0) + 1
            
            if object_counts:
                print(f"\n📈 物件統計:")
                for obj_type, count in object_counts.items():
                    print(f"   {obj_type}: {count} 次檢測")
                    
        else:
            print(f"❌ 無法獲取檢測結果: {results_response.status_code}")
            print(f"錯誤內容: {results_response.text}")
        
        print(f"\n🎉 測試完成! 任務 ID: {task_id}")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")


def test_system_health():
    """測試系統健康狀況"""
    print("🏥 檢查系統健康狀況...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 系統正常運行")
        else:
            print(f"❌ 系統狀態異常: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 無法連接到系統: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 YOLOv11 分析系統完整測試")
    print("=" * 60)
    
    # 先檢查系統健康狀況
    test_system_health()
    
    print("\n" + "-" * 40)
    
    # 測試完整分析流程
    test_create_and_execute_analysis()
    
    print("\n" + "=" * 60)
    print("✅ 測試結束")
    print("=" * 60)
