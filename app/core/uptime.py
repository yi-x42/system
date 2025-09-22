from datetime import datetime

SYSTEM_START_TIME = datetime.now()

def get_system_uptime():
    """計算系統運行時間（秒）"""
    return (datetime.now() - SYSTEM_START_TIME).total_seconds()
