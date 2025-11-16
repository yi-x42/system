"""簡易郵件通知服務，供跌倒警報等功能使用。"""

from __future__ import annotations

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logger import detection_logger


def _build_message(
    subject: str,
    body: str,
    receiver: str,
    frame_path: Optional[str] = None,
) -> MIMEMultipart:
    message = MIMEMultipart()
    message["From"] = settings.smtp_username or ""
    message["To"] = receiver
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    if frame_path and Path(frame_path).exists():
        with open(frame_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(frame_path)}",
            )
            message.attach(part)
    return message


def send_fall_email_alert(
    confidence_score: float,
    receiver_email: str,
    frame_path: Optional[str] = None,
) -> bool:
    """寄送跌倒偵測郵件通知。"""
    if not settings.smtp_username or not settings.smtp_password:
        detection_logger.error("郵件帳號或密碼未設定，無法寄送通知")
        return False
    if not receiver_email:
        detection_logger.warning("未提供收件者，跳過寄送跌倒通知")
        return False

    subject = "FallSafe 警報：偵測到跌倒事件"
    body = (
        "系統偵測到疑似跌倒事件。\n"
        f"模型信心值：{confidence_score:.2f}\n"
        "請立即確認現場狀況。"
    )
    message = _build_message(subject, body, receiver_email, frame_path)

    try:
        if settings.smtp_port == 587:
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.sendmail(settings.smtp_username, receiver_email, message.as_string())
        else:
            with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port) as server:
                server.login(settings.smtp_username, settings.smtp_password)
                server.sendmail(settings.smtp_username, receiver_email, message.as_string())
        detection_logger.info(f"跌倒通知郵件已寄送至 {receiver_email}")
        return True
    except Exception as exc:  # noqa: BLE001
        detection_logger.error(f"寄送跌倒通知失敗: {exc}")
        return False


def send_test_email(receiver_email: str) -> bool:
    """寄送測試郵件，確認 SMTP 設定是否正確。"""
    if not settings.smtp_username or not settings.smtp_password:
        detection_logger.error("郵件帳號或密碼未設定，無法寄送測試郵件")
        return False
    if not receiver_email:
        detection_logger.warning("未提供收件者，跳過寄送測試郵件")
        return False

    subject = "警報通知測試郵件"
    body = (
        "這是一封測試郵件，用來確認郵件通知設定是否可以正常運作。\n"
        "如需停用測試信件，請返回系統的「通知設定」頁調整。"
    )
    message = _build_message(subject, body, receiver_email)

    try:
        if settings.smtp_port == 587:
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.sendmail(settings.smtp_username, receiver_email, message.as_string())
        else:
            with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port) as server:
                server.login(settings.smtp_username, settings.smtp_password)
                server.sendmail(settings.smtp_username, receiver_email, message.as_string())
        detection_logger.info(f"測試郵件已寄送至 {receiver_email}")
        return True
    except Exception as exc:  # noqa: BLE001
        detection_logger.error(f"寄送測試郵件失敗: {exc}")
        return False
