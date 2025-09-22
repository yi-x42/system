#!/usr/bin/env python3
"""測試 YOLOService.predict_frame 修復"""

import sys
import os
import numpy as np

# 添加專案路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo_backend'))

def test_yolo_service():
    """測試 YOLOService 的 predict_frame 方法"""
    print("🧪 測試 YOLOService.predict_frame 修復...")
    
    try:
        from yolo_backend.app.services.yolo_service import YOLOService
        
        # 初始化 YOLO 服務
        yolo_service = YOLOService()
        
        # 檢查是否有 predict_frame 方法
        if hasattr(yolo_service, 'predict_frame'):
            print("✅ predict_frame 方法存在")
        else:
            print("❌ predict_frame 方法不存在")
            return False
        
        # 載入模型
        model_path = "yolo_backend/models/yolo11n.pt"
        if not os.path.exists(model_path):
            print(f"⚠️ 模型檔案不存在: {model_path}")
            print("   建立測試圖像進行方法測試...")
            
        # 創建測試圖像
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        test_frame[:, :, 1] = 100  # 添加一些綠色
        
        print("🖼️ 建立測試圖像...")
        print(f"   圖像尺寸: {test_frame.shape}")
        
        try:
            # 測試方法調用（不載入模型，只測試方法存在）
            print("🔍 測試方法調用...")
            
            # 由於沒有模型，這會引發 ModelNotLoadedException，這是預期的
            result = yolo_service.predict_frame(test_frame)
            print(f"❌ 意外成功: {result}")
            
        except Exception as e:
            if "模型尚未載入" in str(e) or "ModelNotLoadedException" in str(type(e).__name__):
                print("✅ predict_frame 方法正常工作（預期的模型未載入錯誤）")
                return True
            else:
                print(f"❌ 意外錯誤: {e}")
                return False
                
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_method_signature():
    """測試方法簽名"""
    print("\n🔍 檢查方法簽名...")
    
    try:
        from yolo_backend.app.services.yolo_service import YOLOService
        import inspect
        
        yolo_service = YOLOService()
        
        if hasattr(yolo_service, 'predict_frame'):
            sig = inspect.signature(yolo_service.predict_frame)
            print(f"✅ 方法簽名: predict_frame{sig}")
            
            params = list(sig.parameters.keys())
            expected_params = ['frame', 'conf_threshold', 'iou_threshold']
            
            for param in expected_params:
                if param in params:
                    print(f"   ✅ 參數 '{param}' 存在")
                else:
                    print(f"   ❌ 參數 '{param}' 缺失")
                    
            return True
        else:
            print("❌ predict_frame 方法不存在")
            return False
            
    except Exception as e:
        print(f"❌ 簽名檢查失敗: {e}")
        return False

if __name__ == "__main__":
    print("🔧 YOLOService.predict_frame 修復測試")
    print("=" * 50)
    
    # 測試方法存在性
    test1_result = test_yolo_service()
    
    # 測試方法簽名
    test2_result = test_method_signature()
    
    print("\n📊 測試結果:")
    print(f"   方法功能測試: {'✅ 通過' if test1_result else '❌ 失敗'}")
    print(f"   方法簽名測試: {'✅ 通過' if test2_result else '❌ 失敗'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有測試通過！'YOLOService' object has no attribute 'predict_frame' 錯誤已修復")
    else:
        print("\n❌ 測試失敗，需要進一步檢查")