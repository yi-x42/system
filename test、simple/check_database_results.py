#!/usr/bin/env python3
"""
直接查詢資料庫中的檢測結果
"""

import sqlite3
import json
from datetime import datetime

def check_database_results(task_id=74):
    """直接查詢SQLite資料庫中的檢測結果"""
    db_path = "analysis_database.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("🔍 資料庫檢測結果查詢")
        print("=" * 60)
        
        # 檢查任務資訊
        print(f"📋 任務 {task_id} 詳細資訊:")
        cursor.execute("""
            SELECT id, task_type, status, source_info, source_width, source_height, 
                   source_fps, start_time, end_time, created_at
            FROM analysis_tasks 
            WHERE id = ?
        """, (task_id,))
        
        task_row = cursor.fetchone()
        if task_row:
            print(f"   ID: {task_row[0]}")
            print(f"   類型: {task_row[1]}")
            print(f"   狀態: {task_row[2]}")
            print(f"   來源資訊: {task_row[3]}")
            print(f"   解析度: {task_row[4]}x{task_row[5]}")
            print(f"   FPS: {task_row[6]}")
            print(f"   開始時間: {task_row[7]}")
            print(f"   結束時間: {task_row[8]}")
            print(f"   建立時間: {task_row[9]}")
        else:
            print(f"   ❌ 找不到任務 {task_id}")
            return
        
        print(f"\n" + "-" * 40)
        
        # 檢查檢測結果統計
        print(f"📊 檢測結果統計:")
        cursor.execute("""
            SELECT COUNT(*) as total_detections,
                   COUNT(DISTINCT frame_number) as frames_with_detections,
                   COUNT(DISTINCT object_type) as unique_object_types,
                   MIN(confidence) as min_confidence,
                   MAX(confidence) as max_confidence,
                   AVG(confidence) as avg_confidence
            FROM detection_results 
            WHERE task_id = ?
        """, (task_id,))
        
        stats_row = cursor.fetchone()
        if stats_row:
            print(f"   總檢測數量: {stats_row[0]}")
            print(f"   有檢測的幀數: {stats_row[1]}")
            print(f"   不同物件類型: {stats_row[2]}")
            print(f"   信心度範圍: {stats_row[3]:.3f} - {stats_row[4]:.3f}")
            print(f"   平均信心度: {stats_row[5]:.3f}")
        
        # 檢查物件類型分布
        print(f"\n📈 物件類型分布:")
        cursor.execute("""
            SELECT object_type, COUNT(*) as count, AVG(confidence) as avg_conf
            FROM detection_results 
            WHERE task_id = ?
            GROUP BY object_type
            ORDER BY count DESC
        """, (task_id,))
        
        object_types = cursor.fetchall()
        for obj_type, count, avg_conf in object_types:
            print(f"   {obj_type}: {count} 次 (平均信心度: {avg_conf:.3f})")
        
        # 顯示前10個檢測結果
        print(f"\n🔍 前10個檢測結果:")
        cursor.execute("""
            SELECT frame_number, timestamp, object_type, confidence, 
                   bbox_x1, bbox_y1, bbox_x2, bbox_y2, center_x, center_y
            FROM detection_results 
            WHERE task_id = ?
            ORDER BY frame_number, confidence DESC
            LIMIT 10
        """, (task_id,))
        
        detections = cursor.fetchall()
        for det in detections:
            frame, ts, obj_type, conf, x1, y1, x2, y2, cx, cy = det
            print(f"   幀 {frame}: {obj_type} (信心度: {conf:.3f})")
            print(f"      位置: ({x1:.0f},{y1:.0f}) - ({x2:.0f},{y2:.0f})")
            print(f"      中心: ({cx:.0f},{cy:.0f})")
        
        conn.close()
        
        print("=" * 60)
        print("✅ 查詢完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 資料庫查詢錯誤: {e}")

if __name__ == "__main__":
    check_database_results()
