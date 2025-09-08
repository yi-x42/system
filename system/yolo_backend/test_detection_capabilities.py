"""
檢測能力測試工具
測試 YOLO 模型在當前設定下的檢測能力
"""

import asyncio
import cv2
import numpy as np
from app.services.yolo_service import YOLOService
from app.services.camera_service import camera_manager
from app.core.logger import detection_logger

async def test_yolo_detection():
    """測試 YOLO 檢測功能"""
    print("🧪 開始測試 YOLO 檢測功能...")
    
    # 初始化 YOLO 服務
    yolo_service = YOLOService()
    
    # 嘗試攝影機檢測
    try:
        # 啟動攝影機
        print("📷 啟動攝影機...")
        camera_session = await camera_manager.get_camera(0)
        if not camera_session:
            print("❌ 無法啟動攝影機")
            return
        
        print("✅ 攝影機啟動成功")
        
        # 獲取一幀圖像
        print("📸 獲取影像...")
        frame_data = camera_session.get_latest_frame()
        if frame_data is None:
            print("❌ 無法獲取影像")
            return
        
        timestamp, frame = frame_data
        print(f"✅ 獲取影像成功，大小: {frame.shape}")
        
        # 進行檢測 - 使用多個不同的信心度閾值
        confidence_levels = [0.1, 0.25, 0.5, 0.7]
        
        for conf in confidence_levels:
            print(f"\n🔍 測試信心度閾值: {conf}")
            detection_result = await yolo_service.predict(
                frame,
                conf_threshold=conf,
                iou_threshold=0.45
            )
            
            if detection_result and detection_result.get('objects'):
                objects = detection_result['objects']
                print(f"✅ 檢測到 {len(objects)} 個物件:")
                for i, obj in enumerate(objects):
                    print(f"  {i+1}. {obj.get('class', 'unknown')} (信心度: {obj.get('confidence', 0):.3f})")
            else:
                print("❌ 未檢測到任何物件")
        
        # 創建一個測試圖像（包含明顯物件）
        print("\n🎨 創建測試圖像...")
        test_image = create_test_image()
        
        print("🔍 測試合成圖像檢測...")
        test_result = await yolo_service.predict(
            test_image,
            conf_threshold=0.25,
            iou_threshold=0.45
        )
        
        if test_result and test_result.get('objects'):
            objects = test_result['objects']
            print(f"✅ 合成圖像檢測到 {len(objects)} 個物件:")
            for i, obj in enumerate(objects):
                print(f"  {i+1}. {obj.get('class', 'unknown')} (信心度: {obj.get('confidence', 0):.3f})")
        else:
            print("❌ 合成圖像未檢測到任何物件")
            
        # 停止攝影機
        await camera_manager.stop_camera(0)
        print("📷 攝影機已停止")
        
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

def create_test_image():
    """創建一個包含簡單形狀的測試圖像"""
    # 創建640x480的黑色圖像
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 繪製一些簡單的形狀（模擬物件）
    # 矩形 (模擬書本或手機)
    cv2.rectangle(img, (100, 100), (200, 300), (255, 255, 255), -1)
    cv2.rectangle(img, (105, 105), (195, 295), (0, 0, 0), 2)
    
    # 圓形 (模擬球或杯子)
    cv2.circle(img, (400, 200), 50, (255, 255, 255), -1)
    cv2.circle(img, (400, 200), 45, (0, 0, 0), 2)
    
    # 添加一些紋理
    for i in range(0, 640, 20):
        cv2.line(img, (i, 0), (i, 480), (50, 50, 50), 1)
    for i in range(0, 480, 20):
        cv2.line(img, (0, i), (640, i), (50, 50, 50), 1)
    
    return img

async def test_camera_only():
    """僅測試攝影機功能"""
    print("📷 測試攝影機功能...")
    
    try:
        camera_session = await camera_manager.get_camera(0)
        if not camera_session:
            print("❌ 無法啟動攝影機")
            return
        
        print("✅ 攝影機啟動成功")
        
        # 連續獲取幾幀檢查穩定性
        for i in range(5):
            frame_data = camera_session.get_latest_frame()
            if frame_data is not None:
                timestamp, frame = frame_data
                print(f"✅ 第 {i+1} 幀獲取成功，大小: {frame.shape}")
            else:
                print(f"❌ 第 {i+1} 幀獲取失敗")
            
            await asyncio.sleep(0.5)
        
        await camera_manager.stop_camera(0)
        print("📷 攝影機已停止")
        
    except Exception as e:
        print(f"❌ 攝影機測試失敗: {e}")

if __name__ == "__main__":
    print("🚀 開始檢測能力測試")
    print("=" * 50)
    
    # 先測試攝影機
    print("階段 1: 攝影機測試")
    asyncio.run(test_camera_only())
    
    print("\n" + "=" * 50)
    print("階段 2: YOLO 檢測測試")
    asyncio.run(test_yolo_detection())
    
    print("\n" + "=" * 50)
    print("🎯 測試完成")
