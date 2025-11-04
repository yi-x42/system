#!/usr/bin/env python3
"""
測試 Live Person Camera API 的簡單腳本
"""

import json
from fastapi.testclient import TestClient
from main import app

def test_live_person_camera_api():
    """測試 Live Person Camera API"""
    client = TestClient(app)

    # 先獲取可用攝影機列表
    print("獲取可用攝影機列表...")
    cameras_response = client.get("/api/v1/frontend/cameras")
    print(f"攝影機列表狀態碼: {cameras_response.status_code}")
    if cameras_response.status_code == 200:
        cameras = cameras_response.json()
        print(f"可用攝影機: {cameras}")
        if cameras:
            camera_id = cameras[0].get('id') or cameras[0].get('camera_id')
            print(f"使用攝影機ID: {camera_id}")
        else:
            print("沒有可用攝影機，使用模擬ID")
            camera_id = "camera_0"
    else:
        print("無法獲取攝影機列表，使用模擬ID")
        camera_id = "camera_0"

    # 測試啟動 API
    print("\n測試啟動 Live Person Camera API...")
    request_data = {
        "task_name": "測試即時人體檢測",
        "camera_id": camera_id,
        "model_path": "yolov8n.pt",
        "confidence_threshold": 0.35,
        "imgsz": 640,
        "trace_length": 30,
        "heatmap_radius": 40,
        "heatmap_opacity": 0.5,
        "blur_kernel": 25,
        "corner_enabled": True,
        "blur_enabled": False,
        "trace_enabled": False,
        "heatmap_enabled": False,
        "line_enabled": True,
        "zone_enabled": True,
        "csv_path": "",
        "csv_append": False
    }

    response = client.post(
        "/api/v1/frontend/analysis/start-live-person-camera",
        json=request_data
    )

    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")

    if response.status_code == 200:
        task_id = response.json().get("task_id")
        print(f"任務ID: {task_id}")

        # 測試停止 API
        print("\n測試停止 Live Person Camera API...")
        stop_response = client.delete(f"/api/v1/frontend/analysis/live-person-camera/{task_id}")
        print(f"停止狀態碼: {stop_response.status_code}")
        print(f"停止回應: {stop_response.json()}")
    else:
        print("啟動API測試失敗")

if __name__ == "__main__":
    test_live_person_camera_api()
