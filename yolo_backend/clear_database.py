#!/usr/bin/env python3
"""
清除資料庫所有資料的腳本
注意：此操作不可逆，請確認後再執行
"""

import asyncio
import sys
from pathlib import Path

# 添加專案路徑
sys.path.append(st                print("\n✅ 資料庫清除完成！")
                print("🎮 現在系統已準備好使用 Unity 座標格式")
                print("📝 新的檢測結果將直接儲存為 Unity 螢幕座標")
            else:
                print("✅ 資料庫已經是空的或沒有找到資料")
                
        # 清理相關檔案（無論是否清除資料庫）
        print("\n   🔄 清理相關檔案...")
        
        # 清理分析結果檔案
        analysis_dir = Path("analysis_results")
        if analysis_dir.exists():
            for file in analysis_dir.glob("*.csv"):
                try:
                    file.unlink()
                    print(f"      🗑️  已刪除: {file.name}")
                except Exception as e:
                    print(f"      ⚠️  無法刪除 {file.name}: {e}")
        
        # 清理標註影片檔案
        annotated_dir = Path("annotated_videos")
        if annotated_dir.exists():
            for file in annotated_dir.glob("*"):
                if file.is_file():
                    try:
                        file.unlink()
                        print(f"      🗑️  已刪除: {file.name}")
                    except Exception as e:
                        print(f"      ⚠️  無法刪除 {file.name}: {e}")
            
    except Exception as e:
        print(f"❌ 資料庫操作失敗: {e}")
        print("請檢查:")
        print("1. PostgreSQL 服務是否啟動")
        print("2. 資料庫連接設定是否正確")
        print("3. 資料庫是否存在")
        print(f"4. 連接字串: {getattr(settings, 'DATABASE_URL', '未設定')}")e__).parent))

# 使用系統的資料庫設定
from app.core.database import AsyncSessionLocal, async_engine
from app.core.config import settings
from sqlalchemy import text
import os

