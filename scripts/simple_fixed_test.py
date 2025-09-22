"""
最簡單的YOLO測試 - 使用固定圖像
"""

from ultralytics import YOLO
import numpy as np
import cv2

print('🧪 固定圖像YOLO測試')

# 創建一個簡單的測試圖像
img = np.ones((480, 640, 3), dtype=np.uint8) * 128  # 灰色背景

# 繪製一個簡單的白色矩形（模擬物件）
cv2.rectangle(img, (200, 150), (400, 350), (255, 255, 255), -1)
cv2.putText(img, "TEST", (250, 250), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)

print(f'✅ 創建測試圖像: {img.shape}')

# 載入YOLO
model = YOLO('yolo11n.pt')
print('✅ YOLO載入成功')

# 檢測
results = model.predict(img, conf=0.01, verbose=True)
print(f'📊 結果數量: {len(results)}')

if results and len(results) > 0:
    result = results[0]
    if result.boxes is not None and len(result.boxes) > 0:
        print(f'🎯 檢測到 {len(result.boxes)} 個物件')
        for i, box in enumerate(result.boxes):
            cls_id = int(box.cls.item())
            conf = box.conf.item()
            cls_name = model.names[cls_id]
            print(f'  {i+1}. {cls_name} (信心度: {conf:.3f})')
    else:
        print('❌ 沒有檢測到物件')
else:
    print('❌ 沒有結果')

print('\n測試完成')
