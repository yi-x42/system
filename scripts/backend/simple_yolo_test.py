"""
簡單的YOLO檢測測試
"""

import cv2
import numpy as np
import os
import sys

# 添加路徑以便導入模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_detection():
    """基本檢測測試"""
    print("🚀 開始基本檢測測試")
    
    try:
        # 檢查YOLO模型檔案
        from app.core.config import settings
        model_path = settings.YOLO_MODEL_PATH
        print(f"📂 模型路徑: {model_path}")
        
        if not os.path.exists(model_path):
            print(f"❌ 模型檔案不存在: {model_path}")
            # 嘗試下載模型
            print("📥 嘗試下載 YOLOv11 模型...")
            from ultralytics import YOLO
            model = YOLO('yolo11n.pt')  # 這會自動下載
            print("✅ 模型下載完成")
        
        # 初始化YOLO
        from ultralytics import YOLO
        model = YOLO(model_path)
        print("✅ YOLO 模型載入成功")
        
        # 創建測試圖像
        print("🎨 創建測試圖像...")
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        # 繪製一個明顯的矩形
        cv2.rectangle(test_img, (200, 150), (400, 350), (255, 255, 255), -1)
        
        # 進行檢測
        print("🔍 執行檢測...")
        results = model(test_img, conf=0.1, verbose=False)
        
        # 檢查結果
        if results and len(results) > 0:
            detections = results[0].boxes
            if detections is not None and len(detections) > 0:
                print(f"✅ 檢測到 {len(detections)} 個物件")
                for i, detection in enumerate(detections):
                    conf = detection.conf.item()
                    cls = int(detection.cls.item())
                    print(f"  {i+1}. 類別: {cls}, 信心度: {conf:.3f}")
            else:
                print("❌ 未檢測到任何物件（測試圖像）")
        
        # 測試攝影機
        print("\n📷 測試攝影機...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ 無法開啟攝影機")
            return
        
        print("✅ 攝影機開啟成功")
        
        # 獲取一幀
        ret, frame = cap.read()
        if ret:
            print(f"✅ 獲取影像成功，大小: {frame.shape}")
            
            # 對真實影像進行檢測
            print("🔍 對真實影像進行檢測...")
            real_results = model(frame, conf=0.25, verbose=False)
            
            if real_results and len(real_results) > 0:
                real_detections = real_results[0].boxes
                if real_detections is not None and len(real_detections) > 0:
                    print(f"✅ 真實影像檢測到 {len(real_detections)} 個物件")
                    for i, detection in enumerate(real_detections):
                        conf = detection.conf.item()
                        cls = int(detection.cls.item())
                        class_names = model.names
                        class_name = class_names.get(cls, f"class_{cls}")
                        print(f"  {i+1}. {class_name} (信心度: {conf:.3f})")
                else:
                    print("❌ 真實影像未檢測到任何物件")
            
        else:
            print("❌ 無法獲取影像")
        
        cap.release()
        print("📷 攝影機已關閉")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_detection()
