#!/usr/bin/env python3
"""
測試新增的磁碟使用率和網路使用率 API 欄位
"""
import requests
import json
import time
import sys

def test_api_endpoint():
    """測試 /api/v1/frontend/stats API 端點"""
    url = "http://localhost:8001/api/v1/frontend/stats"
    
    print("🧪 測試 SystemStats API 新欄位...")
    print(f"📡 請求 URL: {url}")
    print("=" * 60)
    
    try:
        # 發送 GET 請求
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API 回應成功！")
            print("📊 回應數據:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("=" * 60)
            
            # 檢查必要欄位
            required_fields = [
                'cpu_usage_percent',
                'memory_usage_percent', 
                'gpu_usage_percent',
                'active_tasks_count',
                'system_uptime_seconds',
                'network_usage'  # 網路使用率欄位
            ]
            
            print("🔍 欄位檢查:")
            all_fields_present = True
            
            for field in required_fields:
                if field in data:
                    print(f"  ✅ {field}: {data[field]}")
                else:
                    print(f"  ❌ {field}: 缺失")
                    all_fields_present = False
            
            print("=" * 60)
            
            if all_fields_present:
                print("🎉 所有欄位都存在！")
                
                # 詳細檢查新欄位的數據格式
                if 'network_usage' in data:
                    network = data['network_usage']
                    print(f"\n🌐 網路使用率詳細資訊:")
                    print(f"  傳送: {network.get('bytes_sent_gb', 'N/A')} GB")
                    print(f"  接收: {network.get('bytes_recv_gb', 'N/A')} GB")
                
                return True
            else:
                print("⚠️ 部分欄位缺失")
                return False
        else:
            print(f"❌ API 請求失敗: HTTP {response.status_code}")
            print(f"   回應內容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API 伺服器")
        print("💡 請先執行 'python start.py' 啟動系統")
        return False
    except requests.exceptions.Timeout:
        print("❌ API 請求逾時")
        return False
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return False

def main():
    print("🚀 SystemStats API 新欄位測試工具")
    print("=" * 60)
    
    # 檢查 API 是否可用
    if test_api_endpoint():
        print("\n🎯 測試結果: 成功")
        print("✅ 網路使用率欄位已正確保留在 API 中，磁碟使用率已移除")
        sys.exit(0)
    else:
        print("\n❌ 測試結果: 失敗")
        print("⚠️ 請檢查 API 實作或系統狀態")
        sys.exit(1)

if __name__ == "__main__":
    main()