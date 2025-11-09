"""
PySide6 即時預覽 GUI 啟動管理器

負責從後端觸發 `app/gui/realtime_detection_gui.py`，並記錄
各任務對應的 GUI 子行程，避免重複啟動。
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from app.core.logger import detection_logger


class PreviewProcessRecord:
    """簡易容器，記錄 GUI 行程資訊與啟動指令。"""

    def __init__(
        self,
        process: subprocess.Popen,
        command: list[str],
        log_path: Optional[Path] = None,
    ) -> None:
        self.process = process
        self.command = command
        self.started_at = time.time()
        self.log_path = log_path

    @property
    def pid(self) -> int:
        return self.process.pid

    def is_running(self) -> bool:
        return self.process.poll() is None


class RealtimePreviewGuiManager:
    """管理 PySide6 即時預覽 GUI 的子行程。"""

    def __init__(self) -> None:
        self._processes: Dict[str, PreviewProcessRecord] = {}
        self._lock = threading.Lock()

    def _script_path(self) -> Path:
        script_path = Path(__file__).resolve().parents[1] / "gui" / "realtime_detection_gui.py"
        if not script_path.exists():
            raise FileNotFoundError(f"找不到 GUI 腳本：{script_path}")
        return script_path

    def _logs_dir(self) -> Path:
        logs_dir = Path("logs") / "gui_preview"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir

    @staticmethod
    def _read_log_tail(log_path: Path, max_bytes: int = 2048) -> str:
        if not log_path.exists() or log_path.stat().st_size == 0:
            return ""
        with log_path.open("rb") as fp:
            fp.seek(0, os.SEEK_END)
            size = fp.tell()
            fp.seek(max(0, size - max_bytes), os.SEEK_SET)
            data = fp.read().decode("utf-8", errors="ignore")
        return data.strip()

    def _cleanup_if_needed(self, task_id: str) -> None:
        record = self._processes.get(task_id)
        if record and not record.is_running():
            detection_logger.info(
                f"移除已結束的 GUI 子行程: task_id={task_id} pid={record.pid}"
            )
            self._processes.pop(task_id, None)

    def launch_preview(
        self,
        task_id: str,
        source: str,
        model_path: Optional[str] = None,
        *,
        window_name: Optional[str] = None,
        confidence: Optional[float] = None,
        imgsz: Optional[int] = None,
        device: Optional[str] = None,
    ) -> Dict[str, object]:
        """
        啟動（或返回既有）GUI 預覽視窗。
        """
        with self._lock:
            self._cleanup_if_needed(task_id)
            existing = self._processes.get(task_id)
            if existing and existing.is_running():
                detection_logger.info(
                    f"GUI 已在執行，直接返回: task_id={task_id} pid={existing.pid}"
                )
                return {
                    "pid": existing.pid,
                    "already_running": True,
                    "command": existing.command,
                }

        script_path = self._script_path()
        command: list[str] = [sys.executable, str(script_path), "--source", str(source)]

        if model_path:
            command += ["--model", str(model_path)]
        if imgsz:
            command += ["--imgsz", str(int(imgsz))]
        if confidence is not None:
            command += ["--conf", f"{float(confidence):.4f}"]
        if device:
            command += ["--device", str(device)]
        if window_name:
            command += ["--window-name", window_name]

        detection_logger.info(f"啟動 GUI 子行程: {' '.join(command)}")

        log_path = self._logs_dir() / f"task_{task_id}.log"
        log_handle = log_path.open("wb")

        creationflags = 0
        startupinfo = None
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(  # noqa: S603
            command,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            startupinfo=startupinfo,
            close_fds=os.name != "nt",
        )
        log_handle.close()

        # 確認是否順利啟動；若立即結束，回報錯誤並檢視日誌
        time.sleep(0.5)
        if process.poll() is not None:
            log_excerpt = self._read_log_tail(log_path)
            detection_logger.error(
                f"GUI 子行程啟動失敗 (exit={process.returncode})，詳見 {log_path}"
            )
            raise RuntimeError(
                f"GUI 子行程啟動失敗，請查看 {log_path}。\n"
                f"最近訊息：{log_excerpt or '無'}"
            )

        record = PreviewProcessRecord(process, command, log_path=log_path)
        with self._lock:
            self._processes[task_id] = record

        return {
            "pid": record.pid,
            "already_running": False,
            "command": record.command,
            "log_path": str(log_path),
        }

    def stop_preview(self, task_id: str) -> bool:
        """結束指定任務的 GUI 行程。"""
        with self._lock:
            record = self._processes.pop(task_id, None)

        if not record:
            return False

        process = record.process
        if process.poll() is None:
            detection_logger.info(
                f"結束 GUI 子行程: task_id={task_id} pid={process.pid}"
            )
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        return True


realtime_gui_manager = RealtimePreviewGuiManager()
