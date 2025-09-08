import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
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

  // 模擬攝影機數據
  const [cameras, setCameras] = useState([
    {
      id: "cam_001",
      name: "大門入口",
      location: "1樓大廳",
      status: "online",
      resolution: "1920x1080",
      fps: 30,
      recording: true,
      nightVision: true,
      motionDetection: true,
      ip: "192.168.1.101",
      model: "HC-IPC-D221H",
    },
    {
      id: "cam_002",
      name: "停車場",
      location: "戶外停車區",
      status: "online",
      resolution: "2560x1440",
      fps: 25,
      recording: true,
      nightVision: true,
      motionDetection: false,
      ip: "192.168.1.102",
      model: "HC-IPC-B621H",
    },
    {
      id: "cam_003",
      name: "後門出口",
      location: "1樓後門",
      status: "offline",
      resolution: "1920x1080",
      fps: 30,
      recording: false,
      nightVision: false,
      motionDetection: true,
      ip: "192.168.1.103",
      model: "HC-IPC-D221H",
    },
  ]);

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
        return "線上";
      case "offline":
        return "離線";
      case "warning":
        return "警告";
      default:
        return "未知";
    }
  };

  // 模擬掃描功能
  const startScan = async () => {
    setIsScanning(true);
    setScanProgress(0);
    setShowScanResults(false);
    setScanResults([]);

    // 模擬掃描進度
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 200));
      setScanProgress(i);
    }

    // 模擬掃描結果
    const mockResults = [
      {
        id: "scan_001",
        ip: "192.168.1.105",
        manufacturer: "Hikvision",
        model: "DS-2CD2432F-IW",
        onvifSupport: true,
        rtspUrl: "rtsp://192.168.1.105:554/h264",
        status: "detected",
        description: "2MP Cube Network Camera"
      },
      {
        id: "scan_002",
        ip: "192.168.1.106",
        manufacturer: "Dahua",
        model: "IPC-HFW4431R-Z",
        onvifSupport: true,
        rtspUrl: "rtsp://192.168.1.106:554/cam/realmonitor",
        status: "detected",
        description: "4MP WDR IR Bullet Network Camera"
      },
      {
        id: "scan_003",
        ip: "192.168.1.107",
        manufacturer: "Axis",
        model: "M3046-V",
        onvifSupport: true,
        rtspUrl: "rtsp://192.168.1.107:554/axis-media/media.amp",
        status: "detected",
        description: "Mini Dome Network Camera"
      },
      {
        id: "scan_004",
        ip: "192.168.1.108",
        manufacturer: "Unknown",
        model: "Generic Camera",
        onvifSupport: false,
        rtspUrl: null,
        status: "partial",
        description: "Device found but limited information available"
      }
    ];

    setScanResults(mockResults);
    setShowScanResults(true);
    setIsScanning(false);
  };

  const addCameraToSystem = (device: any) => {
    // 這裡會將掃描到的設備添加到系統中
    console.log("Adding camera to system:", device);
    // 可以在這裡觸發實際的添加邏輯
  };

  // 開啟編輯對話框
  const openEditDialog = (camera: any) => {
    setEditingCamera(camera);
    setEditCameraName(camera.name);
    setEditCameraLocation(camera.location);
    setIsEditDialogOpen(true);
  };

  // 儲存攝影機編輯
  const saveEditCamera = () => {
    if (editingCamera) {
      setCameras(prevCameras => 
        prevCameras.map(camera => 
          camera.id === editingCamera.id 
            ? { ...camera, name: editCameraName, location: editCameraLocation }
            : camera
        )
      );
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

  // 取得選中的攝影機資料
  const selectedCameraData = selectedCamera 
    ? cameras.find(cam => cam.id === selectedCamera) 
    : null;

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
                    onClick={() => setIsAddDialogOpen(false)}
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
                  {selectedCameraData && selectedCameraData.status === "online" ? (
                    <div className="relative h-full">
                      {/* 模擬影像串流 */}
                      <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
                        <div className="text-center text-white space-y-4">
                          <div className="relative">
                            <Camera className="h-16 w-16 mx-auto mb-4 opacity-80" />
                            <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                          </div>
                          <div>
                            <h3>{selectedCameraData.name}</h3>
                            <p className="text-sm text-gray-300">{selectedCameraData.location}</p>
                            <p className="text-xs text-gray-400 mt-2">
                              {selectedCameraData.resolution} • {selectedCameraData.fps} FPS
                            </p>
                          </div>
                          {isStreaming && (
                            <div className="flex items-center justify-center gap-2 text-sm">
                              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                              <span>實況串流中</span>
                            </div>
                          )}
                        </div>
                      </div>
                      {/* 模擬影像噪點效果 */}
                      <div className="absolute inset-0 opacity-10 pointer-events-none">
                        <div className="w-full h-full bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8ZGVmcz4KICAgIDxwYXR0ZXJuIGlkPSJub2lzZSIgd2lkdGg9IjQiIGhlaWdodD0iNCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+CiAgICAgIDxyZWN0IHdpZHRoPSI0IiBoZWlnaHQ9IjQiIGZpbGw9IiNmZmYiLz4KICAgICAgPGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjAuNSIgZmlsbD0iIzAwMCIvPgogICAgICA8Y2lyY2xlIGN4PSIzIiBjeT0iMyIgcj0iMC41IiBmaWxsPSIjMDAwIi8+CiAgICA8L3BhdHRlcm4+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiBmaWxsPSJ1cmwoI25vaXNlKSIvPgo8L3N2Zz4=')]"></div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center text-white h-full flex items-center justify-center">
                      <div>
                        <Camera className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>{selectedCameraData ? "攝影機離線" : "選擇攝影機以檢視即時影像"}</p>
                      </div>
                    </div>
                  )}
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
                          {cameras.filter(cam => cam.status === "online").map((camera) => (
                            <SelectItem key={camera.id} value={camera.id}>
                              {camera.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    {selectedCameraData && (
                      <div className="pt-4 border-t space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">IP地址</span>
                          <span>{selectedCameraData.ip}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">型號</span>
                          <span>{selectedCameraData.model}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">錄影狀態</span>
                          <Badge variant={selectedCameraData.recording ? "default" : "secondary"}>
                            {selectedCameraData.recording ? "錄影中" : "未錄影"}
                          </Badge>
                        </div>
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