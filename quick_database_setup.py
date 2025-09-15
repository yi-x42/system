#!/usr/bin/env python3
"""
YOLOv11系統 - 快速資料庫設置腳本
專門用於快速創建和初始化資料庫

這個腳本會：
1. 創建PostgreSQL資料庫
2. 初始化所有必要的資料表
3. 插入範例資料
4. 驗證資料庫設置

使用方法：
python quick_database_setup.py

作者: YOLOv11開發團隊
日期: 2025/9/15
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuickDatabaseSetup:
    """快速資料庫設置類"""
    
    def __init__(self):
        self.root_path = Path(__file__).parent
        self.backend_path = self.root_path / "yolo_backend"
        
        # 預設資料庫配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "49679904",  # 可修改
            "database": "yolo_analysis"
        }

    def print_header(self, title):
        """打印標題"""
        print("\n" + "=" * 50)
        print(f"🗄️  {title}")
        print("=" * 50)

    def get_database_password(self):
        """獲取資料庫密碼"""
        print("🔐 資料庫認證設置")
        print(f"預設密碼: {self.db_config['password']}")
        
        response = input("使用預設密碼嗎? (y/n): ").lower().strip()
        if response not in ['y', 'yes', '']:
            new_password = input("請輸入PostgreSQL密碼: ").strip()
            if new_password:
                self.db_config["password"] = new_password
                print(f"✅ 已設置新密碼")

    def install_required_packages(self):
        """安裝必要的套件"""
        print("\n📦 檢查必要套件...")
        
        try:
            import psycopg2
            print("✅ psycopg2 已安裝")
        except ImportError:
            print("📥 安裝 psycopg2...")
            import subprocess
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "psycopg2-binary"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ psycopg2 安裝失敗: {result.stderr}")
                return False
            print("✅ psycopg2 安裝完成")
        
        try:
            import sqlalchemy
            print("✅ SQLAlchemy 已安裝")
        except ImportError:
            print("📥 安裝 SQLAlchemy...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "sqlalchemy"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ SQLAlchemy 安裝失敗: {result.stderr}")
                return False
            print("✅ SQLAlchemy 安裝完成")
        
        return True

    def test_postgresql_connection(self):
        """測試PostgreSQL連接"""
        print("\n🔗 測試PostgreSQL連接...")
        
        try:
            import psycopg2
            
            # 連接到預設資料庫
            conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                database="postgres"
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL連接成功")
            print(f"   版本: {version}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ PostgreSQL連接失敗: {e}")
            print("\n請檢查：")
            print("1. PostgreSQL服務是否正在運行")
            print("2. 用戶名和密碼是否正確")
            print("3. 防火牆和網路設定")
            return False

    def create_database(self):
        """創建資料庫"""
        print("\n🏗️  創建資料庫...")
        
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                database="postgres"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # 檢查資料庫是否存在
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (self.db_config["database"],)
            )
            exists = cursor.fetchone()
            
            if exists:
                print(f"✅ 資料庫 '{self.db_config['database']}' 已存在")
            else:
                cursor.execute(f"CREATE DATABASE {self.db_config['database']}")
                print(f"✅ 資料庫 '{self.db_config['database']}' 創建成功")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ 資料庫創建失敗: {e}")
            return False

    def create_tables_directly(self):
        """直接創建資料表（不依賴後端代碼）"""
        print("\n📋 創建資料表...")
        
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                database=self.db_config["database"]
            )
            
            cursor = conn.cursor()
            
            # 創建資料表的SQL語句
            tables_sql = [
                # 1. 分析任務表
                """
                CREATE TABLE IF NOT EXISTS analysis_tasks (
                    id SERIAL PRIMARY KEY,
                    task_type VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    source_info JSONB,
                    source_width INTEGER,
                    source_height INTEGER,
                    source_fps FLOAT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    task_name VARCHAR(200),
                    model_id VARCHAR(100),
                    confidence_threshold FLOAT DEFAULT 0.5
                );
                """,
                
                # 2. 檢測結果表
                """
                CREATE TABLE IF NOT EXISTS detection_results (           
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER NOT NULL,
                    frame_number INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    object_type VARCHAR(50) NOT NULL,
                    confidence FLOAT NOT NULL,
                    bbox_x1 FLOAT NOT NULL,
                    bbox_y1 FLOAT NOT NULL,
                    bbox_x2 FLOAT NOT NULL,
                    bbox_y2 FLOAT NOT NULL,
                    center_x FLOAT NOT NULL,
                    center_y FLOAT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES analysis_tasks(id) ON DELETE CASCADE
                );
                """,
                
                # 3. 行為事件表
                """
                CREATE TABLE IF NOT EXISTS behavior_events (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    description TEXT,
                    confidence_level FLOAT,
                    timestamp TIMESTAMP NOT NULL,
                    additional_data JSONB,
                    FOREIGN KEY (task_id) REFERENCES analysis_tasks(id) ON DELETE CASCADE
                );
                """,
                
                # 4. 資料來源表
                """
                CREATE TABLE IF NOT EXISTS data_sources (
                    id SERIAL PRIMARY KEY,
                    source_type VARCHAR(20) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    config JSONB,
                    status VARCHAR(20) DEFAULT 'active',
                    last_check TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """,
                
                # 5. 使用者表
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'viewer',
                    is_active BOOLEAN DEFAULT true,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """,
                
                # 6. 系統配置表
                """
                CREATE TABLE IF NOT EXISTS system_config (
                    id SERIAL PRIMARY KEY,
                    config_key VARCHAR(100) UNIQUE NOT NULL,
                    config_value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            ]
            
            # 創建索引
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_detection_results_task_id ON detection_results(task_id);",
                "CREATE INDEX IF NOT EXISTS idx_detection_results_timestamp ON detection_results(timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON analysis_tasks(status);",
                "CREATE INDEX IF NOT EXISTS idx_analysis_tasks_created_at ON analysis_tasks(created_at);",
                "CREATE INDEX IF NOT EXISTS idx_behavior_events_task_id ON behavior_events(task_id);",
                "CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);"
            ]
            
            # 執行表格創建
            for sql in tables_sql:
                cursor.execute(sql)
                
            # 執行索引創建
            for sql in indexes_sql:
                cursor.execute(sql)
            
            conn.commit()
            
            # 檢查創建的表格
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            print("✅ 資料表創建完成:")
            for table in tables:
                print(f"   📋 {table[0]}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ 資料表創建失敗: {e}")
            return False

    def insert_sample_data(self):
        """插入範例資料"""
        print("\n📝 插入範例資料...")
        
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                database=self.db_config["database"]
            )
            
            cursor = conn.cursor()
            
            # 插入範例資料來源
            sample_data_sources = [
                ('camera', '大廳攝影機A', '{"url": "rtsp://192.168.1.100:554/stream", "location": "一樓大廳"}'),
                ('camera', '停車場攝影機B', '{"url": "rtsp://192.168.1.101:554/stream", "location": "地下停車場"}'),
                ('video_file', '測試影片1', '{"path": "/uploads/test_video.mp4", "duration": 300}')
            ]
            
            cursor.execute("SELECT COUNT(*) FROM data_sources")
            count = cursor.fetchone()[0]
            
            if count == 0:
                for source_type, name, config in sample_data_sources:
                    cursor.execute(
                        "INSERT INTO data_sources (source_type, name, config) VALUES (%s, %s, %s)",
                        (source_type, name, config)
                    )
                print("✅ 範例資料來源已插入")
            else:
                print("✅ 資料來源表已有資料")
            
            # 插入系統配置
            system_configs = [
                ('detection_confidence', '0.5', '預設物件檢測信心度閾值'),
                ('max_concurrent_tasks', '3', '最大並發任務數量'),
                ('auto_cleanup_days', '30', '自動清理檢測結果的天數'),
                ('default_model', 'yolo11n.pt', '預設YOLO模型'),
                ('max_upload_size_mb', '500', '最大上傳檔案大小(MB)')
            ]
            
            cursor.execute("SELECT COUNT(*) FROM system_config")
            count = cursor.fetchone()[0]
            
            if count == 0:
                for key, value, desc in system_configs:
                    cursor.execute(
                        "INSERT INTO system_config (config_key, config_value, description) VALUES (%s, %s, %s)",
                        (key, value, desc)
                    )
                print("✅ 系統配置已插入")
            else:
                print("✅ 系統配置表已有資料")
            
            # 插入範例使用者
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # 這裡使用簡單的密碼hash，實際應用中應該使用更安全的方法
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                    ('admin', 'admin_hash_placeholder', 'admin')
                )
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                    ('viewer', 'viewer_hash_placeholder', 'viewer')
                )
                print("✅ 範例使用者已插入")
            else:
                print("✅ 使用者表已有資料")
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ 範例資料插入失敗: {e}")
            return False

    def verify_database(self):
        """驗證資料庫設置"""
        print("\n🔍 驗證資料庫設置...")
        
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                database=self.db_config["database"]
            )
            
            cursor = conn.cursor()
            
            # 檢查所有表格
            expected_tables = [
                'analysis_tasks', 'detection_results', 'behavior_events',
                'data_sources', 'users', 'system_config'
            ]
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            
            actual_tables = [row[0] for row in cursor.fetchall()]
            
            print("📋 資料表檢查:")
            for table in expected_tables:
                if table in actual_tables:
                    # 檢查記錄數量
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   ✅ {table} ({count} 筆記錄)")
                else:
                    print(f"   ❌ {table} (缺失)")
            
            # 檢查外鍵約束
            cursor.execute("""
                SELECT tc.constraint_name, tc.table_name, kcu.column_name, 
                       ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_name;
            """)
            
            foreign_keys = cursor.fetchall()
            print(f"\n🔗 外鍵約束: {len(foreign_keys)} 個")
            for fk in foreign_keys:
                print(f"   🔗 {fk[1]}.{fk[2]} -> {fk[3]}.{fk[4]}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ 資料庫驗證失敗: {e}")
            return False

    def save_connection_info(self):
        """保存連接資訊"""
        print("\n💾 保存連接資訊...")
        
        try:
            # 創建連接資訊檔案
            connection_info = {
                "database_config": self.db_config,
                "connection_string": f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}",
                "setup_time": datetime.now().isoformat(),
                "tables_created": [
                    "analysis_tasks", "detection_results", "behavior_events",
                    "data_sources", "users", "system_config"
                ]
            }
            
            # 保存到根目錄
            info_file = self.root_path / "database_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(connection_info, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 連接資訊已保存: {info_file}")
            
            # 也創建.env檔案
            env_content = f"""# YOLOv11系統資料庫配置
POSTGRES_HOST={self.db_config['host']}
POSTGRES_PORT={self.db_config['port']}
POSTGRES_USER={self.db_config['user']}
POSTGRES_PASSWORD={self.db_config['password']}
POSTGRES_DB={self.db_config['database']}

# 生成時間: {datetime.now().isoformat()}
"""
            
            env_file = self.root_path / ".env"
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
                
            print(f"✅ 環境變數檔案已創建: {env_file}")
            return True
            
        except Exception as e:
            print(f"❌ 連接資訊保存失敗: {e}")
            return False

    def run_setup(self):
        """執行完整設置流程"""
        self.print_header("YOLOv11系統快速資料庫設置")
        
        steps = [
            ("取得資料庫密碼", self.get_database_password),
            ("安裝必要套件", self.install_required_packages),
            ("測試PostgreSQL連接", self.test_postgresql_connection),
            ("創建資料庫", self.create_database),
            ("創建資料表", self.create_tables_directly),
            ("插入範例資料", self.insert_sample_data),
            ("驗證資料庫設置", self.verify_database),
            ("保存連接資訊", self.save_connection_info),
        ]
        
        success_count = 0
        
        for step_name, step_func in steps:
            try:
                print(f"\n🔄 {step_name}...")
                if step_func():
                    success_count += 1
                else:
                    print(f"❌ {step_name} 失敗")
                    
            except Exception as e:
                print(f"❌ {step_name} 發生錯誤: {e}")
        
        # 顯示結果
        self.print_header("設置結果")
        print(f"✅ 成功完成: {success_count}/{len(steps)} 個步驟")
        
        if success_count >= 6:  # 核心步驟成功
            print("\n🎉 資料庫設置完成！")
            print("\n📋 資料庫資訊:")
            print(f"   主機: {self.db_config['host']}")
            print(f"   端口: {self.db_config['port']}")
            print(f"   資料庫: {self.db_config['database']}")
            print(f"   用戶: {self.db_config['user']}")
            
            print("\n🚀 下一步:")
            print("   1. 執行 'python start.py' 啟動系統")
            print("   2. 訪問 http://localhost:3000 使用系統")
            print("   3. 查看 database_info.json 了解詳細資訊")
            
        else:
            print("\n❌ 資料庫設置未完全成功")
            print("🔧 請檢查失敗的步驟並重新運行")


def main():
    """主函數"""
    try:
        setup = QuickDatabaseSetup()
        setup.run_setup()
        
    except KeyboardInterrupt:
        print("\n\n👋 設置已被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 設置過程發生錯誤: {e}")
        logger.exception("設置失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()