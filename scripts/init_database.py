#!/usr/bin/env python3
"""
資料庫初始化腳本
"""
import asyncio
import sys
from pathlib import Path

# 添加專案路徑
sys.path.append(str(Path(__file__).parent))

import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """主函數"""
    print("🗄️  YOLOv11 資料庫初始化")
    print("=" * 50)
    
    try:
        # 手動設定環境變數來確保配置正確
        import os
        os.environ['POSTGRES_PASSWORD'] = '49679904'
        os.environ['POSTGRES_DB'] = 'yolo_analysis'
        
        from app.core.config import settings
        from app.core.database import init_database, check_database_connection
        
        print(f"資料庫 URL: {settings.DATABASE_URL}")
        print("")
        
        # 檢查資料庫連接
        print("🔍 檢查資料庫連接...")
        if not await check_database_connection():
            print("❌ 無法連接到資料庫，請檢查：")
            print("   1. PostgreSQL 服務是否已啟動")
            print("   2. 資料庫連接參數是否正確 (.env 檔案)")
            print("   3. 防火牆設定是否允許連接")
            print("   4. 資料庫是否已建立")
            return False
        
        # 初始化資料庫
        print("🔧 初始化資料庫表格...")
        if await init_database():
            print("✅ 資料庫初始化成功！")
            print("\n可用的資料表：")
            print("  📊 analysis_records - 分析記錄")
            print("  🔍 detection_results - 檢測結果")
            print("  🎯 behavior_events - 行為事件")
            return True
        else:
            print("❌ 資料庫初始化失敗")
            return False
            
    except ImportError as e:
        print(f"❌ 模組導入失敗: {e}")
        print("請確認已安裝所有必要的套件：")
        print("   python -m pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"初始化失敗: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 初始化已取消")
    except Exception as e:
        logger.error(f"初始化失敗: {e}")
        sys.exit(1)
