#!/usr/bin/env python3
"""
YOLOv11 資料庫密碼配置修復工具
幫助組員快速設定正確的資料庫密碼

使用方法：
python fix_database_password.py

作者: YOLOv11開發團隊
日期: 2025/9/15
"""

import os
import sys
from pathlib import Path

def fix_database_password():
    """修復資料庫密碼配置"""
    
    print("🔧 YOLOv11 資料庫密碼配置修復工具")
    print("=" * 50)
    print("此工具將幫助您設定正確的 PostgreSQL 密碼")
    print()
    
    # 獲取專案路徑
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    config_file = project_root / "yolo_backend" / "app" / "core" / "config.py"
    
    # 1. 獲取當前 PostgreSQL 密碼
    print("📝 請輸入您的 PostgreSQL 資料庫資訊：")
    
    # 詢問基本資料庫資訊
    db_host = input("資料庫主機 (預設: localhost): ").strip() or "localhost"
    db_port = input("資料庫端口 (預設: 5432): ").strip() or "5432"
    db_user = input("資料庫使用者 (預設: postgres): ").strip() or "postgres"
    
    while True:
        db_password = input("PostgreSQL 密碼 (必填): ").strip()
        if db_password:
            break
        print("❌ 密碼不能為空，請重新輸入！")
    
    db_name = input("資料庫名稱 (預設: yolo_analysis): ").strip() or "yolo_analysis"
    
    print("\n🔄 正在更新配置檔案...")
    
    # 2. 更新 .env 檔案
    try:
        env_content = f"""# YOLOv11 數位雙生分析系統配置

# API 設定
HOST=0.0.0.0
PORT=8000
DEBUG=true

# YOLO 模型設定
MODEL_PATH=yolo11n.pt
DEVICE=auto
CONFIDENCE_THRESHOLD=0.25
IOU_THRESHOLD=0.7

# 檔案上傳設定
MAX_FILE_SIZE=50MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,bmp,mp4,avi,mov,mkv

# 日誌設定
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 資料庫設定
POSTGRES_SERVER={db_host}
POSTGRES_PORT={db_port}
POSTGRES_USER={db_user}
POSTGRES_PASSWORD={db_password}
POSTGRES_DB={db_name}
DATABASE_URL=postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}

# Redis 設定 (可選)
# REDIS_URL=redis://localhost:6379/0

# 安全設定
# SECRET_KEY=your-secret-key-here
# CORS_ORIGINS=["http://localhost:3000"]
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"✅ 已更新 .env 檔案: {env_file}")
        
    except Exception as e:
        print(f"❌ 更新 .env 檔案失敗: {e}")
        return False
    
    # 3. 測試資料庫連接
    print("\n🔍 測試資料庫連接...")
    
    try:
        # 嘗試使用 psycopg2 測試連接
        import psycopg2
        
        # 首先測試連接到 postgres 預設資料庫
        conn = psycopg2.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            database="postgres"  # 先連接預設資料庫
        )
        
        cursor = conn.cursor()
        
        # 檢查目標資料庫是否存在
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"⚠️  資料庫 '{db_name}' 不存在，正在創建...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ 資料庫 '{db_name}' 創建成功！")
        else:
            print(f"✅ 資料庫 '{db_name}' 已存在")
        
        cursor.close()
        conn.close()
        
        # 測試連接到目標資料庫
        conn = psycopg2.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            database=db_name
        )
        conn.close()
        
        print("✅ 資料庫連接測試成功！")
        
    except ImportError:
        print("⚠️  psycopg2 未安裝，跳過連接測試")
        print("   系統將使用 asyncpg 進行連接")
        
    except Exception as e:
        print(f"❌ 資料庫連接測試失敗: {e}")
        print("\n請檢查：")
        print("1. PostgreSQL 服務是否正在運行")
        print("2. 密碼是否正確")
        print("3. 防火牆設定")
        print("4. PostgreSQL 是否允許本地連接")
        
        # 提供一些常見的解決方案
        print("\n💡 常見解決方案：")
        print("1. 檢查 PostgreSQL 服務狀態：")
        if os.name == 'nt':  # Windows
            print("   - 在服務管理器中查看 PostgreSQL 服務")
            print("   - 或執行: net start postgresql-x64-[version]")
        else:  # Linux/Mac
            print("   - sudo systemctl status postgresql")
            print("   - sudo systemctl start postgresql")
        
        print("\n2. 重設 PostgreSQL 密碼：")
        print("   - 使用 pgAdmin 或命令列工具重設密碼")
        
        print("\n3. 檢查 pg_hba.conf 設定檔")
        
        return False
    
    # 4. 提供後續指導
    print("\n🎯 後續步驟：")
    print("1. 重新啟動系統：")
    print("   python start.py")
    print()
    print("2. 如果需要初始化資料庫表格：")
    print("   cd yolo_backend")
    print("   python init_database.py")
    print()
    print("3. 或使用快速設置腳本：")
    print("   python quick_database_setup.py")
    print()
    print("4. 訪問系統：")
    print("   前端: http://localhost:3000")
    print("   API: http://localhost:8001/docs")
    
    print("\n✨ 資料庫密碼配置完成！")
    return True

def check_current_config():
    """檢查當前配置"""
    print("\n🔍 檢查當前配置...")
    
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        print(f"✅ .env 檔案存在: {env_file}")
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查是否包含資料庫配置
            if 'POSTGRES_PASSWORD' in content:
                print("✅ 包含 PostgreSQL 密碼配置")
            else:
                print("❌ 缺少 PostgreSQL 密碼配置")
            
            if 'DATABASE_URL' in content:
                print("✅ 包含資料庫連接字串")
            else:
                print("❌ 缺少資料庫連接字串")
                
        except Exception as e:
            print(f"❌ 讀取 .env 檔案失敗: {e}")
    else:
        print(f"❌ .env 檔案不存在: {env_file}")

def main():
    """主函數"""
    try:
        print("🚀 YOLOv11 資料庫配置工具")
        print("=" * 50)
        
        # 檢查當前配置
        check_current_config()
        
        print("\n請選擇操作：")
        print("1. 設定資料庫密碼")
        print("2. 僅檢查當前配置")
        print("0. 退出")
        
        choice = input("\n請輸入選項 (0-2): ").strip()
        
        if choice == "1":
            success = fix_database_password()
            if success:
                print("\n🎉 配置完成！現在可以啟動系統了。")
            else:
                print("\n⚠️  配置過程中遇到問題，請檢查並重試。")
        elif choice == "2":
            check_current_config()
        elif choice == "0":
            print("👋 再見！")
        else:
            print("❌ 無效選項")
        
    except KeyboardInterrupt:
        print("\n\n👋 程式已被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程式執行失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()