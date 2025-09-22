import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Pagination, PaginationContent, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from "./ui/pagination";
import {
  Search,
  Filter,
  Download,
  Eye,
  Calendar,
  Clock,
  Camera,
  AlertTriangle,
  Play,
  FileText,
  Database,
} from "lucide-react";

export function RecordQuery() {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");

  // 模擬偵測記錄數據
  const detectionRecords = [
    {
      id: "DET_001",
      timestamp: "2024-01-15 14:30:25",
      camera: "大門入口",
      type: "人員偵測",
      object: "person",
      confidence: 0.95,
      thumbnail: "/api/placeholder/80/60",
      status: "confirmed",
    },
    {
      id: "DET_002",
      timestamp: "2024-01-15 14:28:12",
      camera: "停車場",
      type: "車輛偵測",
      object: "car",
      confidence: 0.88,
      thumbnail: "/api/placeholder/80/60",
      status: "pending",
    },
    {
      id: "DET_003",
      timestamp: "2024-01-15 14:25:45",
      camera: "後門出口",
      type: "異常行為",
      object: "person",
      confidence: 0.92,
      thumbnail: "/api/placeholder/80/60",
      status: "false_positive",
    },
    {
      id: "DET_004",
      timestamp: "2024-01-15 14:20:33",
      camera: "走廊A",
      type: "移動偵測",
      object: "person",
      confidence: 0.87,
      thumbnail: "/api/placeholder/80/60",
      status: "confirmed",
    },
    {
      id: "DET_005",
      timestamp: "2024-01-15 14:15:18",
      camera: "停車場",
      type: "車輛偵測",
      object: "motorcycle",
      confidence: 0.91,
      thumbnail: "/api/placeholder/80/60",
      status: "confirmed",
    },
  ];

  // 模擬警報記錄數據
  const alertRecords = [
    {
      id: "ALERT_001",
      timestamp: "2024-01-15 14:30:25",
      camera: "大門入口",
      type: "入侵偵測",
      severity: "高",
      description: "未授權人員進入限制區域",
      status: "已處理",
      handler: "管理員A",
    },
    {
      id: "ALERT_002",
      timestamp: "2024-01-15 14:28:12",
      camera: "停車場",
      type: "異常行為",
      severity: "中",
      description: "可疑人員長時間逗留",
      status: "處理中",
      handler: "操作員B",
    },
    {
      id: "ALERT_003",
      timestamp: "2024-01-15 14:25:45",
      camera: "後門出口",
      type: "設備異常",
      severity: "低",
      description: "攝影機連線不穩定",
      status: "未處理",
      handler: "-",
    },
  ];

  // 模擬系統日誌數據
  const systemLogs = [
    {
      id: "LOG_001",
      timestamp: "2024-01-15 14:30:25",
      level: "INFO",
      module: "Detection Service",
      message: "YOLO模型初始化完成",
      user: "system",
    },
    {
      id: "LOG_002",
      timestamp: "2024-01-15 14:29:18",
      level: "WARNING",
      module: "Camera Service",
      message: "攝影機 CAM_003 連線逾時",
      user: "system",
    },
    {
      id: "LOG_003",
      timestamp: "2024-01-15 14:28:45",
      level: "ERROR",
      module: "Storage Service",
      message: "磁碟空間不足警告",
      user: "system",
    },
    {
      id: "LOG_004",
      timestamp: "2024-01-15 14:27:32",
      level: "INFO",
      module: "User Service",
      message: "用戶 admin 登入系統",
      user: "admin",
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "confirmed":
      case "已處理":
        return "default";
      case "pending":
      case "處理中":
        return "secondary";
      case "false_positive":
      case "未處理":
        return "outline";
      default:
        return "outline";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "confirmed":
        return "已確認";
      case "pending":
        return "待確認";
      case "false_positive":
        return "誤報";
      default:
        return status;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "高":
        return "destructive";
      case "中":
        return "secondary";
      case "低":
        return "outline";
      default:
        return "outline";
    }
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case "ERROR":
        return "destructive";
      case "WARNING":
        return "secondary";
      case "INFO":
        return "default";
      default:
        return "outline";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1>紀錄查詢</h1>
        <div className="flex gap-2">
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            進階篩選
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            匯出資料
          </Button>
        </div>
      </div>

      {/* 搜尋和篩選區域 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            搜尋條件
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <Label htmlFor="search-query">關鍵字搜尋</Label>
              <Input
                id="search-query"
                placeholder="輸入搜尋關鍵字..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="date-from">開始日期</Label>
              <Input id="date-from" type="date" />
            </div>
            <div>
              <Label htmlFor="date-to">結束日期</Label>
              <Input id="date-to" type="date" />
            </div>
            <div>
              <Label htmlFor="camera-filter">攝影機</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="選擇攝影機" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部攝影機</SelectItem>
                  <SelectItem value="cam_001">大門入口</SelectItem>
                  <SelectItem value="cam_002">停車場</SelectItem>
                  <SelectItem value="cam_003">後門出口</SelectItem>
                  <SelectItem value="cam_004">走廊A</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline">重置</Button>
            <Button>
              <Search className="h-4 w-4 mr-2" />
              搜尋
            </Button>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="detection-records">
        <TabsList>
          <TabsTrigger value="detection-records">偵測記錄</TabsTrigger>
          <TabsTrigger value="alert-records">警報記錄</TabsTrigger>
          <TabsTrigger value="system-logs">系統日誌</TabsTrigger>
        </TabsList>

        <TabsContent value="detection-records">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                偵測記錄查詢
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>時間</TableHead>
                    <TableHead>偵測來源</TableHead>
                    <TableHead>偵測類型</TableHead>
                    <TableHead>信心度</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {detectionRecords.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3 text-muted-foreground" />
                          <span className="text-sm">{record.timestamp}</span>
                        </div>
                      </TableCell>
                      <TableCell>{record.camera}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{record.type}</Badge>
                      </TableCell>
                      <TableCell>{(record.confidence * 100).toFixed(1)}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              <div className="flex justify-between items-center mt-4">
                <p className="text-sm text-muted-foreground">
                  顯示第 1-5 筆，共 156 筆記錄
                </p>
                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious href="#" />
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationLink href="#" isActive>1</PaginationLink>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationLink href="#">2</PaginationLink>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationLink href="#">3</PaginationLink>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationNext href="#" />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alert-records">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                警報記錄查詢
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>時間</TableHead>
                    <TableHead>攝影機</TableHead>
                    <TableHead>警報類型</TableHead>
                    <TableHead>嚴重程度</TableHead>
                    <TableHead>描述</TableHead>
                    <TableHead>狀態</TableHead>
                    <TableHead>處理人員</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alertRecords.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3 text-muted-foreground" />
                          <span className="text-sm">{record.timestamp}</span>
                        </div>
                      </TableCell>
                      <TableCell>{record.camera}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{record.type}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getSeverityColor(record.severity)}>
                          {record.severity}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">{record.description}</TableCell>
                      <TableCell>
                        <Badge variant={getStatusColor(record.status)}>
                          {record.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{record.handler}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <FileText className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              <div className="flex justify-between items-center mt-4">
                <p className="text-sm text-muted-foreground">
                  顯示第 1-3 筆，共 89 筆記錄
                </p>
                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious href="#" />
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationLink href="#" isActive>1</PaginationLink>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationLink href="#">2</PaginationLink>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationNext href="#" />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system-logs">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                系統日誌查詢
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <Select defaultValue="all">
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="選擇日誌等級" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全部等級</SelectItem>
                    <SelectItem value="error">ERROR</SelectItem>
                    <SelectItem value="warning">WARNING</SelectItem>
                    <SelectItem value="info">INFO</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>時間</TableHead>
                    <TableHead>等級</TableHead>
                    <TableHead>模組</TableHead>
                    <TableHead>訊息</TableHead>
                    <TableHead>用戶</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {systemLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3 text-muted-foreground" />
                          <span className="text-sm">{log.timestamp}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getLogLevelColor(log.level)}>
                          {log.level}
                        </Badge>
                      </TableCell>
                      <TableCell>{log.module}</TableCell>
                      <TableCell className="max-w-md truncate">{log.message}</TableCell>
                      <TableCell>{log.user}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              <div className="flex justify-between items-center mt-4">
                <p className="text-sm text-muted-foreground">
                  顯示第 1-4 筆，共 234 筆記錄
                </p>
                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious href="#" />
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationLink href="#" isActive>1</PaginationLink>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationLink href="#">2</PaginationLink>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationLink href="#">3</PaginationLink>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationNext href="#" />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}