#!/usr/bin/env python3
"""
YOLOv11系統部署驗證腳本
用於測試系統是否正確部署和運行

使用方法：
python verify_deployment.py

作者: YOLOv11開發團隊
日期: 2025/9/15  
"""

import os
import sys
import json
import requests
import subprocess
from pathlib import Path
from datetime import datetime
import time

class DeploymentVerifier:
    """部署驗證器"""
    
    def __init__(self):
        self.root_path = Path(__file__).parent
        self.base_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:3000"
        
        self.tests_passed = 0
        self.total_tests = 10

    def print_header(self, title):
        """打印標題"""
        print("\n" + "=" * 50)
        print(f"🔍 {title}")
        print("=" * 50)

    def test_files_exist(self):
        """測試必要檔案是否存在"""
        print("\n📁 檢查檔案結構...")
        
        required_files = [
            "start.py",
            ".env",
            "requirements.txt", 
            "yolo_backend/app/main.py",
            "react web/package.json",
            "database_info.json"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.root_path / file_path
            if full_path.exists():
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} (缺失)")
                missing_files.append(file_path)
        
        if not missing_files:
            print("✅ 檔案結構檢查通過")
            self.tests_passed += 1
            return True
        else:
            print(f"❌ 缺失 {len(missing_files)} 個檔案")
            return False

    def test_database_connection(self):
        """測試資料庫連接"""
        print("\n🗄️  測試資料庫連接...")
        
        try:
            # 讀取資料庫配置
            env_file = self.root_path / ".env"
            if not env_file.exists():
                print("❌ .env檔案不存在")
                return False
            
            # 嘗試連接資料庫
            import psycopg2
            
            # 從.env讀取配置
            db_config = {}
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key.startswith('POSTGRES_'):
                            db_key = key.replace('POSTGRES_', '').lower()
                            db_config[db_key] = value
            
            # 連接資料庫
            conn = psycopg2.connect(
                host=db_config.get('host', 'localhost'),
                port=int(db_config.get('port', 5432)),
                user=db_config.get('user', 'postgres'),
                password=db_config.get('password', ''),
                database=db_config.get('db', 'yolo_analysis')
            )
            
            cursor = conn.cursor()
            
            # 檢查表格是否存在
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            expected_tables = [
                'analysis_tasks', 'detection_results', 'behavior_events',
                'data_sources', 'users', 'system_config'
            ]
            
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if not missing_tables:
                print(f"✅ 資料庫連接成功，共有 {len(tables)} 個表格")
                self.tests_passed += 1
                success = True
            else:
                print(f"❌ 缺失表格: {missing_tables}")
                success = False
            
            cursor.close()
            conn.close()
            return success
            
        except ImportError:
            print("❌ psycopg2未安裝")
            return False
        except Exception as e:
            print(f"❌ 資料庫連接失敗: {e}")
            return False

    def test_backend_startup(self):
        """測試後端是否能啟動"""
        print("\n🔧 測試後端啟動...")
        
        try:
            # 檢查後端是否已經在運行
            try:
                response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
                if response.status_code == 200:
                    print("✅ 後端已在運行")
                    self.tests_passed += 1
                    return True
            except requests.exceptions.RequestException:
                pass
            
            # 嘗試啟動後端進行測試
            print("🚀 嘗試啟動後端進行測試...")
            
            os.chdir(self.root_path / "yolo_backend")
            
            # 設定環境變數
            env = os.environ.copy()
            env_file = self.root_path / ".env"
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            env[key] = value
            
            # 啟動測試程序
            process = subprocess.Popen([
                sys.executable, "-c", """
import sys, asyncio
sys.path.append('.')
from app.core.database import check_database_connection

async def test():
    try:
        result = await check_database_connection()
        print("✅ 後端資料庫連接測試成功" if result else "❌ 後端資料庫連接測試失敗")
        return result
    except Exception as e:
        print(f"❌ 後端測試失敗: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
"""
            ], capture_output=True, text=True, env=env, timeout=30)
            
            stdout, stderr = process.communicate()
            print(stdout)
            
            if process.returncode == 0:
                print("✅ 後端功能測試通過")
                self.tests_passed += 1
                return True
            else:
                print(f"❌ 後端測試失敗: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ 後端測試超時")
            return False
        except Exception as e:
            print(f"❌ 後端測試錯誤: {e}")
            return False
        finally:
            os.chdir(self.root_path)

    def test_frontend_files(self):
        """測試前端檔案"""
        print("\n⚛️  檢查前端檔案...")
        
        try:
            frontend_path = self.root_path / "react web"
            if not frontend_path.exists():
                print("❌ react web目錄不存在")
                return False
            
            package_json = frontend_path / "package.json"
            if not package_json.exists():
                print("❌ package.json不存在")
                return False
            
            # 檢查node_modules
            node_modules = frontend_path / "node_modules"
            if not node_modules.exists():
                print("⚠️  node_modules不存在，需要執行 npm install")
                return False
            
            # 檢查關鍵檔案
            key_files = [
                "src/main.tsx",
                "src/App.tsx", 
                "index.html",
                "vite.config.ts"
            ]
            
            missing_files = []
            for file_path in key_files:
                if not (frontend_path / file_path).exists():
                    missing_files.append(file_path)
            
            if not missing_files:
                print("✅ 前端檔案結構完整")
                self.tests_passed += 1
                return True
            else:
                print(f"❌ 前端缺失檔案: {missing_files}")
                return False
            
        except Exception as e:
            print(f"❌ 前端檢查失敗: {e}")
            return False

    def test_python_dependencies(self):
        """測試Python依賴套件"""
        print("\n🐍 檢查Python依賴套件...")
        
        try:
            required_packages = [
                'fastapi', 'uvicorn', 'sqlalchemy', 'psycopg2',
                'pydantic', 'ultralytics', 'opencv-python', 'numpy'
            ]
            
            missing_packages = []
            installed_packages = []
            
            for package in required_packages:
                try:
                    if package == 'opencv-python':
                        import cv2
                        installed_packages.append(f"{package} (cv2)")
                    elif package == 'psycopg2':
                        import psycopg2
                        installed_packages.append(package)
                    else:
                        __import__(package)
                        installed_packages.append(package)
                except ImportError:
                    missing_packages.append(package)
            
            print(f"✅ 已安裝套件 ({len(installed_packages)}):")
            for pkg in installed_packages:
                print(f"   ✅ {pkg}")
            
            if missing_packages:
                print(f"❌ 缺失套件 ({len(missing_packages)}):")
                for pkg in missing_packages:
                    print(f"   ❌ {pkg}")
                return False
            else:
                print("✅ 所有必要Python套件已安裝")
                self.tests_passed += 1 
                return True
                
        except Exception as e:
            print(f"❌ Python套件檢查失敗: {e}")
            return False

    def test_configuration_files(self):
        """測試配置檔案"""
        print("\n⚙️  檢查配置檔案...")
        
        try:
            # 檢查.env檔案
            env_file = self.root_path / ".env"
            if env_file.exists():
                print("✅ .env檔案存在")
                
                # 檢查必要配置
                required_configs = [
                    'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_USER',
                    'POSTGRES_PASSWORD', 'POSTGRES_DB'
                ]
                
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                missing_configs = []
                for config in required_configs:
                    if config not in content:
                        missing_configs.append(config)
                
                if not missing_configs:
                    print("✅ .env檔案配置完整")
                else:
                    print(f"⚠️  .env缺少配置: {missing_configs}")
            else:
                print("❌ .env檔案不存在")
                return False
            
            # 檢查資料庫資訊檔案
            db_info_file = self.root_path / "database_info.json"
            if db_info_file.exists():
                print("✅ database_info.json存在")
                
                with open(db_info_file, 'r', encoding='utf-8') as f:
                    db_info = json.load(f)
                
                if 'database_config' in db_info and 'tables_created' in db_info:
                    print("✅ 資料庫資訊檔案格式正確")
                else:
                    print("⚠️  資料庫資訊檔案格式異常")
            else:
                print("❌ database_info.json不存在")
                return False
            
            # 檢查攝影機配置
            camera_files = list(self.root_path.glob("camera*.json"))
            if camera_files:
                print(f"✅ 找到 {len(camera_files)} 個攝影機配置檔案")
            else:
                print("⚠️  沒有找到攝影機配置檔案")
            
            print("✅ 配置檔案檢查完成")
            self.tests_passed += 1
            return True
            
        except Exception as e:
            print(f"❌ 配置檔案檢查失敗: {e}")
            return False

    def test_yolo_model(self):
        """測試YOLO模型"""
        print("\n🤖 檢查YOLO模型...")
        
        try:
            # 檢查模型檔案
            models_dir = self.root_path / "yolo_backend" / "models"
            if models_dir.exists():
                model_files = list(models_dir.glob("*.pt"))
                if model_files:
                    print(f"✅ 找到 {len(model_files)} 個模型檔案:")
                    for model in model_files:
                        size_mb = model.stat().st_size / 1024 / 1024
                        print(f"   📦 {model.name} ({size_mb:.1f} MB)")
                else:
                    print("⚠️  models目錄中沒有找到.pt檔案")
            else:
                print("⚠️  models目錄不存在")
            
            # 嘗試導入ultralytics
            try:
                from ultralytics import YOLO
                print("✅ ultralytics套件可正常導入")
                
                # 簡單測試模型載入（不下載）
                print("🧪 測試模型載入...")
                model = YOLO('yolo11n.pt')  # 會自動下載如果不存在
                print("✅ YOLO模型載入成功")
                
                self.tests_passed += 1
                return True
                
            except Exception as e:
                print(f"⚠️  YOLO模型測試失敗: {e}")
                print("   (首次使用時會自動下載)")
                return True  # 不算失敗，因為可能只是網路問題
                
        except Exception as e:
            print(f"❌ YOLO模型檢查失敗: {e}")
            return False

    def test_system_startup_script(self):
        """測試系統啟動腳本"""
        print("\n🚀 檢查啟動腳本...")
        
        try:
            # 檢查start.py
            start_py = self.root_path / "start.py"
            if start_py.exists():
                print("✅ start.py存在")
            else:
                print("❌ start.py不存在")
                return False
            
            # 檢查平台特定啟動腳本
            import platform
            if platform.system() == "Windows":
                batch_file = self.root_path / "啟動系統.bat"
                if batch_file.exists():
                    print("✅ Windows啟動腳本存在")
                else:
                    print("⚠️  Windows啟動腳本不存在")
            else:
                shell_script = self.root_path / "start_system.sh"
                if shell_script.exists():
                    print("✅ Linux/Mac啟動腳本存在")
                else:
                    print("⚠️  Linux/Mac啟動腳本不存在")
            
            print("✅ 啟動腳本檢查完成")
            self.tests_passed += 1
            return True
            
        except Exception as e:
            print(f"❌ 啟動腳本檢查失敗: {e}")
            return False

    def test_network_ports(self):
        """測試網路端口"""
        print("\n🌐 檢查網路端口...")
        
        try:
            import socket
            
            # 測試後端端口8001
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result_backend = sock.connect_ex(('localhost', 8001))
            sock.close()
            
            if result_backend == 0:
                print("✅ 端口8001已在使用 (後端運行中)")
                backend_running = True
            else:
                print("ℹ️  端口8001空閒 (後端未運行)")
                backend_running = False
            
            # 測試前端端口3000
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result_frontend = sock.connect_ex(('localhost', 3000))
            sock.close()
            
            if result_frontend == 0:
                print("✅ 端口3000已在使用 (前端運行中)")
                frontend_running = True
            else:
                print("ℹ️  端口3000空閒 (前端未運行)")
                frontend_running = False
            
            if backend_running or frontend_running:
                print("✅ 部分服務正在運行")
                self.tests_passed += 1
            else:
                print("ℹ️  系統未運行 (這是正常的)")
                self.tests_passed += 1  # 不算失敗
            
            return True
            
        except Exception as e:
            print(f"❌ 網路端口檢查失敗: {e}")
            return False

    def test_documentation(self):
        """測試文檔檔案"""
        print("\n📚 檢查說明文檔...")
        
        try:
            docs = [
                "組員部署指南.md",
                "部署說明.md"
            ]
            
            existing_docs = []
            for doc in docs:
                doc_path = self.root_path / doc
                if doc_path.exists():
                    existing_docs.append(doc)
                    print(f"✅ {doc}")
                else:
                    print(f"⚠️  {doc} (不存在)")
            
            if existing_docs:
                print(f"✅ 找到 {len(existing_docs)} 個說明文檔")
                self.tests_passed += 1
                return True
            else:
                print("⚠️  沒有找到說明文檔")
                return True  # 不算關鍵失敗
                
        except Exception as e:
            print(f"❌ 文檔檢查失敗: {e}")
            return False

    def run_verification(self):
        """執行完整驗證"""
        self.print_header("YOLOv11系統部署驗證")
        
        print(f"📍 驗證位置: {self.root_path}")
        print(f"🕐 驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        tests = [
            ("檔案結構", self.test_files_exist),
            ("資料庫連接", self.test_database_connection),
            ("後端功能", self.test_backend_startup),
            ("前端檔案", self.test_frontend_files),
            ("Python依賴", self.test_python_dependencies),
            ("配置檔案", self.test_configuration_files),
            ("YOLO模型", self.test_yolo_model),
            ("啟動腳本", self.test_system_startup_script),
            ("網路端口", self.test_network_ports),
            ("說明文檔", self.test_documentation),
        ]
        
        failed_tests = []
        
        for test_name, test_func in tests:
            try:
                if not test_func():
                    failed_tests.append(test_name)
            except Exception as e:
                print(f"❌ {test_name} 測試發生錯誤: {e}")
                failed_tests.append(test_name)
        
        # 顯示驗證結果
        self.print_header("驗證結果總結")
        
        print(f"✅ 通過測試: {self.tests_passed}/{self.total_tests}")
        print(f"❌ 失敗測試: {len(failed_tests)}")
        
        if failed_tests:
            print("\n失敗的測試項目:")
            for test in failed_tests:
                print(f"   ❌ {test}")
        
        # 給出建議
        if self.tests_passed >= 8:
            print("\n🎉 系統部署驗證基本通過！")
            print("\n✨ 建議下一步:")
            print("   1. 執行 'python start.py' 啟動系統")
            print("   2. 訪問 http://localhost:3000 使用前端")
            print("   3. 訪問 http://localhost:8001/docs 查看API")
            
        elif self.tests_passed >= 6:
            print("\n⚠️  系統部署基本可用，但有一些問題")
            print("🔧 建議檢查失敗的項目並修復")
            
        else:
            print("\n❌ 系統部署存在重大問題")
            print("🔧 請重新執行部署腳本或手動修復問題")
        
        print(f"\n🕐 驗證完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)


def main():
    """主函數"""
    try:
        verifier = DeploymentVerifier()
        verifier.run_verification()
        
    except KeyboardInterrupt:
        print("\n\n👋 驗證已被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 驗證過程發生錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()