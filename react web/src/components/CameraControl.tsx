import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { 
  useScanCameras, 
  CameraDevice, 
  useDeleteCamera,
  useCameras,
  useAddCamera,
  useCameraStreamInfo,
  useToggleCamera,
  CameraInfo,
  AddCameraRequest
} from "../hooks/react-query-hooks";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Switch } from "./ui/switch";
import { Progress } from "./ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import {
  Camera,
  Settings,
  Play,
  Pause,
  RotateCw,
  ZoomIn,
  ZoomOut,
  Plus,
  Edit,
  Trash2,
  MonitorPlay,
  MapPin,
  Search,
  Loader2,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

// 視頻串流組件
interface VideoStreamProps {
  camera: any | null; // 使用映射後的攝影機數據型別
  streamInfo: any | null;
  isLoading: boolean;
  error: Error | null;
  onCameraToggle?: (cameraId: string) => void;
}

function VideoStream({ camera, streamInfo, isLoading, error, onCameraToggle }: VideoStreamProps) {
  // 如果沒有選擇攝影機
  if (!camera) {
    return (
      <div className="text-center text-white h-full flex items-center justify-center">
        <div>
          <Camera className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>選擇攝影機以檢視即時影像</p>
        </div>
      </div>
    );
  }

  // 如果正在載入串流資訊
  if (isLoading) {
    return (
      <div className="text-center text-white h-full flex items-center justify-center">
        <div>
          <Loader2 className="h-8 w-8 mx-auto mb-2 animate-spin" />
          <p>載入串流資訊中...</p>
        </div>
      </div>
    );
  }

  // 如果有錯誤或攝影機離線
  if (error || !streamInfo) {
    return (
      <div className="text-center text-white h-full flex items-center justify-center">
        <div>
          <Camera className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <h3 className="text-lg font-medium mb-2">{camera.name}</h3>
          <p className="text-sm text-gray-300 mb-2">
            {error ? "串流載入失敗" : "攝影機離線"}
          </p>
          {error && (
            <p className="text-xs text-red-400 mb-4">{error.message}</p>
          )}
          <Badge variant="secondary" className="mb-4">
            {camera.resolution} • {camera.fps} FPS
          </Badge>
          <p className="text-xs text-gray-400 mb-4">
            狀態: {(camera.status === 'active' || camera.status === 'online') ? '啟用' : '停用'}
          </p>
          
          {/* 啟用攝影機按鈕 */}
          {(camera.status !== 'active' && camera.status !== 'online') && onCameraToggle && (
            <Button
              onClick={() => onCameraToggle(camera.id)}
              className="bg-blue-500 hover:bg-blue-600 text-white"
            >
              啟用攝影機
            </Button>
          )}
        </div>
      </div>
    );
  }

  // 如果有串流，顯示即時影像
  return (
    <div className="relative h-full">
      <img
        src={`http://localhost:8001${streamInfo.stream_url}`}
        alt={`${camera.name} 即時串流`}
        className="w-full h-full object-cover"
        onError={(e) => {
          console.error('串流載入失敗:', e);
          e.currentTarget.style.display = 'none';
        }}
        onLoad={() => {
          console.log('串流載入成功');
        }}
      />
      
      {/* 串流資訊覆蓋層 */}
      <div className="absolute top-2 left-2 bg-black/70 text-white px-3 py-1 rounded-md text-sm flex items-center gap-2">
        <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
        <span>{camera.name} • {streamInfo.resolution} • {streamInfo.fps}fps</span>
      </div>
      
      {/* 串流狀態指示器 */}
      <div className="absolute top-2 right-2 bg-green-500/80 text-white px-2 py-1 rounded-md text-xs">
        LIVE
      </div>
    </div>
  );
}

