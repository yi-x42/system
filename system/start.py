"""
YOLOv11 系統啟動腳本
"""

import os
import subprocess
import sys
from pathlib import Path

"""
YOLOv11 數位雙生分析系統 - 快速啟動腳本
專為 Radmin 網絡環境優化
"""

import os
import sys
import subprocess
import platform
import threading
import time
import signal
from pathlib import Path

def check_python_installation():
    """檢查 Python 安裝狀態"""
    try:
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
            print(f"❌ Python 版本過舊: {sys.version}")
            print("需要 Python 3.9 或更新版本")
            return False
        
        print(f"✅ Python 版本: {sys.version.split()[0]}")
        print(f"✅ Python 路徑: {sys.executable}")
        return True
    except Exception as e:
        print(f"❌ Python 檢查失敗: {e}")
        return False

def check_critical_packages():
    """檢查關鍵套件"""
    critical_packages = {
        'fastapi': 'FastAPI 框架',
        'uvicorn': 'ASGI 伺服器',
        'jinja2': '模板引擎',
        'psutil': '系統監控',
        'cv2': 'OpenCV 電腦視覺 (攝影機支援)'
    }
    
    missing_packages = []
    print("📦 檢查依賴套件...")
    
    for package, description in critical_packages.items():
        try:
            __import__(package)
            print(f"✅ {description} ({package}) 已安裝")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {description} ({package}) 未安裝")
    
    return missing_packages

def check_app_structure():
    """檢查應用程式結構"""
    required_paths = [
        "app",
        "app/main.py",
    ]
    
    missing_paths = []
    print("📁 檢查應用程式結構...")
    
    for path in required_paths:
        if Path(path).exists():
            print(f"✅ {path}")
        else:
            print(f"❌ {path}")
            missing_paths.append(path)
    
    return missing_paths

def wait_for_stop_command(process):
    """等待用戶輸入停止命令的函數"""
    print("\n💡 提示：輸入 'quit', 'exit', 'stop' 或 'q' 來停止服務")
    print("     輸入 'status' 或 's' 檢查服務狀態")
    print("     或者按 Ctrl+C 強制停止")
    print("-" * 60)
    
    while process.poll() is None:  # 當進程還在運行時
        try:
            user_input = input().strip().lower()
            
            if user_input in ['quit', 'exit', 'stop', 'q']:
                print("🛑 正在停止服務...")
                
                # 優雅地終止進程
                if platform.system() == "Windows":
                    # Windows 系統使用 taskkill
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                 capture_output=True)
                else:
                    # Unix 系統使用 SIGTERM
                    process.terminate()
                
                # 等待進程結束
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                print("✅ 服務已停止")
                break
            
            elif user_input in ['status', 's']:
                # 檢查服務狀態
                print("📊 服務狀態檢查:")
                try:
                    import requests
                    response = requests.get("http://localhost:8001/api/v1/frontend/stats", timeout=5)
                    if response.status_code == 200:
                        print("  ✅ API 服務正常運行")
                        print("  🌐 訪問地址：http://localhost:8001")
                    else:
                        print(f"  ⚠️ API 回應異常：{response.status_code}")
                except Exception as e:
                    print(f"  ❌ 無法連接服務：{e}")
                
                print(f"  🔧 進程狀態：{'運行中' if process.poll() is None else '已停止'}")
                print(f"  🆔 進程 ID：{process.pid}")
                print("-" * 40)
                
        except (EOFError, KeyboardInterrupt):
            # 處理 Ctrl+C 或輸入結束
            break
        except Exception as e:
            # 忽略輸入錯誤，繼續等待
            pass

