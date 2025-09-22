"""
攝影機狀態監控功能測試腳本
測試各種攝影機狀態檢測場景
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# API 基礎 URL
BASE_URL = "http://localhost:8001/api/v1/frontend"

class CameraStatusTest:
    """攝影機狀態測試類別"""
    
    def __init__(self):
        self.test_results = []
        self.session = None
    
    async def setup(self):
        """設置測試環境"""
        print("🔧 設置測試環境...")
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def cleanup(self):
        """清理測試環境"""
        if self.session:
            await self.session.close()
        print("🧹 測試環境已清理")
    
    def log_test_result(self, test_name: str, success: bool, message: str, details: dict = None):
        """記錄測試結果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   詳細資訊: {json.dumps(details, indent=2, ensure_ascii=False)}")
    
    async def test_get_cameras_basic(self):
        """測試基本攝影機列表獲取"""
        try:
            async with self.session.get(f"{BASE_URL}/cameras") as response:
                data = await response.json()
                
                if response.status == 200:
                    cameras = data if isinstance(data, list) else []
                    self.log_test_result(
                        "基本攝影機列表獲取",
                        True,
                        f"成功獲取 {len(cameras)} 個攝影機",
                        {"camera_count": len(cameras), "cameras": cameras[:3]}  # 只顯示前3個
                    )
                    return cameras
                else:
                    self.log_test_result(
                        "基本攝影機列表獲取",
                        False,
                        f"HTTP錯誤: {response.status}",
                        {"status": response.status, "response": data}
                    )
                    return []
                    
        except Exception as e:
            self.log_test_result(
                "基本攝影機列表獲取",
                False,
                f"請求失敗: {str(e)}",
                {"error": str(e)}
            )
            return []
    
    async def test_get_cameras_realtime(self):
        """測試帶即時檢測的攝影機列表獲取"""
        try:
            # 測試帶即時檢測參數的請求
            async with self.session.get(f"{BASE_URL}/cameras?real_time_check=true") as response:
                data = await response.json()
                
                if response.status == 200:
                    cameras = data if isinstance(data, list) else []
                    self.log_test_result(
                        "即時檢測攝影機列表",
                        True,
                        f"成功獲取並檢測 {len(cameras)} 個攝影機狀態",
                        {
                            "camera_count": len(cameras),
                            "status_summary": {
                                camera.get("name", f"Camera {i}"): camera.get("status", "unknown")
                                for i, camera in enumerate(cameras[:5])  # 只顯示前5個
                            }
                        }
                    )
                    return cameras
                else:
                    self.log_test_result(
                        "即時檢測攝影機列表",
                        False,
                        f"HTTP錯誤: {response.status}",
                        {"status": response.status, "response": data}
                    )
                    return []
                    
        except Exception as e:
            self.log_test_result(
                "即時檢測攝影機列表",
                False,
                f"請求失敗: {str(e)}",
                {"error": str(e)}
            )
            return []
    
    async def test_single_camera_status(self, camera_id: int):
        """測試單個攝影機狀態檢測"""
        try:
            async with self.session.get(f"{BASE_URL}/cameras/{camera_id}/status") as response:
                data = await response.json()
                
                if response.status == 200:
                    status = data.get("status", "unknown")
                    self.log_test_result(
                        f"單個攝影機狀態檢測 (ID: {camera_id})",
                        True,
                        f"攝影機狀態: {status}",
                        {"camera_id": camera_id, "status": status, "response": data}
                    )
                    return status
                elif response.status == 404:
                    self.log_test_result(
                        f"單個攝影機狀態檢測 (ID: {camera_id})",
                        False,
                        "攝影機不存在",
                        {"camera_id": camera_id, "status": response.status}
                    )
                    return None
                else:
                    self.log_test_result(
                        f"單個攝影機狀態檢測 (ID: {camera_id})",
                        False,
                        f"HTTP錯誤: {response.status}",
                        {"camera_id": camera_id, "status": response.status, "response": data}
                    )
                    return None
                    
        except Exception as e:
            self.log_test_result(
                f"單個攝影機狀態檢測 (ID: {camera_id})",
                False,
                f"請求失敗: {str(e)}",
                {"camera_id": camera_id, "error": str(e)}
            )
            return None
    
    async def test_check_all_cameras(self):
        """測試檢查所有攝影機狀態"""
        try:
            async with self.session.post(f"{BASE_URL}/cameras/status/check-all") as response:
                data = await response.json()
                
                if response.status == 200:
                    results = data.get("results", {})
                    message = data.get("message", "")
                    self.log_test_result(
                        "檢查所有攝影機狀態",
                        True,
                        message,
                        {"results_count": len(results), "results": results}
                    )
                    return results
                else:
                    self.log_test_result(
                        "檢查所有攝影機狀態",
                        False,
                        f"HTTP錯誤: {response.status}",
                        {"status": response.status, "response": data}
                    )
                    return {}
                    
        except Exception as e:
            self.log_test_result(
                "檢查所有攝影機狀態",
                False,
                f"請求失敗: {str(e)}",
                {"error": str(e)}
            )
            return {}
    
    async def test_performance_timing(self):
        """測試性能和響應時間"""
        try:
            # 測試基本列表獲取時間
            start_time = time.time()
            async with self.session.get(f"{BASE_URL}/cameras") as response:
                await response.json()
            basic_time = time.time() - start_time
            
            # 測試即時檢測時間
            start_time = time.time()
            async with self.session.get(f"{BASE_URL}/cameras?real_time_check=true") as response:
                await response.json()
            realtime_time = time.time() - start_time
            
            # 測試全部狀態檢測時間
            start_time = time.time()
            async with self.session.post(f"{BASE_URL}/cameras/status/check-all") as response:
                await response.json()
            check_all_time = time.time() - start_time
            
            performance_good = basic_time < 2 and realtime_time < 10 and check_all_time < 15
            
            self.log_test_result(
                "性能測試",
                performance_good,
                f"響應時間測試{'通過' if performance_good else '可能需要優化'}",
                {
                    "basic_list_time": f"{basic_time:.2f}秒",
                    "realtime_check_time": f"{realtime_time:.2f}秒",
                    "check_all_time": f"{check_all_time:.2f}秒",
                    "performance_acceptable": performance_good
                }
            )
            
        except Exception as e:
            self.log_test_result(
                "性能測試",
                False,
                f"測試失敗: {str(e)}",
                {"error": str(e)}
            )
    
    async def run_all_tests(self):
        """執行所有測試"""
        print("🚀 開始攝影機狀態監控功能測試")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # 1. 基本功能測試
            print("\n📋 基本功能測試")
            cameras = await self.test_get_cameras_basic()
            
            # 2. 即時檢測測試
            print("\n🔍 即時檢測功能測試")
            await self.test_get_cameras_realtime()
            
            # 3. 單個攝影機狀態測試
            print("\n📷 單個攝影機狀態測試")
            if cameras:
                # 測試第一個攝影機
                first_camera = cameras[0]
                camera_id = first_camera.get("id")
                if camera_id:
                    await self.test_single_camera_status(camera_id)
            
            # 測試不存在的攝影機
            await self.test_single_camera_status(99999)
            
            # 4. 批量狀態檢測測試
            print("\n📊 批量狀態檢測測試")
            await self.test_check_all_cameras()
            
            # 5. 性能測試
            print("\n⚡ 性能測試")
            await self.test_performance_timing()
            
        finally:
            await self.cleanup()
        
        # 生成測試報告
        self.generate_report()
    
    def generate_report(self):
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("📊 測試報告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"總測試數: {total_tests}")
        print(f"通過數: {passed_tests}")
        print(f"失敗數: {failed_tests}")
        print(f"通過率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "無測試")
        
        if failed_tests > 0:
            print("\n❌ 失敗的測試:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print("\n✅ 通過的測試:")
        for result in self.test_results:
            if result["success"]:
                print(f"  - {result['test_name']}: {result['message']}")
        
        # 保存詳細報告到檔案
        report_file = f"camera_status_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "pass_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0
                },
                "test_results": self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 詳細報告已保存到: {report_file}")

async def main():
    """主函數"""
    test = CameraStatusTest()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())