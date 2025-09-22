#!/usr/bin/env python3
"""
直接檢查 FastAPI 應用程式的路由
"""
import sys
sys.path.append('yolo_backend')

try:
    from app.main import app
    print("✅ 成功導入 FastAPI 應用程式")
    
    # 檢查所有路由
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            for method in route.methods:
                if method != 'HEAD':  # 跳過 HEAD 方法
                    routes.append(f"{method} {route.path}")
    
    # 搜尋包含 create-task 的路由
    create_task_routes = [r for r in routes if 'create-task' in r]
    
    print(f"\n🔍 總共找到 {len(routes)} 個路由")
    print(f"🎯 包含 'create-task' 的路由: {len(create_task_routes)}")
    
    if create_task_routes:
        print("✅ create-task 路由已註冊:")
        for route in create_task_routes:
            print(f"   {route}")
    else:
        print("❌ 沒有找到 create-task 路由")
        
        # 顯示分析相關的路由
        analysis_routes = [r for r in routes if '/analysis' in r]
        print(f"\n📋 分析相關路由 ({len(analysis_routes)}):")
        for route in sorted(analysis_routes):
            print(f"   {route}")
            
        # 顯示 new_analysis 相關的路由
        database_routes = [r for r in routes if '/database' in r]
        print(f"\n🗄️ 資料庫相關路由 ({len(database_routes)}):")
        for route in sorted(database_routes):
            print(f"   {route}")
    
except Exception as e:
    print(f"❌ 載入應用程式失敗: {str(e)}")
    import traceback
    traceback.print_exc()
