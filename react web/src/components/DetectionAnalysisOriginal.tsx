import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Progress } from "./ui/progress";
import { Switch } from "./ui/switch";
import { 
  useYoloModelList, 
  useToggleModelStatus, 
  useActiveModels, 
  useVideoUpload, 
  VideoUploadResponse,
  useCreateAnalysisTask,
  AnalysisTaskRequest,
  CreateAnalysisTaskResponse
} from "../hooks/react-query-hooks";
import {
  Brain,
  Upload,
  Play,
  Eye,
  Activity,
  Target,
  Zap,
  FileVideo,
  Camera,
} from "lucide-react";

export function DetectionAnalysisOriginal() {
  console.log("DetectionAnalysisOriginal 開始渲染");

  // 狀態管理
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [analysisProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadResult, setUploadResult] = useState<VideoUploadResponse | null>(null);
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.8);

  // 真實數據獲取
  const { data: yoloModels, isLoading: modelsLoading, error: modelsError, refetch: refetchModels } = useYoloModelList();
  const { data: activeModels, refetch: refetchActiveModels } = useActiveModels();
  const toggleModelMutation = useToggleModelStatus();
  const uploadVideoMutation = useVideoUpload();
  const createTaskMutation = useCreateAnalysisTask();

  console.log("YOLO 模型數據:", yoloModels);
  console.log("啟用的模型:", activeModels);

  // 模擬分析結果數據
  const analysisResults = [
    {
      id: "1",
      videoName: "測試影片.mp4",
      camera: "攝影機01",
      timestamp: "2024-01-15 14:30:25",
      duration: "2:15",
      fileSize: "15.2MB", 
      resolution: "1920x1080",
      detections: [
        { class: "person", count: 3, confidence: 0.92 },
        { class: "car", count: 1, confidence: 0.87 }
      ]
    }
  ];

  // 輔助函式
  const getModelStatusColor = (isActive: boolean) => {
    return isActive ? "default" : "outline";
  };

  const getModelStatusText = (isActive: boolean) => {
    return isActive ? "已啟用" : "未啟用";
  };

  const handleToggleModelStatus = async (modelId: string) => {
    console.log("切換模型狀態:", modelId);
    try {
      await toggleModelMutation.mutateAsync(modelId);
      // 重新獲取數據
      refetchModels();
      refetchActiveModels();
      console.log(`模型 ${modelId} 狀態切換成功`);
    } catch (error) {
      console.error('切換模型狀態失敗:', error);
    }
  };

  // 檢查模型是否已啟用
  const isModelActive = (modelId: string) => {
    return activeModels?.some(activeModel => activeModel.id === modelId) || false;
  };

  // 文件處理函數
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('video/')) {
      setSelectedFile(file);
    } else {
      alert('請選擇影片檔案');
    }
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('video/')) {
        setSelectedFile(file);
      } else {
        alert('請選擇影片檔案');
      }
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      alert('請選擇影片檔案');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      const result = await uploadVideoMutation.mutateAsync(formData);
      setUploadResult(result);
      console.log('上傳成功:', result);
    } catch (error) {
      console.error('上傳失敗:', error);
      alert('上傳失敗，請稍後重試');
    }
  };

  const handleStartAnalysis = async () => {
    if (!uploadResult) {
      alert('請先上傳影片檔案');
      return;
    }

    if (!selectedModel) {
      alert('請選擇要使用的模型');
      return;
    }

    try {
      // 準備分析任務資料
      const taskData: AnalysisTaskRequest = {
        task_type: 'video_file',
        source_info: {
          file_path: uploadResult.file_path,
          original_filename: uploadResult.original_name,
          confidence_threshold: confidenceThreshold,
        },
        source_width: parseInt(uploadResult.video_info.resolution.split('x')[0]) || 1920,
        source_height: parseInt(uploadResult.video_info.resolution.split('x')[1]) || 1080,
        source_fps: uploadResult.video_info.fps || 25.0,
      };

      console.log('創建分析任務:', taskData);
      
      const result = await createTaskMutation.mutateAsync(taskData);
      console.log('分析任務創建成功:', result);
      
      alert(`分析任務已創建！任務 ID: ${result.task_id}\n狀態: ${result.task.status}`);
      
    } catch (error) {
      console.error('創建分析任務失敗:', error);
      alert('創建分析任務失敗，請稍後重試');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1>檢測分析</h1>
        <div className="flex gap-2">
          
          
        </div>
      </div>

      <Tabs defaultValue="video-analysis">
        <TabsList>
          <TabsTrigger value="video-analysis">影片分析</TabsTrigger>
          <TabsTrigger value="camera-analysis">攝影機配置</TabsTrigger>
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
                <div>
                  <Label htmlFor="video-file">選擇影片檔案</Label>
                  <div 
                    className={`border-2 border-dashed rounded-lg p-8 text-center mt-2 transition-colors ${
                      isDragging ? 'border-primary bg-primary/10' : 'border-border'
                    }`}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                  >
                    <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    {selectedFile ? (
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-foreground">
                          已選擇: {selectedFile.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          檔案大小: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                        </p>
                        {uploadResult && (
                          <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700">
                            上傳成功! 檔案已保存至: {uploadResult.file_path}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div>
                        <p className="text-sm text-muted-foreground">
                          拖拽影片檔案到此處或點擊上傳
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          支援格式: MP4, AVI, MOV (最大 500MB)
                        </p>
                      </div>
                    )}
                    <input
                      type="file"
                      id="video-file"
                      accept="video/*"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    <Button 
                      variant="outline" 
                      className="mt-4"
                      onClick={() => document.getElementById('video-file')?.click()}
                    >
                      選擇檔案
                    </Button>
                  </div>
                </div>

                <div>
                  <Label htmlFor="detection-model">偵測模型</Label>
                  <Select 
                    value={selectedModel} 
                    onValueChange={(value) => {
                      if (value !== "no-models") {
                        setSelectedModel(value);
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="選擇偵測模型" />
                    </SelectTrigger>
                    <SelectContent>
                      {activeModels && activeModels.length > 0 ? (
                        activeModels.map((model) => (
                          <SelectItem key={model.id} value={model.id}>
                            {model.name}
                          </SelectItem>
                        ))
                      ) : (
                        <SelectItem value="no-models" disabled>無可用模型</SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="confidence-threshold">信心度閾值</Label>
                    <span className="text-sm text-muted-foreground">{confidenceThreshold.toFixed(1)}</span>
                  </div>
                  <input
                    id="confidence-threshold"
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.1"
                    value={confidenceThreshold}
                    onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                {analysisProgress > 0 && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>分析進度</span>
                      <span>{analysisProgress}%</span>
                    </div>
                    <Progress value={analysisProgress} />
                  </div>
                )}

                {selectedFile && !uploadResult ? (
                  <Button 
                    onClick={handleUpload}
                    disabled={uploadVideoMutation.isPending}
                    className="w-full"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    {uploadVideoMutation.isPending ? '上傳中...' : '上傳影片'}
                  </Button>
                ) : uploadResult ? (
                  <Button 
                    className="w-full" 
                    disabled={!selectedModel || createTaskMutation.isPending}
                    onClick={handleStartAnalysis}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    {createTaskMutation.isPending ? '創建任務中...' : '開始分析'}
                  </Button>
                ) : (
                  <Button 
                    className="w-full" 
                    disabled={true}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    請先選擇影片檔案
                  </Button>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>分析結果</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analysisResults.map((result) => (
                    <div key={result.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <p className="font-medium">{result.videoName}</p>
                          <p className="text-sm text-muted-foreground">{result.camera}</p>
                          <p className="text-xs text-muted-foreground">{result.timestamp}</p>
                          <div className="flex gap-2 mt-1">
                            <span className="text-xs text-muted-foreground">時長: {result.duration}</span>
                            <span className="text-xs text-muted-foreground">大小: {result.fileSize}</span>
                            <span className="text-xs text-muted-foreground">解析度: {result.resolution}</span>
                          </div>
                        </div>
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </div>
                      
                      <div className="space-y-2">
                        {result.detections.map((detection, index) => (
                          <div key={index} className="flex justify-between items-center">
                            <span className="text-sm">{detection.class}</span>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">
                                數量: {detection.count}
                              </Badge>
                              <Badge variant="secondary">
                                {(detection.confidence * 100).toFixed(1)}%
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="camera-analysis">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Camera className="h-5 w-5" />
                攝影機配置
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="camera-select">選擇攝影機</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="選擇要分析的攝影機" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="cam_001">大門入口</SelectItem>
                        <SelectItem value="cam_002">停車場</SelectItem>
                        <SelectItem value="cam_004">走廊A</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="analysis-model">分析模型</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="選擇分析模型" />
                      </SelectTrigger>
                      <SelectContent>
                        {activeModels && activeModels.length > 0 ? (
                          activeModels.map((model) => (
                            <SelectItem key={model.id} value={model.id}>
                              {model.name}
                            </SelectItem>
                          ))
                        ) : (
                          <SelectItem value="no-models" disabled>無可用模型</SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-3">
                    
                    
                    <div className="flex items-center justify-between">
                      <Label htmlFor="auto-alert">自動警報</Label>
                      <Switch id="auto-alert" />
                    </div>
                    
                    
                  </div>

                  <Button className="w-full">
                    <Activity className="h-4 w-4 mr-2" />
                    開始即時分析
                  </Button>
                </div>

                <div className="space-y-4">
                  <div className="aspect-video bg-black rounded-lg flex items-center justify-center">
                    <div className="text-center text-white">
                      <Target className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>即時分析預覽</p>
                      <p className="text-sm opacity-75">選擇攝影機開始分析</p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-medium">即時偵測統計</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">人員數量</span>
                        <p className="text-xl">0</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">車輛數量</span>
                        <p className="text-xl">0</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">平均信心度</span>
                        <p className="text-xl">0%</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">處理速度</span>
                        <p className="text-xl">0 FPS</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="yolo-models">
          <div className="space-y-6">
            {modelsLoading && (
              <div className="text-center py-8">
                <p>載入模型中...</p>
              </div>
            )}
            
            {modelsError && (
              <div className="text-center py-8 text-red-500">
                <p>載入錯誤: {modelsError.message}</p>
                <Button onClick={() => refetchModels()} className="mt-2">
                  重新載入
                </Button>
              </div>
            )}
            
            {yoloModels && (
              <div className="grid gap-4">
                {yoloModels.map((model) => {
                  const isActive = isModelActive(model.id);
                  return (
                    <Card key={model.id}>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Brain className="h-5 w-5" />
                            <div>
                              <CardTitle>{model.name}</CardTitle>
                            </div>
                          </div>
                          <Badge variant={getModelStatusColor(isActive)}>
                            {getModelStatusText(isActive)}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid gap-4 md:grid-cols-4">
                          <div>
                            <p className="text-sm text-muted-foreground">模型類型</p>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant="outline">{model.modelType}</Badge>
                            </div>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">參數量</p>
                            <p className="text-xl">{model.parameterCount}</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">文件大小</p>
                            <p className="text-xl">{model.fileSize}</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">啟用狀態</p>
                            <div className="flex items-center gap-2 mt-1">
                              {isActive && (
                                <Zap className="h-4 w-4 text-green-500" />
                              )}
                              <span className="text-sm">{getModelStatusText(isActive)}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex justify-end gap-2 mt-6">
                          <Button 
                            size="sm" 
                            variant={isActive ? "outline" : "default"}
                            onClick={() => handleToggleModelStatus(model.id)}
                            disabled={toggleModelMutation.isPending}
                          >
                            {toggleModelMutation.isPending ? "處理中..." : (isActive ? "停用" : "啟用")}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}

            {/* 模型上傳卡片 */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Upload className="h-5 w-5" />
                  <div>
                    <CardTitle>模型上傳</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      上傳自定義 YOLO 模型文件
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  

                  <div>
                    <Label>模型文件</Label>
                    <div className="border-2 border-dashed border-border rounded-lg p-6 text-center mt-2 hover:border-primary/50 transition-colors">
                      <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                      <p className="text-sm text-muted-foreground mb-2">
                        拖拽文件到此處或點擊選擇
                      </p>
                      <p className="text-xs text-muted-foreground mb-3">
                        支援格式: .pt, .onnx, .engine (最大 500MB)
                      </p>
                      <Button variant="outline" size="sm">
                        選擇文件
                      </Button>
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    
                    <div>
                      <Label htmlFor="model-type">模型類型</Label>
                      <Select>
                        <SelectTrigger className="mt-2">
                          <SelectValue placeholder="選擇模型類型" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="detection">物體偵測</SelectItem>
                          <SelectItem value="classification">分類</SelectItem>
                          <SelectItem value="segmentation">語義分割</SelectItem>
                          <SelectItem value="pose">姿態估計</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  

                  

                  <div className="flex justify-end gap-2">
                    <Button variant="outline">取消</Button>
                    <Button>
                      <Upload className="h-4 w-4 mr-2" />
                      上傳模型
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
