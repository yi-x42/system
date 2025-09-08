import cv2
from ultralytics import YOLO
import time

print('� 超簡單檢測測試')
print('=' * 30)

# 測試攝影機
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print('❌ 攝影機無法開啟')
    exit()

print('✅ 攝影機開啟成功')

# 獲取影像
ret, frame = cap.read()
if not ret:
    print('❌ 無法獲取影像')
    cap.release()
    exit()

print(f'✅ 獲取影像成功: {frame.shape}')
print(f'📊 像素值範圍: {frame.min()} - {frame.max()}')

# 載入YOLO模型
print('🤖 載入YOLO模型...')
model = YOLO('yolo11n.pt')
print('✅ YOLO模型載入完成')
print(f'📋 支援類別數量: {len(model.names)}')

# 執行檢測 - 使用超低信心度
print('🔍 開始檢測...')
start_time = time.time()
results = model.predict(frame, conf=0.01, verbose=True, save=False, show=False)
inference_time = time.time() - start_time

print(f'⏱️ 推論時間: {inference_time:.3f}秒')

# 檢查結果
if results and len(results) > 0:
    result = results[0]
    print(f'📊 結果物件: {type(result)}')
    print(f'📊 是否有boxes: {result.boxes is not None}')
    
    if result.boxes is not None:
        boxes = result.boxes
        print(f'🎯 檢測到 {len(boxes)} 個物件!')
        
        if len(boxes) > 0:
            for i, box in enumerate(boxes):
                cls_id = int(box.cls.item())
                conf = box.conf.item()
                cls_name = model.names[cls_id]
                xyxy = box.xyxy[0].tolist()
                print(f'  {i+1}. {cls_name} (信心度: {conf:.3f}) [{xyxy[0]:.0f},{xyxy[1]:.0f},{xyxy[2]:.0f},{xyxy[3]:.0f}]')
        else:
            print('❌ boxes存在但為空')
    else:
        print('❌ 沒有boxes')
else:
    print('❌ 沒有檢測結果')

# 嘗試更低的信心度
print('\n🔍 嘗試信心度 0.001...')
results2 = model.predict(frame, conf=0.001, verbose=True, save=False, show=False)
if results2 and len(results2) > 0 and results2[0].boxes is not None:
    boxes2 = results2[0].boxes
    print(f'🎯 超低信心度檢測到 {len(boxes2)} 個物件!')
    for i, box in enumerate(boxes2[:5]):  # 只顯示前5個
        cls_id = int(box.cls.item())
        conf = box.conf.item()
        cls_name = model.names[cls_id]
        print(f'  {i+1}. {cls_name} (信心度: {conf:.3f})')
else:
    print('❌ 超低信心度也沒有檢測到')

cap.release()
print('\n✅ 測試完成')
print('=' * 30)
