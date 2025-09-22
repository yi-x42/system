import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Switch } from "./ui/switch";
import { Textarea } from "./ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from "./ui/dialog";
import { Progress } from "./ui/progress";
import { Skeleton } from "./ui/skeleton";
import {
  Settings,
  Users,
  Database,
  Shield,
  Download,
  Upload,
  RefreshCw,
  HardDrive,
  Wifi,
  Plus,
  Edit,
  Trash2,
  Key,
  Clock,
  Server,
  Power,
} from "lucide-react";
import { useSystemStats } from "../hooks/react-query-hooks";

export function SystemSettings() {
  const [isUserDialogOpen, setIsUserDialogOpen] = useState(false);
  const [backupProgress, setBackupProgress] = useState(0);
  
  // 獲取真實系統統計數據
  const { data: systemStats, isLoading, isError } = useSystemStats();

  // 模擬用戶數據
  const users = [
    {
      id: "user_001",
      username: "admin",
      name: "系統管理員",
      email: "admin@company.com",
      role: "管理員",
      status: "啟用",
      lastLogin: "2024-01-15 14:30:25",
      permissions: ["全部權限"],
    },
    {
      id: "user_002",
      username: "operator1",
      name: "操作員A",
      email: "operator1@company.com",
      role: "操作員",
      status: "啟用",
      lastLogin: "2024-01-15 13:45:12",
      permissions: ["查看監控", "警報處理"],
    },
    {
      id: "user_003",
      username: "viewer1",
      name: "觀察員B",
      email: "viewer1@company.com",
      role: "觀察員",
      status: "停用",
      lastLogin: "2024-01-10 09:30:00",
      permissions: ["查看監控"],
    },
  ];

  // 模擬系統配置
  const systemConfig = {
    general: {
      systemName: "智慧偵測監控系統",
      timezone: "Asia/Taipei",
      language: "zh-TW",
      sessionTimeout: 30,
      maxLoginAttempts: 5,
    },
    storage: {
      videoRetention: 30,
      alertRetention: 90,
      logRetention: 180,
      autoCleanup: true,
      storageWarning: 80,
    },
    performance: {
      maxConcurrentStreams: 20,
      videoQuality: "high",
      cpuThreshold: 80,
      memoryThreshold: 85,
      gpuThreshold: 75,
      enableGPU: true,
    },
    security: {
      enableSSL: true,
      forcePasswordChange: true,
      passwordExpiry: 90,
      enableTwoFactor: false,
      ipWhitelist: true,
    },
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case "管理員":
        return "destructive";
      case "操作員":
        return "default";
      case "觀察員":
        return "secondary";
      default:
        return "outline";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "啟用":
        return "default";
      case "停用":
        return "outline";
      default:
        return "outline";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1>系統設定</h1>
        <div className="flex gap-2">
          <div className="flex gap-2">
            <Button variant="outline" className="text-[14px]">
              <RefreshCw className="h-4 w-4 mr-2" />
              重新啟動系統
            </Button>
            <Button variant="destructive" className="text-[14px]">
              <Power className="h-4 w-4 mr-2" />
              停止系統
            </Button>
          </div>
        </div>
      </div>

      <Tabs defaultValue="general">
        <TabsList>
          <TabsTrigger value="general">一般設定</TabsTrigger>
          <TabsTrigger value="users">用戶管理</TabsTrigger>
          <TabsTrigger value="storage">存儲設定</TabsTrigger>
          <TabsTrigger value="security">資料庫管理</TabsTrigger>
          <TabsTrigger value="backup">備份還原</TabsTrigger>
          <TabsTrigger value="performance">效能監控</TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                一般系統設定
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="system-name">系統名稱</Label>
                  <Input 
                    id="system-name" 
                    defaultValue={systemConfig.general.systemName}
                    placeholder="輸入系統名稱" 
                  />
                </div>
                <div>
                  <Label htmlFor="timezone">時區</Label>
                  <Select value={systemConfig.general.timezone}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Asia/Taipei">台北 (GMT+8)</SelectItem>
                      <SelectItem value="Asia/Tokyo">東京 (GMT+9)</SelectItem>
                      <SelectItem value="Asia/Shanghai">上海 (GMT+8)</SelectItem>
                      <SelectItem value="UTC">UTC (GMT+0)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="language">系統語言</Label>
                  <Select value={systemConfig.general.language}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="zh-TW">繁體中文</SelectItem>
                      <SelectItem value="zh-CN">简体中文</SelectItem>
                      <SelectItem value="en-US">English</SelectItem>
                      <SelectItem value="ja-JP">日本語</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline">重置</Button>
                <Button>儲存設定</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3>用戶管理</h3>
              <Dialog open={isUserDialogOpen} onOpenChange={setIsUserDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    新增用戶
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>新增用戶</DialogTitle>
                    <DialogDescription>
                      建立新的系統用戶帳戶並設定權限
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <Label htmlFor="new-username">用戶名稱</Label>
                        <Input id="new-username" placeholder="輸入用戶名稱" />
                      </div>
                      <div>
                        <Label htmlFor="new-name">真實姓名</Label>
                        <Input id="new-name" placeholder="輸入真實姓名" />
                      </div>
                    </div>
                    
                    <div>
                      <Label htmlFor="new-email">電子郵件</Label>
                      <Input id="new-email" type="email" placeholder="輸入電子郵件" />
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <Label htmlFor="new-password">密碼</Label>
                        <Input id="new-password" type="password" placeholder="輸入密碼" />
                      </div>
                      <div>
                        <Label htmlFor="new-role">角色</Label>
                        <Select>
                          <SelectTrigger>
                            <SelectValue placeholder="選擇角色" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="admin">管理員</SelectItem>
                            <SelectItem value="operator">操作員</SelectItem>
                            <SelectItem value="viewer">觀察員</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="flex justify-end gap-2">
                      <Button variant="outline" onClick={() => setIsUserDialogOpen(false)}>
                        取消
                      </Button>
                      <Button onClick={() => setIsUserDialogOpen(false)}>確認新增</Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>

            <Card>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>用戶名稱</TableHead>
                      <TableHead>真實姓名</TableHead>
                      <TableHead>電子郵件</TableHead>
                      <TableHead>角色</TableHead>
                      <TableHead>狀態</TableHead>
                      <TableHead>最後登入</TableHead>
                      <TableHead>操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell>{user.username}</TableCell>
                        <TableCell>{user.name}</TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>
                          <Badge variant={getRoleColor(user.role)}>
                            {user.role}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusColor(user.status)}>
                            {user.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            <span className="text-sm">{user.lastLogin}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm">
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button variant="outline" size="sm">
                              <Key className="h-4 w-4" />
                            </Button>
                            <Button variant="outline" size="sm">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="storage">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                存儲管理設定
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <Label htmlFor="video-retention">影片保存期限 (天)</Label>
                  <Input 
                    id="video-retention" 
                    type="number"
                    defaultValue={systemConfig.storage.videoRetention}
                    placeholder="30" 
                  />
                </div>
                <div>
                  <Label htmlFor="alert-retention">警報保存期限 (天)</Label>
                  <Input 
                    id="alert-retention" 
                    type="number"
                    defaultValue={systemConfig.storage.alertRetention}
                    placeholder="90" 
                  />
                </div>
                <div>
                  <Label htmlFor="log-retention">日誌保存期限 (天)</Label>
                  <Input 
                    id="log-retention" 
                    type="number"
                    defaultValue={systemConfig.storage.logRetention}
                    placeholder="180" 
                  />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="auto-cleanup">自動清理過期檔案</Label>
                  <Switch id="auto-cleanup" checked={systemConfig.storage.autoCleanup} />
                </div>
                <div>
                  <Label htmlFor="storage-limit">儲存空間上限 (TB)</Label>
                  <Input 
                    id="storage-limit" 
                    type="number"
                    step="0.1"
                    defaultValue="5.0"
                    placeholder="5.0" 
                  />
                </div>
                <div>
                  <Label htmlFor="storage-warning">存儲空間警告閾值 (%)</Label>
                  <Input 
                    id="storage-warning" 
                    type="number"
                    defaultValue={systemConfig.storage.storageWarning}
                    placeholder="80" 
                  />
                </div>
              </div>

              <div className="space-y-3">
                <h4>當前存儲狀態</h4>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>總存儲使用量</span>
                    <span>3.2TB / 5.0TB</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                    <div className="flex h-2 bg-gray-200 rounded-full overflow-hidden dark:bg-gray-700">
                      <div className="bg-blue-500 transition-all duration-300 ease-in-out" style={{ width: '50%' }}></div>
                      <div className="bg-green-500 transition-all duration-300 ease-in-out" style={{ width: '9%' }}></div>
                      <div className="bg-orange-500 transition-all duration-300 ease-in-out" style={{ width: '5%' }}></div>
                    </div>
                  </div>
                  <div className="grid gap-2 mt-2 text-xs text-muted-foreground md:grid-cols-3">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-sm bg-blue-500"></div>
                      影片檔案: 2.5TB
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-sm bg-green-500"></div>
                      系統數據: 450GB
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-sm bg-orange-500"></div>
                      其他: 250GB
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline">重置</Button>
                <Button>儲存設定</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  資料庫備份
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <Label htmlFor="db-backup-type">備份類型</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="選擇備份類型" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="full">完整備份</SelectItem>
                        <SelectItem value="incremental">增量備份</SelectItem>
                        <SelectItem value="differential">差異備份</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="db-backup-location">備份位置</Label>
                    <Input 
                      id="db-backup-location" 
                      placeholder="/backup/database"
                      defaultValue="/backup/database"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="auto-db-backup">啟用自動備份</Label>
                    <p className="text-sm text-muted-foreground">定期自動備份資料庫</p>
                  </div>
                  <Switch id="auto-db-backup" />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <Label htmlFor="backup-frequency">備份頻率</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="選擇頻率" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="hourly">每小時</SelectItem>
                        <SelectItem value="daily">每日</SelectItem>
                        <SelectItem value="weekly">每週</SelectItem>
                        <SelectItem value="monthly">每月</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="backup-retention">備份保留期限 (天)</Label>
                    <Input 
                      id="backup-retention" 
                      type="number"
                      placeholder="30"
                      defaultValue="30"
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  <h4>資料庫狀態</h4>
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="p-3 border rounded-lg">
                      <p className="text-sm text-muted-foreground">資料庫大小</p>
                      <p className="text-lg font-medium">2.34 GB</p>
                    </div>
                    <div className="p-3 border rounded-lg">
                      <p className="text-sm text-muted-foreground">總記錄數</p>
                      <p className="text-lg font-medium">1,245,890</p>
                    </div>
                    <div className="p-3 border rounded-lg">
                      <p className="text-sm text-muted-foreground">最後備份</p>
                      <p className="text-lg font-medium">2024-01-15 03:00</p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button>
                    <Download className="h-4 w-4 mr-2" />
                    立即備份
                  </Button>
                  <Button variant="outline">
                    <Upload className="h-4 w-4 mr-2" />
                    還原備份
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-destructive">
                  <Trash2 className="h-5 w-5" />
                  危險操作
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="p-4 border-destructive/20 border rounded-lg bg-destructive/5">
                  <h4 className="text-destructive mb-2">清空資料庫</h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    此操作將永久刪除所有資料庫記錄，包括用戶數據、檢測記錄、警報歷史等。此操作無法復原。
                  </p>
                  
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="clear-confirmation">確認操作</Label>
                      <Input 
                        id="clear-confirmation" 
                        placeholder="輸入 'CLEAR DATABASE' 以確認"
                      />
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="understand-risk" className="rounded" />
                      <Label htmlFor="understand-risk" className="text-sm">
                        我理解此操作的風險並同意繼續
                      </Label>
                    </div>
                    
                    <Button variant="destructive" disabled>
                      <Trash2 className="h-4 w-4 mr-2" />
                      清空資料庫
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="backup">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Download className="h-5 w-5" />
                  系統備份
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="backup-type">備份類型</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="選擇備份類型" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="full">完整備份</SelectItem>
                      <SelectItem value="config">僅配置文件</SelectItem>
                      <SelectItem value="database">僅數據庫</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="backup-location">備份位置</Label>
                  <Input 
                    id="backup-location" 
                    placeholder="/backup/system"
                    defaultValue="/backup/system"
                  />
                </div>

                {backupProgress > 0 && (
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>備份進度</span>
                      <span>{backupProgress}%</span>
                    </div>
                    <Progress value={backupProgress} />
                  </div>
                )}

                <Button className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  立即備份
                </Button>

                <div className="space-y-2">
                  <h4>自動備份設定</h4>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">啟用自動備份</span>
                    <Switch />
                  </div>
                  <div>
                    <Label htmlFor="backup-schedule">備份頻率</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="選擇頻率" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">每日</SelectItem>
                        <SelectItem value="weekly">每週</SelectItem>
                        <SelectItem value="monthly">每月</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  系統還原
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="restore-file">選擇備份檔案</Label>
                  <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
                    <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      上傳備份檔案進行還原
                    </p>
                    <Button variant="outline" className="mt-2">選擇檔案</Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4>最近的備份</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-2 border rounded">
                      <div>
                        <p className="text-sm font-medium">完整備份 - 2024-01-15</p>
                        <p className="text-xs text-muted-foreground">大小: 2.3GB</p>
                      </div>
                      <Button variant="outline" size="sm">還原</Button>
                    </div>
                    <div className="flex justify-between items-center p-2 border rounded">
                      <div>
                        <p className="text-sm font-medium">配置備份 - 2024-01-14</p>
                        <p className="text-xs text-muted-foreground">大小: 15MB</p>
                      </div>
                      <Button variant="outline" size="sm">還原</Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="h-5 w-5" />
                  效能監控設定
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  
                  
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <Label htmlFor="cpu-threshold">CPU 使用率警告閾值 (%)</Label>
                    <Input 
                      id="cpu-threshold" 
                      type="number"
                      defaultValue={systemConfig.performance.cpuThreshold}
                      placeholder="80" 
                    />
                  </div>
                  <div>
                    <Label htmlFor="memory-threshold">記憶體使用率警告閾值 (%)</Label>
                    <Input 
                      id="memory-threshold" 
                      type="number"
                      defaultValue={systemConfig.performance.memoryThreshold}
                      placeholder="85" 
                    />
                  </div>
                  <div>
                    <Label htmlFor="gpu-threshold">GPU 使用率警告閾值 (%)</Label>
                    <Input 
                      id="gpu-threshold" 
                      type="number"
                      defaultValue={systemConfig.performance.gpuThreshold}
                      placeholder="75" 
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="enable-gpu">啟用 GPU 加速</Label>
                    <p className="text-sm text-muted-foreground">使用 GPU 加速影片處理</p>
                  </div>
                  <Switch id="enable-gpu" checked={systemConfig.performance.enableGPU} />
                </div>

                <div className="flex justify-end gap-2">
                  <Button variant="outline">重置</Button>
                  <Button>儲存設定</Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>當前系統狀態</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    {Array.from({ length: 4 }).map((_, index) => (
                      <div key={index} className="space-y-2">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-2 w-full" />
                      </div>
                    ))}
                  </div>
                ) : isError ? (
                  <div className="text-center py-4 text-muted-foreground">
                    無法載入系統狀態數據
                  </div>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>CPU 使用率</span>
                        <span>{systemStats?.cpu_usage?.toFixed(1)}%</span>
                      </div>
                      <Progress value={systemStats?.cpu_usage || 0} />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>記憶體使用率</span>
                        <span>{systemStats?.memory_usage?.toFixed(1)}%</span>
                      </div>
                      <Progress value={systemStats?.memory_usage || 0} />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>GPU 使用率</span>
                        <span>{systemStats?.gpu_usage?.toFixed(1)}%</span>
                      </div>
                      <Progress value={systemStats?.gpu_usage || 0} />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>網路使用率</span>
                        <span>{systemStats?.network_usage?.toFixed(2)} MB/s</span>
                      </div>
                      <Progress value={Math.min((systemStats?.network_usage || 0) * 10, 100)} />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}