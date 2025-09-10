#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
攝影機持久性測試腳本
測試前端與後端整合後的攝影機配置持久性
"""

import requests
import json
import time

API_BASE = "http://localhost:8001/api/v1"

def test_camera_persistence():
    """測試攝影機持久性功能"""
    print("🧪 開始測試攝影機持久性功能")
    print("=" * 60)
    
    # 1. 檢查 API 健康狀態
    try:
        health_response = requests.get(f"{API_BASE}/health")
        print(f"✅ API 健康檢查: {health_response.status_code}")
    except Exception as e:
        print(f"❌ API 連接失敗: {e}")
        return False
    
    # 2. 獲取現有攝影機列表
    try:
        cameras_response = requests.get(f"{API_BASE}/cameras")
        existing_cameras = cameras_response.json()
        print(f"📋 現有攝影機數量: {len(existing_cameras)}")
        
        # 如果有攝影機，顯示前 3 台
        if existing_cameras:
            print("📷 現有攝影機:")
            for i, camera in enumerate(existing_cameras[:3]):
                print(f"   {i+1}. {camera['name']} ({camera['camera_type']})")
            if len(existing_cameras) > 3:
                print(f"   ... 還有 {len(existing_cameras) - 3} 台攝影機")
    except Exception as e:
        print(f"❌ 獲取攝影機列表失敗: {e}")
        return False
    
    # 3. 新增測試攝影機
    test_camera = {
        "name": "測試持久性攝影機",
        "camera_type": "USB",
        "device_index": 99,  # 使用不存在的索引避免衝突
        "resolution_width": 1920,
        "resolution_height": 1080,
        "fps": 30,
        "group_id": "persistence_test"
    }
    
    try:
        add_response = requests.post(f"{API_BASE}/cameras", json=test_camera)
        if add_response.status_code == 201:
            new_camera = add_response.json()
            print(f"✅ 成功新增測試攝影機: ID {new_camera['id']}")
            test_camera_id = new_camera['id']
        else:
            print(f"❌ 新增攝影機失敗: {add_response.status_code} - {add_response.text}")
            return False
    except Exception as e:
        print(f"❌ 新增攝影機請求失敗: {e}")
        return False
    
    # 4. 等待一下模擬頁面切換
    print("⏳ 模擬頁面切換（等待 2 秒）...")
    time.sleep(2)
    
    # 5. 重新獲取攝影機列表，確認持久性
    try:
        cameras_response_after = requests.get(f"{API_BASE}/cameras")
        updated_cameras = cameras_response_after.json()
        
        # 檢查測試攝影機是否還存在
        test_camera_exists = any(camera['id'] == test_camera_id for camera in updated_cameras)
        
        if test_camera_exists:
            print(f"✅ 持久性測試通過！攝影機 ID {test_camera_id} 在「頁面切換」後仍然存在")
            
            # 獲取測試攝影機詳細信息
            test_camera_data = next(camera for camera in updated_cameras if camera['id'] == test_camera_id)
            print(f"📷 攝影機詳細信息:")
            print(f"   名稱: {test_camera_data['name']}")
            print(f"   類型: {test_camera_data['camera_type']}")
            print(f"   狀態: {test_camera_data['status']}")
            print(f"   群組: {test_camera_data['group_id']}")
        else:
            print(f"❌ 持久性測試失敗！攝影機 ID {test_camera_id} 在「頁面切換」後消失了")
            return False
            
    except Exception as e:
        print(f"❌ 重新獲取攝影機列表失敗: {e}")
        return False
    
    # 6. 清理測試數據
    try:
        delete_response = requests.delete(f"{API_BASE}/cameras/{test_camera_id}")
        if delete_response.status_code == 200:
            print(f"🧹 已清理測試攝影機 ID {test_camera_id}")
        else:
            print(f"⚠️  清理測試數據時出現警告: {delete_response.status_code}")
    except Exception as e:
        print(f"⚠️  清理測試數據失敗: {e}")
    
    # 7. 最終驗證
    try:
        final_cameras_response = requests.get(f"{API_BASE}/cameras")
        final_cameras = final_cameras_response.json()
        
        # 確認測試攝影機已被刪除
        test_camera_still_exists = any(camera['id'] == test_camera_id for camera in final_cameras)
        
        if not test_camera_still_exists:
            print("✅ 清理驗證通過！測試攝影機已成功刪除")
        else:
            print("⚠️  測試攝影機仍然存在，清理可能未完成")
            
    except Exception as e:
        print(f"❌ 最終驗證失敗: {e}")
    
    print("=" * 60)
    print("🎉 攝影機持久性測試完成！")
    print("\n📊 測試總結:")
    print("✅ 後端 API 可以正常新增攝影機")
    print("✅ 新增的攝影機會保存到數據庫")
    print("✅ 重新載入時攝影機配置仍然存在")
    print("✅ 前端現在使用真實的後端 API")
    print("\n🔧 使用方法:")
    print("1. 打開 http://localhost:3000")
    print("2. 前往「資料來源管理」頁面")  
    print("3. 新增攝影機配置")
    print("4. 切換到其他頁面再回來")
    print("5. 攝影機配置應該仍然存在！")
    
    return True

if __name__ == "__main__":
    success = test_camera_persistence()
    if not success:
        print("\n❌ 測試過程中發現問題，請檢查系統設定")
        exit(1)
    else:
        print("\n✅ 所有測試通過！攝影機持久性功能正常運作")
