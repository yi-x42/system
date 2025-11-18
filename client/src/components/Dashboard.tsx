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
import {
  useSystemStats,
  useCameras,
  useActiveAlerts,
  type ActiveAlert,
} from "../hooks/react-query-hooks";
import { Skeleton } from "./ui/skeleton";

export function Dashboard() {
  const { data: systemStats, isLoading, isError, error } = useSystemStats();
  const { data: camerasData, isLoading: camerasLoading, error: camerasError } = useCameras();
  const {
    data: activeAlertsData,
    isLoading: activeAlertsLoading,
    isError: activeAlertsError,
    error: activeAlertsErrorInstance,
  } = useActiveAlerts();
  
  // 添加調試資訊
  console.log('🔍 Dashboard - 攝影機資料更新:', {
    camerasData,
    camerasLoading,
    camerasError: camerasError?.message,
    timestamp: new Date().toISOString()
  });

  // 格式化運行時間
  const formatUptime = (seconds: number | undefined) => {
    if (seconds === undefined) {
      return "0 分鐘";
    }
    if (seconds < 86400) {
      // 少於一天，顯示分鐘
      const minutes = Math.floor(seconds / 60);
      return `${minutes} 分鐘`;
    } else {
      // 超過一天，顯示天和分鐘
      const days = Math.floor(seconds / 86400);
      const remainingSeconds = seconds % 86400;
      const minutes = Math.floor(remainingSeconds / 60);
      return `${days} 天 ${minutes} 分鐘`;
    }
  };
  const formatAlertTimestamp = (value?: string | null) => {
    if (!value) {
      return "時間未知";
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }
    return parsed.toLocaleString();
  };

  const getSeverityBadgeVariant = (severity?: string | null) => {
    const normalized = severity?.toLowerCase?.() ?? "";
    if (
      normalized === "critical" ||
      normalized === "high" ||
      (severity?.includes("高") ?? false) ||
      (severity?.includes("嚴") ?? false)
    ) {
      return "destructive" as const;
    }
    if (
      normalized === "medium" ||
      normalized === "moderate" ||
      (severity?.includes("中") ?? false)
    ) {
      return "secondary" as const;
    }
    return "outline" as const;
  };

  const getSeverityLabel = (severity?: string | null) => {
    const normalized = severity?.toLowerCase?.() ?? "";
    if (normalized === "critical") {
      return "嚴重";
    }
    if (normalized === "high") {
      return "高";
    }
    if (normalized === "medium" || normalized === "moderate") {
      return "中";
    }
    if (normalized === "low") {
      return "低";
    }
    return severity || "未知";
  };

  const getAlertSourceLabel = (alert: ActiveAlert) => {
    if (alert.camera) {
      return alert.camera;
    }
    if (alert.task_id) {
      return `任務 #${alert.task_id}`;
    }
    if (alert.rule_name) {
      return alert.rule_name;
    }
    return "未指定來源";
  };

  const topActiveAlerts = (activeAlertsData ?? [])
    .slice()
    .sort((a, b) => {
      const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
      const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
      return timeB - timeA;
    })
    .slice(0, 3);

  // 使用真實的攝影機數據，直接使用API返回的即時狀態
  const cameras = camerasData?.map(camera => {
    console.log('🔍 攝影機映射:', {
      原始資料: camera,
      API返回狀態: camera.status,
      最終顯示狀態: camera.status === "online" ? "online" : 
                   camera.status === "offline" ? "offline" : 
                   camera.status === "error" ? "warning" : 
                   camera.status === "inactive" ? "offline" : "offline"
    });
    return {
      id: camera.id,
      name: camera.name,
      // 直接使用API返回的即時檢測狀態，不需要額外映射
      status: camera.status === "online" ? "online" : 
              camera.status === "offline" ? "offline" : 
              camera.status === "error" ? "warning" : 
              camera.status === "inactive" ? "offline" : "offline",
      lastSeen: "即時更新"
    };
  }) || [];
  
  console.log('🔍 Dashboard - 最終攝影機列表:', cameras);

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
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <div className="text-2xl">{systemStats?.total_cameras}</div>
                <p className="text-xs text-muted-foreground">
                  線上: {systemStats?.online_cameras}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">今日警報</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <div className="text-2xl">{systemStats?.total_alerts_today}</div>
                <p className="text-xs text-muted-foreground">
                  較昨日 {systemStats?.alerts_vs_yesterday}%
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">目前運行的任務數</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <div className="text-2xl">{systemStats?.active_tasks}</div>
                <p className="text-xs text-muted-foreground">處理中的檢測任務</p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">系統運行時間</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <div className="text-2xl">{formatUptime(systemStats?.system_uptime_seconds)}</div>
                <p className="text-xs text-muted-foreground">持續穩定運行</p>
              </>
            )}
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
              {camerasLoading ? (
                // 加載狀態顯示骨架屏
                Array.from({ length: 3 }).map((_, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Skeleton className="h-4 w-4 rounded-full" />
                      <div>
                        <Skeleton className="h-4 w-24 mb-1" />
                        <Skeleton className="h-3 w-16" />
                      </div>
                    </div>
                    <Skeleton className="h-6 w-12 rounded-full" />
                  </div>
                ))
              ) : camerasError ? (
                // 錯誤狀態顯示
                <div className="text-center py-4">
                  <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">載入攝影機狀態失敗</p>
                  <p className="text-xs text-red-500">{camerasError.message}</p>
                </div>
              ) : cameras.length === 0 ? (
                // 無攝影機時的顯示
                <div className="text-center py-4">
                  <Camera className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">尚未配置攝影機</p>
                </div>
              ) : (
                // 正常狀態顯示攝影機列表
                cameras.map((camera) => (
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
                ))
              )}
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
              {activeAlertsLoading ? (
                Array.from({ length: 3 }).map((_, index) => (
                  <Alert key={`alert-skeleton-${index}`}>
                    <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                    <AlertDescription>
                      <div className="flex justify-between items-start">
                        <div className="space-y-2 w-full">
                          <Skeleton className="h-4 w-24" />
                          <Skeleton className="h-3 w-32" />
                        </div>
                        <Skeleton className="h-5 w-12 rounded-full" />
                      </div>
                    </AlertDescription>
                  </Alert>
                ))
              ) : activeAlertsError ? (
                <div className="text-sm text-destructive">
                  取得活躍警報失敗：{activeAlertsErrorInstance?.message || "請稍後再試"}
                </div>
              ) : topActiveAlerts.length === 0 ? (
                <div className="text-sm text-muted-foreground text-center py-4">
                  目前沒有活躍警報
                </div>
              ) : (
                topActiveAlerts.map((alert) => (
                  <Alert key={alert.id}>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{alert.type || alert.rule_name || "警報"}</p>
                          <p className="text-sm text-muted-foreground">
                            {getAlertSourceLabel(alert)} • {formatAlertTimestamp(alert.timestamp)}
                          </p>
                        </div>
                        <Badge variant={getSeverityBadgeVariant(alert.severity)}>
                          {getSeverityLabel(alert.severity)}
                        </Badge>
                      </div>
                    </AlertDescription>
                  </Alert>
                ))
              )}
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
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-2xl">{systemStats?.cpu_usage?.toFixed(1) || 0}%</p>
              )}
              <Progress value={systemStats?.cpu_usage || 0} className="mt-2" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">GPU 使用率</p>
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-2xl">{systemStats?.gpu_usage?.toFixed(1) || 0}%</p>
              )}
              <Progress value={systemStats?.gpu_usage || 0} className="mt-2" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">記憶體使用率</p>
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-2xl">{systemStats?.memory_usage?.toFixed(1) || 0}%</p>
              )}
              <Progress value={systemStats?.memory_usage || 0} className="mt-2" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
