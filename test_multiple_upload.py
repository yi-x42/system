#!/usr/bin/env python3
"""
測試前端上傳功能是否正常
"""

import requests
import time
from datetime import datetime

# API 基礎 URL
BASE_URL = "http://localhost:8001/api/v1"

def test_multiple_uploads():
    """測試多次上傳功能"""
    print("🎬 測試多次影片上傳功能")
    print("=" * 50)
    
    # 使用現有的測試影片檔案進行多次上傳
    test_video_path = "D:/project/system/yolo_backend/uploads/videos/20250909_221552_test_video.mp4"
    
    try:
        for i in range(3):
            print(f"\n📤 第 {i+1} 次上傳測試")
            
            with open(test_video_path, "rb") as video_file:
                files = {
                    'file': (f'test_video_{i+1}.mp4', video_file, 'video/mp4')
                }
                
                print(f"📁 上傳檔案: test_video_{i+1}.mp4")
                
                response = requests.post(
                    f"{BASE_URL}/frontend/data-sources/upload/video",
                    files=files,
                    timeout=30
                )
                
                print(f"🌐 HTTP 狀態碼: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 第 {i+1} 次上傳成功!")
                    print(f"   - 檔案ID: {result.get('source_id')}")
                    print(f"   - 檔案路徑: {result.get('file_path')}")
                    print(f"   - 原始檔名: {result.get('original_name')}")
                else:
                    print(f"❌ 第 {i+1} 次上傳失敗: {response.status_code}")
                    print(f"錯誤詳情: {response.text}")
            
            # 稍作延遲
            time.sleep(1)
                    
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")

def check_uploaded_files():
    """檢查已上傳的檔案列表"""
    print(f"\n📋 檢查上傳檔案列表")
    print("=" * 50)
    
    # 檢查上傳目錄中的檔案
    import os
    upload_dir = "D:/project/system/yolo_backend/uploads/videos"
    
    if os.path.exists(upload_dir):
        files = os.listdir(upload_dir)
        print(f"✅ 找到 {len(files)} 個檔案:")
        
        for i, filename in enumerate(files, 1):
            file_path = os.path.join(upload_dir, filename)
            size = os.path.getsize(file_path)
            mod_time = os.path.getmtime(file_path)
            mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"   {i}. {filename}")
            print(f"      大小: {size} bytes")
            print(f"      修改時間: {mod_time_str}")
    else:
        print(f"❌ 上傳目錄不存在: {upload_dir}")

if __name__ == "__main__":
    print("🚀 開始測試多次上傳功能")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 檢查目前檔案狀態
    check_uploaded_files()
    
    # 2. 測試多次上傳
    test_multiple_uploads()
    
    # 3. 再次檢查檔案狀態
    check_uploaded_files()
    
    print("\n🏁 測試完成")
