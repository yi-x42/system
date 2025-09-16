
# 跨環境部署指南

## 自動路徑檢測功能
系統現在支援自動檢測模型目錄，無需手動修改路徑。

## 支援的部署結構
1. **標準結構**: `/project/system/yolo_backend/模型/`
2. **GitHub 結構**: `/GitHub/system/system/yolo_backend/模型/`
3. **自訂結構**: 任何包含 `yolo_backend/模型/` 的目錄

## 部署步驟
1. 將整個專案複製到目標電腦
2. 保持 `yolo_backend/模型/` 目錄結構
3. 執行 `python start.py`

## 環境變數設定（可選）
如果自動檢測失敗，可設定環境變數：
```bash
# Windows
set YOLO_MODELS_DIR=C:\path\to\yolo_backend\模型

# Linux/Mac
export YOLO_MODELS_DIR=/path/to/yolo_backend/模型
```

## 驗證部署
執行以下命令驗證模型路徑：
```bash
python -c "import sys; sys.path.append('yolo_backend'); from app.api.v1.frontend import find_models_directory; print('模型目錄:', find_models_directory())"
```
