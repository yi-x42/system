import { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Progress } from "./ui/progress";
import { Switch } from "./ui/switch";
import { Alert, AlertDescription } from "./ui/alert";
import { useVideoUpload, VideoUploadResponse, useYoloModelList, YoloModelFileInfo, useToggleModelStatus, useActiveModels, useCameras } from "../hooks/react-query-hooks";
import {
  Brain,
  Upload,
  Play,
  Download,
  Settings,
  Eye,
  Activity,
  Target,
  Zap,
  FileVideo,
  Camera,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

export function 
DetectionAnalysis() {
  console.log("DetectionAnalysis 組件開始渲染");

  // ===== 狀態變數定義 =====
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadResult, setUploadResult] = useState<VideoUploadResponse | null>(null);
  
  // ===== Hooks 定義 =====
  console.log("開始初始化 hooks");
  
  // 使用影片上傳 mutation
  const videoUploadMutation = useVideoUpload();
  console.log("videoUploadMutation 初始化成功");

  // 取得 YOLO 模型清單
  const { data: yoloModelList, isLoading: isModelLoading, isError: isModelError, refetch: refetchModels } = useYoloModelList();
  console.log("yoloModelList hook 初始化成功", { yoloModelList, isModelLoading, isModelError });
  
  // 取得已啟用的模型清單（供選擇器使用）
  const { data: activeModels, refetch: refetchActiveModels } = useActiveModels();
  console.log("activeModels hook 初始化成功", { activeModels });
  
  // 取得攝影機列表
  const { data: cameras, isLoading: isCamerasLoading, isError: isCamerasError } = useCameras();
  console.log("cameras hook 初始化成功", { cameras, isCamerasLoading, isCamerasError });
  
  // 模型狀態切換 mutation
  const toggleModelMutation = useToggleModelStatus();
  console.log("toggleModelMutation 初始化成功");

  // ===== 事件處理函式 =====
  // 拖曳上傳相關 handler
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  // 檔案 input 變更 handler
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  // 影片上傳 handler
  const handleVideoUpload = () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append('video', selectedFile);
    videoUploadMutation.mutate(formData, {
      onSuccess: (data) => {
        setUploadResult(data);
      },
      onError: (error: any) => {
        alert(`影片上傳失敗: ${error.message}`);
      },
    });
  };

  // ===== 輔助函式 =====
  // 模型狀態處理函式
  const getModelStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "default";
      case "inactive":
        return "secondary";
      case "loading":
        return "outline";
      default:
        return "outline";
    }
  };

  const getModelStatusText = (status: string) => {
    switch (status) {
      case "active":
        return "已啟用";
      case "inactive":
        return "未啟用";
      case "loading":
        return "載入中";
      default:
        return "未知";
    }
  };

  // 切換模型啟用狀態
  const toggleModelStatus = (modelId: string) => {
    toggleModelMutation.mutate(modelId, {
      onSuccess: () => {
        // 重新獲取模型清單以更新狀態
        refetchModels();
        // 同時更新已啟用模型清單
        refetchActiveModels();
      },
      onError: (error: any) => {
        alert(`切換模型狀態失敗: ${error.message}`);
      },
    });
  };

  // 模擬分析結果
  const analysisResults = [
    {
      id: 1,
      camera: "攝影機-01",
      videoName: "停車場監控_20240115.mp4",
      timestamp: "2024-01-15 14:30:25",
      detections: [
        { class: "person", confidence: 0.95, count: 3 },
        { class: "car", confidence: 0.88, count: 2 },
      ],
      thumbnail: "/api/placeholder/150/100",
      duration: "未知",
      fileSize: "未知",
      resolution: "未知",
    },
    {
      id: 2,
      camera: "攝影機-05",
      videoName: "大門入口_20240115_1428.mp4",
      timestamp: "2024-01-15 14:28:12",
      detections: [
        { class: "person", confidence: 0.92, count: 1 },
        { class: "bicycle", confidence: 0.87, count: 1 },
      ],
      thumbnail: "/api/placeholder/150/100",
      duration: "未知",
      fileSize: "未知",
      resolution: "未知",
    },
  ];


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
                    className={`border-2 border-dashed rounded-lg p-8 text-center mt-2 transition-colors cursor-pointer ${
                      isDragging 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border hover:border-primary/50'
                    }`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('video-file-input')?.click()}
                  >
                    <Upload className={`h-8 w-8 mx-auto mb-2 ${
                      isDragging ? 'text-primary' : 'text-muted-foreground'
                    }`} />
                    <p className="text-sm text-muted-foreground">
                      {selectedFile ? selectedFile.name : '拖拽影片檔案到此處或點擊上傳'}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      支援格式: MP4, AVI, MOV (最大 500MB)
                    </p>
                    {selectedFile && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        檔案大小: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                      </div>
                    )}
                    <input
                      id="video-file-input"
                      type="file"
                      accept="video/mp4,video/avi,video/mov,video/quicktime"
                      onChange={handleFileInputChange}
                      className="hidden"
                    />
                  </div>
                </div>

                {/* 上傳成功訊息 */}
                {uploadResult && (
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      影片上傳成功！檔案名稱: {uploadResult.original_name}
                      <br />
                      時長: {Math.round(uploadResult.video_info.duration)} 秒 | 
                      解析度: {uploadResult.video_info.resolution} | 
                      FPS: {uploadResult.video_info.fps.toFixed(1)}
                    </AlertDescription>
                  </Alert>
                )}

                {/* 上傳失敗訊息 */}
                {videoUploadMutation.isError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      上傳失敗: {videoUploadMutation.error?.message}
                    </AlertDescription>
                  </Alert>
                )}

                <div>
                  <Label htmlFor="detection-model">偵測模型</Label>
                  <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger>
                      <SelectValue placeholder="選擇偵測模型" />
                    </SelectTrigger>
                    <SelectContent>
                      {activeModels && activeModels.length > 0 ? (
                        activeModels.map((model) => (
                          <SelectItem key={model.name} value={model.name}>
                            {model.name}
                          </SelectItem>
                        ))
                      ) : (
                        <SelectItem value="" disabled>
                          請先在模型管理中啟用模型
                        </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="confidence-threshold">信心度閾值</Label>
                    <span className="text-sm text-muted-foreground">0.8</span>
                  </div>
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.1"
                    defaultValue="0.8"
                    className="w-full"
                  />
                </div>

                {/* 上傳進度 */}
                {videoUploadMutation.isPending && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>上傳進度</span>
                      <span>上傳中...</span>
                    </div>
                    <Progress value={undefined} className="animate-pulse" />
                  </div>
                )}

                {analysisProgress > 0 && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>分析進度</span>
                      <span>{analysisProgress}%</span>
                    </div>
                    <Progress value={analysisProgress} />
                  </div>
                )}

                <div className="flex gap-2">
                  {selectedFile && !uploadResult && (
                    <Button 
                      onClick={handleVideoUpload}
                      disabled={videoUploadMutation.isPending}
                      className="flex-1"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      {videoUploadMutation.isPending ? '上傳中...' : '上傳影片'}
                    </Button>
                  )}
                  
                  {uploadResult && (
                    <Button 
                      className="flex-1" 
                      disabled={!selectedModel}
                      onClick={() => {
                        // 這裡可以添加開始分析的邏輯
                        console.log('開始分析影片:', uploadResult.file_path);
                        alert(`開始分析影片: ${uploadResult.original_name}`);
                      }}
                    >
                      <Play className="h-4 w-4 mr-2" />
                      開始分析
                    </Button>
                  )}
                  
                  {!selectedFile && !uploadResult && (
                    <Button className="w-full" disabled>
                      <Play className="h-4 w-4 mr-2" />
                      請先上傳影片
                    </Button>
                  )}
                </div>
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
                        <SelectValue placeholder={isCamerasLoading ? "載入攝影機列表中..." : "選擇要分析的攝影機"} />
                      </SelectTrigger>
                      <SelectContent>
                        {isCamerasLoading ? (
                          <SelectItem value="" disabled>載入中...</SelectItem>
                        ) : isCamerasError ? (
                          <SelectItem value="" disabled>載入攝影機列表失敗</SelectItem>
                        ) : cameras && cameras.length > 0 ? (
                          cameras.map((camera) => (
                            <SelectItem key={camera.id} value={camera.id.toString()}>
                              {camera.name} ({camera.status})
                            </SelectItem>
                          ))
                        ) : (
                          <SelectItem value="" disabled>
                            沒有可用的攝影機設備
                          </SelectItem>
                        )}
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
                            <SelectItem key={model.name} value={model.name}>
                              {model.name}
                            </SelectItem>
                          ))
                        ) : (
                          <SelectItem value="" disabled>
                            請先在模型管理中啟用模型
                          </SelectItem>
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
            <div className="grid gap-4">
              {isModelLoading && <div className="text-muted-foreground">載入中...</div>}
              {isModelError && <div className="text-destructive">模型清單載入失敗</div>}
              {yoloModelList && yoloModelList.length === 0 && <div className="text-muted-foreground">目前沒有模型檔案</div>}
              {yoloModelList && yoloModelList.map((model) => (
                <Card key={model.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Brain className="h-5 w-5" />
                        <div>
                          <CardTitle>{model.name}</CardTitle>
                        </div>
                      </div>
                      <Badge variant={getModelStatusColor(model.status)}>
                        {getModelStatusText(model.status)}
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
                          {model.status === "active" && (
                            <Zap className="h-4 w-4 text-green-500" />
                          )}
                          <span className="text-sm">{getModelStatusText(model.status)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end gap-2 mt-6">
                      {model.status !== "loading" && (
                        <Button 
                          size="sm" 
                          variant={model.status === "active" ? "outline" : "default"}
                          onClick={() => toggleModelStatus(model.id)}
                          disabled={toggleModelMutation.isPending}
                        >
                          {model.status === "active" ? "停用" : "啟用"}
                        </Button>
                      )}
                      {model.status === "loading" && (
                        <Button size="sm" disabled>
                          載入中...
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            {/* 模型上傳卡片以下內容... */}
          </div>

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