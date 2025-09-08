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
import { Alert, AlertDescription } from "./ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from "./ui/dialog";
import {
  AlertTriangle,
  Bell,
  Settings,
  Mail,
  MessageSquare,
  Phone,
  Plus,
  Edit,
  Trash2,
  Check,
  X,
  Clock,
  User,
} from "lucide-react";

export function AlertManagement() {
  const [selectedAlert, setSelectedAlert] = useState<string | null>(null);
  const [isRuleDialogOpen, setIsRuleDialogOpen] = useState(false);

  // 模擬活躍警報數據
  const activeAlerts = [
    {
      id: "ALERT_001",
      type: "入侵偵測",
      camera: "大門入口",
      severity: "高",
      timestamp: "2024-01-15 14:30:25",
      description: "未授權人員進入限制區域",
      status: "未處理",
      assignee: null,
    },
    {
      id: "ALERT_002",
      type: "異常行為",
      camera: "停車場",
      severity: "中",
      timestamp: "2024-01-15 14:28:12",
      description: "可疑人員長時間逗留",
      status: "處理中",
      assignee: "操作員B",
    },
    {
      id: "ALERT_003",
      type: "設備異常",
      camera: "後門出口",
      severity: "低",
      timestamp: "2024-01-15 14:25:45",
      description: "攝影機連線不穩定",
      status: "未處理",
      assignee: null,
    },
  ];

  // 模擬警報規則數據
  const alertRules = [
    {
      id: "RULE_001",
      name: "高風險區域入侵",
      type: "入侵偵測",
      cameras: ["大門入口", "後門出口"],
      conditions: "人員在23:00-06:00期間進入",
      actions: ["發送郵件", "推送通知", "簡訊通知"],
      enabled: true,
      severity: "高",
    },
    {
      id: "RULE_002",
      name: "車輛違規停放",
      type: "車輛偵測",
      cameras: ["停車場"],
      conditions: "車輛停放超過24小時",
      actions: ["發送郵件"],
      enabled: true,
      severity: "中",
    },
    {
      id: "RULE_003",
      name: "設備離線監控",
      type: "設備異常",
      cameras: ["全部攝影機"],
      conditions: "攝影機離線超過5分鐘",
      actions: ["推送通知", "簡訊通知"],
      enabled: false,
      severity: "低",
    },
  ];

  // 模擬通知設定
  const notificationSettings = {
    email: {
      enabled: true,
      address: "admin@company.com",
      highSeverity: true,
      mediumSeverity: true,
      lowSeverity: false,
    },
    sms: {
      enabled: true,
      number: "+886-912-345-678",
      highSeverity: true,
      mediumSeverity: false,
      lowSeverity: false,
    },
    push: {
      enabled: true,
      highSeverity: true,
      mediumSeverity: true,
      lowSeverity: true,
    },
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "已處理":
        return "default";
      case "處理中":
        return "secondary";
      case "未處理":
        return "destructive";
      default:
        return "outline";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1>警報管理</h1>
        <div className="flex gap-2">
          <Dialog open={isRuleDialogOpen} onOpenChange={setIsRuleDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                新增規則
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>新增警報規則</DialogTitle>
                <DialogDescription>
                  設定新的警報規則以監控特定事件和條件
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <Label htmlFor="rule-name">規則名稱</Label>
                    <Input id="rule-name" placeholder="輸入規則名稱" />
                  </div>
                  <div>
                    <Label htmlFor="rule-type">警報類型</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="選擇警報類型" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="intrusion">入侵偵測</SelectItem>
                        <SelectItem value="behavior">異常行為</SelectItem>
                        <SelectItem value="vehicle">車輛偵測</SelectItem>
                        <SelectItem value="device">設備異常</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="rule-cameras">適用攝影機</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="選擇攝影機" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部攝影機</SelectItem>
                      <SelectItem value="cam_001">大門入口</SelectItem>
                      <SelectItem value="cam_002">停車場</SelectItem>
                      <SelectItem value="cam_003">後門出口</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="rule-conditions">觸發條件</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="選擇觸發條件" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="unknown">未知</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="rule-severity">嚴重程度</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="選擇嚴重程度" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="high">高</SelectItem>
                      <SelectItem value="medium">中</SelectItem>
                      <SelectItem value="low">低</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>通知方式</Label>
                  <div className="flex flex-wrap gap-4 mt-2">
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="email-action" />
                      <Label htmlFor="email-action">郵件通知</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="push-action" />
                      <Label htmlFor="push-action">推送通知</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="sms-action" />
                      <Label htmlFor="sms-action">簡訊通知</Label>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsRuleDialogOpen(false)}>
                    取消
                  </Button>
                  <Button onClick={() => setIsRuleDialogOpen(false)}>確認新增</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Tabs defaultValue="active-alerts">
        <TabsList>
          <TabsTrigger value="active-alerts">活躍警報</TabsTrigger>
          <TabsTrigger value="alert-rules">警報規則</TabsTrigger>
          <TabsTrigger value="notification-settings">通知設定</TabsTrigger>
        </TabsList>

        <TabsContent value="active-alerts">
          <div className="grid gap-4">
            {activeAlerts.map((alert) => (
              <Alert key={alert.id} className="border-l-4 border-l-red-500">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <div className="flex justify-between items-start">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant={getSeverityColor(alert.severity)}>
                          {alert.severity}
                        </Badge>
                        <Badge variant="outline">{alert.type}</Badge>
                        <Badge variant={getStatusColor(alert.status)}>
                          {alert.status}
                        </Badge>
                      </div>
                      <div>
                        <p className="font-medium">{alert.description}</p>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {alert.timestamp}
                          </span>
                          <span>{alert.camera}</span>
                          {alert.assignee && (
                            <span className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {alert.assignee}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {alert.status === "未處理" && (
                        <Button size="sm" variant="outline">
                          <User className="h-4 w-4 mr-1" />
                          指派
                        </Button>
                      )}
                      <Button size="sm" variant="outline">
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="alert-rules">
          <div className="space-y-4">
            {alertRules.map((rule) => (
              <Card key={rule.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          {rule.name}
                          {rule.enabled ? (
                            <Badge variant="default">啟用</Badge>
                          ) : (
                            <Badge variant="outline">停用</Badge>
                          )}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground">
                          類型: {rule.type} • 嚴重程度: {rule.severity}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Switch checked={rule.enabled} />
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-muted-foreground">適用攝影機</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {rule.cameras.map((camera) => (
                          <Badge key={camera} variant="outline">
                            {camera}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">觸發條件</p>
                      <p className="text-sm">{rule.conditions}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">通知方式</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {rule.actions.map((action) => (
                          <Badge key={action} variant="secondary">
                            {action}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="notification-settings">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* 郵件通知設定 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  郵件通知
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="email-enabled">啟用郵件通知</Label>
                  <Switch id="email-enabled" checked={notificationSettings.email.enabled} />
                </div>

                <div>
                  <Label htmlFor="email-address">郵件地址</Label>
                  <Input 
                    id="email-address" 
                    type="email" 
                    defaultValue={notificationSettings.email.address}
                    placeholder="輸入郵件地址" 
                  />
                </div>

                <div className="space-y-3">
                  <Label>通知等級</Label>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">高級別警報</span>
                      <Switch checked={notificationSettings.email.highSeverity} />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">中級別警報</span>
                      <Switch checked={notificationSettings.email.mediumSeverity} />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">低級別警報</span>
                      <Switch checked={notificationSettings.email.lowSeverity} />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 簡訊通知設定 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  簡訊通知
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="sms-enabled">啟用簡訊通知</Label>
                  <Switch id="sms-enabled" checked={notificationSettings.sms.enabled} />
                </div>

                <div>
                  <Label htmlFor="phone-number">手機號碼</Label>
                  <Input 
                    id="phone-number" 
                    type="tel" 
                    defaultValue={notificationSettings.sms.number}
                    placeholder="輸入手機號碼" 
                  />
                </div>

                <div className="space-y-3">
                  <Label>通知等級</Label>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">高級別警報</span>
                      <Switch checked={notificationSettings.sms.highSeverity} />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">中級別警報</span>
                      <Switch checked={notificationSettings.sms.mediumSeverity} />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">低級別警報</span>
                      <Switch checked={notificationSettings.sms.lowSeverity} />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 推送通知設定 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  推送通知
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="push-enabled">啟用推送通知</Label>
                  <Switch id="push-enabled" checked={notificationSettings.push.enabled} />
                </div>

                <div className="space-y-3">
                  <Label>通知等級</Label>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">高級別警報</span>
                      <Switch checked={notificationSettings.push.highSeverity} />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">中級別警報</span>
                      <Switch checked={notificationSettings.push.mediumSeverity} />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">低級別警報</span>
                      <Switch checked={notificationSettings.push.lowSeverity} />
                    </div>
                  </div>
                </div>

                <div>
                  <Label>通知聲音</Label>
                  <Select defaultValue="default">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">預設</SelectItem>
                      <SelectItem value="urgent">緊急</SelectItem>
                      <SelectItem value="soft">柔和</SelectItem>
                      <SelectItem value="silent">靜音</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline">重置</Button>
            <Button>儲存設定</Button>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}