#!/usr/bin/env python3
"""
建立 PostgreSQL 資料庫
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

def create_database():
    """建立 yolo_analysis 資料庫"""
    try:
        # 連接到 postgres 預設資料庫
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="49679904",
            database="postgres"  # 連接預設資料庫
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # 檢查資料庫是否已存在
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'yolo_analysis'")
        exists = cursor.fetchone()
        
        if exists:
            print("✅ 資料庫 'yolo_analysis' 已存在")
        else:
            # 建立資料庫
            cursor.execute("CREATE DATABASE yolo_analysis")
            print("✅ 資料庫 'yolo_analysis' 建立成功")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 建立資料庫失敗: {e}")
        return False

if __name__ == "__main__":
    print("🗄️  建立 PostgreSQL 資料庫")
    print("=" * 40)
    
    if create_database():
        print("\n✅ 準備就緒！現在可以執行 'python init_database.py'")
    else:
        print("\n❌ 請檢查 PostgreSQL 是否正在運行以及密碼是否正確")
        sys.exit(1)
