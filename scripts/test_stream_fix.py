#!/usr/bin/env python3
"""測試攝影機串流修復"""

import sys
import os

# 添加專案路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

async def test_stream_endpoint():
    """測試攝影機串流端點"""
    print("🧪 測試攝影機串流修復...")
    
    try:
        from fastapi.testclient import TestClient
        from yolo_backend.app.main import app
        
        client = TestClient(app)
        
        # 測試攝影機串流端點
        print("📹 測試攝影機串流端點...")
        response = client.get("/api/v1/frontend/cameras/0/stream")
        
        if response.status_code == 200:
            print("✅ 攝影機串流端點正常回應")
        else:
            print(f"❌ 攝影機串流端點回應錯誤: {response.status_code}")
            print(f"   錯誤詳細: {response.text}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_stream_endpoint())