export function CameraControl() {
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanResults, setScanResults] = useState<any[]>([]);
  const [showScanResults, setShowScanResults] = useState(false);
  const [scanConfig, setScanConfig] = useState({
    ipRange: "192.168.1.1-192.168.1.254",
    ports: "80,554,8080",
    timeout: "10",
    onvifScan: true,
    rtspScan: true
  });
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingCamera, setEditingCamera] = useState<any>(null);
  const [editCameraName, setEditCameraName] = useState("");
  const [editCameraLocation, setEditCameraLocation] = useState("");
  const [activeTab, setActiveTab] = useState("device-list");
  const [isStreaming, setIsStreaming] = useState(false);

  // 使用真實的攝影機數據從後端API
  const { data: rawCameras = [], isLoading: camerasLoading, refetch: refetchCameras } = useCameras();
  const addCameraMutation = useAddCamera();
  const toggleCameraMutation = useToggleCamera();

  // 映射後端數據到前端UI格式
  const cameras = rawCameras.map(camera => ({
    ...camera,
    // 添加前端UI需要的欄位，如果後端沒有則提供預設值
    location: camera.group_id || "未指定位置",
    ip: camera.device_index !== undefined ? `本機設備 #${camera.device_index}` : camera.rtsp_url || "未知",
    model: camera.camera_type === "USB" ? "本機攝影機" : "網路攝影機",
    recording: false, // 預設值，可以從其他API獲取
    nightVision: false, // 預設值
    motionDetection: false, // 預設值
  }));

  const getStatusColor = (status: string) => {
    switch (status) {
      case "online":
        return "default";
      case "offline":
        return "destructive";
      case "warning":
        return "secondary";
      default:
        return "outline";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "online":
      case "active":
        return "線上";
      case "offline":
      case "inactive":
        return "離線";
      case "warning":
        return "警告";
      default:
        return "未知";
    }
  };

  // 使用真實的攝影機掃描 API
  const scanCamerasMutation = useScanCameras();
  
  // 刪除攝影機的 mutation
  const deleteCameraMutation = useDeleteCamera();

  const startScan = async () => {
    setIsScanning(true);
    setScanProgress(0);
    setShowScanResults(false);
    setScanResults([]);

    // 模擬掃描進度動畫（保持 UI 效果）
    const progressAnimation = async () => {
      const steps = [0, 15, 30, 45, 60, 75, 90];
      for (const progress of steps) {
        setScanProgress(progress);
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    };

    // 同時執行進度動畫和真實掃描
    const progressPromise = progressAnimation();
    
    try {
      // 呼叫真實的攝影機掃描 API
      const scanResult = await scanCamerasMutation.mutateAsync({
        max_index: 6,        // 掃描 0-5 號攝影機
        warmup_frames: 3,    // 快速模式
        force_probe: false,
        retries: 1
      });

      // 將後端回傳的資料轉換為前端需要的格式
      const formattedResults = scanResult.devices
        .filter(device => device.frame_ok) // 只顯示能正常工作的攝影機
        .map((device: CameraDevice, index: number) => ({
          id: `camera_${device.index}`,
          ip: `本機攝影機 #${device.index}`,
          manufacturer: "本機設備",
          model: `攝影機 ${device.index}`,
          onvifSupport: true,
          rtspUrl: `/camera/${device.index}`,
          status: "detected",
          description: `解析度: ${device.width}x${device.height}, 後端: ${device.backend}`,
          cameraIndex: device.index,
          width: device.width,
          height: device.height,
          backend: device.backend
        }));

      // 等待進度動畫完成
      await progressPromise;
      setScanProgress(100);

      // 顯示掃描結果
      setScanResults(formattedResults);
      setShowScanResults(true);
      
    } catch (error) {
      console.error('攝影機掃描失敗:', error);
      
      // 即使失敗也要完成進度動畫
      await progressPromise;
      setScanProgress(100);
      
      // 顯示錯誤訊息
      setScanResults([{
        id: "error",
        ip: "掃描失敗",
        manufacturer: "系統錯誤",
        model: "無法掃描攝影機",
        onvifSupport: false,
        rtspUrl: null,
        status: "error",
        description: `錯誤訊息: ${error instanceof Error ? error.message : '未知錯誤'}`
      }]);
      setShowScanResults(true);
    } finally {
      setIsScanning(false);
    }
  };

  const addCameraToSystem = async (device: any) => {
    // 將掃描到的設備添加到系統中
    console.log("Adding camera to system:", device);
    
    if (device.cameraIndex !== undefined) {
      // 對於本機攝影機，使用攝影機 index
      const newCamera = {
        id: `cam_${Date.now()}`,
        name: `攝影機 ${device.cameraIndex}`,
        location: `本機攝影機 #${device.cameraIndex}`,
        status: "online",
        resolution: device.width && device.height ? `${device.width}x${device.height}` : "未知",
        fps: 30,
        recording: false,
        nightVision: false,
        motionDetection: false,
        ip: `本機設備 #${device.cameraIndex}`,
        model: device.model || "本機攝影機",
        cameraIndex: device.cameraIndex,
        backend: device.backend
      };
      
      // 使用API新增攝影機
      try {
        const cameraData: AddCameraRequest = {
          name: newCamera.name,
          camera_type: "USB",
          resolution: newCamera.resolution,
          fps: newCamera.fps,
          device_index: device.cameraIndex
        };
        
        await addCameraMutation.mutateAsync(cameraData);
        // 重新取得攝影機列表
        refetchCameras();
        
        // 關閉掃描結果對話框
        setShowScanResults(false);
      
        console.log("已新增攝影機:", newCamera);
      } catch (error) {
        console.error("新增攝影機失敗:", error);
      }
    } else {
      console.log("設備資料不完整，無法新增");
    }
  };

  // 切換攝影機狀態
  const handleCameraToggle = async (cameraId: string) => {
    try {
      await toggleCameraMutation.mutateAsync(cameraId);
      // 重新取得攝影機列表以更新狀態
      refetchCameras();
      // 如果是當前選中的攝影機，也重新載入串流資訊
      if (cameraId === selectedCamera) {
        // 串流資訊會自動重新載入，因為我們有dependency在攝影機狀態上
      }
    } catch (error) {
      console.error('切換攝影機狀態失敗:', error);
      alert('切換攝影機狀態失敗，請稍後再試');
    }
  };

  // 開啟編輯對話框
  const openEditDialog = (camera: any) => {
    setEditingCamera(camera);
    setEditCameraName(camera.name);
    setEditCameraLocation(camera.location);
    setIsEditDialogOpen(true);
  };

  // 儲存攝影機編輯
  const saveEditCamera = async () => {
    if (editingCamera) {
      // TODO: 實現攝影機編輯API調用
      console.log("編輯攝影機功能待實現");
      setIsEditDialogOpen(false);
      setEditingCamera(null);
      setEditCameraName("");
      setEditCameraLocation("");
    }
  };

  // 開始即時預覽
  const startLivePreview = (cameraId: string) => {
    setSelectedCamera(cameraId);
    setActiveTab("live-view");
    setIsStreaming(true);
  };

  // 刪除攝影機
  const handleDeleteCamera = async (cameraId: string) => {
    if (window.confirm('確定要刪除這個攝影機配置嗎？')) {
      try {
        await deleteCameraMutation.mutateAsync(cameraId);
        // 重新取得攝影機列表
        refetchCameras();
        // 如果刪除的是當前選中的攝影機，清除選擇
        if (selectedCamera === cameraId) {
          setSelectedCamera(null);
        }
      } catch (error) {
        console.error('刪除攝影機失敗:', error);
        alert('刪除攝影機失敗，請稍後再試');
      }
    }
  };

  // 取得選中的攝影機資料
  const selectedCameraData = selectedCamera 
    ? cameras.find(cam => cam.id === selectedCamera) 
    : null;

  // 取得攝影機串流資訊
  const { data: streamInfo, isLoading: streamLoading, error: streamError } = useCameraStreamInfo(selectedCamera);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1>攝影機控制中心</h1>
        <Button
          onClick={() => {
            setIsAddDialogOpen(true);
            startScan();
          }}
        >
          <Search className="h-4 w-4 mr-2" />
          自動掃描
        </Button>
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>自動掃描</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 max-w-4xl">
              {isScanning ? (
                <div className="space-y-4 text-center py-8">
                  <div className="flex items-center justify-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin" />
                    <h3>正在掃描網絡設備...</h3>
                  </div>
                  <Progress value={scanProgress} className="w-full max-w-md mx-auto" />
                  <p className="text-sm text-muted-foreground">掃描進度: {scanProgress}%</p>
                  <p className="text-xs text-muted-foreground">
                    掃描範圍: {scanConfig.ipRange} | 端口: {scanConfig.ports}
                  </p>
                  <Button 
                    variant="outline" 
                    onClick={() => {
                      setIsScanning(false);
                      setScanProgress(0);
                      setShowScanResults(false);
                    }}
                    className="mt-4"
                  >
                    取消
                  </Button>
                </div>
              ) : showScanResults ? (
                <>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3>掃描結果</h3>
                      <Badge variant="outline">{scanResults.length} 個設備</Badge>
                    </div>
                    
                    <div className="max-h-96 overflow-auto border rounded-lg">
                      <div className="space-y-3 p-4">
                        {scanResults.map((device) => (
                          <div key={device.id} className="border rounded-lg p-4 space-y-3">
                            <div className="flex items-start justify-between">
                              <div className="space-y-1 flex-1">
                                <div className="flex items-center gap-2">
                                  <h4 className="text-sm">{device.manufacturer}</h4>
                                  <Badge variant="secondary" className="text-xs">{device.ip}</Badge>
                                </div>
                                <p className="text-sm text-muted-foreground">{device.model}</p>
                                <p className="text-xs text-muted-foreground">{device.description}</p>
                              </div>
                              <Button 
                                size="sm" 
                                className="ml-4"
                                onClick={() => addCameraToSystem(device)}
                                disabled={device.status !== "detected"}
                              >
                                新增配置
                              </Button>
                            </div>
                            
                            <div className="flex items-center justify-between pt-2 border-t">
                              <div className="flex items-center gap-2">
                                {device.status === "detected" ? (
                                  <CheckCircle className="h-4 w-4 text-green-500" />
                                ) : (
                                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                                )}
                                <span className="text-sm">
                                  {device.status === "detected" ? "已偵測" : "部分資訊"}
                                </span>
                              </div>
                              <div className="flex gap-2">
                                {device.onvifSupport && (
                                  <Badge variant="outline" className="text-xs">ONVIF</Badge>
                                )}
                                {device.rtspUrl && (
                                  <Badge variant="outline" className="text-xs">RTSP</Badge>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end gap-2 pt-4">
                    <Button 
                      variant="outline" 
                      onClick={() => {
                        setShowScanResults(false);
                        setScanResults([]);
                        startScan();
                      }}
                    >
                      重新掃描
                    </Button>
                    <Button onClick={() => setIsAddDialogOpen(false)}>
                      完成
                    </Button>
                  </div>
                </>
              ) : null}
            </div>
          </DialogContent>
        </Dialog>

        {/* 編輯攝影機對話框 */}
        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>編輯攝影機</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="edit-camera-name">攝影機名稱</Label>
                <Input
                  id="edit-camera-name"
                  value={editCameraName}
                  onChange={(e) => setEditCameraName(e.target.value)}
                  placeholder="輸入攝影機名稱"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-camera-location">安裝位置</Label>
                <Input
                  id="edit-camera-location"
                  value={editCameraLocation}
                  onChange={(e) => setEditCameraLocation(e.target.value)}
                  placeholder="輸入安裝位置"
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                  取消
                </Button>
                <Button onClick={saveEditCamera}>
                  儲存
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="device-list">設備列表</TabsTrigger>
          <TabsTrigger value="live-view">即時監控</TabsTrigger>
          
        </TabsList>

        <TabsContent value="device-list">
          <div className="grid gap-4">
            {cameras.map((camera) => (
              <Card key={camera.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Camera className="h-5 w-5" />
                      <div>
                        <CardTitle>{camera.name}</CardTitle>
                        <p className="text-sm text-muted-foreground flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {camera.location}
                        </p>
                      </div>
                    </div>
                    <Badge variant={getStatusColor(camera.status)}>
                      {getStatusText(camera.status)}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <div>
                      <p className="text-sm text-muted-foreground">解析度</p>
                      <p>{camera.resolution}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">幀率</p>
                      <p>{camera.fps} FPS</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">IP地址</p>
                      <p>{camera.ip}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">型號</p>
                      <p>{camera.model}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-4">
                    <div className="flex items-center gap-4">
                      
                      
                      
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => openEditDialog(camera)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => handleDeleteCamera(camera.id)}
                        disabled={deleteCameraMutation.isPending}
                        className="text-destructive hover:bg-destructive hover:text-destructive-foreground"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    
                      <Button variant="outline" size="sm" onClick={() => startLivePreview(camera.id)}>
                        <MonitorPlay className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="live-view">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* 即時影像區域 */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>即時影像串流</CardTitle>
                  {selectedCameraData && (
                    <div className="flex items-center gap-2">
                      <Badge variant={getStatusColor(selectedCameraData.status)}>
                        {getStatusText(selectedCameraData.status)}
                      </Badge>
                      <Badge variant="outline">{selectedCameraData.resolution}</Badge>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="aspect-video bg-black rounded-lg overflow-hidden relative">
                  <VideoStream
                    camera={selectedCameraData}
                    streamInfo={streamInfo}
                    isLoading={streamLoading}
                    error={streamError}
                    onCameraToggle={handleCameraToggle}
                  />
                </div>
                
              </CardContent>
            </Card>

            {/* 控制面板 */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>攝影機選擇</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="camera-select">選擇攝影機</Label>
                      <Select value={selectedCamera || ""} onValueChange={(value) => {
                        setSelectedCamera(value);
                        setIsStreaming(false);
                      }}>
                        <SelectTrigger>
                          <SelectValue placeholder="選擇要串流的攝影機" />
                        </SelectTrigger>
                        <SelectContent>
                          {cameras.map((camera) => (
                            <SelectItem key={camera.id} value={camera.id}>
                              <div className="flex items-center gap-2">
                                <div 
                                  className={`w-2 h-2 rounded-full ${
                                    camera.status === 'active' ? 'bg-green-500' : 
                                    camera.status === 'inactive' ? 'bg-gray-400' : 'bg-red-500'
                                  }`}
                                />
                                {camera.name}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    {selectedCameraData && (
                      <div className="pt-4 border-t space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">攝影機ID</span>
                          <span>{selectedCameraData.id}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">名稱</span>
                          <span>{selectedCameraData.name}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">狀態</span>
                          <Badge variant={getStatusColor(selectedCameraData.status)}>
                            {getStatusText(selectedCameraData.status)}
                          </Badge>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">攝影機類型</span>
                          <span>{selectedCameraData.camera_type}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">解析度</span>
                          <span>{selectedCameraData.resolution}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">幀率</span>
                          <span>{selectedCameraData.fps} FPS</span>
                        </div>
                        {selectedCameraData.ip && (
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">IP地址</span>
                            <span>{selectedCameraData.ip}</span>
                          </div>
                        )}
                        {selectedCameraData.model && (
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">型號</span>
                            <span>{selectedCameraData.model}</span>
                          </div>
                        )}
                        {selectedCameraData.location && (
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">位置</span>
                            <span>{selectedCameraData.location}</span>
                          </div>
                        )}
                        {selectedCameraData.rtsp_url && (
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">RTSP URL</span>
                            <span className="text-xs break-all">{selectedCameraData.rtsp_url}</span>
                          </div>
                        )}
                        {selectedCameraData.recording !== undefined && (
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">錄影狀態</span>
                            <Badge variant={selectedCameraData.recording ? "default" : "secondary"}>
                              {selectedCameraData.recording ? "錄影中" : "未錄影"}
                            </Badge>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              
            </div>
          </div>
        </TabsContent>

        <TabsContent value="settings">
          
        </TabsContent>
      </Tabs>
    </div>
  );
}