import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import {
  useScanCameras,
  useDeleteCamera,
  useCameras,
  useCameraStreamInfo,
  useToggleCamera,
  CameraInfo,
  CameraStreamInfo,
  RegisteredCameraInfo,
} from "../hooks/react-query-hooks";
import apiClient from "../lib/api";
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
} from "lucide-react";

type ScanResultItem = {
  id: string;
  name: string;
  deviceIndex?: number;
  resolution: string;
  fps: number;
  details?: string;
  status?: "success" | "error";
};

// 視頻串流組件
const waitForIceGathering = (pc: RTCPeerConnection) =>
  new Promise<void>((resolve) => {
    if (pc.iceGatheringState === "complete") {
      resolve();
      return;
    }

    const checkState = () => {
      if (pc.iceGatheringState === "complete") {
        pc.removeEventListener("icegatheringstatechange", checkState);
        resolve();
      }
    };

    pc.addEventListener("icegatheringstatechange", checkState);
    setTimeout(() => {
      pc.removeEventListener("icegatheringstatechange", checkState);
      resolve();
    }, 2000);
  });

interface VideoStreamProps {
  camera: CameraInfo | null;
  streamInfo: CameraStreamInfo | undefined;
  isLoading: boolean;
  error: Error | null;
  onCameraToggle?: (cameraId: string) => void;
}

function VideoStream({ camera, streamInfo, isLoading, error, onCameraToggle }: VideoStreamProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const peerRef = useRef<RTCPeerConnection | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("");

  useEffect(() => {
    let isMounted = true;
    let cancelled = false;

    const cleanup = () => {
      if (peerRef.current) {
        peerRef.current.getSenders().forEach((sender) => {
          try {
            sender.track?.stop();
          } catch {
            /* ignore */
          }
        });
        try {
          peerRef.current.close();
        } catch {
          /* ignore */
        }
        peerRef.current = null;
      }
      const video = videoRef.current;
      if (video) {
        video.srcObject = null;
      }
    };

    if (!camera || !streamInfo) {
      cleanup();
      if (isMounted) {
        setStatusMessage("");
      }
      return () => {
        cancelled = true;
        isMounted = false;
        cleanup();
      };
    }

    const startConnection = async () => {
      setStatusMessage(streamInfo.is_active ? "連線中…" : "攝影機離線，嘗試連線…");

      const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });
      peerRef.current = pc;

      pc.ontrack = (event) => {
        if (!isMounted || cancelled) {
          return;
        }
        const [stream] = event.streams;
        if (stream) {
          const video = videoRef.current;
          if (video) {
            video.srcObject = stream;
          }
        }
      };

      pc.onconnectionstatechange = () => {
        if (!isMounted || cancelled) {
          return;
        }
        switch (pc.connectionState) {
          case "connected":
            setStatusMessage("");
            break;
          case "connecting":
            setStatusMessage("連線中…");
            break;
          case "disconnected":
            setStatusMessage("連線中斷，重新嘗試中…");
            break;
          case "failed":
            setStatusMessage("WebRTC 連線失敗");
            break;
          case "closed":
            setStatusMessage("連線已關閉");
            break;
          default:
            break;
        }
      };

      pc.oniceconnectionstatechange = () => {
        if (!isMounted || cancelled) {
          return;
        }
        if (pc.iceConnectionState === "failed") {
          setStatusMessage("ICE 連線失敗");
        }
      };

      pc.addTransceiver("video", { direction: "recvonly" });

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      await waitForIceGathering(pc);

      const localDescription = pc.localDescription;
      if (!localDescription) {
        throw new Error("無法建立本地 SDP");
      }

      const { data } = await apiClient.post(streamInfo.webrtc_endpoint, {
        sdp: localDescription.sdp,
        type: localDescription.type,
      });

      const answer = new RTCSessionDescription(data);
      await pc.setRemoteDescription(answer);
      if (!cancelled) {
        setStatusMessage("");
      }
    };

    startConnection().catch((err) => {
      console.error("建立攝影機 WebRTC 連線失敗:", err);
      if (!cancelled) {
        setStatusMessage("建立 WebRTC 連線失敗");
      }
      cleanup();
    });

    return () => {
      cancelled = true;
      isMounted = false;
      cleanup();
    };
  }, [camera?.id, streamInfo?.webrtc_endpoint, streamInfo?.is_active]);

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
            狀態: {(camera.status === "active" || camera.status === "online") ? "啟用" : "停用"}
          </p>

          {(camera.status !== "active" && camera.status !== "online") && onCameraToggle && (
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

  return (
    <div className="relative h-full">
      <video
        ref={videoRef}
        className="w-full h-full object-cover rounded-lg bg-black"
        autoPlay
        playsInline
        muted
      />

      {statusMessage && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/60 text-white">
          {statusMessage.includes("連線") ? (
            <Loader2 className="h-10 w-10 animate-spin opacity-70" />
          ) : (
            <Camera className="h-10 w-10 opacity-70" />
          )}
          <p className="text-sm">{statusMessage}</p>
          <p className="text-xs opacity-70">{camera.name}</p>
        </div>
      )}

      <div className="absolute top-2 left-2 bg-black/70 text-white px-3 py-1 rounded-md text-sm flex items-center gap-2">
        <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
        <span>{camera.name}</span>
        <Badge variant="secondary" className="text-xs">
          {camera.resolution} • {camera.fps} FPS
        </Badge>
      </div>

      <div className="absolute bottom-2 left-2 bg-black/60 text-white px-3 py-1 rounded-md text-xs space-y-1">
        <div>狀態: {(camera.status === "active" || camera.status === "online") ? "啟用" : "停用"}</div>
        <div>類型: {camera.camera_type}</div>
        {camera.ip && <div>IP: {camera.ip}</div>}
        {camera.model && <div>型號: {camera.model}</div>}
      </div>
    </div>
  );
}


