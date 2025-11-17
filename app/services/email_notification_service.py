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


def _send_email(
    *,
    subject: str,
    body_lines: list[str],
    receiver_email: str,
    frame_path: Optional[str] = None,
) -> bool:
    if not settings.smtp_username or not settings.smtp_password:
        detection_logger.error("郵件帳號或密碼未設定，無法寄送通知")
        return False
    if not receiver_email:
        detection_logger.warning("未提供收件者，跳過寄送郵件")
        return False

    body = "\n".join(body_lines)
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
        detection_logger.info(f"通知郵件已寄送至 {receiver_email}")
        return True
    except Exception as exc:  # noqa: BLE001
        detection_logger.error(f"寄送郵件失敗: {exc}")
        return False


def send_fall_email_alert(
    confidence_score: float,
    receiver_email: str,
    frame_path: Optional[str] = None,
) -> bool:
    """寄送跌倒偵測郵件通知。"""
    subject = "即時警報通知：偵測到跌倒事件"
    body_lines = [
        "系統偵測到疑似跌倒事件。",
        f"模型信心值：{confidence_score:.2f}",
        "請立即確認現場狀況。",
    ]
    return _send_email(
        subject=subject,
        body_lines=body_lines,
        receiver_email=receiver_email,
        frame_path=frame_path,
    )


def send_test_email(receiver_email: str) -> bool:
    """寄送測試郵件，確認 SMTP 設定是否正確。"""
    subject = "警報通知測試郵件"
    body_lines = [
        "這是一封測試郵件，用來確認郵件通知設定是否可以正常運作。",
        "如需停用測試信件，請返回系統的「通知設定」頁調整。",
    ]
    return _send_email(subject=subject, body_lines=body_lines, receiver_email=receiver_email)


def send_alert_rule_email(
    *,
    rule_name: str,
    rule_type: str,
    severity: str,
    receiver_email: str,
    description: str,
    body_lines: list[str],
    frame_path: Optional[str] = None,
) -> bool:
    """一般警報規則郵件通知。"""
    subject = f"即時警報通知：{rule_name or rule_type}"
    full_body = [
        f"警報類型：{rule_type}",
        f"嚴重程度：{severity}",
        description,
        "",
        *body_lines,
    ]
    return _send_email(
        subject=subject,
        body_lines=full_body,
        receiver_email=receiver_email,
        frame_path=frame_path,
    )


__all__ = [
    "send_fall_email_alert",
    "send_test_email",
    "send_alert_rule_email",
]
