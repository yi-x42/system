"""攝影機管理服務：負責啟動/停止本機攝影機並緩存最新影格。

注意：
 - 僅支援本機裝置 index (0,1,2...)
 - 每個啟動對應一個 analysis_task（realtime_camera）
 - 提供取得最新 JPEG 影格的方法
"""

from __future__ import annotations
import cv2
import threading
import time
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field


@dataclass
class CameraSession:
    task_id: int
    camera_index: int
    width: int
    height: int
    fps: float
    backend_name: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    _cap: Optional[cv2.VideoCapture] = field(default=None, init=False)
    _thread: Optional[threading.Thread] = field(default=None, init=False)
    _running: bool = field(default=False, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _latest_frame: Optional[Tuple[float, any]] = field(default=None, init=False)  # (ts, frame)

    def start(self):
        if self._running:
            return
        
        # 嘗試多個後端來確保攝影機能正常工作
        backends_to_try = [
            ('CAP_DSHOW', getattr(cv2, 'CAP_DSHOW', None)),
            ('DEFAULT', None),
            ('CAP_MSMF', getattr(cv2, 'CAP_MSMF', None))
        ]
        
        self._cap = None
        last_error = None
        
        for backend_name, backend_flag in backends_to_try:
            try:
                if backend_flag is not None:
                    cap = cv2.VideoCapture(self.camera_index, backend_flag)
                else:
                    cap = cv2.VideoCapture(self.camera_index)
                
                if cap.isOpened():
                    # 測試是否能讀取畫面
                    time.sleep(0.1)  # 給攝影機一點時間初始化
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        self._cap = cap
                        self.backend_name = backend_name
                        print(f"✅ 攝影機 {self.camera_index} 使用 {backend_name} 後端成功啟動")
                        break
                    else:
                        cap.release()
                        last_error = f"後端 {backend_name} 無法讀取畫面"
                else:
                    cap.release()
                    last_error = f"後端 {backend_name} 無法開啟攝影機"
                    
            except Exception as e:
                last_error = f"後端 {backend_name} 發生錯誤: {e}"
                continue
        
        if self._cap is None:
            raise RuntimeError(f"Camera index {self.camera_index} 無法啟動，嘗試的所有後端都失敗。最後錯誤: {last_error}")
        
        # 設置攝影機參數
        try:
            if self.width > 0:
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            if self.height > 0:
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        except:
            pass  # 某些攝影機不支持設置解析度
        
        # 重新讀取實際參數
        self.width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH) or self.width or 640)
        self.height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or self.height or 480)
        self.fps = float(self._cap.get(cv2.CAP_PROP_FPS) or self.fps or 30.0)
        
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        consecutive_failures = 0
        max_failures = 10  # 連續失敗10次後停止
        
        while self._running:
            try:
                ok, frame = self._cap.read()
                if ok and frame is not None:
                    consecutive_failures = 0  # 重置失敗計數
                    ts = time.time()
                    with self._lock:
                        self._latest_frame = (ts, frame)
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print(f"❌ 攝影機 {self.camera_index} 連續讀取失敗 {max_failures} 次，停止循環")
                        self._running = False
                        break
                    
                # 控制抓取頻率（避免 CPU 過高）
                time.sleep(0.03)  # 約30 FPS
                
            except Exception as e:
                consecutive_failures += 1
                print(f"⚠️ 攝影機 {self.camera_index} 讀取錯誤: {e}")
                if consecutive_failures >= max_failures:
                    print(f"❌ 攝影機 {self.camera_index} 錯誤過多，停止循環")
                    self._running = False
                    break
                time.sleep(0.1)  # 錯誤時等待較長時間

    def get_latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            data = self._latest_frame
        if not data:
            return None
        _, frame = data
        ok, buf = cv2.imencode('.jpg', frame)
        if not ok:
            return None
        return buf.tobytes()

    def get_latest_frame(self) -> Optional[Tuple[float, any]]:
        """獲取最新的原始影格數據（用於 YOLO 檢測）"""
        with self._lock:
            return self._latest_frame

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
        self._cap = None


