#!/usr/bin/env python3
"""
測試影片列表 API
"""

import requests
import json
from datetime import datetime

# API 基礎 URL
BASE_URL = "http://localhost:8001/api/v1"

def test_video_list_api():
    """測試影片列表 API"""
    print("📋 測試影片列表 API")
    print("=" * 50)
    
    try:
        # 測試影片列表端點
        response = requests.get(f"{BASE_URL}/frontend/video-list", timeout=10)
        
        print(f"🌐 HTTP 狀態碼: {response.status_code}")
        print(f"📄 回應內容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API 調用成功!")
            print(f"📊 影片總數: {result.get('total', 0)}")
            
            videos = result.get('videos', [])
            if videos:
                print(f"📋 影片列表:")
                for i, video in enumerate(videos, 1):
                    print(f"   {i}. {video['name']}")
                    print(f"      上傳時間: {video['upload_time']}")
                    print(f"      檔案大小: {video['size']}")
                    print(f"      時長: {video.get('duration', '未知')}")
                    print(f"      解析度: {video.get('resolution', '未知')}")
                    print(f"      狀態: {video['status']}")
                    print()
            else:
                print("📭 沒有找到影片檔案")
                
        else:
            print(f"❌ API 調用失敗: {response.status_code}")
            print(f"錯誤詳情: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API 服務器")
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")

def test_available_endpoints():
    """測試可用的端點"""
    print(f"\n🔍 測試相關端點")
    print("=" * 50)
    
    endpoints = [
        "/frontend/stats",
        "/frontend/video-list",
        "/frontend/data-sources",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"✅ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: 無法訪問 ({str(e)[:50]})")

if __name__ == "__main__":
    print("🚀 開始測試影片列表 API")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 測試可用端點
    test_available_endpoints()
    
    # 2. 測試影片列表 API
    test_video_list_api()
    
    print("\n🏁 測試完成")
