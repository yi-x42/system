import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { Alert, AlertDescription } from "./ui/alert";
import {
  Camera,
  Shield,
  AlertTriangle,
  Activity,
  Users,
  HardDrive,
  Wifi,
  CheckCircle,
  XCircle,
  Clock,
} from "lucide-react";

export function Dashboard() {
  // 模擬數據
  const systemStats = {
    totalCameras: 24,
    onlineCameras: 22,
    totalAlerts: 15,
    activeUsers: 8,
    storageUsed: 75,
    systemUptime: 99.8,
  };

  const recentAlerts = [
    {
      id: 1,
      type: "入侵偵測",
      camera: "攝影機-01",
      time: "2024-01-15 14:30:25",
      severity: "高",
    },
    {
      id: 2,
      type: "移動偵測",
      camera: "攝影機-05",
      time: "2024-01-15 14:28:12",
      severity: "中",
    },
    {
      id: 3,
      type: "異常行為",
      camera: "攝影機-12",
      time: "2024-01-15 14:25:45",
      severity: "高",
    },
  ];

  const cameras = [
    { id: 1, name: "大門入口", status: "online", lastSeen: "剛剛" },
    { id: 2, name: "停車場", status: "online", lastSeen: "1分鐘前" },
    { id: 3, name: "後門出口", status: "offline", lastSeen: "5分鐘前" },
    { id: 4, name: "走廊A", status: "online", lastSeen: "剛剛" },
    { id: 5, name: "走廊B", status: "warning", lastSeen: "3分鐘前" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1>系統儀表板</h1>
        <Badge variant="outline" className="flex items-center gap-2">
          <Activity className="h-3 w-3" />
          系統運行中
        </Badge>
      </div>

      {/* 系統狀態總覽 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">攝影機總數</CardTitle>
            <Camera className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl">{systemStats.totalCameras}</div>
            <p className="text-xs text-muted-foreground">
              線上: {systemStats.onlineCameras}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">今日警報</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl">{systemStats.totalAlerts}</div>
            <p className="text-xs text-muted-foreground">較昨日 +3</p>
          </CardContent>
        </Card>



        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">目前運行的任務數</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl">8</div>
            <p className="text-xs text-muted-foreground">處理中的檢測任務</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">系統運行時間</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl">15天</div>
            <p className="text-xs text-muted-foreground">持續穩定運行</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* 攝影機線上狀態 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wifi className="h-5 w-5" />
              攝影機狀態
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {cameras.map((camera) => (
                <div key={camera.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {camera.status === "online" && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    {camera.status === "offline" && (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    {camera.status === "warning" && (
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    )}
                    <div>
                      <p className="font-medium">{camera.name}</p>
                      <p className="text-xs text-muted-foreground">
                        最後更新: {camera.lastSeen}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant={
                      camera.status === "online"
                        ? "default"
                        : camera.status === "offline"
                        ? "destructive"
                        : "secondary"
                    }
                  >
                    {camera.status === "online"
                      ? "線上"
                      : camera.status === "offline"
                      ? "離線"
                      : "警告"}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 警報通知 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              最新警報
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentAlerts.map((alert) => (
                <Alert key={alert.id}>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">{alert.type}</p>
                        <p className="text-sm text-muted-foreground">
                          {alert.camera} • {alert.time}
                        </p>
                      </div>
                      <Badge
                        variant={
                          alert.severity === "高" ? "destructive" : "secondary"
                        }
                      >
                        {alert.severity}
                      </Badge>
                    </div>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 系統性能指標 */}
      <Card>
        <CardHeader>
          <CardTitle>系統性能</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-sm text-muted-foreground">CPU 使用率</p>
              <p className="text-2xl">45%</p>
              <Progress value={45} className="mt-2" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">GPU 使用率</p>
              <p className="text-2xl">72%</p>
              <Progress value={72} className="mt-2" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">記憶體使用率</p>
              <p className="text-2xl">68%</p>
              <Progress value={68} className="mt-2" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}