class CameraManager:
    def __init__(self):
        self._sessions: Dict[int, CameraSession] = {}
        self._lock = threading.Lock()
        # backend 快取：index -> backend_name (CAP_DSHOW / CAP_MSMF / DEFAULT)
        self._backend_cache: Dict[int, str] = {}
        self._cache_path = self._resolve_cache_path()
        self._load_cache()

    # -------- 快取處理 --------
    def _resolve_cache_path(self) -> str:
        import os
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        path = os.path.join(base, 'camera_backend_cache.json')
        return path

    def _load_cache(self):
        import json, os
        try:
            if os.path.exists(self._cache_path):
                with open(self._cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._backend_cache = {int(k): v for k, v in data.items()}
        except Exception:
            self._backend_cache = {}

    def _save_cache(self):
        import json, os
        try:
            os.makedirs(os.path.dirname(self._cache_path), exist_ok=True)
            with open(self._cache_path, 'w', encoding='utf-8') as f:
                json.dump(self._backend_cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def record_backend(self, index: int, backend_name: str):
        if not backend_name:
            return
        if self._backend_cache.get(index) == backend_name:
            return
        self._backend_cache[index] = backend_name
        self._save_cache()

    def get_cached_backend(self, index: int) -> Optional[str]:
        return self._backend_cache.get(index)

    def scan_simple(self, max_index: int = 6, warmup_frames: int = 5) -> List[int]:
        """簡單掃描：回傳可用攝影機索引列表（舊格式相容）"""
        detailed_results = self.scan(max_index=max_index, warmup_frames=warmup_frames, force_probe=True, retries=2)
        return [r['index'] for r in detailed_results if r.get('frame_ok', False)]

    def scan(
        self,
        max_index: int = 4,  # 減少掃描數量，通常攝影機都在0-3
        warmup_frames: int = 1,  # 只需1影格驗證即可
        frame_interval: float = 0.01,  # 最小間隔
        force_probe: bool = False,
        retries: int = 1
    ) -> List[Dict[str, any]]:
        """超快速攝影機掃描 - 專為即時預覽優化。

        回傳每個成功的 index 詳細資訊 (index, backend, width, height, frame_ok, source="normal|forced|cache").
        - 使用最激進的快速檢測策略
        - 優先使用快取，避免重複檢測
        - 一旦成功立即跳出
        """
        print(f"🔍 開始超快速攝影機掃描 (max_index={max_index})")
        results: List[Dict[str, any]] = []
        
        # 超快速模式：只使用最快的後端
        backend = ("DEFAULT", None)  # 只使用 DEFAULT，最快
        
        for idx in range(max_index):
            print(f"📷 檢測攝影機 {idx}...")
            
            # 檢查快取，如果有就直接使用
            cached_backend = self.get_cached_backend(idx)
            if cached_backend:
                print(f"⚡ 攝影機 {idx} 使用快取後端: {cached_backend}")
                # 快速驗證快取是否還有效
                cap = None
                try:
                    if cached_backend == "CAP_DSHOW":
                        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                    elif cached_backend == "CAP_MSMF":
                        cap = cv2.VideoCapture(idx, cv2.CAP_MSMF)
                    else:
                        cap = cv2.VideoCapture(idx)
                    
                    if cap.isOpened():
                        ok, frame = cap.read()
                        if ok and frame is not None and frame.shape[0] > 0:
                            h, w = frame.shape[:2]
                            results.append({
                                "index": idx,
                                "backend": cached_backend,
                                "backend_name": cached_backend,
                                "frame_ok": True,
                                "width": w,
                                "height": h,
                                "source": "cache",
                                "attempts": [{"backend": cached_backend, "from_cache": True}],
                                "name": f"攝影機 {idx}"
                            })
                            print(f"✅ 攝影機 {idx} 快取驗證成功")
                            cap.release()
                            continue
                    cap.release()
                except:
                    pass
            
            # 如果快取失效，進行超快速檢測
            cap = None
            try:
                cap = cv2.VideoCapture(idx)  # 只用最簡單的方式
                
                # 最小等待時間
                time.sleep(0.05)
                
                if cap.isOpened():
                    # 只讀一影格就確定
                    ok, frame = cap.read()
                    if ok and frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
                        h, w = frame.shape[:2]
                        
                        # 更新快取
                        self.record_backend(idx, "DEFAULT")
                        
                        results.append({
                            "index": idx,
                            "backend": "DEFAULT",
                            "backend_name": "DEFAULT",
                            "frame_ok": True,
                            "width": w,
                            "height": h,
                            "source": "normal",
                            "attempts": [{"backend": "DEFAULT", "success": True}],
                            "name": f"攝影機 {idx}"
                        })
                        print(f"✅ 攝影機 {idx} 檢測成功: DEFAULT 後端, 解析度 {w}x{h}")
                    else:
                        print(f"❌ 攝影機 {idx} 無法讀取影格")
                else:
                    print(f"❌ 攝影機 {idx} 無法開啟")
                    
            except Exception as e:
                print(f"❌ 攝影機 {idx} 例外: {str(e)}")
            finally:
                if cap is not None:
                    try:
                        cap.release()
                    except:
                        pass
                # 最小清理時間
                time.sleep(0.01)
        
        print(f"🔍 掃描完成，總共找到 {len(results)} 個可用攝影機")
        return results

    def detailed_scan(self, max_index: int = 6, warmup_frames: int = 3, frame_interval: float = 0.03) -> List[Dict[str, any]]:  # 減少預設值
        """回傳包含每個索引各後端嘗試結果的詳細資訊，支援多幀暖機。"""
        backends = [
            ("DEFAULT", None),  # 優先 DEFAULT
            ("CAP_DSHOW", getattr(cv2, 'CAP_DSHOW', None)),
            ("CAP_MSMF", getattr(cv2, 'CAP_MSMF', None))
        ]
        results: List[Dict[str, any]] = []
        for idx in range(max_index):
            entry = {"index": idx, "opened": False, "backends": [], "frame_read": False, "width": None, "height": None, "warmup_frames": warmup_frames}
            for name, flag in backends:
                try:
                    if flag is not None:
                        cap = cv2.VideoCapture(idx, flag)
                    else:
                        cap = cv2.VideoCapture(idx)
                    opened = cap.isOpened()
                    backend_info = {"backend": name, "opened": opened}
                    if opened:
                        ok = False
                        frame = None
                        # 快速暖機
                        warmup_count = min(3, warmup_frames)  # 最多3影格
                        for _ in range(warmup_count):
                            ok, frame = cap.read()
                            if ok and frame is not None:
                                break
                            time.sleep(0.03)  # 減少等待時間
                        backend_info["frame_ok"] = bool(ok)
                        if ok and frame is not None:
                            h, w = frame.shape[:2]
                            entry.update({"frame_read": True, "width": w, "height": h, "opened": True})
                            # 如果成功就跳出這個攝影機的其他後端測試
                            entry["backends"].append(backend_info)
                            break
                    entry["backends"].append(backend_info)
                except Exception as e:
                    entry["backends"].append({"backend": name, "error": str(e)})
                finally:
                    try:
                        cap.release()
                    except Exception:
                        pass
            results.append(entry)
        return results

    def create_session(self, task_id: int, camera_index: int, preferred_backend: Optional[str] = None) -> CameraSession:
        with self._lock:
            if task_id in self._sessions:
                return self._sessions[task_id]
            # 多後端回退打開
            ordered: List[Tuple[str, Optional[int]]] = [
                ("CAP_DSHOW", getattr(cv2, 'CAP_DSHOW', None)),
                ("CAP_MSMF", getattr(cv2, 'CAP_MSMF', None)),
                ("DEFAULT", None)
            ]
            cached = self.get_cached_backend(camera_index)
            if preferred_backend and preferred_backend in [o[0] for o in ordered]:
                ordered = [o for o in ordered if o[0] == preferred_backend] + [o for o in ordered if o[0] != preferred_backend]
            elif cached:
                ordered = [o for o in ordered if o[0] == cached] + [o for o in ordered if o[0] != cached]
            backends_try = [flag for _, flag in ordered]
            cap = None
            used_backend_name = None
            for flag in backends_try:
                if flag is not None:
                    cap = cv2.VideoCapture(camera_index, flag)
                    used_backend_name = [n for n, f in ordered if f == flag][0]
                else:
                    cap = cv2.VideoCapture(camera_index)
                    used_backend_name = "DEFAULT"
                if cap.isOpened():
                    break
                try:
                    cap.release()
                except Exception:
                    pass
            if not cap or not cap.isOpened():
                raise RuntimeError(f"Camera index {camera_index} 無法開啟 (多後端嘗試失敗)")
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            cap.release()
            session = CameraSession(task_id=task_id, camera_index=camera_index, width=w, height=h, fps=fps, backend_name=used_backend_name)
            session.start()
            self._sessions[task_id] = session
            # 記錄成功 backend
            if used_backend_name:
                self.record_backend(camera_index, used_backend_name)
            return session

    # -------- 進階設備列舉（使用 ffmpeg dshow） --------
    def ffmpeg_list_devices(self) -> List[str]:
        import subprocess, re
        try:
            proc = subprocess.run([
                'ffmpeg', '-f', 'dshow', '-list_devices', 'true', '-i', 'dummy'
            ], capture_output=True, text=True, timeout=8)
            output = proc.stderr.splitlines()
            devices = []
            capture = False
            for line in output:
                if 'DirectShow video devices' in line:
                    capture = True
                    continue
                if capture:
                    m = re.search(r'"(.+?)"', line)
                    if m:
                        devices.append(m.group(1))
                    # 遇到音訊段落停止
                    if 'DirectShow audio devices' in line:
                        break
            return devices
        except Exception:
            return []

    def advanced_scan(self, warmup_frames: int = 8) -> List[Dict[str, any]]:
        """使用 ffmpeg dshow 名稱嘗試 VideoCapture('video=<name>')"""
        names = self.ffmpeg_list_devices()
        results = []
        for name in names:
            entry = {"device_name": name, "opened": False, "frame_ok": False, "width": None, "height": None}
            try:
                cap = cv2.VideoCapture(f"video={name}", getattr(cv2, 'CAP_DSHOW', 0))
                if not cap.isOpened():
                    cap.release()
                    cap = cv2.VideoCapture(f"video={name}")
                if cap.isOpened():
                    entry["opened"] = True
                    for _ in range(warmup_frames):
                        ok, frame = cap.read()
                        if ok and frame is not None:
                            h, w = frame.shape[:2]
                            entry.update({"frame_ok": True, "width": w, "height": h})
                            break
                cap.release()
            except Exception as e:
                entry["error"] = str(e)
            results.append(entry)
        return results

    def get(self, task_id: int) -> Optional[CameraSession]:
        return self._sessions.get(task_id)

    def list(self) -> List[Dict[str, any]]:
        out = []
        with self._lock:
            for s in self._sessions.values():
                out.append({
                    'task_id': s.task_id,
                    'camera_index': s.camera_index,
                    'width': s.width,
                    'height': s.height,
                    'fps': s.fps,
                    'uptime_sec': round(time.time() - s.started_at, 1)
                })
        return out

    def stop(self, task_id: int) -> bool:
        with self._lock:
            s = self._sessions.pop(task_id, None)
        if s:
            s.stop()
            return True
        return False

    def stop_all(self):
        with self._lock:
            ids = list(self._sessions.keys())
        for tid in ids:
            self.stop(tid)


camera_manager = CameraManager()
"""
攝影機服務
管理攝影機的掃描、配置和狀態控制
"""

import cv2
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.core.logger import api_logger

@dataclass
class Camera:
    """攝影機數據類"""
    id: str
    name: str
    status: str  # online/offline
    camera_type: str  # USB/Network
    resolution: str
    fps: int
    group_id: Optional[str] = None
    device_index: Optional[int] = None
    rtsp_url: Optional[str] = None

class CameraService:
    """攝影機管理服務"""
    
    def __init__(self):
        self.cameras: Dict[str, Camera] = {}
        self._initialize_default_cameras()
    
    def _initialize_default_cameras(self):
        """初始化預設攝影機"""
        default_cameras = [
            Camera(
                id="cam_001",
                name="前門攝影機",
                status="online",
                camera_type="USB",
                resolution="1920x1080",
                fps=30,
                device_index=0
            ),
            Camera(
                id="cam_002",
                name="後門攝影機",
                status="offline",
                camera_type="Network",
                resolution="1280x720",
                fps=25,
                rtsp_url="rtsp://admin:password@192.168.1.100/stream1"
            ),
            Camera(
                id="cam_003",
                name="停車場東側",
                status="online",
                camera_type="Network",
                resolution="1920x1080",
                fps=30,
                rtsp_url="rtsp://admin:password@192.168.1.101/stream1"
            ),
            Camera(
                id="cam_004",
                name="停車場西側",
                status="online",
                camera_type="Network",
                resolution="1920x1080",
                fps=30,
                rtsp_url="rtsp://admin:password@192.168.1.102/stream1"
            ),
            Camera(
                id="cam_005",
                name="停車場南側",
                status="online",
                camera_type="Network",
                resolution="1280x720",
                fps=25,
                rtsp_url="rtsp://admin:password@192.168.1.103/stream1"
            ),
            Camera(
                id="cam_006",
                name="大廳攝影機",
                status="online",
                camera_type="USB",
                resolution="1920x1080",
                fps=30,
                device_index=1
            )
        ]
        
        for camera in default_cameras:
            self.cameras[camera.id] = camera
        
        api_logger.info(f"初始化了 {len(default_cameras)} 個預設攝影機")
    
    async def get_cameras(self) -> List[Camera]:
        """獲取所有攝影機"""
        return list(self.cameras.values())
    
    async def get_camera_by_id(self, camera_id: str) -> Optional[Camera]:
        """根據ID獲取攝影機"""
        return self.cameras.get(camera_id)
    
    async def toggle_camera(self, camera_id: str) -> str:
        """切換攝影機狀態"""
        try:
            camera = self.cameras.get(camera_id)
            if not camera:
                raise ValueError(f"攝影機不存在: {camera_id}")
            
            # 切換狀態
            new_status = "offline" if camera.status == "online" else "online"
            camera.status = new_status
            
            api_logger.info(f"攝影機 {camera.name} 狀態已切換為: {new_status}")
            return new_status
            
        except Exception as e:
            api_logger.error(f"切換攝影機狀態失敗: {e}")
            raise
    
    async def scan_cameras(self) -> List[Dict[str, Any]]:
        """掃描可用的攝影機"""
        try:
            discovered_cameras = []
            
            # 掃描USB攝影機
            api_logger.info("開始掃描USB攝影機...")
            usb_cameras = await self._scan_usb_cameras()
            discovered_cameras.extend(usb_cameras)
            
            # 掃描網路攝影機（簡化版，實際應該掃描網段）
            api_logger.info("開始掃描網路攝影機...")
            network_cameras = await self._scan_network_cameras()
            discovered_cameras.extend(network_cameras)
            
            api_logger.info(f"掃描完成，發現 {len(discovered_cameras)} 個攝影機")
            return discovered_cameras
            
        except Exception as e:
            api_logger.error(f"掃描攝影機失敗: {e}")
            raise
    
    async def _scan_usb_cameras(self) -> List[Dict[str, Any]]:
        """掃描USB攝影機"""
        usb_cameras = []
        
        try:
            # 嘗試打開攝影機設備 0-4
            for index in range(5):
                try:
                    cap = cv2.VideoCapture(index)
                    if cap.isOpened():
                        # 獲取攝影機資訊
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = int(cap.get(cv2.CAP_PROP_FPS))
                        
                        camera_info = {
                            "device_index": index,
                            "name": f"USB Camera {index}",
                            "type": "USB",
                            "resolution": f"{width}x{height}",
                            "fps": fps if fps > 0 else 30,
                            "status": "available"
                        }
                        
                        usb_cameras.append(camera_info)
                        api_logger.info(f"發現USB攝影機: {camera_info}")
                        
                    cap.release()
                    
                except Exception as e:
                    # 無法打開此設備，繼續下一個
                    continue
                    
        except Exception as e:
            api_logger.error(f"掃描USB攝影機時發生錯誤: {e}")
        
        return usb_cameras
    
    async def _scan_network_cameras(self) -> List[Dict[str, Any]]:
        """掃描網路攝影機（簡化版）"""
        # 實際應用中應該掃描網段或使用ONVIF發現協議
        # 這裡返回模擬的網路攝影機
        network_cameras = [
            {
                "ip": "192.168.1.100",
                "name": "Network Camera 1",
                "type": "Network",
                "resolution": "1920x1080",
                "fps": 30,
                "rtsp_url": "rtsp://admin:password@192.168.1.100/stream1",
                "status": "available"
            },
            {
                "ip": "192.168.1.101",
                "name": "Network Camera 2",
                "type": "Network",
                "resolution": "1280x720",
                "fps": 25,
                "rtsp_url": "rtsp://admin:password@192.168.1.101/stream1",
                "status": "available"
            }
        ]
        
        return network_cameras
    
    async def add_camera(
        self,
        name: str,
        camera_type: str,
        resolution: str,
        fps: int,
        device_index: Optional[int] = None,
        rtsp_url: Optional[str] = None
    ) -> str:
        """添加新攝影機"""
        try:
            import uuid
            camera_id = f"cam_{uuid.uuid4().hex[:8]}"
            
            camera = Camera(
                id=camera_id,
                name=name,
                status="offline",
                camera_type=camera_type,
                resolution=resolution,
                fps=fps,
                device_index=device_index,
                rtsp_url=rtsp_url
            )
            
            self.cameras[camera_id] = camera
            api_logger.info(f"新增攝影機: {name} (ID: {camera_id})")
            
            return camera_id
            
        except Exception as e:
            api_logger.error(f"添加攝影機失敗: {e}")
            raise
    
    async def remove_camera(self, camera_id: str):
        """移除攝影機"""
        try:
            if camera_id in self.cameras:
                camera_name = self.cameras[camera_id].name
                del self.cameras[camera_id]
                api_logger.info(f"移除攝影機: {camera_name} (ID: {camera_id})")
            else:
                raise ValueError(f"攝影機不存在: {camera_id}")
                
        except Exception as e:
            api_logger.error(f"移除攝影機失敗: {e}")
            raise
    
    async def test_camera_connection(self, camera_id: str) -> bool:
        """測試攝影機連接"""
        try:
            camera = self.cameras.get(camera_id)
            if not camera:
                return False
            
            if camera.camera_type == "USB" and camera.device_index is not None:
                # 測試USB攝影機
                cap = cv2.VideoCapture(camera.device_index)
                is_connected = cap.isOpened()
                cap.release()
                return is_connected
                
            elif camera.camera_type == "Network" and camera.rtsp_url:
                # 測試網路攝影機（簡化版）
                # 實際應該嘗試連接RTSP串流
                return True  # 模擬連接成功
            
            return False
            
        except Exception as e:
            api_logger.error(f"測試攝影機連接失敗: {e}")
            return False
    
    def get_camera_stream_url(self, camera_id: str) -> Optional[str]:
        """獲取攝影機串流URL"""
        camera = self.cameras.get(camera_id)
        if not camera:
            return None
        
        if camera.camera_type == "USB":
            return f"/api/v1/stream/usb/{camera.device_index}"
        elif camera.camera_type == "Network":
            return camera.rtsp_url
        
        return None
