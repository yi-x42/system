import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { VideoUpload } from "./VideoUpload";
import {
  Camera,
  Upload,
  Video,
  MonitorPlay,
  Plus,
  Settings,
  Play,
  Pause,
  AlertCircle,
  CheckCircle,
} from "lucide-react";

// 模擬資料來源數據
const mockDataSources = [
  {
    id: 1,
    name: "大門入口攝影機",
    type: "camera",
    status: "active",
    config: {
      ip: "192.168.1.101",
      resolution: "1920x1080",
      fps: 30
    },
    created_at: "2024-01-15T09:30:00Z"
  },
  {
    id: 2,
    name: "停車場監控",
    type: "camera", 
    status: "active",
    config: {
      ip: "192.168.1.102",
      resolution: "2560x1440",
      fps: 25
    },
    created_at: "2024-01-15T10:15:00Z"
  },
  {
    id: 3,
    name: "測試影片.mp4",
    type: "video_file",
    status: "active",
    config: {
      path: "uploads/videos/20240915_143022_測試影片.mp4",
      original_name: "測試影片.mp4",
      duration: 120.5,
      fps: 30,
      resolution: "1920x1080",
      frame_count: 3615
    },
    created_at: "2024-01-20T14:30:22Z"
  }
];

export function DataSourceManager() {
  const [dataSources, setDataSources] = useState(mockDataSources);
  const [activeTab, setActiveTab] = useState("list");

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "default";
      case "inactive":
        return "secondary";
      case "error":
        return "destructive";
      default:
        return "outline";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "camera":
        return <Camera className="h-4 w-4" />;
      case "video_file":
        return <Video className="h-4 w-4" />;
      default:
        return <MonitorPlay className="h-4 w-4" />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "camera":
        return "攝影機";
      case "video_file":
        return "影片檔案";
      default:
        return "未知";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-TW');
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const handleUploadSuccess = (uploadInfo: any) => {
    // 新增上傳成功的資料來源到列表
    const newDataSource = {
      id: uploadInfo.source_id,
      name: uploadInfo.original_name,
      type: "video_file",
      status: "active",
      config: {
        path: uploadInfo.file_path,
        original_name: uploadInfo.original_name,
        duration: uploadInfo.video_info.duration,
        fps: uploadInfo.video_info.fps,
        resolution: uploadInfo.video_info.resolution,
        frame_count: uploadInfo.video_info.frame_count
      },
      created_at: new Date().toISOString()
    };

    setDataSources(prev => [newDataSource, ...prev]);
    
    // 顯示成功訊息
    alert(`影片 "${uploadInfo.original_name}" 上傳成功！`);
  };

  const handleUploadError = (error: string) => {
    alert(`上傳失敗: ${error}`);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">資料來源管理</h1>
          <p className="text-muted-foreground">
            管理攝影機設備和影片檔案資料來源
          </p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="list" className="flex items-center gap-2">
            <MonitorPlay className="h-4 w-4" />
            資料來源列表
          </TabsTrigger>
          <TabsTrigger value="upload" className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            影片上傳
          </TabsTrigger>
          <TabsTrigger value="cameras" className="flex items-center gap-2">
            <Camera className="h-4 w-4" />
            攝影機管理
          </TabsTrigger>
        </TabsList>

        {/* 資料來源列表 */}
        <TabsContent value="list" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>已註冊的資料來源</CardTitle>
                <Badge variant="outline">
                  共 {dataSources.length} 個資料來源
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {dataSources.map((source) => (
                  <div
                    key={source.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex items-center gap-4">
                      <div className="p-2 bg-muted rounded-lg">
                        {getTypeIcon(source.type)}
                      </div>
                      <div>
                        <h3 className="font-medium">{source.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {getTypeLabel(source.type)} • 
                          建立於 {formatDate(source.created_at)}
                        </p>
                        
                        {/* 顯示詳細資訊 */}
                        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                          {source.type === "camera" && (
                            <>
                              <span>IP: {source.config.ip}</span>
                              <span>解析度: {source.config.resolution}</span>
                              <span>FPS: {source.config.fps}</span>
                            </>
                          )}
                          {source.type === "video_file" && (
                            <>
                              <span>時長: {formatDuration(source.config.duration || 0)}</span>
                              <span>解析度: {source.config.resolution}</span>
                              <span>FPS: {source.config.fps}</span>
                              <span>總幀數: {(source.config.frame_count || 0).toLocaleString()}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getStatusColor(source.status)}>
                        {source.status === "active" ? "使用中" : 
                         source.status === "inactive" ? "停用" : "錯誤"}
                      </Badge>
                      <Button variant="ghost" size="sm">
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        className="text-green-600 hover:text-green-700"
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 影片上傳 */}
        <TabsContent value="upload" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                影片檔案上傳
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                上傳影片檔案作為 YOLO 物件辨識的資料來源
              </p>
            </CardHeader>
          </Card>
          
          <VideoUpload 
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        </TabsContent>

        {/* 攝影機管理 */}
        <TabsContent value="cameras" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Camera className="h-5 w-5" />
                  攝影機設備管理
                </CardTitle>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  新增攝影機
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                攝影機管理功能開發中...
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
