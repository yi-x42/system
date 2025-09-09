import { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Progress } from "./ui/progress";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Alert, AlertDescription } from "./ui/alert";
import { useYoloModelList, useVideoUpload, VideoUploadResponse, useToggleModelStatus, useActiveModels } from "../hooks/react-query-hooks";

export function DetectionAnalysisSimple() {
  console.log("DetectionAnalysisSimple 組件開始渲染");
  
  const [activeTab, setActiveTab] = useState("tasks");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  
  // React Query hooks
  const { data: models, isLoading: modelsLoading, error: modelsError } = useYoloModelList();
  const { data: activeModels } = useActiveModels();
  const uploadVideoMutation = useVideoUpload();
  const toggleModelMutation = useToggleModelStatus();
  
  console.log("模型數據:", models, "載入中:", modelsLoading, "錯誤:", modelsError);

  // 事件處理函式
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('video/')) {
      setSelectedFile(file);
    }
  }, []);

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('video/')) {
      setSelectedFile(file);
    }
  }, []);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;
    
    try {
      const formData = new FormData();
      formData.append('video_file', selectedFile);
      formData.append('save_path', 'D:\\project\\system\\uploads\\videos');
      
      const result = await uploadVideoMutation.mutateAsync(formData);
      console.log('上傳成功:', result);
      setSelectedFile(null);
    } catch (error) {
      console.error('上傳失敗:', error);
    }
  }, [selectedFile, uploadVideoMutation]);

  const handleToggleModel = useCallback(async (modelId: string) => {
    try {
      await toggleModelMutation.mutateAsync(modelId);
    } catch (error) {
      console.error('切換模型狀態失敗:', error);
    }
  }, [toggleModelMutation]);

  return (
    <div className="container mx-auto p-4 space-y-6">
      <h1 className="text-3xl font-bold mb-6 text-center">任務配置</h1>
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="tasks">任務管理</TabsTrigger>
          <TabsTrigger value="models">模型管理</TabsTrigger>
        </TabsList>
        
        <TabsContent value="tasks" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>影片上傳</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                className={`border-2 border-dashed p-8 text-center rounded-lg transition-colors ${
                  isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                <p className="text-gray-600 mb-4">拖放影片檔案到此處，或點選下方按鈕選擇檔案</p>
                <Input
                  type="file"
                  accept="video/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="video-upload"
                />
                <Label htmlFor="video-upload" className="cursor-pointer">
                  <Button type="button">選擇影片檔案</Button>
                </Label>
              </div>
              
              {selectedFile && (
                <div className="space-y-2">
                  <p>已選擇檔案: {selectedFile.name}</p>
                  <Button onClick={handleUpload} disabled={uploadVideoMutation.isPending}>
                    {uploadVideoMutation.isPending ? '上傳中...' : '開始上傳'}
                  </Button>
                </div>
              )}
              
              {uploadVideoMutation.isError && (
                <Alert>
                  <AlertDescription>
                    上傳失敗: {uploadVideoMutation.error?.message}
                  </AlertDescription>
                </Alert>
              )}
              
              {uploadVideoMutation.isSuccess && (
                <Alert>
                  <AlertDescription>
                    影片上傳成功！
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="models" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>測試模型管理</CardTitle>
            </CardHeader>
            <CardContent>
              <p>這是簡化版的模型管理頁面</p>
              {modelsLoading && <p>載入模型中...</p>}
              {modelsError && <p>載入錯誤: {modelsError.message}</p>}
              {models && (
                <div>
                  <p>找到 {models.length} 個模型</p>
                  <p>啟用中的模型: {activeModels?.length || 0} 個</p>
                  {models.map((model, index) => {
                    const isActive = activeModels?.some(activeModel => activeModel.id === model.id) || false;
                    return (
                      <div key={index} className="p-4 border rounded mt-2 flex justify-between items-center">
                        <div>
                          <p><strong>模型:</strong> {model.name}</p>
                          <p><strong>大小:</strong> {model.fileSize}</p>
                          <p><strong>參數:</strong> {model.parameterCount}</p>
                          <p><strong>狀態:</strong> {isActive ? '已啟用' : '未啟用'}</p>
                        </div>
                        <Button
                          onClick={() => handleToggleModel(model.id)}
                          disabled={toggleModelMutation.isPending}
                          variant={isActive ? "destructive" : "default"}
                        >
                          {isActive ? '停用' : '啟用'}
                        </Button>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