export function CameraControl() {
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanResults, setScanResults] = useState<ScanResultItem[]>([]);
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
  const toggleCameraMutation = useToggleCamera();

  const newlyRegisteredCount = scanResults.filter((item) => item.status !== "error").length;

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
        register_new: true,
      });

      // 將後端回傳的資料轉換為前端需要的格式
      const registeredDevices = scanResult.registered ?? [];
      const formattedResults = registeredDevices.map((device: RegisteredCameraInfo) => ({
        id: device.id,
        name: device.name || `攝影機 ${device.device_index}`,
        deviceIndex: device.device_index,
        resolution: device.resolution || "未知",
        fps: device.fps || 0,
        details: "已自動加入設備列表",
        status: "success",
      }));

      // 等待進度動畫完成
      await progressPromise;
      setScanProgress(100);

      // 顯示掃描結果
      setScanResults(formattedResults);
      await refetchCameras();
      setShowScanResults(true);
      
    } catch (error) {
      console.error('攝影機掃描失敗:', error);
      
      // 即使失敗也要完成進度動畫
      await progressPromise;
      setScanProgress(100);
      
      // 顯示錯誤訊息
      setScanResults([{
        id: "error",
        name: "掃描失敗",
        resolution: "未知",
        fps: 0,
        details: `錯誤訊息: ${error instanceof Error ? error.message : "未知錯誤"}`,
        status: "error",
      }]);
      setShowScanResults(true);
    } finally {
      setIsScanning(false);
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
                        <Badge variant="outline">{newlyRegisteredCount} 個新設備</Badge>
                      </div>
                      
                      <div className="max-h-96 overflow-auto border rounded-lg">
                        <div className="space-y-3 p-4">
                          {scanResults.length === 0 ? (
                            <div className="text-center text-sm text-muted-foreground py-10">
                              沒有新的設備需要新增
                            </div>
                          ) : (
                            scanResults.map((device) => (
                              <div key={device.id} className="border rounded-lg p-4 space-y-3">
                                <div className="flex items-start justify-between">
                                  <div className="space-y-1 flex-1">
                                    <div className="flex items-center gap-2">
                                      <h4 className="text-sm">{device.name}</h4>
                                      <Badge variant="secondary" className="text-xs">
                                        {device.deviceIndex !== undefined
                                          ? `本機攝影機 #${device.deviceIndex}`
                                          : "未知設備"}
                                      </Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                      解析度: {device.resolution} | FPS: {device.fps ? device.fps : "未知"}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                      {device.details ?? "已自動加入設備列表"}
                                    </p>
                                  </div>
                                  {device.status === "error" ? (
                                    <Badge variant="destructive" className="text-xs">
                                      失敗
                                    </Badge>
                                  ) : (
                                    <Badge variant="default" className="text-xs">
                                      已新增
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            ))
                          )}
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

