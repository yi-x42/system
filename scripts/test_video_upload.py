#!/usr/bin/env python3
"""
測試影片上傳 API
"""

import requests
import os
from datetime import datetime

# API 基礎 URL
BASE_URL = "http://localhost:8001/api/v1"

def test_video_upload():
    """測試影片上傳功能"""
    print("🎬 測試影片上傳 API")
    print("=" * 50)
    
    # 使用現有的測試影片檔案
    upload_dir = "D:/project/system/yolo_backend/uploads/videos"
    existing_files = os.listdir(upload_dir) if os.path.exists(upload_dir) else []
    
    if existing_files:
        test_video_path = os.path.join(upload_dir, existing_files[0])
        print(f"✅ 使用現有測試影片: {existing_files[0]}")
    else:
        print("❌ 沒有可用的測試影片檔案")
        return
    
    try:
        # 準備檔案上傳
        with open(test_video_path, "rb") as video_file:
            files = {
                'file': ('test_video.mp4', video_file, 'video/mp4')
            }
            
            print(f"📤 上傳檔案: {test_video_path}")
            print(f"📁 目標目錄: {BASE_URL}/frontend/data-sources/upload/video")
            
            # 發送上傳請求
            response = requests.post(
                f"{BASE_URL}/frontend/data-sources/upload/video",
                files=files,
                timeout=30
            )
            
            print(f"🌐 HTTP 狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 上傳成功!")
                print(f"📋 回應資料:")
                print(f"   - 訊息: {result.get('message')}")
                print(f"   - 來源ID: {result.get('source_id')}")
                print(f"   - 檔案路徑: {result.get('file_path')}")
                print(f"   - 原始檔名: {result.get('original_name')}")
                print(f"   - 檔案大小: {result.get('size')} bytes")
                
                if 'video_info' in result:
                    info = result['video_info']
                    print(f"   - 影片資訊:")
                    print(f"     * 時長: {info.get('duration')}秒")
                    print(f"     * FPS: {info.get('fps')}")
                    print(f"     * 解析度: {info.get('resolution')}")
                    print(f"     * 總幀數: {info.get('frame_count')}")
                
                # 檢查檔案是否真的被保存
                uploaded_path = result.get('file_path')
                if uploaded_path and os.path.exists(uploaded_path):
                    print(f"✅ 檔案已成功保存到: {uploaded_path}")
                else:
                    print(f"❌ 檔案未找到: {uploaded_path}")
                    
            else:
                print(f"❌ 上傳失敗: {response.status_code}")
                print(f"錯誤詳情: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API 服務器，請確認後端服務是否啟動")
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")

def check_upload_directory():
    """檢查上傳目錄"""
    print(f"\n📁 檢查上傳目錄")
    print("=" * 50)
    
    upload_dir = "D:/project/system/yolo_backend/uploads/videos"
    
    if os.path.exists(upload_dir):
        files = os.listdir(upload_dir)
        print(f"✅ 上傳目錄存在: {upload_dir}")
        print(f"📊 目錄中的檔案數量: {len(files)}")
        
        if files:
            print("📋 檔案列表:")
            for i, filename in enumerate(files[:5], 1):  # 只顯示前5個
                file_path = os.path.join(upload_dir, filename)
                size = os.path.getsize(file_path)
                print(f"   {i}. {filename} ({size} bytes)")
            
            if len(files) > 5:
                print(f"   ... 還有 {len(files) - 5} 個檔案")
        else:
            print("📭 目錄為空")
    else:
        print(f"❌ 上傳目錄不存在: {upload_dir}")

if __name__ == "__main__":
    print("🚀 開始測試影片上傳功能")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 檢查上傳目錄
    check_upload_directory()
    
    # 2. 測試上傳功能
    test_video_upload()
    
    print("\n🏁 測試完成")
