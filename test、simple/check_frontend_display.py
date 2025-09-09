#!/usr/bin/env python3
"""
檢查前端頁面是否正確顯示模型
"""

import requests
import json
import time

def check_frontend_models_display():
    """檢查前端是否正確顯示模型選擇器"""
    print("=" * 60)
    print("🔍 檢查前端模型顯示")
    print("=" * 60)
    
    # 首先檢查API是否正常
    print("1️⃣ 檢查後端API...")
    try:
        response = requests.get("http://localhost:8001/api/v1/frontend/models/active")
        if response.status_code == 200:
            active_models = response.json()
            print(f"   ✅ 後端API正常，活動模型: {len(active_models)} 個")
            if active_models:
                print(f"   🎯 活動模型: {[m.get('id') for m in active_models]}")
        else:
            print(f"   ❌ 後端API異常: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ 後端API錯誤: {e}")
        return
    
    print(f"\n2️⃣ 檢查前端頁面...")
    print("   💡 請手動檢查以下內容:")
    print("   1. 打開瀏覽器到 http://localhost:3000")
    print("   2. 找到 '偵測模型' 下拉選單")
    print("   3. 點擊下拉選單，應該看到 'yolo11n.pt' 選項")
    print("   4. 選擇模型後，影片卡片中的 '開始分析此影片' 按鈕應該變為可點擊狀態")
    print("   5. 按鈕不再是灰色，且點擊時會執行分析")
    
    print(f"\n3️⃣ 如果模型選擇器為空:")
    print("   💡 解決方案:")
    print("   1. 在瀏覽器中按 F5 刷新頁面")
    print("   2. 或按 Ctrl+Shift+R 強制刷新")
    print("   3. 檢查瀏覽器開發者工具的Console是否有錯誤")
    
    print("=" * 60)
    print("✅ 檢查完成")
    print("=" * 60)

if __name__ == "__main__":
    check_frontend_models_display()
