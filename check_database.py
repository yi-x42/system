#!/usr/bin/env python3
"""檢查資料庫狀況並新增必要的欄位"""

import sqlite3
import os

def check_and_modify_database():
    db_path = 'analysis_database.db'
    
    if not os.path.exists(db_path):
        print('❌ 找不到資料庫檔案 analysis_database.db')
        print('🔍 當前目錄的 .db 檔案:')
        for file in os.listdir('.'):
            if file.endswith('.db'):
                print(f'  - {file}')
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 查看所有表格
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = cursor.fetchall()
        
        print('📊 資料庫中的表格:')
        if tables:
            for table in tables:
                table_name = table[0]
                print(f'  - {table_name}')
                
                # 顯示每個表格的結構
                cursor.execute(f'PRAGMA table_info({table_name})')
                columns = cursor.fetchall()
                col_names = [col[1] for col in columns]
                print(f'    欄位: {col_names}')
                
                # 如果是 analysis_tasks 表格，檢查並新增欄位
                if table_name == 'analysis_tasks':
                    print(f'\n🔧 正在修改 {table_name} 表格...')
                    
                    # 檢查需要新增的欄位
                    new_columns = [
                        ('task_name', 'VARCHAR(200)'),
                        ('model_id', 'VARCHAR(100)'),
                        ('confidence_threshold', 'FLOAT DEFAULT 0.5')
                    ]
                    
                    for col_name, col_type in new_columns:
                        if col_name not in col_names:
                            try:
                                cursor.execute(f'ALTER TABLE analysis_tasks ADD COLUMN {col_name} {col_type}')
                                print(f'✓ 已新增 {col_name} 欄位')
                            except sqlite3.OperationalError as e:
                                print(f'× {col_name} 錯誤: {e}')
                        else:
                            print(f'• {col_name} 欄位已存在')
                    
                    # 確認變更並顯示最新結構
                    conn.commit()
                    cursor.execute(f'PRAGMA table_info({table_name})')
                    updated_columns = cursor.fetchall()
                    print(f'\n📋 更新後的 {table_name} 表格結構:')
                    for col in updated_columns:
                        print(f'  - {col[1]} ({col[2]})')
                
                print()
        else:
            print('  (沒有找到任何表格)')
            
    except Exception as e:
        print(f'❌ 執行過程中發生錯誤: {e}')
    finally:
        conn.close()
        print('\n✅ 資料庫檢查完成')

if __name__ == '__main__':
    check_and_modify_database()