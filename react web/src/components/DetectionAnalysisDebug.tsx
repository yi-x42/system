import { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Progress } from "./ui/progress";
import { Switch } from "./ui/switch";
import { Alert, AlertDescription } from "./ui/alert";
import { useYoloModelList, useVideoUpload, useToggleModelStatus, useActiveModels, VideoUploadResponse } from "../hooks/react-query-hooks";
import {
  Brain,
  Upload,
  Play,
  CheckCircle,
  AlertCircle,
  FileVideo,
  Camera,
  Settings,
  Eye,
  Activity,
  Target,
  Zap,
  Download,
} from "lucide-react";

export function DetectionAnalysisFixed() {
  console.log("DetectionAnalysisFixed 開始渲染");
  
  try {
    const [test, setTest] = useState("測試");
    console.log("基本 useState 正常");
    
    // 添加原始組件中的狀態變數
    const [selectedModel, setSelectedModel] = useState<string>("");
    const [analysisProgress, setAnalysisProgress] = useState(0);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [uploadResult, setUploadResult] = useState<VideoUploadResponse | null>(null);
    console.log("所有狀態變數初始化成功");
    
    // 測試添加所有 React Query hooks
    const { data: models, isLoading, error } = useYoloModelList();
    console.log("useYoloModelList hook 測試:", { models, isLoading, error });
    
    const { data: activeModels } = useActiveModels();
    console.log("useActiveModels hook 測試:", { activeModels });
    
    const videoUploadMutation = useVideoUpload();
    console.log("useVideoUpload hook 測試:", videoUploadMutation);
    
    const toggleModelMutation = useToggleModelStatus();
    console.log("useToggleModelStatus hook 測試:", toggleModelMutation);
    
    // 添加事件處理函式
    const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(true);
    }, []);
    
    const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
    }, []);
    
    const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        setSelectedFile(e.dataTransfer.files[0]);
      }
    }, []);
    
    const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        setSelectedFile(e.target.files[0]);
      }
    }, []);
    
    const handleVideoUpload = useCallback(() => {
      if (!selectedFile) return;
      
      const formData = new FormData();
      formData.append('video_file', selectedFile);
      formData.append('save_path', 'D:\\project\\system\\uploads\\videos');
      
      videoUploadMutation.mutate(formData, {
        onSuccess: (data) => {
          setUploadResult(data);
          console.log('影片上傳成功:', data);
        },
        onError: (error: any) => {
          console.error('影片上傳失敗:', error);
          alert(`影片上傳失敗: ${error.message}`);
        },
      });
    }, [selectedFile, videoUploadMutation]);
    
    const handleToggleModel = useCallback(async (modelId: string) => {
      try {
        await toggleModelMutation.mutateAsync(modelId);
        console.log(`模型 ${modelId} 狀態切換成功`);
      } catch (error) {
        console.error('切換模型狀態失敗:', error);
      }
    }, [toggleModelMutation]);
    
    console.log("所有事件處理函式初始化成功");
    
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1>檢測分析</h1>
        </div>

        <Tabs defaultValue="video-analysis">
          <TabsList>
            <TabsTrigger value="video-analysis">影片分析</TabsTrigger>
            <TabsTrigger value="yolo-models">YOLO 模型管理</TabsTrigger>
          </TabsList>

          <TabsContent value="video-analysis">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileVideo className="h-5 w-5" />
                    影片上傳分析
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div
                    className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                      isDragging
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-300"
                    }`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <p className="text-gray-600 mb-4">
                      拖放影片檔案到此處，或點選下方按鈕選擇檔案
                    </p>
                    <Input
                      type="file"
                      accept="video/*"
                      onChange={handleFileInputChange}
                      className="hidden"
                      id="video-upload"
                    />
                    <Label htmlFor="video-upload" className="cursor-pointer">
                      <Button type="button">選擇影片檔案</Button>
                    </Label>
                  </div>
                  
                  {selectedFile && (
                    <div className="space-y-2">
                      <p className="text-sm text-gray-600">
                        已選擇檔案: {selectedFile.name}
                      </p>
                      <Button onClick={handleVideoUpload} disabled={videoUploadMutation.isPending}>
                        {videoUploadMutation.isPending ? "上傳中..." : "開始上傳"}
                      </Button>
                    </div>
                  )}
                  
                  {videoUploadMutation.isError && (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        上傳失敗: {videoUploadMutation.error?.message}
                      </AlertDescription>
                    </Alert>
                  )}
                  
                  {uploadResult && (
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>
                        影片上傳成功！檔案路徑: {uploadResult.file_path}
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="yolo-models">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  YOLO 模型管理
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading && <p>載入模型中...</p>}
                {error && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>載入錯誤: {error.message}</AlertDescription>
                  </Alert>
                )}
                
                {models && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <p className="text-sm text-gray-600">
                        找到 {models.length} 個模型，啟用中: {activeModels?.length || 0} 個
                      </p>
                    </div>
                    
                    <div className="grid gap-4">
                      {models.map((model) => {
                        const isActive = activeModels?.some(activeModel => activeModel.id === model.id) || false;
                        return (
                          <Card key={model.id} className="p-4">
                            <div className="flex justify-between items-start">
                              <div className="space-y-2">
                                <div className="flex items-center gap-2">
                                  <h3 className="font-semibold">{model.name}</h3>
                                  <Badge variant={isActive ? "default" : "secondary"}>
                                    {isActive ? "已啟用" : "未啟用"}
                                  </Badge>
                                </div>
                                <div className="text-sm text-gray-600 space-y-1">
                                  <p><strong>模型類型:</strong> {model.modelType}</p>
                                  <p><strong>參數數量:</strong> {model.parameterCount}</p>
                                  <p><strong>檔案大小:</strong> {model.fileSize}</p>
                                </div>
                              </div>
                              <Button
                                onClick={() => handleToggleModel(model.id)}
                                disabled={toggleModelMutation.isPending}
                                variant={isActive ? "destructive" : "default"}
                                size="sm"
                              >
                                {isActive ? "停用" : "啟用"}
                              </Button>
                            </div>
                          </Card>
                        );
                      })}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    );
  } catch (error) {
    console.error("DetectionAnalysisDebug 渲染錯誤:", error);
    return <div>渲染錯誤: {error?.toString()}</div>;
  }
}