async def clear_all_data():
    """清除所有資料表的資料"""
    
    print("⚠️  準備清除資料庫所有資料")
    print("=" * 50)
    
    try:
        # 使用系統的資料庫連接
        print(f"🔗 連接資料庫: {settings.DATABASE_URL}")
        
        async with AsyncSessionLocal() as session:
            print("🔍 檢查資料表狀態...")
            
            # 檢查各表的資料筆數
            tables_info = []
            
            try:
                # 檢查 behavior_events 表
                result = await session.execute(text("SELECT COUNT(*) FROM behavior_events"))
                behavior_count = result.scalar()
                tables_info.append(("behavior_events", behavior_count))
            except Exception as e:
                tables_info.append(("behavior_events", f"表格不存在或錯誤: {e}"))
            
            try:
                # 檢查 detection_results 表
                result = await session.execute(text("SELECT COUNT(*) FROM detection_results"))
                detection_count = result.scalar()
                tables_info.append(("detection_results", detection_count))
            except Exception as e:
                tables_info.append(("detection_results", f"表格不存在或錯誤: {e}"))
            
            try:
                # 檢查 analysis_records 表
                result = await session.execute(text("SELECT COUNT(*) FROM analysis_records"))
                analysis_count = result.scalar()
                tables_info.append(("analysis_records", analysis_count))
            except Exception as e:
                tables_info.append(("analysis_records", f"表格不存在或錯誤: {e}"))
            
            # 檢查所有資料表
            try:
                result = await session.execute(text("""
                    SELECT table_name, 
                           (xpath('/row/c/text()', 
                                  query_to_xml(format('select count(*) as c from %I.%I', 
                                                      table_schema, table_name), false, true, ''))
                           )[1]::text::int as row_count
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                      AND table_type = 'BASE TABLE'
                """))
                all_tables = result.fetchall()
                
                print("\n📊 所有資料表狀態:")
                total_all_records = 0
                for table_name, row_count in all_tables:
                    if row_count is not None:
                        print(f"   📋 {table_name}: {row_count:,} 筆資料")
                        total_all_records += row_count
                    else:
                        print(f"   📋 {table_name}: 無法查詢")
                        
                print(f"\n📈 資料庫總共 {total_all_records:,} 筆資料")
                
            except Exception as e:
                print(f"⚠️  無法查詢所有表格: {e}")
                
                # 顯示原本檢查的結果
                print("\n📊 主要資料表狀態:")
                total_records = 0
                for table_name, count in tables_info:
                    if isinstance(count, int):
                        print(f"   📋 {table_name}: {count:,} 筆資料")
                        total_records += count
                    else:
                        print(f"   📋 {table_name}: {count}")
                
                print(f"\n📈 主要表格總共 {total_records:,} 筆資料")
            
            # 如果有資料，詢問是否清除
            if total_all_records > 0 or any(isinstance(count, int) and count > 0 for _, count in tables_info):
                # 確認清除操作
                print("\n⚠️  這將會刪除所有資料，包括:")
                print("   🔸 所有檢測結果 (舊的像素座標格式)")
                print("   🔸 所有行為事件")
                print("   🔸 所有分析記錄")
                print("   🔸 所有關聯的追蹤 ID 和時間戳記")
                print("\n💡 清除後，新的檢測將使用 Unity 座標格式儲存")
                
                confirm = input("\n❓ 確定要清除所有資料嗎？輸入 'YES' 確認: ").strip()
                
                if confirm != 'YES':
                    print("❌ 操作已取消")
                    return
                
                print("\n🗑️  開始清除資料...")
                
                # 依照外鍵關係順序刪除
                try:
                    print("   🔄 清除行為事件資料...")
                    result = await session.execute(text("DELETE FROM behavior_events"))
                    await session.commit()
                    print(f"      ✅ 已刪除 {result.rowcount} 筆行為事件")
                except Exception as e:
                    print(f"      ⚠️  行為事件表: {e}")
                
                try:
                    print("   🔄 清除檢測結果資料...")
                    result = await session.execute(text("DELETE FROM detection_results"))
                    await session.commit()
                    print(f"      ✅ 已刪除 {result.rowcount} 筆檢測結果")
                except Exception as e:
                    print(f"      ⚠️  檢測結果表: {e}")
                
                try:
                    print("   🔄 清除分析記錄資料...")
                    result = await session.execute(text("DELETE FROM analysis_records"))
                    await session.commit()
                    print(f"      ✅ 已刪除 {result.rowcount} 筆分析記錄")
                except Exception as e:
                    print(f"      ⚠️  分析記錄表: {e}")
                
                # 重置自動遞增 ID
                print("   🔄 重置資料表 ID 序列...")
                try:
                    await session.execute(text("ALTER SEQUENCE analysis_records_id_seq RESTART WITH 1"))
                    await session.execute(text("ALTER SEQUENCE detection_results_id_seq RESTART WITH 1"))
                    await session.execute(text("ALTER SEQUENCE behavior_events_id_seq RESTART WITH 1"))
                    await session.commit()
                    print("      ✅ ID 序列已重置")
                except Exception as e:
                    print(f"      ⚠️  重置序列: {e}")
                
                print("\n✅ 資料庫清除完成！")
                print("🎮 現在系統已準備好使用 Unity 座標格式")
                print("� 新的檢測結果將直接儲存為 Unity 螢幕座標")
            else:
                print("✅ 資料庫已經是空的或沒有找到資料")
            
    except Exception as e:
        print(f"❌ 資料庫操作失敗: {e}")
        print("請檢查:")
        print("1. PostgreSQL 服務是否啟動")
        print("2. 資料庫連接設定是否正確")
        print("3. 資料庫是否存在")

def main():
    """主函數"""
    print("🗑️  YOLOv11 資料庫清除工具")
    print("=" * 50)
    
    print("💡 此工具將清除所有舊的座標資料")
    print("   清除後，新檢測將使用 Unity 座標格式")
    print("")
    
    # 運行清除操作
    asyncio.run(clear_all_data())
    
    print("\n" + "=" * 50)
    print("🎯 建議後續步驟:")
    print("1. 重新啟動 YOLO 服務")
    print("2. 進行新的影片分析")
    print("3. 確認新資料使用 Unity 座標格式")
    print("")
    input("按 Enter 鍵退出...")

if __name__ == "__main__":
    main()
