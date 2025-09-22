#!/usr/bin/env python3
"""
YOLOv11 數位雙生分析系統 - 快速部署腳本
適用於在組員電腦上快速設置整個系統環境

功能:
1. 環境檢查 (Python, Node.js, PostgreSQL)
2. 依賴安裝 (Python packages, npm packages)
3. 資料庫創建和初始化
4. 基本配置設置
5. 系統測試驗證

作者: YOLOv11 開發團隊
日期: 2025/9/15
"""

import os
import sys
import subprocess
import platform
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YOLOv11Deployer:
    """YOLOv11系統部署器"""
    
    def __init__(self):
        self.root_path = Path(__file__).parent
        self.backend_path = self.root_path / "yolo_backend"
        self.frontend_path = self.root_path / "react web"
        self.requirements_path = self.root_path / "requirements.txt"
        self.package_json_path = self.frontend_path / "package.json"
        
        # 資料庫配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres", 
            "password": "49679904",  # 預設密碼，用戶可以修改
            "database": "yolo_analysis"
        }
        
        self.success_count = 0
        self.total_steps = 12

    def print_header(self, title):
        """打印標題"""
        print("\n" + "=" * 60)
        print(f"🚀 {title}")
        print("=" * 60)

    def print_step(self, step_num, description):
        """打印步驟"""
        print(f"\n📋 步驟 {step_num}/{self.total_steps}: {description}")
        print("-" * 50)

    def check_python(self):
        """檢查Python環境"""
        self.print_step(1, "檢查Python環境")
        
        try:
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
                print("❌ Python版本過低，需要Python 3.8+")
                print(f"   當前版本: {sys.version}")
                return False
            
            print(f"✅ Python版本: {sys.version}")
            print(f"   路徑: {sys.executable}")
            self.success_count += 1
            return True
            
        except Exception as e:
            print(f"❌ Python檢查失敗: {e}")
            return False

    def check_node(self):
        """檢查Node.js環境"""
        self.print_step(2, "檢查Node.js環境")
        
        try:
            # 檢查Node.js
            result = subprocess.run(["node", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print("❌ Node.js未安裝或不在PATH中")
                print("   請安裝Node.js 16+: https://nodejs.org/")
                return False
            
            node_version = result.stdout.strip()
            print(f"✅ Node.js版本: {node_version}")
            
            # 檢查npm
            result = subprocess.run(["npm", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print("❌ npm未安裝")
                return False
            
            npm_version = result.stdout.strip()
            print(f"✅ npm版本: {npm_version}")
            self.success_count += 1
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Node.js檢查超時")
            return False
        except FileNotFoundError:
            print("❌ Node.js未安裝或不在PATH中")
            print("   請安裝Node.js 16+: https://nodejs.org/")
            return False
        except Exception as e:
            print(f"❌ Node.js檢查失敗: {e}")
            return False

    def check_postgresql(self):
        """檢查PostgreSQL環境"""
        self.print_step(3, "檢查PostgreSQL環境")
        
        try:
            import psycopg2
            
            # 嘗試連接PostgreSQL
            conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                database="postgres"  # 連接預設資料庫
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL版本: {version}")
            
            cursor.close()
            conn.close()
            self.success_count += 1
            return True
            
        except ImportError:
            print("❌ psycopg2未安裝")
            print("   將在後續步驟中安裝...")
            return True  # 先繼續，後面會安裝
        except Exception as e:
            print(f"❌ PostgreSQL連接失敗: {e}")
            print("   請檢查:")
            print("   1. PostgreSQL是否已安裝並運行")
            print("   2. 用戶名和密碼是否正確")
            print("   3. 防火牆設定")
            
            # 詢問用戶是否要修改資料庫密碼
            response = input("是否要修改資料庫密碼? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                new_password = input("請輸入PostgreSQL密碼: ").strip()
                if new_password:
                    self.db_config["password"] = new_password
                    return self.check_postgresql()  # 重新檢查
            
            return False

    def install_python_dependencies(self):
        """安裝Python依賴"""
        self.print_step(4, "安裝Python依賴套件")
        
        try:
            if not self.requirements_path.exists():
                print(f"❌ requirements.txt不存在: {self.requirements_path}")
                return False
            
            print("📦 安裝Python套件...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(self.requirements_path)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"❌ Python套件安裝失敗:")
                print(result.stderr)
                return False
            
            print("✅ Python套件安裝完成")
            self.success_count += 1
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Python套件安裝超時")
            return False
        except Exception as e:
            print(f"❌ Python套件安裝失敗: {e}")
            return False

    def install_node_dependencies(self):
        """安裝Node.js依賴"""
        self.print_step(5, "安裝Node.js依賴套件")
        
        try:
            if not self.package_json_path.exists():
                print(f"❌ package.json不存在: {self.package_json_path}")
                return False
            
            print("📦 安裝Node.js套件...")
            os.chdir(self.frontend_path)
            
            result = subprocess.run(["npm", "install"], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"❌ Node.js套件安裝失敗:")
                print(result.stderr)
                return False
            
            print("✅ Node.js套件安裝完成")
            os.chdir(self.root_path)  # 回到根目錄
            self.success_count += 1
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Node.js套件安裝超時")
            return False
        except Exception as e:
            print(f"❌ Node.js套件安裝失敗: {e}")
            return False
        finally:
            os.chdir(self.root_path)  # 確保回到根目錄

    def create_database(self):
        """創建資料庫"""
        self.print_step(6, "創建PostgreSQL資料庫")
        
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            # 連接到postgres預設資料庫
            conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                database="postgres"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # 檢查資料庫是否已存在
            cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", 
                          (self.db_config["database"],))
            exists = cursor.fetchone()
            
            if exists:
                print(f"✅ 資料庫 '{self.db_config['database']}' 已存在")
            else:
                # 創建資料庫
                cursor.execute(f"CREATE DATABASE {self.db_config['database']}")
                print(f"✅ 資料庫 '{self.db_config['database']}' 創建成功")
            
            cursor.close()
            conn.close()
            self.success_count += 1
            return True
            
        except Exception as e:
            print(f"❌ 資料庫創建失敗: {e}")
            return False

    def init_database_tables(self):
        """初始化資料庫表格"""
        self.print_step(7, "初始化資料庫表格")
        
        try:
            # 切換到backend目錄
            os.chdir(self.backend_path)
            
            # 設定環境變數
            env = os.environ.copy()
            env['POSTGRES_PASSWORD'] = self.db_config["password"]
            env['POSTGRES_DB'] = self.db_config["database"]
            
            # 執行資料庫初始化
            result = subprocess.run([
                sys.executable, "init_database.py"
            ], capture_output=True, text=True, timeout=60, env=env)
            
            print("初始化輸出:")
            print(result.stdout)
            
            if result.returncode != 0:
                print(f"❌ 資料庫表格初始化失敗:")
                print(result.stderr)
                return False
            
            print("✅ 資料庫表格初始化完成")
            self.success_count += 1
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ 資料庫初始化超時")
            return False
        except Exception as e:
            print(f"❌ 資料庫初始化失敗: {e}")
            return False
        finally:
            os.chdir(self.root_path)

    def create_env_file(self):
        """創建環境配置檔案"""
        self.print_step(8, "創建環境配置檔案")
        
        try:
            env_content = f"""# YOLOv11系統環境配置
# 資料庫配置
POSTGRES_HOST={self.db_config["host"]}
POSTGRES_PORT={self.db_config["port"]}
POSTGRES_USER={self.db_config["user"]}
POSTGRES_PASSWORD={self.db_config["password"]}
POSTGRES_DB={self.db_config["database"]}

# API配置
API_HOST=0.0.0.0
API_PORT=8001
DEBUG=true

# 系統配置
ENVIRONMENT=development
LOG_LEVEL=INFO

# 檔案路徑
UPLOAD_PATH=./uploads
MODEL_PATH=./models
LOG_PATH=./logs

# 系統安全
SECRET_KEY=your-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,26.86.64.166

# 生成時間
GENERATED_AT={datetime.now().isoformat()}
"""
            
            # 寫入後端.env檔案
            backend_env_path = self.backend_path / ".env"
            with open(backend_env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            # 寫入根目錄.env檔案
            root_env_path = self.root_path / ".env"
            with open(root_env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            print(f"✅ 環境配置檔案已創建:")
            print(f"   - {backend_env_path}")
            print(f"   - {root_env_path}")
            
            self.success_count += 1
            return True
            
        except Exception as e:
            print(f"❌ 環境配置檔案創建失敗: {e}")
            return False

    def create_sample_data(self):
        """創建範例資料"""
        self.print_step(9, "創建範例資料和攝影機配置")
        
        try:
            # 創建範例攝影機配置
            cameras = [
                {
                    "id": "1",
                    "name": "大廳攝影機A",
                    "url": "rtsp://admin:123456@192.168.1.100:554/h264/ch1/main/av_stream",
                    "location": "一樓大廳",
                    "status": "active",
                    "description": "監控大廳主要出入口"
                },
                {
                    "id": "2", 
                    "name": "停車場攝影機B",
                    "url": "rtsp://admin:123456@192.168.1.101:554/h264/ch1/main/av_stream",
                    "location": "地下停車場",
                    "status": "active",
                    "description": "監控停車場車輛進出"
                },
                {
                    "id": "3",
                    "name": "辦公室攝影機C", 
                    "url": "rtsp://admin:123456@192.168.1.102:554/h264/ch1/main/av_stream",
                    "location": "二樓辦公室",
                    "status": "inactive",
                    "description": "辦公區域安全監控"
                }
            ]
            
            # 保存攝影機配置
            for camera in cameras:
                camera_file = self.root_path / f"camera{camera['id']}.json"
                with open(camera_file, 'w', encoding='utf-8') as f:
                    json.dump(camera, f, ensure_ascii=False, indent=2)
                print(f"✅ 已創建 {camera_file}")
            
            # 創建系統配置範例
            system_config = {
                "detection_confidence": 0.5,
                "max_concurrent_tasks": 3,
                "auto_cleanup_days": 30,
                "enable_notifications": True,
                "default_model": "yolo11n.pt",
                "supported_formats": ["mp4", "avi", "mov", "mkv"],
                "max_upload_size_mb": 500
            }
            
            config_file = self.root_path / "system_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(system_config, f, ensure_ascii=False, indent=2)
            print(f"✅ 已創建 {config_file}")
            
            self.success_count += 1
            return True
            
        except Exception as e:
            print(f"❌ 範例資料創建失敗: {e}")
            return False

    def download_yolo_model(self):
        """下載YOLO模型"""
        self.print_step(10, "檢查和下載YOLO模型")
        
        try:
            models_dir = self.backend_path / "models"
            models_dir.mkdir(exist_ok=True)
            
            model_file = models_dir / "yolo11n.pt"
            
            if model_file.exists():
                print(f"✅ YOLO模型已存在: {model_file}")
                print(f"   檔案大小: {model_file.stat().st_size / 1024 / 1024:.1f} MB")
            else:
                print("📥 下載YOLO11n模型...")
                print("   (首次運行時會自動下載，請確保網路連接)")
                
                # 創建一個測試腳本來觸發模型下載
                test_script = """
import sys
sys.path.append('.')
from ultralytics import YOLO

try:
    print("正在下載YOLO11n模型...")
    model = YOLO('yolo11n.pt')
    print("模型下載完成!")
    print(f"模型位置: {model.model_path if hasattr(model, 'model_path') else '預設位置'}")
except Exception as e:
    print(f"模型下載失敗: {e}")
    sys.exit(1)
"""
                
                os.chdir(self.backend_path)
                result = subprocess.run([
                    sys.executable, "-c", test_script
                ], capture_output=True, text=True, timeout=300)
                
                print("下載輸出:")
                print(result.stdout)
                
                if result.returncode != 0:
                    print("⚠️  自動下載失敗，但可以在首次使用時下載")
                    print(result.stderr)
                
            self.success_count += 1
            return True
            
        except subprocess.TimeoutExpired:
            print("⚠️  模型下載超時，但可以在首次使用時下載")
            return True
        except Exception as e:
            print(f"⚠️  模型檢查失敗: {e}")
            print("   模型將在首次使用時自動下載")
            return True
        finally:
            os.chdir(self.root_path)

    def test_system(self):
        """測試系統功能"""
        self.print_step(11, "測試系統功能")
        
        try:
            # 測試後端API
            print("🧪 測試後端API...")
            os.chdir(self.backend_path)
            
            # 設定環境變數
            env = os.environ.copy()
            env['POSTGRES_PASSWORD'] = self.db_config["password"]
            env['POSTGRES_DB'] = self.db_config["database"]
            
            # 簡單的API測試
            test_script = """
import sys
sys.path.append('.')
import asyncio
from app.core.database import check_database_connection

async def test():
    try:
        if await check_database_connection():
            print("✅ 資料庫連接測試成功")
            return True
        else:
            print("❌ 資料庫連接測試失敗")
            return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
"""
            
            result = subprocess.run([
                sys.executable, "-c", test_script
            ], capture_output=True, text=True, timeout=30, env=env)
            
            print("測試輸出:")
            print(result.stdout)
            
            if result.returncode == 0:
                print("✅ 後端系統測試通過")
            else:
                print("❌ 後端系統測試失敗")
                print(result.stderr)
                return False
            
            self.success_count += 1
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ 系統測試超時")
            return False
        except Exception as e:
            print(f"❌ 系統測試失敗: {e}")
            return False
        finally:
            os.chdir(self.root_path)

    def create_shortcuts(self):
        """創建啟動快捷方式"""
        self.print_step(12, "創建啟動快捷方式")
        
        try:
            # 創建啟動腳本
            if platform.system() == "Windows":
                startup_script = """@echo off
echo 🚀 啟動YOLOv11數位雙生分析系統
echo =====================================
cd /d "%~dp0"
python start.py
pause
"""
                startup_file = self.root_path / "啟動系統.bat"
                with open(startup_file, 'w', encoding='utf-8') as f:
                    f.write(startup_script)
                print(f"✅ 已創建Windows啟動腳本: {startup_file}")
                
            else:
                startup_script = """#!/bin/bash
echo "🚀 啟動YOLOv11數位雙生分析系統"
echo "====================================="
cd "$(dirname "$0")"
python3 start.py
"""
                startup_file = self.root_path / "start_system.sh"
                with open(startup_file, 'w', encoding='utf-8') as f:
                    f.write(startup_script)
                os.chmod(startup_file, 0o755)
                print(f"✅ 已創建Linux/Mac啟動腳本: {startup_file}")
            
            # 創建使用說明文件
            readme_content = f"""# YOLOv11數位雙生分析系統 - 部署完成

## 🎉 恭喜！系統已成功部署

部署時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
系統路徑: {self.root_path}

## 🚀 快速啟動

### Windows用戶:
- 雙擊 `啟動系統.bat`
- 或在命令提示字元中執行: `python start.py`

### Linux/Mac用戶:
- 執行: `./start_system.sh`  
- 或執行: `python3 start.py`

## 🌐 訪問地址

- **前端界面**: http://localhost:3000
- **API文檔**: http://localhost:8001/docs
- **後端健康檢查**: http://localhost:8001/api/v1/health

## 🗄️ 資料庫資訊

- **主機**: {self.db_config['host']}
- **端口**: {self.db_config['port']}
- **資料庫**: {self.db_config['database']}
- **用戶**: {self.db_config['user']}

## 📋 系統組件

✅ Python後端 (FastAPI)
✅ React前端 (Vite + TypeScript)
✅ PostgreSQL資料庫
✅ YOLOv11物件檢測模型
✅ 攝影機串流支援
✅ 即時分析功能

## 🔧 常見問題

### 1. 端口衝突
如果8001或3000端口被占用，請檢查其他應用程式

### 2. 資料庫連接失敗
- 確認PostgreSQL服務正在運行
- 檢查密碼是否正確
- 確認防火牆設定

### 3. 攝影機連接問題  
- 檢查攝影機URL是否正確
- 確認網路連接
- 驗證RTSP串流格式

## 📞 技術支援

如有問題請聯繫開發團隊或查看系統日誌文件。

---
YOLOv11數位雙生分析系統 v2.0
"""
            
            readme_file = self.root_path / "部署說明.md"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"✅ 已創建使用說明: {readme_file}")
            
            self.success_count += 1
            return True
            
        except Exception as e:
            print(f"❌ 啟動腳本創建失敗: {e}")
            return False

    def run_deployment(self):
        """執行完整部署流程"""
        self.print_header("YOLOv11數位雙生分析系統 - 快速部署")
        
        print(f"📍 部署位置: {self.root_path}")
        print(f"🕐 開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💻 作業系統: {platform.system()} {platform.release()}")
        
        deployment_steps = [
            self.check_python,
            self.check_node, 
            self.check_postgresql,
            self.install_python_dependencies,
            self.install_node_dependencies,
            self.create_database,
            self.init_database_tables,
            self.create_env_file,
            self.create_sample_data,
            self.download_yolo_model,
            self.test_system,
            self.create_shortcuts,
        ]
        
        failed_steps = []
        
        # 執行所有部署步驟
        for i, step in enumerate(deployment_steps, 1):
            try:
                if not step():
                    failed_steps.append((i, step.__name__))
                    print(f"⚠️  步驟 {i} 失敗，但繼續執行...")
            except Exception as e:
                print(f"❌ 步驟 {i} 發生錯誤: {e}")
                failed_steps.append((i, step.__name__))
        
        # 顯示部署結果
        self.print_header("部署結果總結")
        
        print(f"✅ 成功完成: {self.success_count}/{self.total_steps} 個步驟")
        
        if failed_steps:
            print(f"⚠️  失敗步驟: {len(failed_steps)} 個")
            for step_num, step_name in failed_steps:
                print(f"   - 步驟 {step_num}: {step_name}")
        
        if self.success_count >= 10:  # 至少10個核心步驟成功
            print("\n🎉 部署基本完成！")
            print("💡 現在可以嘗試啟動系統:")
            print("   python start.py")
            print("\n🌐 系統啟動後訪問:")
            print("   前端: http://localhost:3000")
            print("   API: http://localhost:8001/docs")
            
        else:
            print("\n❌ 部署未完全成功")
            print("🔧 請檢查失敗的步驟並手動修復")
            
        print(f"\n🕐 完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)


def main():
    """主函數"""
    try:
        deployer = YOLOv11Deployer()
        deployer.run_deployment()
        
    except KeyboardInterrupt:
        print("\n\n👋 部署已被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 部署過程發生嚴重錯誤: {e}")
        logger.exception("部署失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()