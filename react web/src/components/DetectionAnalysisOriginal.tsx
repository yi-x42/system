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
  useCreateAndExecuteAnalysisTask,
  AnalysisTaskRequest,
  CreateAnalysisTaskResponse,
  useVideoList,
  VideoFileInfo,
  useDeleteVideo,
  useCameras,
  useStartRealtimeAnalysis,
  RealtimeAnalysisRequest
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
  Plus,
  Trash2,
} from "lucide-react";

export function DetectionAnalysisOriginal() {
  console.log("DetectionAnalysisOriginal 開始渲染");

  // 狀態管理
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [analysisProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadResult, setUploadResult] = useState<VideoUploadResponse | null>(null);
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.5);
  const [selectedVideo, setSelectedVideo] = useState<VideoFileInfo | null>(null);
  
  // 即時分析相關狀態
  const [selectedCamera, setSelectedCamera] = useState<string>("");
  const [realtimeModel, setRealtimeModel] = useState<string>("");
  const [isRealtimeAnalysisRunning, setIsRealtimeAnalysisRunning] = useState(false);

  // 真實數據獲取
  const { data: yoloModels, isLoading: modelsLoading, error: modelsError, refetch: refetchModels } = useYoloModelList();
  const { data: activeModels, refetch: refetchActiveModels } = useActiveModels();
  const { data: videoListData, isLoading: videoListLoading, refetch: refetchVideoList } = useVideoList();
  const { data: cameras, isLoading: isCamerasLoading, isError: isCamerasError } = useCameras();
  const toggleModelMutation = useToggleModelStatus();
  const uploadVideoMutation = useVideoUpload();
  const createTaskMutation = useCreateAnalysisTask();
  const createAndExecuteTaskMutation = useCreateAndExecuteAnalysisTask();
  const deleteVideoMutation = useDeleteVideo();
  const startRealtimeAnalysisMutation = useStartRealtimeAnalysis();

  console.log("YOLO 模型數據:", yoloModels);
  console.log("啟用的模型:", activeModels);
  console.log("攝影機數據:", cameras);

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
      
      // 重新載入影片列表
      refetchVideoList();
    } catch (error) {
      console.error('上傳失敗:', error);
      alert('上傳失敗，請稍後重試');
    }
  };

  const handleStartAnalysis = async (video?: VideoFileInfo) => {
    // 優先使用傳入的video參數，其次使用selectedVideo，最後使用uploadResult
    const targetVideo = video || selectedVideo;
    
    if (!targetVideo && !uploadResult) {
      alert('請先選擇或上傳影片檔案');
      return;
    }

    if (!selectedModel) {
      alert('請選擇要使用的模型');
      return;
    }

    try {
      let taskData: AnalysisTaskRequest;
      
      if (targetVideo) {
        // 從影片列表中選擇的影片
        const [width, height] = targetVideo.resolution 
          ? targetVideo.resolution.split('x').map(Number)
          : [1920, 1080];

        taskData = {
          task_type: 'video_file',
          source_info: {
            file_path: targetVideo.file_path,
            original_filename: targetVideo.name,
            confidence_threshold: confidenceThreshold,
          },
          source_width: width || 1920,
          source_height: height || 1080,
          source_fps: 30.0, // 預設值，因為VideoFileInfo沒有fps欄位
        };
      } else if (uploadResult) {
        // 新上傳的影片
        const [width, height] = uploadResult.video_info.resolution 
          ? uploadResult.video_info.resolution.split('x').map(Number)
          : [1920, 1080];

        taskData = {
          task_type: 'video_file',
          source_info: {
            file_path: uploadResult.file_path,
            original_filename: uploadResult.original_name,
            confidence_threshold: confidenceThreshold,
          },
          source_width: width || 1920,
          source_height: height || 1080,
          source_fps: uploadResult.video_info.fps || 30.0,
        };
      } else {
        throw new Error('無效的影片資料');
      }

      console.log('創建並執行分析任務:', taskData);
      
      // 使用新的 create-and-execute API
      const result = await createAndExecuteTaskMutation.mutateAsync(taskData);
      console.log('分析任務已創建並開始執行:', result);
      
      alert(`分析任務已開始執行！\n任務 ID: ${result.task_id}\n狀態: ${result.status}\n${result.message}`);
      
      // 重新載入影片列表以更新狀態
      refetchVideoList();
      
    } catch (error) {
      console.error('創建並執行分析任務失敗:', error);
      alert('創建並執行分析任務失敗，請稍後重試');
    }
  };

  // 刪除影片的處理函式
  const handleDeleteVideo = async (video: VideoFileInfo) => {
    // 確認刪除
    const confirmDelete = window.confirm(`確定要刪除影片「${video.name}」嗎？此操作無法復原。`);
    if (!confirmDelete) {
      return;
    }

    try {
      console.log('刪除影片:', video.id);
      
      const result = await deleteVideoMutation.mutateAsync(video.id);
      console.log('影片刪除成功:', result);
      
      alert(`影片「${video.name}」已成功刪除`);
      
      // 重新載入影片列表
      refetchVideoList();
      
    } catch (error) {
      console.error('刪除影片失敗:', error);
      alert('刪除影片失敗，請稍後重試');
    }
  };

  // 開始即時分析的處理函數
  const handleStartRealtimeAnalysis = async () => {
    if (!selectedCamera) {
      alert('請選擇攝影機');
      return;
    }

    if (!realtimeModel) {
      alert('請選擇YOLO模型');
      return;
    }

    try {
      setIsRealtimeAnalysisRunning(true);
      
      const requestData: RealtimeAnalysisRequest = {
        task_name: `即時分析_${new Date().toLocaleString()}`,
        camera_id: selectedCamera,
        model_id: realtimeModel,
        confidence: confidenceThreshold,
        iou_threshold: 0.45,
        description: "前端發起的即時分析任務"
      };

      console.log('開始即時分析:', requestData);
      
      const result = await startRealtimeAnalysisMutation.mutateAsync(requestData);
      console.log('即時分析已開始:', result);
      
      alert(`即時分析已開始！\n任務 ID: ${result.task_id}\n狀態: ${result.status}\n${result.message}`);
      
    } catch (error) {
      console.error('開始即時分析失敗:', error);
      alert('開始即時分析失敗，請稍後重試');
      setIsRealtimeAnalysisRunning(false);
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
            {/* 左邊：影片上傳卡片 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  影片上傳
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
                    <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    {selectedFile ? (
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-foreground">
                          已選擇: {selectedFile.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          檔案大小: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                        </p>
                        {uploadResult && (
                          <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
                            <div className="flex items-center gap-2">
                              <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                              上傳成功！影片已加入列表
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div>
                        <p className="text-sm text-muted-foreground mb-2">
                          拖拽影片檔案到此處或點擊選擇
                        </p>
                        <p className="text-xs text-muted-foreground">
                          支援格式: MP4, AVI, MOV, MKV (最大 500MB)
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
                      <FileVideo className="h-4 w-4 mr-2" />
                      選擇影片檔案
                    </Button>
                  </div>
                </div>

                {/* 上傳按鈕 */}
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
                  <div className="space-y-3">
                    <Button 
                      className="w-full" 
                      variant="outline"
                      onClick={() => {
                        setSelectedFile(null);
                        setUploadResult(null);
                        // 重置 mutation 狀態
                        uploadVideoMutation.reset();
                        // 重置檔案輸入元素
                        const fileInput = document.getElementById('video-file') as HTMLInputElement;
                        if (fileInput) {
                          fileInput.value = '';
                        }
                      }}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      繼續上傳更多影片
                    </Button>
                  </div>
                ) : (
                  <Button 
                    className="w-full" 
                    disabled={true}
                    variant="outline"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    請先選擇影片檔案
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* 右邊：影片列表與分析卡片 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileVideo className="h-5 w-5" />
                    影片列表與分析
                  </div>
                  <Badge variant="secondary">
                    {videoListData?.total || 0} 個影片
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 分析參數設置 */}
                <div className="space-y-3 p-3 bg-muted/50 rounded-lg">
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
                </div>

                {/* 影片列表 */}
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {videoListLoading ? (
                    <div className="text-center py-8 text-muted-foreground">
                      載入影片列表中...
                    </div>
                  ) : videoListData && videoListData.videos.length > 0 ? (
                    videoListData.videos.map((video: VideoFileInfo) => (
                      <div 
                        key={video.id} 
                        className="border rounded-lg p-3 hover:bg-muted/30 transition-colors cursor-pointer"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm truncate">{video.name}</p>
                            <p className="text-xs text-muted-foreground">{video.upload_time}</p>
                          </div>
                          <div className="flex items-center gap-2 ml-2">
                            {video.status === 'ready' && (
                              <Badge variant="outline" className="text-xs">
                                待分析
                              </Badge>
                            )}
                            {video.status === 'analyzing' && (
                              <Badge variant="default" className="text-xs">
                                分析中
                              </Badge>
                            )}
                            {video.status === 'completed' && (
                              <Badge variant="secondary" className="text-xs">
                                已完成
                              </Badge>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                          <div className="flex gap-3">
                            <span>時長: {video.duration || '未知'}</span>
                            <span>大小: {video.size}</span>
                            <span>解析度: {video.resolution || '未知'}</span>
                          </div>
                        </div>

                        {video.status === 'ready' && (
                          <div className="flex gap-2">
                            <Button 
                              size="sm" 
                              className="flex-1"
                              disabled={!selectedModel}
                              onClick={() => handleStartAnalysis(video)}
                            >
                              <Play className="h-4 w-4 mr-2" />
                              開始分析此影片
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              disabled={deleteVideoMutation.isPending}
                              onClick={() => handleDeleteVideo(video)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
                        
                        {video.status === 'analyzing' && (
                          <div className="space-y-2">
                            <div className="flex justify-between text-xs">
                              <span>分析進度</span>
                              <span>65%</span>
                            </div>
                            <Progress value={65} className="h-2" />
                            <div className="flex justify-end">
                              <Button
                                size="sm"
                                variant="destructive"
                                disabled={deleteVideoMutation.isPending}
                                onClick={() => handleDeleteVideo(video)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        )}
                        
                        {video.status === 'completed' && (
                          <div className="space-y-2">
                            <div className="text-center py-2">
                              <Badge variant="secondary" className="text-xs">
                                分析已完成
                              </Badge>
                            </div>
                            <div className="flex justify-end">
                              <Button
                                size="sm"
                                variant="destructive"
                                disabled={deleteVideoMutation.isPending}
                                onClick={() => handleDeleteVideo(video)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <FileVideo className="h-12 w-12 mx-auto mb-3 opacity-50" />
                      <p>暫無影片檔案</p>
                      <p className="text-xs mt-1">請先上傳影片檔案</p>
                    </div>
                  )}
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
                    <Select value={selectedCamera} onValueChange={setSelectedCamera}>
                      <SelectTrigger>
                        <SelectValue placeholder={isCamerasLoading ? "載入攝影機列表中..." : "選擇要分析的攝影機"} />
                      </SelectTrigger>
                      <SelectContent>
                        {isCamerasLoading ? (
                          <SelectItem value="loading" disabled>載入中...</SelectItem>
                        ) : isCamerasError ? (
                          <SelectItem value="error" disabled>載入攝影機列表失敗</SelectItem>
                        ) : cameras && cameras.length > 0 ? (
                          cameras.map((camera) => (
                            <SelectItem 
                              key={camera.id} 
                              value={camera.id?.toString() || `camera-${camera.name}`}
                            >
                              {camera.name} ({camera.status})
                            </SelectItem>
                          ))
                        ) : (
                          <SelectItem value="no-cameras" disabled>
                            沒有可用的攝影機設備
                          </SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="analysis-model">分析模型</Label>
                    <Select value={realtimeModel} onValueChange={setRealtimeModel}>
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

                  <Button 
                    className="w-full" 
                    onClick={handleStartRealtimeAnalysis}
                    disabled={isRealtimeAnalysisRunning || startRealtimeAnalysisMutation.isPending}
                  >
                    <Activity className="h-4 w-4 mr-2" />
                    {isRealtimeAnalysisRunning || startRealtimeAnalysisMutation.isPending ? '分析中...' : '開始即時分析'}
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
