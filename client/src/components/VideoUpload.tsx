import React, { useState, useRef, DragEvent } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Upload, AlertCircle, CheckCircle, X } from 'lucide-react';
import { Alert, AlertDescription } from './ui/alert';
import { useVideoUpload } from '../hooks/react-query-hooks';

// 簡單的 cn 函數實現
function cn(...classes: (string | undefined | null | boolean)[]) {
  return classes.filter(Boolean).join(' ');
}

interface VideoFile {
  file: File;
  id: string;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
  uploadedInfo?: {
    source_id: number;
    file_path: string;
    video_info: {
      duration: number;
      fps: number;
      resolution: string;
      frame_count: number;
    };
  };
}

interface VideoUploadProps {
  onUploadSuccess?: (uploadInfo: any) => void;
  onUploadError?: (error: string) => void;
  className?: string;
}

export function VideoUpload({ onUploadSuccess, onUploadError, className }: VideoUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [files, setFiles] = useState<VideoFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 支援的影片格式
  const SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'];
  const MAX_SIZE = 500 * 1024 * 1024; // 500MB

  // 驗證檔案
  const validateFile = (file: File): string | null => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED_FORMATS.includes(extension)) {
      return `不支援的檔案格式。支援的格式: ${SUPPORTED_FORMATS.join(', ')}`;
    }
    if (file.size > MAX_SIZE) {
      return `檔案太大。最大支援 500MB，您的檔案為 ${(file.size / 1024 / 1024).toFixed(1)}MB`;
    }
    return null;
  };

  // 處理檔案拖放
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  // 處理檔案選擇
  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    handleFiles(selectedFiles);
    
    // 重置 input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 處理檔案陣列
  const handleFiles = (fileList: File[]) => {
    const newFiles: VideoFile[] = fileList.map(file => {
      const error = validateFile(file);
      return {
        file,
        id: `${Date.now()}_${Math.random()}`,
        progress: 0,
        status: error ? 'error' : 'pending',
        error: error || undefined
      };
    });

    setFiles(prev => [...prev, ...newFiles]);
    
    // 開始上傳有效檔案
    newFiles.forEach(videoFile => {
      if (videoFile.status === 'pending') {
        uploadFile(videoFile);
      }
    });
  };

  // 上傳檔案
  const uploadFile = async (videoFile: VideoFile) => {
    try {
      // 更新狀態為上傳中
      setFiles(prev => prev.map(f => 
        f.id === videoFile.id ? { ...f, status: 'uploading', progress: 0 } : f
      ));

      const formData = new FormData();
      formData.append('file', videoFile.file);

      // 建立 XMLHttpRequest 以追蹤進度
      const xhr = new XMLHttpRequest();
      
      // 追蹤上傳進度
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setFiles(prev => prev.map(f => 
            f.id === videoFile.id ? { ...f, progress } : f
          ));
        }
      };

      // 處理完成
      xhr.onload = () => {
        if (xhr.status === 200) {
          try {
            const response = JSON.parse(xhr.responseText);
            setFiles(prev => prev.map(f => 
              f.id === videoFile.id ? { 
                ...f, 
                status: 'success', 
                progress: 100,
                uploadedInfo: response
              } : f
            ));
            
            onUploadSuccess?.(response);
          } catch (e) {
            throw new Error('回應格式錯誤');
          }
        } else {
          throw new Error(`HTTP ${xhr.status}: ${xhr.statusText}`);
        }
      };

      // 處理錯誤
      xhr.onerror = () => {
        throw new Error('網路錯誤');
      };

      // 開始上傳
      xhr.open('POST', 'http://localhost:8001/api/v1/frontend/data-sources/upload/video');
      xhr.send(formData);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知錯誤';
      setFiles(prev => prev.map(f => 
        f.id === videoFile.id ? { 
          ...f, 
          status: 'error', 
          error: errorMessage 
        } : f
      ));
      onUploadError?.(errorMessage);
    }
  };

  // 移除檔案
  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  // 重試上傳
  const retryUpload = (fileId: string) => {
    const file = files.find(f => f.id === fileId);
    if (file) {
      uploadFile(file);
    }
  };

  // 格式化檔案大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化影片時長
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* 上傳區域 */}
      <Card>
        <CardContent className="p-6">
          <div
            className={cn(
              "border-2 border-dashed border-border rounded-lg p-8 text-center transition-all",
              isDragOver && "border-primary bg-primary/5",
              "hover:border-primary/50 cursor-pointer"
            )}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={handleFileSelect}
          >
            <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              拖拽影片檔案到此處或點擊上傳
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              支援格式: MP4, AVI, MOV (最大 500MB)
            </p>
            <Button className="mt-4">
              選擇檔案
            </Button>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            multiple
            className="hidden"
            onChange={handleFileInputChange}
          />
        </CardContent>
      </Card>

      {/* 檔案列表 */}
      {files.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h3 className="font-semibold mb-4">上傳檔案</h3>
            <div className="space-y-4">
              {files.map((videoFile) => (
                <div key={videoFile.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{videoFile.file.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatFileSize(videoFile.file.size)}
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {videoFile.status === 'success' && (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      )}
                      {videoFile.status === 'error' && (
                        <AlertCircle className="h-5 w-5 text-red-500" />
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(videoFile.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {/* 進度條 */}
                  {videoFile.status === 'uploading' && (
                    <div className="mb-2">
                      <Progress value={videoFile.progress} className="h-2" />
                      <p className="text-xs text-muted-foreground mt-1">
                        上傳中... {videoFile.progress}%
                      </p>
                    </div>
                  )}

                  {/* 錯誤訊息 */}
                  {videoFile.status === 'error' && videoFile.error && (
                    <Alert className="mb-2">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        {videoFile.error}
                        <Button
                          variant="outline"
                          size="sm"
                          className="ml-2"
                          onClick={() => retryUpload(videoFile.id)}
                        >
                          重試
                        </Button>
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* 成功資訊 */}
                  {videoFile.status === 'success' && videoFile.uploadedInfo && (
                    <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
                      <p className="text-sm text-green-800 dark:text-green-200 font-medium mb-2">
                        上傳成功！
                      </p>
                      <div className="text-xs text-green-700 dark:text-green-300 space-y-1">
                        <p>時長: {formatDuration(videoFile.uploadedInfo.video_info.duration)}</p>
                        <p>解析度: {videoFile.uploadedInfo.video_info.resolution}</p>
                        <p>FPS: {videoFile.uploadedInfo.video_info.fps}</p>
                        <p>總幀數: {videoFile.uploadedInfo.video_info.frame_count.toLocaleString()}</p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
