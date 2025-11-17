"""
PySide6 即時偵測子行程管理器

負責啟動 `app/gui/realtime_detection_gui.py`，並透過控制通道
顯示/隱藏視窗或關閉偵測。
"""

from __future__ import annotations

import json
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from app.core.logger import detection_logger


@dataclass
class PreviewProcessRecord:
    process: subprocess.Popen
    command: list[str]
    log_path: Path
    control_port: Optional[int] = None
    control_token: Optional[str] = None
    start_hidden: bool = True

    @property
    def pid(self) -> int:
        return self.process.pid

    def is_running(self) -> bool:
        return self.process.poll() is None


class RealtimeDetectionProcessManager:
    """管理 PySide6 偵測程式（隱藏 + GUI 預覽）。"""

    def __init__(self) -> None:
        self._processes: Dict[str, PreviewProcessRecord] = {}
        self._lock = threading.Lock()

    def _script_path(self) -> Path:
        script_path = (
            Path(__file__).resolve().parents[1] / "gui" / "realtime_detection_gui.py"
        )
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

    @staticmethod
    def _reserve_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def _build_command(
        self,
        *,
        task_id: str,
        parent_pid: Optional[int],
        source: str,
        model_path: Optional[str],
        window_name: Optional[str],
        confidence: Optional[float],
        imgsz: Optional[int],
        device: Optional[str],
        start_hidden: bool,
        control_port: Optional[int],
        control_token: Optional[str],
        fall_alert_enabled: bool,
        alert_rules_path: Optional[str],
    ) -> list[str]:
        command: list[str] = [
            sys.executable,
            str(self._script_path()),
            "--task-id",
            str(task_id),
            "--source",
            str(source),
        ]

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
        if start_hidden:
            command.append("--start-hidden")
        if control_port:
            command += [
                "--control-host",
                "127.0.0.1",
                "--control-port",
                str(control_port),
            ]
        if control_token:
            command += ["--control-token", control_token]
        if fall_alert_enabled:
            command.append("--enable-fall-alert")
        if alert_rules_path:
            command += ["--alert-rules", str(alert_rules_path)]
        if parent_pid:
            command += ["--parent-pid", str(parent_pid)]
        return command

    def _spawn_process(
        self,
        task_id: str,
        command: list[str],
    ) -> PreviewProcessRecord:
        log_path = self._logs_dir() / f"task_{task_id}.log"
        log_handle = log_path.open("wb")
        creationflags = 0
        startupinfo = None
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        detection_logger.info(f"啟動偵測子行程: {' '.join(command)}")
        process = subprocess.Popen(  # noqa: S603
            command,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            startupinfo=startupinfo,
            close_fds=os.name != "nt",
        )
        log_handle.close()

        time.sleep(0.5)
        if process.poll() is not None:
            log_excerpt = self._read_log_tail(log_path)
            detection_logger.error(
                f"偵測子行程啟動失敗 (exit={process.returncode})，詳見 {log_path}"
            )
            raise RuntimeError(
                f"偵測子行程啟動失敗，請查看 {log_path}。\n"
                f"最近訊息：{log_excerpt or '無'}"
            )

        return PreviewProcessRecord(
            process=process,
            command=command,
            log_path=log_path,
        )

    def _cleanup_if_needed(self, task_id: str) -> None:
        record = self._processes.get(task_id)
        if record and not record.is_running():
            detection_logger.info(
                f"移除已結束的偵測子行程: task_id={task_id} pid={record.pid}"
            )
            self._processes.pop(task_id, None)

    def start_detection(
        self,
        task_id: str,
        *,
        source: str,
        model_path: Optional[str] = None,
        window_name: Optional[str] = None,
        confidence: Optional[float] = None,
        imgsz: Optional[int] = None,
        device: Optional[str] = None,
        start_hidden: bool = True,
        fall_alert_enabled: bool = False,
        alert_rules_path: Optional[str] = None,
    ) -> Dict[str, object]:
        """啟動（或返回已存在的）偵測子行程。"""
        with self._lock:
            self._cleanup_if_needed(task_id)
            existing = self._processes.get(task_id)
            if existing and existing.is_running():
                return {
                    "pid": existing.pid,
                    "already_running": True,
                    "log_path": str(existing.log_path),
                }

            control_port = self._reserve_port()
            control_token = secrets.token_hex(16)
            command = self._build_command(
                task_id=task_id,
                parent_pid=os.getpid(),
                source=source,
                model_path=model_path,
                window_name=window_name,
                confidence=confidence,
                imgsz=imgsz,
                device=device,
                start_hidden=start_hidden,
                control_port=control_port,
                control_token=control_token,
                fall_alert_enabled=fall_alert_enabled,
                alert_rules_path=alert_rules_path,
            )
            record = self._spawn_process(task_id, command)
            record.control_port = control_port
            record.control_token = control_token
            record.start_hidden = start_hidden
            self._processes[task_id] = record

        return {
            "pid": record.pid,
            "already_running": False,
            "log_path": str(record.log_path),
            "control_port": control_port,
            "control_token": control_token,
        }

    def _send_control_command(self, record: PreviewProcessRecord, action: str) -> None:
        if not record.control_port:
            raise RuntimeError("此子行程未啟用控制通道，無法切換顯示狀態")

        payload = json.dumps(
            {"action": action, "token": record.control_token}
        ).encode("utf-8")

        with socket.create_connection(("127.0.0.1", record.control_port), timeout=3) as conn:
            conn.sendall(payload)
            try:
                conn.recv(1024)
            except socket.timeout:
                pass

    def show_window(self, task_id: str) -> Dict[str, object]:
        with self._lock:
            record = self._processes.get(task_id)

        if not record or not record.is_running():
            raise RuntimeError("找不到對應的偵測子行程，請重新啟動任務")

        self._send_control_command(record, "show")
        return {
            "pid": record.pid,
            "log_path": str(record.log_path),
        }

    def stop_process(self, task_id: str) -> bool:
        with self._lock:
            record = self._processes.pop(task_id, None)

        if not record:
            return False

        if record.is_running():
            try:
                self._send_control_command(record, "shutdown")
                record.process.wait(timeout=5)
            except Exception:
                detection_logger.warning(
                    f"透過控制通道結束子行程失敗，嘗試強制終止 task_id={task_id}"
                )

        if record.process.poll() is None:
            record.process.terminate()
            try:
                record.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                record.process.kill()
        return True


realtime_gui_manager = RealtimeDetectionProcessManager()
