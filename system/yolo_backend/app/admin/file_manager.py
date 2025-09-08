"""
YOLOv11 檔案管理模組
處理檔案上傳、瀏覽、刪除等操作
"""

import os
import shutil
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class FileManager:
    """檔案管理器"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.allowed_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'],
            'document': ['.txt', '.pdf', '.doc', '.docx', '.md'],
            'config': ['.json', '.yaml', '.yml', '.ini', '.cfg', '.env'],
            'model': ['.pt', '.pth', '.onnx', '.pb'],
            'log': ['.log']
        }
        
    def list_directory(self, path: str) -> Dict[str, Any]:
        """列出目錄內容"""
        try:
            target_path = self._resolve_path(path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"路徑不存在: {path}")
            
            if not target_path.is_dir():
                raise NotADirectoryError(f"不是目錄: {path}")
            
            items = []
            for item in target_path.iterdir():
                # 跳過隱藏檔案和系統檔案
                if item.name.startswith('.') or item.name.startswith('__'):
                    continue
                
                try:
                    stat = item.stat()
                    file_info = {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else 0,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "path": str(item.relative_to(self.base_path)),
                        "absolute_path": str(item),
                        "extension": item.suffix.lower() if item.is_file() else "",
                        "file_type": self._get_file_type(item) if item.is_file() else "folder"
                    }
                    items.append(file_info)
                except (OSError, PermissionError):
                    # 跳過無法訪問的檔案
                    continue
            
            # 按類型和名稱排序（目錄在前）
            items.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
            
            return {
                "current_path": str(target_path.relative_to(self.base_path)),
                "absolute_path": str(target_path),
                "parent_path": str(target_path.parent.relative_to(self.base_path)) if target_path.parent != target_path else None,
                "items": items,
                "total_items": len(items)
            }
            
        except Exception as e:
            raise Exception(f"列出目錄失敗: {str(e)}")
    
    def upload_file(self, file_content: bytes, filename: str, target_path: str) -> Dict[str, Any]:
        """上傳檔案"""
        try:
            target_dir = self._resolve_path(target_path)
            
            # 確保目標目錄存在
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 檢查檔案名是否安全
            safe_filename = self._sanitize_filename(filename)
            file_path = target_dir / safe_filename
            
            # 如果檔案已存在，生成新的檔案名
            if file_path.exists():
                base_name = file_path.stem
                extension = file_path.suffix
                counter = 1
                while file_path.exists():
                    new_name = f"{base_name}_{counter}{extension}"
                    file_path = target_dir / new_name
                    counter += 1
            
            # 寫入檔案
            file_path.write_bytes(file_content)
            
            # 獲取檔案資訊
            stat = file_path.stat()
            
            return {
                "filename": file_path.name,
                "path": str(file_path.relative_to(self.base_path)),
                "absolute_path": str(file_path),
                "size": stat.st_size,
                "type": self._get_file_type(file_path),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
        except Exception as e:
            raise Exception(f"上傳檔案失敗: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """刪除檔案或目錄"""
        try:
            target_path = self._resolve_path(file_path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"檔案不存在: {file_path}")
            
            # 檢查是否為系統重要檔案
            if self._is_system_file(target_path):
                raise PermissionError("不能刪除系統重要檔案")
            
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
            
            return True
            
        except Exception as e:
            raise Exception(f"刪除檔案失敗: {str(e)}")
    
    def create_directory(self, dir_path: str, dir_name: str) -> Dict[str, Any]:
        """建立目錄"""
        try:
            parent_dir = self._resolve_path(dir_path)
            safe_dir_name = self._sanitize_filename(dir_name)
            new_dir = parent_dir / safe_dir_name
            
            if new_dir.exists():
                raise FileExistsError(f"目錄已存在: {safe_dir_name}")
            
            new_dir.mkdir(parents=True)
            
            return {
                "name": new_dir.name,
                "path": str(new_dir.relative_to(self.base_path)),
                "absolute_path": str(new_dir)
            }
            
        except Exception as e:
            raise Exception(f"建立目錄失敗: {str(e)}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """獲取檔案詳細資訊"""
        try:
            target_path = self._resolve_path(file_path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"檔案不存在: {file_path}")
            
            stat = target_path.stat()
            
            file_info = {
                "name": target_path.name,
                "path": str(target_path.relative_to(self.base_path)),
                "absolute_path": str(target_path),
                "type": "directory" if target_path.is_dir() else "file",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],
                "extension": target_path.suffix.lower() if target_path.is_file() else "",
                "file_type": self._get_file_type(target_path) if target_path.is_file() else "folder"
            }
            
            # 如果是檔案，添加 MIME 類型
            if target_path.is_file():
                mime_type, _ = mimetypes.guess_type(str(target_path))
                file_info["mime_type"] = mime_type or "application/octet-stream"
                
                # 如果是圖片或影片，嘗試獲取元數據
                if file_info["file_type"] in ["image", "video"]:
                    file_info["metadata"] = self._get_media_metadata(target_path)
            
            return file_info
            
        except Exception as e:
            raise Exception(f"獲取檔案資訊失敗: {str(e)}")
    
    def search_files(self, query: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """搜尋檔案"""
        try:
            results = []
            
            for item in self.base_path.rglob("*"):
                if item.is_file() and not item.name.startswith('.'):
                    # 檢查檔案名是否包含查詢字串
                    if query.lower() in item.name.lower():
                        # 檢查檔案類型篩選
                        if file_type is None or self._get_file_type(item) == file_type:
                            try:
                                stat = item.stat()
                                results.append({
                                    "name": item.name,
                                    "path": str(item.relative_to(self.base_path)),
                                    "absolute_path": str(item),
                                    "size": stat.st_size,
                                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                    "file_type": self._get_file_type(item)
                                })
                            except (OSError, PermissionError):
                                continue
            
            # 按相關性排序（完全匹配在前）
            results.sort(key=lambda x: (not x["name"].lower().startswith(query.lower()), x["name"].lower()))
            
            return results
            
        except Exception as e:
            raise Exception(f"搜尋檔案失敗: {str(e)}")
    
    def _resolve_path(self, path: str) -> Path:
        """解析路徑，確保在基礎路徑內"""
        target_path = (self.base_path / path).resolve()
        
        # 確保路徑在基礎路徑內（安全檢查）
        try:
            target_path.relative_to(self.base_path)
        except ValueError:
            raise PermissionError("路徑訪問被拒絕")
        
        return target_path
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理檔案名，移除危險字符"""
        # 移除或替換危險字符
        dangerous_chars = '<>:"/\\|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # 移除前後空格和點
        filename = filename.strip('. ')
        
        # 確保不為空
        if not filename:
            filename = "unnamed_file"
        
        return filename
    
    def _get_file_type(self, file_path: Path) -> str:
        """根據副檔名判斷檔案類型"""
        extension = file_path.suffix.lower()
        
        for file_type, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return file_type
        
        return "other"
    
    def _is_system_file(self, file_path: Path) -> bool:
        """檢查是否為系統重要檔案"""
        system_files = {
            "app", "start.py", "requirements.txt", ".env", "README.md"
        }
        
        return file_path.name in system_files or file_path.name.startswith('.')
    
    def _get_media_metadata(self, file_path: Path) -> Dict[str, Any]:
        """獲取媒體檔案元數據"""
        metadata = {}
        
        try:
            # 這裡可以使用 PIL (Pillow) 獲取圖片資訊
            # 或使用 ffprobe 獲取影片資訊
            # 為了簡化，這裡只返回基本資訊
            metadata["file_size"] = file_path.stat().st_size
            
        except Exception:
            pass
        
        return metadata

# 全域檔案管理器實例
file_manager = FileManager()
