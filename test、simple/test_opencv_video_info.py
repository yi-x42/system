"""
測試 OpenCV 影片資訊讀取功能
"""
import os
import cv2
from datetime import datetime

def test_video_info(file_path):
    """測試單個影片檔案的資訊讀取"""
    print(f"\n🎬 正在分析影片：{os.path.basename(file_path)}")
    print("=" * 60)
    
    try:
        # 檔案基本資訊
        if not os.path.exists(file_path):
            print("❌ 檔案不存在")
            return
        
        stat_info = os.stat(file_path)
        file_size = stat_info.st_size
        upload_time = datetime.fromtimestamp(stat_info.st_mtime)
        
        # 格式化檔案大小
        if file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f}KB"
        elif file_size < 1024 * 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f}MB"
        else:
            size_str = f"{file_size / (1024 * 1024 * 1024):.1f}GB"
        
        print(f"📁 檔案大小：{size_str}")
        print(f"🕐 修改時間：{upload_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # OpenCV 分析
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            print("❌ OpenCV 無法開啟影片檔案")
            return
        
        # 獲取影片屬性
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"📺 解析度：{width}x{height}")
        print(f"🎯 幀率：{fps:.2f} FPS")
        print(f"📊 總幀數：{total_frames}")
        
        # 計算時長
        if fps > 0 and total_frames > 0:
            duration_seconds = total_frames / fps
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            print(f"⏱️  影片時長：{minutes}:{seconds:02d} ({duration_seconds:.1f}秒)")
        else:
            print("⚠️  無法計算影片時長")
        
        # 檢查編碼格式
        fourcc = cap.get(cv2.CAP_PROP_FOURCC)
        codec = "".join([chr((int(fourcc) >> 8 * i) & 0xFF) for i in range(4)])
        print(f"🎨 編碼格式：{codec}")
        
        cap.release()
        print("✅ 分析完成")
        
    except Exception as e:
        print(f"❌ 分析失敗：{e}")

def test_all_videos():
    """測試目錄中所有影片"""
    videos_dir = "D:/project/system/yolo_backend/uploads/videos"
    
    if not os.path.exists(videos_dir):
        print(f"❌ 影片目錄不存在：{videos_dir}")
        return
    
    supported_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    video_files = []
    
    for filename in os.listdir(videos_dir):
        if any(filename.lower().endswith(ext) for ext in supported_extensions):
            file_path = os.path.join(videos_dir, filename)
            if os.path.isfile(file_path):
                video_files.append(file_path)
    
    if not video_files:
        print("❌ 沒有找到影片檔案")
        return
    
    print(f"🔍 找到 {len(video_files)} 個影片檔案")
    
    for file_path in video_files:
        test_video_info(file_path)

if __name__ == "__main__":
    print("🎬 OpenCV 影片資訊分析測試")
    print("=" * 60)
    test_all_videos()
