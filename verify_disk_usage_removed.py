#!/usr/bin/env python3
"""
驗證磁碟使用率已從 API 中移除
"""
import requests
import json
import sys

def test_disk_usage_removed():
    """測試磁碟使用率是否已從API中移除"""
    url = "http://localhost:8001/api/v1/frontend/stats"
    
    print("🧪 驗證磁碟使用率已從 API 中移除...")
    print(f"📡 請求 URL: {url}")
    print("=" * 60)
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API 回應成功！")
            print("📊 API 回應數據:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("=" * 60)
            
            # 檢查磁碟使用率是否已移除
            if 'disk_usage' in data:
                print("❌ 磁碟使用率仍然存在於 API 回應中")
                print(f"   磁碟使用率值: {data['disk_usage']}")
                return False
            else:
                print("✅ 磁碟使用率已成功從 API 中移除")
                
                # 確認其他欄位仍然存在
                expected_fields = ['cpu_usage', 'memory_usage', 'gpu_usage', 'network_usage', 'active_tasks']
                missing_fields = []
                
                for field in expected_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"⚠️ 缺少預期欄位: {missing_fields}")
                else:
                    print("✅ 所有其他預期欄位都存在")
                
                return len(missing_fields) == 0
        else:
            print(f"❌ API 請求失敗: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API 伺服器")
        print("💡 請先執行 'python start.py' 啟動系統")
        return False
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return False

def main():
    print("🚀 磁碟使用率移除驗證工具")
    print("=" * 60)
    
    if test_disk_usage_removed():
        print("\n🎯 驗證結果: 成功 ✅")
        print("✅ 磁碟使用率已成功從 API 中移除")
        print("✅ 其他系統監控欄位正常運作")
        sys.exit(0)
    else:
        print("\n❌ 驗證結果: 失敗")
        print("⚠️ 請檢查 API 實作")
        sys.exit(1)

if __name__ == "__main__":
    main()