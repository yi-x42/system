#!/usr/bin/env python3
"""
測試刪除影片 API
"""

import requests
import os
from datetime import datetime

# API 基礎 URL
BASE_URL = "http://localhost:8001/api/v1"

def test_get_videos():
    """先獲取影片列表"""
    print("📁 獲取影片列表...")
    
    try:
        response = requests.get(f"{BASE_URL}/frontend/videos")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 獲取成功！共找到 {data['total']} 個影片")
            
            if data['videos']:
                print("\n📋 影片列表：")
                for i, video in enumerate(data['videos'], 1):
                    print(f"  {i}. {video['name']} ({video['size']}) - {video['status']}")
                    
                return data['videos']
            else:
                print("❌ 沒有找到任何影片")
                return []
        else:
            print(f"❌ 請求失敗: {response.status_code}")
            print(f"回應: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ 請求出錯: {e}")
        return []

def test_delete_video(video_id):
    """測試刪除影片"""
    print(f"\n🗑️  測試刪除影片: {video_id}")
    
    try:
        response = requests.delete(f"{BASE_URL}/frontend/videos/{video_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 刪除成功！")
            print(f"訊息: {data['message']}")
            print(f"已刪除檔案: {data['deleted_file']}")
            return True
        else:
            print(f"❌ 刪除失敗: {response.status_code}")
            print(f"回應: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 請求出錯: {e}")
        return False

def create_test_file():
    """創建測試檔案用於刪除測試"""
    videos_dir = "D:/project/system/yolo_backend/uploads/videos"
    
    # 確保目錄存在
    os.makedirs(videos_dir, exist_ok=True)
    
    # 創建一個小的測試檔案
    test_filename = f"test_delete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    test_filepath = os.path.join(videos_dir, test_filename)
    
    with open(test_filepath, 'w') as f:
        f.write("# 這是一個測試檔案，用於測試刪除功能\n")
    
    print(f"📄 已創建測試檔案: {test_filename}")
    return test_filename

if __name__ == "__main__":
    print("🚀 開始測試刪除影片功能")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 先獲取現有影片列表
    videos = test_get_videos()
    
    # 2. 如果沒有影片，創建一個測試檔案
    if not videos:
        print("\n🔧 沒有現有影片，創建測試檔案...")
        test_filename = create_test_file()
        
        # 重新獲取影片列表
        videos = test_get_videos()
        
        if not videos:
            print("❌ 創建測試檔案後仍無法獲取影片列表")
            exit(1)
    
    # 3. 選擇第一個影片進行刪除測試
    first_video = videos[0]
    video_id = first_video['id']
    
    print(f"\n🎯 選擇測試目標: {video_id}")
    
    # 確認刪除
    confirm = input(f"確定要刪除 '{video_id}' 嗎？(y/N): ").lower()
    
    if confirm == 'y':
        # 4. 測試刪除
        success = test_delete_video(video_id)
        
        if success:
            print("\n🔍 驗證刪除結果...")
            # 重新獲取影片列表確認刪除
            updated_videos = test_get_videos()
            
            # 檢查是否還存在
            deleted_video_exists = any(v['id'] == video_id for v in updated_videos)
            
            if not deleted_video_exists:
                print("✅ 刪除驗證成功！影片已從列表中移除")
            else:
                print("❌ 刪除驗證失敗！影片仍在列表中")
        else:
            print("❌ 刪除測試失敗")
    else:
        print("❌ 用戶取消刪除測試")
    
    print("\n🏁 測試完成")
