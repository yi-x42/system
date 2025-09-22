#!/usr/bin/env python3
"""
完整的影片分析功能測試
測試從影片列表選擇影片並執行分析的完整流程
"""

import requests
import json
import time

def test_complete_video_analysis():
    """測試完整的影片分析流程"""
    base_url = "http://localhost:8001/api/v1"
    
    print("=" * 60)
    print("🧪 完整影片分析功能測試")
    print("=" * 60)
    
    # 1. 檢查系統狀態
    print("1️⃣ 檢查系統狀態...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ 系統運行正常")
        else:
            print(f"   ❌ 系統狀態異常: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ 無法連接系統: {e}")
        return
    
    # 2. 獲取影片列表
    print("\n2️⃣ 獲取影片列表...")
    try:
        response = requests.get(f"{base_url}/video-files")
        if response.status_code == 200:
            video_data = response.json()
            videos = video_data.get('videos', [])
            print(f"   ✅ 找到 {len(videos)} 個影片")
            
            if videos:
                # 顯示第一個影片的資訊
                first_video = videos[0]
                print(f"   📹 第一個影片: {first_video.get('name', 'Unknown')}")
                print(f"      路徑: {first_video.get('file_path', 'Unknown')}")
                print(f"      解析度: {first_video.get('resolution', 'Unknown')}")
                print(f"      時長: {first_video.get('duration', 'Unknown')}")
            else:
                print("   ⚠️ 沒有找到影片檔案")
                return
        else:
            print(f"   ❌ 獲取影片列表失敗: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ 獲取影片列表錯誤: {e}")
        return
    
    # 3. 創建並執行分析任務
    print("\n3️⃣ 創建並執行分析任務...")
    try:
        first_video = videos[0]
        
        # 解析解析度
        resolution = first_video.get('resolution', '1920x1080')
        width, height = map(int, resolution.split('x'))
        
        task_data = {
            "task_type": "video_file",
            "source_info": {
                "file_path": first_video.get('file_path'),
                "original_filename": first_video.get('name'),
                "confidence_threshold": 0.5
            },
            "source_width": width,
            "source_height": height,
            "source_fps": 30.0
        }
        
        print(f"   📝 任務資料: {json.dumps(task_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(f"{base_url}/tasks/create-and-execute", json=task_data)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"   ✅ 任務創建並開始執行成功!")
            print(f"      任務 ID: {task_id}")
            print(f"      狀態: {result.get('status', 'unknown')}")
            print(f"      訊息: {result.get('message', 'No message')}")
            
            # 4. 監控任務狀態
            print(f"\n4️⃣ 監控任務 {task_id} 狀態...")
            max_wait_time = 60  # 最多等待60秒
            wait_time = 0
            check_interval = 3  # 每3秒檢查一次
            
            while wait_time < max_wait_time:
                try:
                    status_response = requests.get(f"{base_url}/tasks/{task_id}")
                    if status_response.status_code == 200:
                        task_status = status_response.json()
                        status = task_status.get('status', 'unknown')
                        
                        print(f"   ⏱️ {wait_time}s: 狀態 = {status}")
                        
                        if status == 'completed':
                            print(f"   ✅ 任務完成!")
                            end_time = task_status.get('end_time')
                            start_time = task_status.get('start_time')
                            print(f"      開始時間: {start_time}")
                            print(f"      結束時間: {end_time}")
                            break
                        elif status == 'failed':
                            print(f"   ❌ 任務失敗!")
                            break
                        elif status in ['scheduled', 'running', 'pending']:
                            time.sleep(check_interval)
                            wait_time += check_interval
                        else:
                            print(f"   ⚠️ 未知狀態: {status}")
                            break
                    else:
                        print(f"   ❌ 無法獲取任務狀態: {status_response.status_code}")
                        break
                except Exception as e:
                    print(f"   ❌ 狀態檢查錯誤: {e}")
                    break
            
            if wait_time >= max_wait_time:
                print(f"   ⏰ 等待超時 ({max_wait_time}s)")
            
            # 5. 檢查檢測結果
            print(f"\n5️⃣ 檢查檢測結果...")
            try:
                results_response = requests.get(f"{base_url}/tasks/{task_id}/results")
                if results_response.status_code == 200:
                    results_data = results_response.json()
                    detections = results_data.get('detections', [])
                    statistics = results_data.get('statistics', {})
                    
                    print(f"   📊 檢測結果統計:")
                    print(f"      總檢測數: {len(detections)}")
                    print(f"      統計資料: {json.dumps(statistics, indent=6, ensure_ascii=False)}")
                    
                    if detections:
                        print(f"   🔍 前3個檢測結果:")
                        for i, detection in enumerate(detections[:3]):
                            print(f"      {i+1}. 幀 {detection.get('frame_number', 'N/A')}: "
                                  f"{detection.get('object_type', 'unknown')} "
                                  f"(信心度: {detection.get('confidence', 0):.3f})")
                else:
                    print(f"   ❌ 無法獲取檢測結果: {results_response.status_code}")
            except Exception as e:
                print(f"   ❌ 檢測結果檢查錯誤: {e}")
            
        else:
            print(f"   ❌ 任務創建失敗: {response.status_code}")
            print(f"      回應: {response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ 任務創建錯誤: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ 完整影片分析功能測試完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_video_analysis()
