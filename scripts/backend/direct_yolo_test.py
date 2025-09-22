"""
直接檢測測試工具 - 用於診斷YOLO檢測問題
"""

import cv2
import numpy as np
import os
import sys
import time
from pathlib import Path

# 添加路徑
sys.path.append(str(Path(__file__).parent))

def test_direct_yolo():
    """直接測試YOLO檢測"""
    print("🚀 開始直接YOLO檢測測試")
    print("=" * 50)
    
    try:
        # 導入YOLO
        from ultralytics import YOLO
        print("✅ YOLO導入成功")
        
        # 檢查模型檔案
        model_path = "yolo11n.pt"
        if not os.path.exists(model_path):
            print(f"📥 下載模型: {model_path}")
            model = YOLO(model_path)  # 會自動下載
        else:
            print(f"✅ 模型存在: {model_path}")
            model = YOLO(model_path)
        
        print("✅ YOLO模型載入成功")
        print(f"📋 模型類別數: {len(model.names)}")
        print(f"📋 前10個類別: {list(model.names.values())[:10]}")
        
        # 測試攝影機
        print("\n📷 測試攝影機...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ 無法開啟攝影機")
            return
            
        # 設定攝影機屬性
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("✅ 攝影機開啟成功")
        
        # 連續檢測幾幀
        print("\n🔍 開始連續檢測測試...")
        for i in range(10):
            ret, frame = cap.read()
            if not ret:
                print(f"❌ 第{i+1}幀獲取失敗")
                continue
                
            print(f"📸 第{i+1}幀: {frame.shape}")
            
            # 進行檢測 - 使用多個信心度閾值
            for conf in [0.05, 0.1, 0.25, 0.5]:
                start_time = time.time()
                results = model(frame, conf=conf, verbose=False)
                inference_time = time.time() - start_time
                
                detections = results[0].boxes
                if detections is not None and len(detections) > 0:
                    print(f"  ✅ 信心度{conf}: 檢測到{len(detections)}個物件 (推論時間: {inference_time:.3f}s)")
                    for j, detection in enumerate(detections):
                        conf_score = detection.conf.item()
                        cls = int(detection.cls.item())
                        class_name = model.names.get(cls, f"class_{cls}")
                        bbox = detection.xyxy[0].tolist()
                        print(f"    {j+1}. {class_name} ({conf_score:.3f}) [{bbox[0]:.0f},{bbox[1]:.0f},{bbox[2]:.0f},{bbox[3]:.0f}]")
                else:
                    print(f"  ❌ 信心度{conf}: 未檢測到物件")
            
            time.sleep(0.5)
        
        # 創建測試圖像
        print("\n🎨 測試合成圖像...")
        test_img = create_test_image_with_objects()
        
        for conf in [0.05, 0.1, 0.25, 0.5]:
            results = model(test_img, conf=conf, verbose=False)
            detections = results[0].boxes
            if detections is not None and len(detections) > 0:
                print(f"✅ 合成圖像 信心度{conf}: 檢測到{len(detections)}個物件")
                for j, detection in enumerate(detections):
                    conf_score = detection.conf.item()
                    cls = int(detection.cls.item())
                    class_name = model.names.get(cls, f"class_{cls}")
                    print(f"  {j+1}. {class_name} ({conf_score:.3f})")
            else:
                print(f"❌ 合成圖像 信心度{conf}: 未檢測到物件")
        
        cap.release()
        print("\n✅ 測試完成")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def create_test_image_with_objects():
    """創建包含明顯物件的測試圖像"""
    # 創建白底圖像
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # 繪製類似手機的矩形 (黑色)
    cv2.rectangle(img, (100, 150), (250, 400), (0, 0, 0), -1)
    cv2.rectangle(img, (110, 160), (240, 190), (100, 100, 100), -1)  # 螢幕
    
    # 繪製類似杯子的圓形 (藍色)
    cv2.circle(img, (450, 300), 60, (255, 0, 0), -1)
    cv2.circle(img, (450, 300), 50, (200, 200, 200), -1)
    
    # 繪製類似書本的矩形 (綠色)
    cv2.rectangle(img, (300, 100), (500, 200), (0, 255, 0), -1)
    cv2.line(img, (300, 150), (500, 150), (0, 200, 0), 3)
    
    # 添加一些紋理
    cv2.putText(img, "TEST", (320, 160), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return img

def test_camera_only():
    """僅測試攝影機"""
    print("📷 攝影機功能測試")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ 攝影機無法開啟")
        return False
        
    for i in range(5):
        ret, frame = cap.read()
        if ret:
            print(f"✅ 第{i+1}幀: {frame.shape}, 像素範圍: {frame.min()}-{frame.max()}")
        else:
            print(f"❌ 第{i+1}幀獲取失敗")
        time.sleep(0.2)
    
    cap.release()
    return True

if __name__ == "__main__":
    print("🔧 YOLO檢測診斷工具")
    print("=" * 50)
    
    # 先測試攝影機
    if test_camera_only():
        print("\n" + "=" * 50)
        # 再測試YOLO
        test_direct_yolo()
    else:
        print("❌ 攝影機測試失敗，停止後續測試")
