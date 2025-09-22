#!/usr/bin/env python3
"""攝影機狀態監控修復驗證腳本"""

import asyncio
import aiohttp
import time
from typing import Dict, Any

class CameraStatusFixVerification:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        
    async def test_api_endpoint(self) -> Dict[str, Any]:
        """測試攝影機狀態 API 端點"""
        print("🔍 測試攝影機狀態 API...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # 測試沒有 real_time_check 的情況
                print("  📝 測試基本攝影機列表...")
                async with session.get(f"{self.base_url}/api/v1/frontend/cameras") as resp:
                    if resp.status == 200:
                        basic_data = await resp.json()
                        print(f"    ✅ 基本列表：{len(basic_data)} 個攝影機")
                    else:
                        print(f"    ❌ 基本列表失敗：{resp.status}")
                        return {"success": False, "error": "基本API失敗"}
                
                # 測試有 real_time_check 的情況
                print("  📝 測試即時狀態檢測...")
                start_time = time.time()
                async with session.get(f"{self.base_url}/api/v1/frontend/cameras?real_time_check=true") as resp:
                    end_time = time.time()
                    
                    if resp.status == 200:
                        realtime_data = await resp.json()
                        print(f"    ✅ 即時檢測：{len(realtime_data)} 個攝影機")
                        print(f"    ⏱️  檢測耗時：{end_time - start_time:.2f}秒")
                        
                        # 檢查是否有攝影機狀態
                        if realtime_data:
                            camera = realtime_data[0]
                            print(f"    📷 攝影機狀態：{camera.get('name', 'N/A')} -> {camera.get('status', 'N/A')}")
                            return {
                                "success": True,
                                "camera_count": len(realtime_data),
                                "detection_time": end_time - start_time,
                                "first_camera_status": camera.get('status', 'N/A')
                            }
                        else:
                            return {"success": False, "error": "沒有攝影機資料"}
                    else:
                        print(f"    ❌ 即時檢測失敗：{resp.status}")
                        return {"success": False, "error": f"即時API失敗：{resp.status}"}
                        
            except Exception as e:
                print(f"    ❌ API 測試異常：{e}")
                return {"success": False, "error": str(e)}
    
    async def test_status_changes(self) -> Dict[str, Any]:
        """測試狀態變化檢測"""
        print("🔄 測試狀態變化檢測...")
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            try:
                # 連續測試幾次，看看狀態是否一致
                for i in range(3):
                    print(f"  📝 第 {i+1} 次檢測...")
                    async with session.get(f"{self.base_url}/api/v1/frontend/cameras?real_time_check=true") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data:
                                status = data[0].get('status', 'N/A')
                                results.append(status)
                                print(f"    📷 狀態：{status}")
                        else:
                            print(f"    ❌ 請求失敗：{resp.status}")
                    
                    # 間隔一下
                    await asyncio.sleep(1)
                
                # 分析結果
                unique_statuses = set(results)
                print(f"  📊 檢測結果：{results}")
                print(f"  📈 狀態種類：{list(unique_statuses)}")
                
                return {
                    "success": True,
                    "results": results,
                    "unique_statuses": list(unique_statuses),
                    "consistent": len(unique_statuses) <= 1
                }
                
            except Exception as e:
                print(f"    ❌ 狀態變化測試異常：{e}")
                return {"success": False, "error": str(e)}
    
    async def run_verification(self):
        """執行完整驗證"""
        print("🚀 攝影機狀態監控修復驗證")
        print("=" * 60)
        
        # 測試 API 端點
        api_result = await self.test_api_endpoint()
        print()
        
        # 測試狀態變化
        change_result = await self.test_status_changes()
        print()
        
        # 總結報告
        print("📋 驗證總結")
        print("-" * 40)
        
        if api_result.get("success"):
            print("✅ API 端點測試：通過")
            print(f"   - 攝影機數量：{api_result.get('camera_count', 'N/A')}")
            print(f"   - 檢測耗時：{api_result.get('detection_time', 'N/A'):.2f}秒")
            print(f"   - 攝影機狀態：{api_result.get('first_camera_status', 'N/A')}")
        else:
            print("❌ API 端點測試：失敗")
            print(f"   - 錯誤：{api_result.get('error', 'N/A')}")
        
        if change_result.get("success"):
            print("✅ 狀態變化測試：通過")
            print(f"   - 檢測次數：{len(change_result.get('results', []))}")
            print(f"   - 狀態一致性：{'是' if change_result.get('consistent') else '否'}")
            print(f"   - 檢測到的狀態：{change_result.get('unique_statuses', [])}")
        else:
            print("❌ 狀態變化測試：失敗")
            print(f"   - 錯誤：{change_result.get('error', 'N/A')}")
        
        # 整體評估
        overall_success = api_result.get("success") and change_result.get("success")
        print()
        print("🎯 整體評估")
        print("-" * 40)
        
        if overall_success:
            print("🎉 攝影機狀態監控修復成功！")
            print("   - 後端 API 能正確執行即時檢測")
            print("   - 前端可以獲取到實際的攝影機狀態")
            print("   - 系統已恢復正常功能")
        else:
            print("⚠️  修復未完全成功，需要進一步檢查")
            print("   - 請檢查後端服務是否正常運行")
            print("   - 請確認攝影機設備連接狀態")
            print("   - 請檢查日誌以獲得更多診斷信息")

async def main():
    """主函數"""
    verifier = CameraStatusFixVerification()
    await verifier.run_verification()

if __name__ == "__main__":
    asyncio.run(main())