def main():
    """主啟動函數"""
    print("🚀 啟動 YOLOv11 數位雙生分析系統 - Radmin 網絡版")
    print("=" * 60)
    
    # 確保在正確的工作目錄
    script_dir = Path(__file__).parent
    yolo_backend_dir = script_dir / "yolo_backend"
    
    # 切換到 yolo_backend 目錄
    os.chdir(yolo_backend_dir)
    print(f"✅ 工作目錄: {os.getcwd()}")
    
    # 檢查 Python 安裝
    if not check_python_installation():
        print("⚠️  請更新到 Python 3.9 或更新版本")
        input("按 Enter 鍵退出...")
        return
    
    # 檢查應用程式結構
    missing_paths = check_app_structure()
    if missing_paths:
        print(f"\n❌ 缺少必要檔案或目錄: {', '.join(missing_paths)}")
        print("請確保所有後台管理檔案都已正確創建")
        input("按 Enter 鍵退出...")
        return
    
    # 檢查關鍵套件
    missing_packages = check_critical_packages()
    if missing_packages:
        print(f"\n⚠️  缺少關鍵套件: {', '.join(missing_packages)}")
        print("安裝命令:")
        print(f"  {sys.executable} -m pip install {' '.join(missing_packages)}")
        
        # 嘗試自動安裝
        try:
            print("\n🔧 嘗試自動安裝缺少的套件...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages, check=True, capture_output=True, text=True)
            print("✅ 套件安裝成功")
        except subprocess.CalledProcessError as e:
            print("❌ 自動安裝失敗，請手動安裝")
            print(f"錯誤: {e}")
            input("按 Enter 鍵退出...")
            return
        except Exception as e:
            print(f"❌ 安裝過程發生錯誤: {e}")
            input("按 Enter 鍵退出...")
            return
    
    # 確保日誌目錄存在
    Path("logs").mkdir(exist_ok=True)
    
    # 所有檢查通過，啟動服務
    print("\n✅ 所有檢查通過，準備啟動服務")
    print("🔧 正在啟動 FastAPI 服務...")
    print("")
    print("📖 本機 API 文件: http://localhost:8001/docs")
    print("🔍 本機健康檢查: http://localhost:8001/api/v1/health")
    print(" 現代化網站: http://localhost:8001/website/")
    print("")
    print("🌐 Radmin 網絡訪問:")
    print("   - API 文件: http://26.86.64.166:8001/docs")
    print("   - 現代化網站: http://26.86.64.166:8001/website/")
    print("   - API 連接測試: http://26.86.64.166:8001/website/connection_test.html")
    print("   - Radmin 診斷工具: http://26.86.64.166:8001/website/radmin_diagnostic.html")
    print("   ✅ 組員可透過您的 Radmin IP 訪問所有功能")
    print("   🔧 前端已支援自動偵測 API 地址，無需手動配置")
    print("   🧪 如遇問題請使用診斷工具檢查連接狀態")
    print("")
    print("🎮 Unity 整合專用 API:")
    print("   - 簡單檢測 API: 執行 'python simple_detection_api.py' 啟動")
    print("   - Unity API 地址: http://26.86.64.166:8002")
    print("   - API 文檔: http://26.86.64.166:8002/docs")
    print("   - 檢測結果: http://26.86.64.166:8002/detection-results/latest")
    print("   - 使用指南: 參考 UNITY_API_GUIDE.md")
    print("")
    print("🆕 現代化原型網站:")
    print("     🎛️ 主控台 - 系統儀表板與即時監控")
    print("     🤖 智能分析引擎 - YOLO 模型配置與檢測")
    print("     🗂 資料來源管理 - 攝影機與影片檔案管理")
    print("     ⏰ 任務排程與執行 - 自動化分析任務")
    print("     📈 結果分析與報表 - 數據視覺化與統計")
    print("     💾 數據管理與匯出 - 檢測結果管理")
    print("     ⚙️ 系統配置與維護 - 進階系統設定")
    print("     🔬 進階功能 - AI 訓練與模型優化")
    print("     🎨 現代化界面 - 紫色漸層設計，響應式佈局")
    print("     🌙 深色/淺色主題 - 可切換的視覺模式")
    print("")
    print("按 Ctrl+C 或輸入 'quit'/'exit'/'stop'/'q' 停止服務")
    print("輸入 'status'/'s' 檢查服務狀態")
    print("=" * 60)
    
    process = None
    
    try:
        # 啟動 FastAPI 服務
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",  # 允許外部訪問（Radmin 網絡）
            "--port", "8001",
            "--log-level", "info",
            "--reload"  # 開發模式，程式碼變更時自動重新載入
        ]
        
        print(f"執行命令: {' '.join(cmd)}")
        print("🚀 正在啟動服務，請稍候...")
        
        # 使用 Popen 啟動進程，這樣可以在背景運行
        process = subprocess.Popen(cmd, cwd=yolo_backend_dir)
        
        # 等待一下讓服務啟動
        time.sleep(3)
        
        # 檢查進程是否正常啟動
        if process.poll() is None:
            print("✅ 服務啟動成功！")
            print()
            
            # 在背景執行等待停止命令的函數
            stop_thread = threading.Thread(target=wait_for_stop_command, args=(process,))
            stop_thread.daemon = True
            stop_thread.start()
            
            # 等待進程結束
            process.wait()
        else:
            print("❌ 服務啟動失敗")
            return
        
    except KeyboardInterrupt:
        print("\n🛑 收到停止信號...")
        if process and process.poll() is None:
            print("正在停止服務...")
            
            # 優雅地終止進程
            if platform.system() == "Windows":
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                             capture_output=True)
            else:
                process.terminate()
            
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("👋 服務已停止")
        
    except FileNotFoundError:
        print("\n❌ 找不到 uvicorn，請安裝: pip install uvicorn")
        input("按 Enter 鍵退出...")
        
    except Exception as e:
        print(f"\n❌ 啟動失敗: {e}")
        print("\n💡 常見解決方案:")
        print("   1. 確認所有套件已安裝: pip install fastapi uvicorn jinja2 psutil")
        print("   2. 檢查端口 8001 是否被佔用: netstat -ano | findstr :8001")
        print("   3. 以管理員身份運行 PowerShell")
        print("   4. 確認 Radmin VPN 連接正常")
        print("   5. 檢查防火牆設定")
        input("按 Enter 鍵退出...")
        
    finally:
        # 確保進程被清理
        if process and process.poll() is None:
            try:
                if platform.system() == "Windows":
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                 capture_output=True)
                else:
                    process.kill()
            except:
                pass

if __name__ == "__main__":
    main()
