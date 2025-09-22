"""
攝影機狀態監控服務
負責定期檢測攝影機連線狀態並更新資料庫
"""

import asyncio
import aiohttp
import cv2
import socket
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import subprocess
import platform
import logging

from app.models.database import DataSource
from app.services.new_database_service import DatabaseService

# 設置日誌
logger = logging.getLogger(__name__)

class CameraConnectionStatus:
    """攝影機連線狀態類別"""
    ONLINE = "active"
    OFFLINE = "inactive"
    ERROR = "error"

class CameraStatusMonitor:
    """攝影機狀態監控服務"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.check_interval = 30  # 檢查間隔（秒）
        self.timeout = 10  # 連線超時時間
        self.running = False
        
    async def ping_host(self, host: str) -> bool:
        """
        Ping 主機檢測網路連通性
        """
        try:
            # Windows 和 Linux 的 ping 命令不同
            system = platform.system().lower()
            if system == "windows":
                cmd = ["ping", "-n", "1", "-w", str(self.timeout * 1000), host]
            else:
                cmd = ["ping", "-c", "1", "-W", str(self.timeout), host]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=self.timeout + 5
            )
            
            return process.returncode == 0
            
        except Exception as e:
            logger.warning(f"Ping {host} 失敗: {e}")
            return False
    
    async def test_rtsp_stream(self, rtsp_url: str) -> bool:
        """
        測試 RTSP 串流連線
        """
        try:
            # 使用 OpenCV 測試 RTSP 連線
            cap = cv2.VideoCapture(rtsp_url)
            
            # 設置讀取超時
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # 嘗試讀取一幀
            ret, frame = cap.read()
            cap.release()
            
            return ret and frame is not None
            
        except Exception as e:
            logger.warning(f"RTSP 測試失敗 {rtsp_url}: {e}")
            return False
    
    async def test_http_camera(self, http_url: str) -> bool:
        """
        測試 HTTP 攝影機連線
        """
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(http_url) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.warning(f"HTTP 攝影機測試失敗 {http_url}: {e}")
            return False
    
    async def test_usb_camera(self, device_id: int) -> bool:
        """
        測試 USB 攝影機連線
        """
        try:
            cap = cv2.VideoCapture(device_id)
            
            if not cap.isOpened():
                return False
            
            # 嘗試讀取一幀
            ret, frame = cap.read()
            cap.release()
            
            return ret and frame is not None
            
        except Exception as e:
            logger.warning(f"USB 攝影機測試失敗 {device_id}: {e}")
            return False
    
    async def check_camera_status(self, camera: DataSource) -> str:
        """
        檢查單個攝影機的狀態
        
        Args:
            camera: DataSource 實例
            
        Returns:
            str: 攝影機狀態 (active/inactive/error)
        """
        try:
            config = camera.config or {}
            
            if camera.source_type == "camera":
                # 網路攝影機
                if "rtsp_url" in config:
                    rtsp_url = config["rtsp_url"]
                    
                    # 先 ping 主機
                    parsed_url = urlparse(rtsp_url)
                    host = parsed_url.hostname
                    
                    if host:
                        ping_ok = await self.ping_host(host)
                        if not ping_ok:
                            logger.info(f"攝影機 {camera.name} 主機 {host} 無法連通")
                            return CameraConnectionStatus.OFFLINE
                    
                    # 測試 RTSP 串流
                    rtsp_ok = await self.test_rtsp_stream(rtsp_url)
                    if rtsp_ok:
                        return CameraConnectionStatus.ONLINE
                    else:
                        return CameraConnectionStatus.OFFLINE
                        
                elif "http_url" in config:
                    # HTTP 攝影機
                    http_ok = await self.test_http_camera(config["http_url"])
                    return CameraConnectionStatus.ONLINE if http_ok else CameraConnectionStatus.OFFLINE
                    
                elif "device_id" in config or "device_index" in config:
                    # USB 攝影機 - 支援 device_id 和 device_index 兩種配置
                    device_id = config.get("device_id") or config.get("device_index", 0)
                    usb_ok = await self.test_usb_camera(device_id)
                    return CameraConnectionStatus.ONLINE if usb_ok else CameraConnectionStatus.OFFLINE
                else:
                    # 攝影機配置不完整
                    logger.warning(f"攝影機 {camera.name} 配置不完整：{config}")
                    return CameraConnectionStatus.ERROR
                    
            elif camera.source_type == "video_file":
                # 影片檔案，檢查檔案是否存在
                import os
                file_path = config.get("file_path", "")
                if file_path and os.path.exists(file_path):
                    return CameraConnectionStatus.ONLINE
                else:
                    logger.warning(f"影片檔案 {camera.name} 路徑不存在: {file_path}")
                    return CameraConnectionStatus.OFFLINE
            
            # 未知類型
            logger.error(f"攝影機 {camera.name} 類型未知: {camera.source_type}")
            return CameraConnectionStatus.ERROR
            
        except Exception as e:
            logger.error(f"檢查攝影機 {camera.name} 狀態時發生錯誤: {e}")
            return CameraConnectionStatus.ERROR
    
    async def update_camera_status_in_db(self, camera_id: int, new_status: str):
        """
        更新資料庫中的攝影機狀態
        """
        try:
            from app.core.database import get_db
            
            async for db in get_db():
                # 更新攝影機狀態
                await self.db_service.update_data_source_status(
                    db, camera_id, new_status
                )
                
                logger.info(f"攝影機 {camera_id} 狀態已更新為: {new_status}")
                break
                
        except Exception as e:
            logger.error(f"更新攝影機 {camera_id} 狀態失敗: {e}")
    
    async def check_all_cameras(self) -> Dict[int, str]:
        """
        檢查所有攝影機狀態
        
        Returns:
            Dict[int, str]: 攝影機 ID 對應狀態的字典
        """
        try:
            from app.core.database import get_db
            
            results = {}
            
            async for db in get_db():
                # 獲取所有攝影機
                cameras = await self.db_service.get_data_sources(
                    db, source_type="camera"
                )
                
                logger.info(f"開始檢查 {len(cameras)} 個攝影機的狀態")
                
                # 並發檢查所有攝影機
                tasks = []
                for camera in cameras:
                    task = self.check_camera_status(camera)
                    tasks.append((camera.id, camera.name, task))
                
                # 等待所有檢查完成
                for camera_id, camera_name, task in tasks:
                    try:
                        new_status = await task
                        results[camera_id] = new_status
                        
                        # 獲取當前攝影機資料以比較狀態
                        current_camera = await self.db_service.get_data_source(db, camera_id)
                        if current_camera and current_camera.status != new_status:
                            logger.info(f"攝影機 {camera_name} 狀態變化: {current_camera.status} -> {new_status}")
                            # 更新資料庫狀態
                            await self.update_camera_status_in_db(camera_id, new_status)
                        
                    except Exception as e:
                        logger.error(f"檢查攝影機 {camera_name} 時發生錯誤: {e}")
                        results[camera_id] = CameraConnectionStatus.ERROR
                
                break
            
            return results
            
        except Exception as e:
            logger.error(f"檢查所有攝影機狀態失敗: {e}")
            return {}
    
    async def start_monitoring(self):
        """
        開始監控服務
        """
        if self.running:
            logger.warning("監控服務已經在運行中")
            return
            
        self.running = True
        logger.info(f"攝影機狀態監控服務啟動，檢查間隔: {self.check_interval} 秒")
        
        try:
            while self.running:
                start_time = time.time()
                
                # 檢查所有攝影機狀態
                results = await self.check_all_cameras()
                
                elapsed_time = time.time() - start_time
                logger.info(f"攝影機狀態檢查完成，耗時: {elapsed_time:.2f} 秒")
                
                # 等待下次檢查
                await asyncio.sleep(self.check_interval)
                
        except Exception as e:
            logger.error(f"監控服務發生錯誤: {e}")
        finally:
            self.running = False
            logger.info("攝影機狀態監控服務已停止")
    
    def stop_monitoring(self):
        """
        停止監控服務
        """
        self.running = False
        logger.info("正在停止攝影機狀態監控服務...")
    
    async def get_camera_status_immediately(self, camera_id: int) -> Optional[str]:
        """
        立即檢查指定攝影機的狀態（用於API調用）
        
        Args:
            camera_id: 攝影機 ID
            
        Returns:
            str: 攝影機狀態或 None（如果攝影機不存在）
        """
        try:
            logger.info(f"開始即時檢查攝影機 {camera_id}")
            from app.core.database import get_db
            
            async for db in get_db():
                logger.info(f"獲取攝影機 {camera_id} 的資料庫記錄")
                camera = await self.db_service.get_data_source(db, camera_id)
                if not camera:
                    logger.warning(f"攝影機 {camera_id} 在資料庫中不存在")
                    return None
                
                logger.info(f"攝影機 {camera_id} 記錄: type={type(camera)}, name={camera.name}")
                status = await self.check_camera_status(camera)
                logger.info(f"攝影機 {camera_id} 檢查結果: {status}")
                
                # 如果狀態有變化，更新資料庫
                if camera.status != status:
                    await self.update_camera_status_in_db(camera_id, status)
                
                return status
            
        except Exception as e:
            import traceback
            logger.error(f"立即檢查攝影機 {camera_id} 狀態失敗: {e}")
            logger.error(f"錯誤堆疊: {traceback.format_exc()}")
            return CameraConnectionStatus.ERROR


# 全域監控服務實例
camera_monitor = None

def get_camera_monitor(db_service: DatabaseService) -> CameraStatusMonitor:
    """
    獲取攝影機監控服務實例（單例模式）
    """
    global camera_monitor
    if camera_monitor is None:
        camera_monitor = CameraStatusMonitor(db_service)
    return camera_monitor