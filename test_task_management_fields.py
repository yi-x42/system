#!/usr/bin/env python3
"""
測試任務管理系統的新欄位功能
驗證 task_name, model_id, confidence_threshold 欄位
"""

import asyncio
import asyncpg
import sys
import os

# 將 yolo_backend 加入路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

from app.core.config import settings

async def test_task_management_fields():
    """測試新增的任務管理欄位"""
    
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    
    print("🧪 測試任務管理系統的新欄位功能")
    print("=" * 50)
    
    try:
        # 連接資料庫
        conn = await asyncpg.connect(db_url)
        
        # 測試 1: 檢查欄位是否存在
        print("📋 檢查新欄位是否正確新增...")
        
        columns = await conn.fetch("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'analysis_tasks'
            AND column_name IN ('task_name', 'model_id', 'confidence_threshold')
            ORDER BY column_name;
        """)
        
        expected_columns = ['confidence_threshold', 'model_id', 'task_name']
        found_columns = [col['column_name'] for col in columns]
        
        for col_name in expected_columns:
            if col_name in found_columns:
                col_info = next(col for col in columns if col['column_name'] == col_name)
                print(f"✓ {col_name}: {col_info['data_type']} (預設: {col_info['column_default']})")
            else:
                print(f"× {col_name}: 未找到")
                return False
        
        # 測試 2: 插入測試資料
        print(f"\n🔬 測試插入包含新欄位的資料...")
        
        test_task_id = await conn.fetchval("""
            INSERT INTO analysis_tasks (
                task_type, status, source_info, 
                task_name, model_id, confidence_threshold
            ) VALUES (
                'realtime_camera', 'pending', '{"camera_id": "test_cam_1"}',
                '測試攝影機任務', 'yolo11n.pt', 0.7
            ) RETURNING id;
        """)
        
        print(f"✓ 成功插入測試任務，ID: {test_task_id}")
        
        # 測試 3: 查詢測試資料
        print(f"\n📊 查詢測試資料...")
        
        task_data = await conn.fetchrow("""
            SELECT id, task_type, status, task_name, model_id, confidence_threshold
            FROM analysis_tasks WHERE id = $1;
        """, test_task_id)
        
        if task_data:
            print("✓ 查詢成功，資料內容：")
            print(f"  - ID: {task_data['id']}")
            print(f"  - 任務類型: {task_data['task_type']}")
            print(f"  - 狀態: {task_data['status']}")
            print(f"  - 任務名稱: {task_data['task_name']}")
            print(f"  - 模型ID: {task_data['model_id']}")
            print(f"  - 信心度閾值: {task_data['confidence_threshold']}")
        else:
            print("× 查詢失敗，找不到測試資料")
            return False
        
        # 測試 4: 更新測試資料
        print(f"\n🔄 測試更新新欄位的資料...")
        
        await conn.execute("""
            UPDATE analysis_tasks 
            SET task_name = '更新後的任務名稱', 
                model_id = 'yolo11s.pt',
                confidence_threshold = 0.8
            WHERE id = $1;
        """, test_task_id)
        
        updated_data = await conn.fetchrow("""
            SELECT task_name, model_id, confidence_threshold
            FROM analysis_tasks WHERE id = $1;
        """, test_task_id)
        
        if updated_data:
            print("✓ 更新成功，新資料：")
            print(f"  - 任務名稱: {updated_data['task_name']}")
            print(f"  - 模型ID: {updated_data['model_id']}")
            print(f"  - 信心度閾值: {updated_data['confidence_threshold']}")
        else:
            print("× 更新失敗")
            return False
        
        # 測試 5: 清理測試資料
        print(f"\n🧹 清理測試資料...")
        
        deleted_count = await conn.fetchval("""
            DELETE FROM analysis_tasks WHERE id = $1;
        """, test_task_id)
        
        print(f"✓ 已清理測試資料")
        
        await conn.close()
        
        print(f"\n🎉 所有測試通過！")
        print("新增的任務管理欄位功能正常：")
        print("  ✓ task_name - 任務名稱")
        print("  ✓ model_id - YOLO模型ID") 
        print("  ✓ confidence_threshold - 信心度閾值")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

if __name__ == '__main__':
    try:
        success = asyncio.run(test_task_management_fields())
        if not success:
            sys.exit(1)
        else:
            print(f"\n✅ 資料庫任務管理欄位測試完成，系統準備就緒！")
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 執行測試時發生錯誤: {e}")
        sys.exit(1)