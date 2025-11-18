import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from "recharts";
import { Download, Filter } from "lucide-react";
import { useCameraPerformance } from "../hooks/react-query-hooks";

const RANGE_DAY_MAP = {
  "1day": 1,
  "7days": 7,
  "30days": 30,
  "90days": 90,
} as const;

type RangeOption = keyof typeof RANGE_DAY_MAP;

const STATUS_LABEL_MAP: Record<string, string> = {
  running: "正常運行",
  pending: "待啟動",
  completed: "已完成",
  failed: "異常",
};

const STATUS_VARIANT_MAP: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  running: "default",
  pending: "secondary",
  completed: "secondary",
  failed: "destructive",
};

export function StatisticalAnalysis() {
  const [range, setRange] = useState<RangeOption>("7days");
  const selectedDays = RANGE_DAY_MAP[range];
  const {
    data: cameraPerformance = [],
    isLoading: cameraPerformanceLoading,
    isError: cameraPerformanceError,
  } = useCameraPerformance({ days: selectedDays, limit: 5 });

  // 模擬統計數據
  const dailyDetections = [
    { date: "01/01", person: 145, vehicle: 89, total: 234 },
    { date: "01/02", person: 162, vehicle: 93, total: 255 },
    { date: "01/03", person: 178, vehicle: 85, total: 263 },
    { date: "01/04", person: 155, vehicle: 91, total: 246 },
    { date: "01/05", person: 189, vehicle: 97, total: 286 },
    { date: "01/06", person: 203, vehicle: 102, total: 305 },
    { date: "01/07", person: 195, vehicle: 88, total: 283 },
  ];

  const hourlyActivity = [
    { hour: "00", count: 12 },
    { hour: "01", count: 8 },
    { hour: "02", count: 5 },
    { hour: "03", count: 3 },
    { hour: "04", count: 7 },
    { hour: "05", count: 15 },
    { hour: "06", count: 25 },
    { hour: "07", count: 45 },
    { hour: "08", count: 67 },
    { hour: "09", count: 82 },
    { hour: "10", count: 95 },
    { hour: "11", count: 88 },
    { hour: "12", count: 102 },
    { hour: "13", count: 94 },
    { hour: "14", count: 89 },
    { hour: "15", count: 76 },
    { hour: "16", count: 85 },
    { hour: "17", count: 98 },
    { hour: "18", count: 112 },
    { hour: "19", count: 89 },
    { hour: "20", count: 67 },
    { hour: "21", count: 45 },
    { hour: "22", count: 32 },
    { hour: "23", count: 18 },
  ];

  const detectionTypes = [
    { name: "人員", value: 1245, color: "#8884d8" },
    { name: "車輛", value: 632, color: "#82ca9d" },
    { name: "自行車", value: 189, color: "#ffc658" },
    { name: "其他", value: 94, color: "#ff7c7c" },
  ];

  const alertTrends = [
    { date: "01/01", high: 8, medium: 15, low: 23 },
    { date: "01/02", high: 12, medium: 18, low: 19 },
    { date: "01/03", high: 6, medium: 22, low: 25 },
    { date: "01/04", high: 9, medium: 16, low: 21 },
    { date: "01/05", high: 14, medium: 20, low: 18 },
    { date: "01/06", high: 11, medium: 24, low: 22 },
    { date: "01/07", high: 7, medium: 19, low: 26 },
  ];

  const COLORS = ["#8884d8", "#82ca9d", "#ffc658", "#ff7c7c"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1>統計分析</h1>
        <div className="flex gap-2">
          <Select value={range} onValueChange={(value: RangeOption) => setRange(value)}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1day">今日</SelectItem>
              <SelectItem value="7days">近7天</SelectItem>
              <SelectItem value="30days">近30天</SelectItem>
              <SelectItem value="90days">近90天</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            篩選
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            匯出報告
          </Button>
        </div>
      </div>

      {/* 關鍵指標概覽 */}
      

      <Tabs defaultValue="camera-performance">
        <TabsList>
          <TabsTrigger value="camera-performance">攝影機效能</TabsTrigger>
          <TabsTrigger value="alert-analysis">警報分析</TabsTrigger>
          <TabsTrigger value="time-analysis">時間分析</TabsTrigger>
        </TabsList>

        <TabsContent value="camera-performance">
          <Card>
            <CardHeader>
              <CardTitle>攝影機效能分析</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {cameraPerformanceLoading && (
                  <p className="text-sm text-muted-foreground">載入攝影機效能中...</p>
                )}
                {cameraPerformanceError && (
                  <p className="text-sm text-destructive">無法取得攝影機效能資料</p>
                )}
                {!cameraPerformanceLoading && !cameraPerformanceError && cameraPerformance.length === 0 && (
                  <p className="text-sm text-muted-foreground">選定期間內沒有攝影機偵測紀錄。</p>
                )}
                {!cameraPerformanceLoading &&
                  !cameraPerformanceError &&
                  cameraPerformance.map((camera) => {
                    const statusKey = camera.status ?? "unknown";
                    const statusLabel = STATUS_LABEL_MAP[statusKey] ?? "未知狀態";
                    const statusVariant = STATUS_VARIANT_MAP[statusKey] ?? "outline";
                    const runtimeLabel = `${(camera.runtime_hours ?? 0).toFixed(1)} 小時`;
                    const cameraName = camera.camera_name || camera.camera_id || "未命名攝影機";
                    const key = camera.camera_id ?? camera.camera_name ?? `${camera.detections}-${runtimeLabel}`;

                    return (
                      <div key={key} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                          <h4 className="font-medium">{cameraName}</h4>
                          <Badge variant="outline">{camera.detections} 次偵測</Badge>
                        </div>
                        <div className="grid gap-4 md:grid-cols-2">
                          <div>
                            <p className="text-sm text-muted-foreground">運行時間</p>
                            <p>{runtimeLabel}</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">狀態</p>
                            <Badge variant={statusVariant}>{statusLabel}</Badge>
                          </div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alert-analysis">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>警報趨勢分析</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={alertTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="high"
                      stackId="1"
                      stroke="#ff4d4f"
                      fill="#ff4d4f"
                      name="高級別"
                    />
                    <Area
                      type="monotone"
                      dataKey="medium"
                      stackId="1"
                      stroke="#faad14"
                      fill="#faad14"
                      name="中級別"
                    />
                    <Area
                      type="monotone"
                      dataKey="low"
                      stackId="1"
                      stroke="#52c41a"
                      fill="#52c41a"
                      name="低級別"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>警報分類統計</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>入侵偵測</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div className="bg-red-500 h-2 rounded-full w-3/4"></div>
                      </div>
                      <span className="text-sm">75</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>異常行為</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div className="bg-orange-500 h-2 rounded-full w-1/2"></div>
                      </div>
                      <span className="text-sm">42</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>移動偵測</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div className="bg-yellow-500 h-2 rounded-full w-1/3"></div>
                      </div>
                      <span className="text-sm">28</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>設備異常</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-500 h-2 rounded-full w-1/6"></div>
                      </div>
                      <span className="text-sm">11</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="time-analysis">
          <Card>
            <CardHeader>
              <CardTitle>24小時活動分析</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={hourlyActivity}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#8884d8"
                    strokeWidth={2}
                    dot={{ fill: "#8884d8" }}
                    name="偵測次數"
                  />
                </LineChart>
              </ResponsiveContainer>
              <div className="mt-4 grid gap-4 md:grid-cols-3">
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">高峰時段</p>
                  <p className="text-lg">18:00 - 19:00</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">低峰時段</p>
                  <p className="text-lg">03:00 - 04:00</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">平均每小時</p>
                  <p className="text-lg">58 次</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}