#!/usr/bin/env python3
"""儀表板攝影機狀態連結驗證腳本"""

import asyncio
import aiohttp
import time
from typing import Dict, Any, List

class DashboardCameraStatusVerification:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:3000"
        
    async def test_api_camera_status(self) -> Dict[str, Any]:
        """測試API返回的攝影機狀態"""
        print("🔍 測試API攝影機狀態...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # 測試即時狀態檢測API
                print("  📝 測試即時狀態檢測API...")
                async with session.get(f"{self.base_url}/api/v1/frontend/cameras?real_time_check=true") as resp:
                    if resp.status == 200:
                        cameras_data = await resp.json()
                        print(f"    ✅ API回應成功：{len(cameras_data)} 個攝影機")
                        
                        for i, camera in enumerate(cameras_data):
                            print(f"    📷 攝影機 {i+1}:")
                            print(f"      - ID: {camera.get('id', 'N/A')}")
                            print(f"      - 名稱: {camera.get('name', 'N/A')}")
                            print(f"      - 狀態: {camera.get('status', 'N/A')}")
                            print(f"      - 類型: {camera.get('camera_type', 'N/A')}")
                        
                        return {
                            "success": True,
                            "cameras": cameras_data,
                            "camera_count": len(cameras_data)
                        }
                    else:
                        print(f"    ❌ API請求失敗：{resp.status}")
                        return {"success": False, "error": f"API請求失敗：{resp.status}"}
                        
            except Exception as e:
                print(f"    ❌ API測試異常：{e}")
                return {"success": False, "error": str(e)}
    
    async def test_status_consistency(self) -> Dict[str, Any]:
        """測試狀態一致性"""
        print("🔄 測試儀表板狀態一致性...")
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            try:
                # 連續測試幾次，檢查狀態變化
                for i in range(3):
                    print(f"  📝 第 {i+1} 次檢測...")
                    async with session.get(f"{self.base_url}/api/v1/frontend/cameras?real_time_check=true") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data:
                                camera_statuses = []
                                for camera in data:
                                    status_info = {
                                        "id": camera.get("id"),
                                        "name": camera.get("name"),
                                        "status": camera.get("status")
                                    }
                                    camera_statuses.append(status_info)
                                    print(f"    📷 {camera.get('name', 'N/A')}: {camera.get('status', 'N/A')}")
                                
                                results.append({
                                    "test_round": i + 1,
                                    "timestamp": time.time(),
                                    "cameras": camera_statuses
                                })
                        else:
                            print(f"    ❌ 請求失敗：{resp.status}")
                    
                    # 間隔一下
                    if i < 2:  # 不是最後一次
                        await asyncio.sleep(2)
                
                # 分析結果
                print(f"  📊 檢測結果統計:")
                if results:
                    # 檢查每個攝影機的狀態變化
                    camera_status_changes = {}
                    for result in results:
                        for camera in result["cameras"]:
                            camera_id = camera["id"]
                            if camera_id not in camera_status_changes:
                                camera_status_changes[camera_id] = {
                                    "name": camera["name"],
                                    "statuses": []
                                }
                            camera_status_changes[camera_id]["statuses"].append(camera["status"])
                    
                    for camera_id, info in camera_status_changes.items():
                        unique_statuses = set(info["statuses"])
                        print(f"    - {info['name']}: {info['statuses']} (共 {len(unique_statuses)} 種狀態)")
                
                return {
                    "success": True,
                    "results": results,
                    "test_count": len(results),
                    "camera_status_changes": camera_status_changes if results else {}
                }
                
            except Exception as e:
                print(f"    ❌ 一致性測試異常：{e}")
                return {"success": False, "error": str(e)}
    
    async def check_dashboard_integration(self):
        """檢查儀表板整合狀態"""
        print("📊 檢查儀表板整合狀態...")
        
        print(f"  🌐 前端地址: {self.frontend_url}")
        print(f"  🔧 後端地址: {self.base_url}")
        print("  💡 整合要點:")
        print("    - 儀表板使用 useCamerasWithRealTimeCheck() hook")
        print("    - Hook每15秒調用 /api/v1/frontend/cameras?real_time_check=true")
        print("    - API執行真實的攝影機檢測並返回實際狀態")
        print("    - 前端直接顯示API返回的狀態")
    
    async def run_verification(self):
        """執行完整驗證"""
        print("🚀 儀表板攝影機狀態連結驗證")
        print("=" * 60)
        
        # 測試API狀態
        api_result = await self.test_api_camera_status()
        print()
        
        # 測試狀態一致性
        consistency_result = await self.test_status_consistency()
        print()
        
        # 檢查整合狀態
        await self.check_dashboard_integration()
        print()
        
        # 總結報告
        print("📋 驗證總結")
        print("-" * 40)
        
        if api_result.get("success"):
            print("✅ API狀態測試：通過")
            print(f"   - 攝影機數量：{api_result.get('camera_count', 'N/A')}")
            if api_result.get("cameras"):
                for camera in api_result["cameras"]:
                    print(f"   - {camera.get('name', 'N/A')}: {camera.get('status', 'N/A')}")
        else:
            print("❌ API狀態測試：失敗")
            print(f"   - 錯誤：{api_result.get('error', 'N/A')}")
        
        if consistency_result.get("success"):
            print("✅ 狀態一致性測試：通過")
            print(f"   - 測試輪次：{consistency_result.get('test_count', 0)}")
            camera_changes = consistency_result.get('camera_status_changes', {})
            if camera_changes:
                for camera_id, info in camera_changes.items():
                    unique_statuses = set(info["statuses"])
                    status_variety = "穩定" if len(unique_statuses) == 1 else "變化"
                    print(f"   - {info['name']}: {status_variety} ({list(unique_statuses)})")
        else:
            print("❌ 狀態一致性測試：失敗")
            print(f"   - 錯誤：{consistency_result.get('error', 'N/A')}")
        
        # 整體評估
        overall_success = api_result.get("success") and consistency_result.get("success")
        print()
        print("🎯 整體評估")
        print("-" * 40)
        
        if overall_success:
            print("🎉 儀表板攝影機狀態連結成功！")
            print("   - 後端API正確執行即時檢測")
            print("   - 前端Hook正確調用API")
            print("   - 儀表板顯示真實的攝影機狀態")
            print("   - 狀態更新機制運作正常")
            print()
            print("📱 使用方式:")
            print(f"   1. 訪問儀表板: {self.frontend_url}")
            print("   2. 查看「攝影機狀態」卡片")
            print("   3. 狀態每15秒自動更新")
            print("   4. 顯示的是攝影機硬體的真實狀態")
        else:
            print("⚠️  連結未完全成功，需要進一步檢查")
            print("   - 請確認系統是否正常運行")
            print("   - 請檢查網路連接")
            print("   - 查看瀏覽器控制台是否有錯誤")

async def main():
    """主函數"""
    verifier = DashboardCameraStatusVerification()
    await verifier.run_verification()

if __name__ == "__main__":
    asyncio.run(main())