"""
攝影機診斷工具
"""
import cv2
import sys

def test_camera(camera_index=0):
    print(f"🔍 測試攝影機 {camera_index}...")
    
    # 測試不同的後端
    backends = [
        ('DEFAULT', None),
        ('CAP_DSHOW', getattr(cv2, 'CAP_DSHOW', None)),
        ('CAP_MSMF', getattr(cv2, 'CAP_MSMF', None))
    ]
    
    for backend_name, backend_flag in backends:
        print(f"\n📡 嘗試後端: {backend_name}")
        
        try:
            if backend_flag is not None:
                cap = cv2.VideoCapture(camera_index, backend_flag)
            else:
                cap = cv2.VideoCapture(camera_index)
            
            if cap.isOpened():
                print(f"  ✅ 攝影機已開啟")
                
                # 測試讀取畫面
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    print(f"  ✅ 成功讀取畫面: {width}x{height}")
                    print(f"  📊 FPS: {cap.get(cv2.CAP_PROP_FPS)}")
                    cap.release()
                    return True
                else:
                    print(f"  ❌ 無法讀取畫面")
            else:
                print(f"  ❌ 無法開啟攝影機")
                
            cap.release()
            
        except Exception as e:
            print(f"  ❌ 錯誤: {e}")
    
    return False

def scan_cameras():
    print("🔍 掃描可用攝影機...")
    found_cameras = []
    
    for i in range(5):  # 測試攝影機 0-4
        print(f"\n🎥 檢查攝影機 {i}:")
        if test_camera(i):
            found_cameras.append(i)
            print(f"  ✅ 攝影機 {i} 可用")
        else:
            print(f"  ❌ 攝影機 {i} 不可用")
    
    print(f"\n📋 總結:")
    if found_cameras:
        print(f"  ✅ 找到可用攝影機: {found_cameras}")
    else:
        print(f"  ❌ 沒有找到可用的攝影機")
        print(f"  💡 建議檢查:")
        print(f"     - 攝影機是否正確連接")
        print(f"     - 其他程式是否正在使用攝影機")
        print(f"     - 攝影機驅動程式是否正常")

if __name__ == "__main__":
    scan_cameras()
