"""
媒體資訊工具：提供解析度量測（以 OpenCV 為主，ffprobe 可選擇性支援）。

用法：
    from app.utils.media_info import probe_resolution
    w, h = probe_resolution(source)

設計說明：
    - 先嘗試從 VideoCapture 的屬性取得寬高；若為 0，嘗試讀第一張影格。
    - 支援本機檔案與串流 URL（rtsp/http）。
    - 失敗時回傳 (None, None)。
"""

from typing import Optional, Tuple
import cv2


def _try_capture_props(cap: cv2.VideoCapture) -> Tuple[Optional[int], Optional[int]]:
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if width > 0 and height > 0:
        return width, height
    return None, None


def _try_read_first_frame(cap: cv2.VideoCapture) -> Tuple[Optional[int], Optional[int]]:
    # 嘗試讀取最多數張影格，以避免某些串流初始化較慢
    for _ in range(5):
        ok, frame = cap.read()
        if ok and frame is not None:
            h, w = frame.shape[:2]
            if w > 0 and h > 0:
                return w, h
    return None, None


def probe_resolution(source: str, timeout_ms: int = 3000) -> Tuple[Optional[int], Optional[int]]:
    """
    量測影片檔或串流來源的解析度。

    參數：
        source: 檔案路徑或串流 URL (rtsp/http)
        timeout_ms: 開啟串流的逾時毫秒數（對某些後端有效）

    回傳：
        (width, height)；若失敗，回傳 (None, None)
    """
    if not source:
        return None, None

    # 針對某些串流協定可設定逾時，OpenCV 不一定支援所有參數，盡力而為
    params = [
        cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_ms,
        cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout_ms,
    ]

    try:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            # 再嘗試帶參數的打開（部分後端支援）
            cap = cv2.VideoCapture(source, cv2.CAP_ANY, params)
            if not cap.isOpened():
                return None, None

        # 先用屬性拿寬高
        w, h = _try_capture_props(cap)
        if w and h:
            cap.release()
            return w, h

        # 再嘗試讀取第一張影格
        w, h = _try_read_first_frame(cap)
        cap.release()
        return w, h
    except Exception:
        # 靜默失敗，交由呼叫端決策
        try:
            cap.release()  # 型別保險
        except Exception:
            pass
        return None, None
