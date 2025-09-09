#!/usr/bin/env python3
"""
使用PostgreSQL查詢檢測結果
"""

import asyncio
import asyncpg
from datetime import datetime

async def check_postgresql_results(task_id=74):
    """查詢PostgreSQL中的檢測結果"""
    
    # 資料庫連接參數
    dsn = "postgresql://postgres:49679904@localhost:5432/yolo_analysis"
    
    try:
        conn = await asyncpg.connect(dsn)
        
        print("=" * 60)
        print("🔍 PostgreSQL 檢測結果查詢")
        print("=" * 60)
        
        # 檢查任務資訊
        print(f"📋 任務 {task_id} 詳細資訊:")
        task_row = await conn.fetchrow("""
            SELECT id, task_type, status, source_info, source_width, source_height, 
                   source_fps, start_time, end_time, created_at
            FROM analysis_tasks 
            WHERE id = $1
        """, task_id)
        
        if task_row:
            print(f"   ID: {task_row['id']}")
            print(f"   類型: {task_row['task_type']}")
            print(f"   狀態: {task_row['status']}")
            print(f"   來源資訊: {task_row['source_info']}")
            print(f"   解析度: {task_row['source_width']}x{task_row['source_height']}")
            print(f"   FPS: {task_row['source_fps']}")
            print(f"   開始時間: {task_row['start_time']}")
            print(f"   結束時間: {task_row['end_time']}")
            print(f"   建立時間: {task_row['created_at']}")
        else:
            print(f"   ❌ 找不到任務 {task_id}")
            return
        
        print(f"\n" + "-" * 40)
        
        # 檢查檢測結果統計
        print(f"📊 檢測結果統計:")
        stats_row = await conn.fetchrow("""
            SELECT COUNT(*) as total_detections,
                   COUNT(DISTINCT frame_number) as frames_with_detections,
                   COUNT(DISTINCT object_type) as unique_object_types,
                   MIN(confidence) as min_confidence,
                   MAX(confidence) as max_confidence,
                   AVG(confidence) as avg_confidence
            FROM detection_results 
            WHERE task_id = $1
        """, task_id)
        
        if stats_row and stats_row['total_detections'] > 0:
            print(f"   總檢測數量: {stats_row['total_detections']}")
            print(f"   有檢測的幀數: {stats_row['frames_with_detections']}")
            print(f"   不同物件類型: {stats_row['unique_object_types']}")
            print(f"   信心度範圍: {stats_row['min_confidence']:.3f} - {stats_row['max_confidence']:.3f}")
            print(f"   平均信心度: {stats_row['avg_confidence']:.3f}")
        else:
            print("   ❌ 沒有找到檢測結果")
        
        # 檢查物件類型分布
        print(f"\n📈 物件類型分布:")
        object_types = await conn.fetch("""
            SELECT object_type, COUNT(*) as count, AVG(confidence) as avg_conf
            FROM detection_results 
            WHERE task_id = $1
            GROUP BY object_type
            ORDER BY count DESC
        """, task_id)
        
        if object_types:
            for obj_type_row in object_types:
                print(f"   {obj_type_row['object_type']}: {obj_type_row['count']} 次 (平均信心度: {obj_type_row['avg_conf']:.3f})")
        else:
            print("   沒有檢測結果")
        
        # 顯示前10個檢測結果
        print(f"\n🔍 前10個檢測結果:")
        detections = await conn.fetch("""
            SELECT frame_number, timestamp, object_type, confidence, 
                   bbox_x1, bbox_y1, bbox_x2, bbox_y2, center_x, center_y
            FROM detection_results 
            WHERE task_id = $1
            ORDER BY frame_number, confidence DESC
            LIMIT 10
        """, task_id)
        
        if detections:
            for det in detections:
                print(f"   幀 {det['frame_number']}: {det['object_type']} (信心度: {det['confidence']:.3f})")
                print(f"      位置: ({det['bbox_x1']:.0f},{det['bbox_y1']:.0f}) - ({det['bbox_x2']:.0f},{det['bbox_y2']:.0f})")
                print(f"      中心: ({det['center_x']:.0f},{det['center_y']:.0f})")
        else:
            print("   沒有檢測結果")
        
        await conn.close()
        
        print("=" * 60)
        print("✅ 查詢完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 資料庫查詢錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(check_postgresql_results())
