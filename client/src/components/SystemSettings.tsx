import { useEffect, useState, useRef, ChangeEvent } from "react";
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
import {
  useSystemStats,
  useShutdownSystem,
  useRestartSystem,
  useDatabaseBackupInfo,
  useUpdateDatabaseBackupSettings,
  useRestoreDatabaseBackup,
  useClearDatabase,
  type DatabaseBackupSettingsPayload,
} from "../hooks/react-query-hooks";
import apiClient from "../lib/api";
import {
  DEFAULT_LANGUAGE,
  languageOptions,
  useLanguage,
  type LanguageCode,
} from "../lib/language";
import {
  timezoneOptions,
  useTimezone,
  type TimezoneValue,
} from "../lib/timezone";
import {
  DEFAULT_SYSTEM_NAME,
  GENERAL_CONFIG_EVENT,
  GENERAL_CONFIG_STORAGE_KEY,
} from "../lib/systemBranding";

type GeneralConfig = {
  systemName: string;
  timezone: TimezoneValue;
  language: LanguageCode;
  sessionTimeout: number;
  maxLoginAttempts: number;
};

type StorageConfig = {
  videoRetention: number;
  alertRetention: number;
  logRetention: number;
  autoCleanup: boolean;
  storageWarning: number;
  storageLimit: number;
};

type SystemConfig = {
  general: GeneralConfig;
  storage: StorageConfig;
  performance: {
    maxConcurrentStreams: number;
    videoQuality: string;
    cpuThreshold: number;
    memoryThreshold: number;
    gpuThreshold: number;
    enableGPU: boolean;
  };
  security: {
    enableSSL: boolean;
    forcePasswordChange: boolean;
    passwordExpiry: number;
    enableTwoFactor: boolean;
    ipWhitelist: boolean;
  };
};

type StorageAnalysisStats = {
  detection_size: number;
  video_size: number;
  log_size: number;
  total_size: number;
  free_space: number;
};

const BYTES_PER_TB = 1024 ** 4;
const STORAGE_ANALYSIS_REFRESH_MS = 30_000;

const normalizePercentages = (segments: number[]) => {
  const sanitized = segments.map((value) =>
    Number.isFinite(value) ? Math.max(0, value) : 0,
  );
  const total = sanitized.reduce((sum, value) => sum + value, 0);
  if (total <= 100) {
    return sanitized.map((value) => Math.min(value, 100));
  }
  return sanitized.map((value) => (value / total) * 100);
};

const defaultGeneralConfig: GeneralConfig = {
  systemName: DEFAULT_SYSTEM_NAME,
  timezone: "Asia/Taipei" as TimezoneValue,
  language: DEFAULT_LANGUAGE,
  sessionTimeout: 30,
  maxLoginAttempts: 5,
};

const defaultStorageConfig: StorageConfig = {
  videoRetention: 30,
  alertRetention: 90,
  logRetention: 180,
  autoCleanup: true,
  storageWarning: 80,
  storageLimit: 5,
};

const defaultBackupConfig: DatabaseBackupSettingsPayload = {
  backup_type: "full",
  backup_location: "C:\\Users\\yi_x\\Downloads",
  auto_backup_enabled: false,
  backup_frequency: "daily",
  retention_days: 30,
};

const loadGeneralConfig = (
  language: LanguageCode,
  timezone: TimezoneValue,
): GeneralConfig => {
  const fallback: GeneralConfig = {
    ...defaultGeneralConfig,
    language,
    timezone,
  };

  if (typeof window === "undefined") {
    return fallback;
  }

  try {
    const raw = localStorage.getItem(GENERAL_CONFIG_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        ...fallback,
        ...parsed,
        language: parsed.language ?? fallback.language,
        timezone: parsed.timezone ?? fallback.timezone,
      };
    }
  } catch (error) {
    console.warn("Failed to parse stored general config", error);
  }

  return fallback;
};

const loadStorageConfig = (): StorageConfig => {
  if (typeof window === "undefined") {
    return defaultStorageConfig;
  }

  try {
    const raw = localStorage.getItem("storageSystemConfig");
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        ...defaultStorageConfig,
        ...parsed,
      };
    }
  } catch (error) {
    console.warn("Failed to parse stored storage config", error);
  }

  return defaultStorageConfig;
};

const createInitialSystemConfig = (
  language: LanguageCode,
  timezone: TimezoneValue,
): SystemConfig => ({
  general: loadGeneralConfig(language, timezone),
  storage: loadStorageConfig(),
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
});

export function SystemSettings() {
  const [isUserDialogOpen, setIsUserDialogOpen] = useState(false);
  const [backupProgress, setBackupProgress] = useState(0);
  const [confirmingShutdown, setConfirmingShutdown] = useState(false);
  const { mutate: triggerShutdown, isPending: isShuttingDown, isSuccess: shutdownSuccess, error: shutdownError, data: shutdownData } = useShutdownSystem();
  const { mutate: triggerRestart, isPending: isRestarting, isSuccess: restartSuccess, error: restartError } = useRestartSystem();
  const { language, setLanguage, t } = useLanguage();
  const { timezone, setTimezone } = useTimezone();
  
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
  const [systemConfig, setSystemConfig] = useState<SystemConfig>(() =>
    createInitialSystemConfig(language, timezone),
  );
  const [isGeneralSaving, setIsGeneralSaving] = useState(false);
  const [saveHint, setSaveHint] = useState<{ key: string; isError?: boolean } | null>(
    null,
  );
  const [isStorageSaving, setIsStorageSaving] = useState(false);
  const [storageSaveHint, setStorageSaveHint] = useState<{ message: string; isError?: boolean } | null>(null);
  const [storageAnalysis, setStorageAnalysis] = useState<StorageAnalysisStats | null>(null);
  const [storageAnalysisLoading, setStorageAnalysisLoading] = useState(false);
  const [storageAnalysisError, setStorageAnalysisError] = useState<string | null>(null);
  const [clearConfirmText, setClearConfirmText] = useState("");
  const [clearAcknowledge, setClearAcknowledge] = useState(false);
  const [clearMessage, setClearMessage] = useState<{ text: string; isError?: boolean } | null>(null);
  const [disabledFeatureNotice, setDisabledFeatureNotice] = useState<{ open: boolean; message: string }>({
    open: false,
    message: "",
  });
  const [activeTab, setActiveTab] = useState("general");
  useEffect(() => {
    let isMounted = true;

    const fetchStorageAnalysis = async (silent = false) => {
      if (!silent) {
        setStorageAnalysisLoading(true);
      }
      try {
        const { data } = await apiClient.get<StorageAnalysisStats>(
          "/frontend/storage-analysis",
        );
        if (!isMounted) {
          return;
        }
        setStorageAnalysis(data);
        setStorageAnalysisError(null);
      } catch (error) {
        console.error("Failed to fetch storage analysis", error);
        if (!isMounted) {
          return;
        }
        setStorageAnalysisError("無法取得儲存資訊");
      } finally {
        if (isMounted && !silent) {
          setStorageAnalysisLoading(false);
        }
      }
    };

    fetchStorageAnalysis();
    const intervalId = setInterval(
      () => fetchStorageAnalysis(true),
      STORAGE_ANALYSIS_REFRESH_MS,
    );

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);
  const {
    data: backupInfo,
    isLoading: isBackupLoading,
    isFetching: isBackupFetching,
    refetch: refetchBackupInfo,
  } = useDatabaseBackupInfo(activeTab === "security");
  const updateBackupSettingsMutation = useUpdateDatabaseBackupSettings();
  const restoreBackupMutation = useRestoreDatabaseBackup();
  const clearDatabaseMutation = useClearDatabase();
  const [backupForm, setBackupForm] = useState<DatabaseBackupSettingsPayload>(defaultBackupConfig);
  const [backupMessage, setBackupMessage] = useState<{ text: string; isError?: boolean } | null>(null);
  const restoreInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setSystemConfig((prev) => ({
      ...prev,
      general: {
        ...prev.general,
        language,
      },
    }));
  }, [language]);

  useEffect(() => {
    setSystemConfig((prev) => ({
      ...prev,
      general: {
        ...prev.general,
        timezone,
      },
    }));
  }, [timezone]);

  useEffect(() => {
    if (backupInfo) {
      setBackupForm({
        backup_type: backupInfo.backup_type,
        backup_location: backupInfo.backup_location,
        auto_backup_enabled: backupInfo.auto_backup_enabled,
        backup_frequency: backupInfo.backup_frequency,
        retention_days: backupInfo.retention_days,
      });
    }
  }, [backupInfo]);

  const showDisabledFeatureNotice = (message = "此功能目前尚未啟用") => {
    setDisabledFeatureNotice({ open: true, message });
  };

  const handleDisabledFeatureNoticeChange = (open: boolean) => {
    setDisabledFeatureNotice((prev) => ({
      open,
      message: open ? prev.message : "",
    }));
  };

  const handleGeneralInputChange = (
    field: "systemName" | "timezone" | "language",
    value: string,
  ) => {
    setSystemConfig((prev) => ({
      ...prev,
      general: {
        ...prev.general,
        [field]:
          field === "language"
            ? (value as LanguageCode)
            : field === "timezone"
            ? (value as TimezoneValue)
            : value,
      },
    }));
  };

  const handleLanguageChange = (value: string) => {
    const languageCode = value as LanguageCode;
    setLanguage(languageCode);
    handleGeneralInputChange("language", languageCode);
  };

  const handleTimezoneChange = (value: string) => {
    const tzValue = value as TimezoneValue;
    setTimezone(tzValue);
    handleGeneralInputChange("timezone", tzValue);
  };

  const handleSaveGeneral = async () => {
    setIsGeneralSaving(true);
    setSaveHint(null);
    try {
      if (typeof window !== "undefined") {
        localStorage.setItem(
          GENERAL_CONFIG_STORAGE_KEY,
          JSON.stringify(systemConfig.general),
        );
        window.dispatchEvent(
          new CustomEvent(GENERAL_CONFIG_EVENT, {
            detail: { general: systemConfig.general },
          }),
        );
      }
      await new Promise((resolve) => setTimeout(resolve, 600));
      setSaveHint({ key: "systemSettings.messages.saved" });
    } catch (error) {
      console.error("Failed to save general settings", error);
      setSaveHint({ key: "systemSettings.messages.saveError", isError: true });
    } finally {
      setIsGeneralSaving(false);
    }
  };

  const handleResetGeneral = () => {
    const resetGeneral = { ...defaultGeneralConfig };
    setSystemConfig((prev) => ({
      ...prev,
      general: resetGeneral,
    }));
    if (typeof window !== "undefined") {
      localStorage.removeItem(GENERAL_CONFIG_STORAGE_KEY);
      window.dispatchEvent(
        new CustomEvent(GENERAL_CONFIG_EVENT, { detail: { general: resetGeneral } }),
      );
    }
    setLanguage(DEFAULT_LANGUAGE);
    setTimezone(defaultGeneralConfig.timezone);
    setSaveHint({ key: "systemSettings.messages.reset" });
  };

  const handleStorageInputChange = <T extends keyof StorageConfig>(
    field: T,
    value: StorageConfig[T],
  ) => {
    setSystemConfig((prev) => ({
      ...prev,
      storage: {
        ...prev.storage,
        [field]: value,
      },
    }));
  };

  const handleStorageNumberChange = <
    T extends Exclude<keyof StorageConfig, "autoCleanup">
  >(
    field: T,
    value: string,
  ) => {
    const numericValue = value === "" ? 0 : Number(value);
    handleStorageInputChange(field, numericValue as StorageConfig[T]);
  };

  const handleSaveStorage = async () => {
    setIsStorageSaving(true);
    setStorageSaveHint(null);
    try {
      if (typeof window !== "undefined") {
        localStorage.setItem("storageSystemConfig", JSON.stringify(systemConfig.storage));
      }
      await new Promise((resolve) => setTimeout(resolve, 600));
      setStorageSaveHint({ message: "儲存設定已更新" });
    } catch (error) {
      console.error("Failed to save storage settings", error);
      setStorageSaveHint({ message: "儲存失敗，請稍後再試", isError: true });
    } finally {
      setIsStorageSaving(false);
    }
  };

  const handleResetStorage = () => {
    const resetStorage = { ...defaultStorageConfig };
    setSystemConfig((prev) => ({
      ...prev,
      storage: resetStorage,
    }));
    if (typeof window !== "undefined") {
      localStorage.removeItem("storageSystemConfig");
    }
    setStorageSaveHint({ message: "已還原預設值" });
  };

  const handleBackupFormChange = <K extends keyof DatabaseBackupSettingsPayload>(
    field: K,
    value: DatabaseBackupSettingsPayload[K],
  ) => {
    let nextValue = value;
    if (field === "backup_location" && typeof value === "string") {
      nextValue = value.replace(/["']/g, "") as DatabaseBackupSettingsPayload[K];
    }
    setBackupForm((prev) => ({
      ...prev,
      [field]: nextValue,
    }));
  };

  const handleBackupSettingsSave = async () => {
    setBackupMessage(null);
    try {
      await updateBackupSettingsMutation.mutateAsync(backupForm);
      setBackupMessage({ text: "備份設定已更新" });
    } catch (error) {
      console.error("Failed to update backup settings", error);
      setBackupMessage({ text: "儲存備份設定失敗", isError: true });
    }
  };


  const handleRestoreFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setBackupMessage(null);
    try {
      const response = await restoreBackupMutation.mutateAsync(file);
      setBackupMessage({ text: response.message });
      await refetchBackupInfo();
    } catch (error) {
      console.error("Restore backup failed", error);
      setBackupMessage({ text: "還原失敗，請確認備份檔案", isError: true });
    } finally {
      event.target.value = "";
    }
  };

  const handleRestoreClick = () => {
    restoreInputRef.current?.click();
  };

  const handleClearDatabase = async () => {
    setClearMessage(null);
    try {
      const response = await clearDatabaseMutation.mutateAsync();
      setClearMessage({ text: response.message });
      setClearConfirmText("");
      setClearAcknowledge(false);
      await refetchBackupInfo();
    } catch (error) {
      console.error("Clear database failed", error);
      setClearMessage({ text: "清空失敗，請稍後再試", isError: true });
    }
  };

  const getApiRootUrl = () => {
    const baseURL = apiClient.defaults.baseURL ?? window.location.origin;
    const trimmed = baseURL.replace(/\/$/, "");
    const match = trimmed.match(/(.*)\/api\/v1$/);
    return match ? match[1] : trimmed;
  };

  const downloadBackupFile = async (downloadUrl: string, fileName?: string) => {
    if (!downloadUrl) {
      return;
    }
    const resolvedUrl = downloadUrl.startsWith("http")
      ? downloadUrl
      : `${getApiRootUrl()}${downloadUrl}`;
    const response = await fetch(resolvedUrl, { credentials: "include" });
    if (!response.ok) {
      throw new Error("下載備份失敗");
    }
    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = fileName || "database_backup.sql";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(blobUrl);
  };

  const formatBytes = (value?: number | null) => {
    if (!value || value <= 0) {
      return "0 B";
    }
    const units = ["B", "KB", "MB", "GB", "TB"];
    let index = 0;
    let size = value;
    while (size >= 1024 && index < units.length - 1) {
      size /= 1024;
      index += 1;
    }
    const digits = size >= 10 ? 1 : 2;
    return `${size.toFixed(digits)} ${units[index]}`;
  };

  const formatBackupDate = (value?: string | null) => {
    if (!value) {
      return "尚未備份";
    }
    return new Date(value).toLocaleString();
  };

  const isSavingBackupSettings = updateBackupSettingsMutation.isPending;
  const isRestoringBackup = restoreBackupMutation.isPending;
  const backupStatsLoading =
    activeTab === "security" && ((isBackupLoading && !backupInfo) || isBackupFetching);
  const clearConfirmationValid = clearConfirmText.trim().toUpperCase() === "CLEAR DATABASE";
  const isClearDatabaseDisabled =
    !clearConfirmationValid || !clearAcknowledge || clearDatabaseMutation.isPending;
  const storageLimitBytes =
    systemConfig.storage.storageLimit > 0
      ? systemConfig.storage.storageLimit * BYTES_PER_TB
      : 0;
  const displayStorageLimitBytes =
    storageLimitBytes > 0 ? storageLimitBytes : storageAnalysis?.total_size ?? 0;
  const storagePercentBase =
    displayStorageLimitBytes || storageAnalysis?.total_size || 1;
  const storageSegments = [
    { label: "影片檔案", color: "bg-blue-500", value: storageAnalysis?.video_size ?? 0 },
    { label: "系統數據", color: "bg-green-500", value: storageAnalysis?.detection_size ?? 0 },
    { label: "其他", color: "bg-orange-500", value: storageAnalysis?.log_size ?? 0 },
  ];
  const storageSegmentPercents = normalizePercentages(
    storageSegments.map((segment) => (segment.value / storagePercentBase) * 100),
  );
  const storageUsageSummary = storageAnalysis
    ? `${formatBytes(storageAnalysis.total_size)} / ${formatBytes(
        displayStorageLimitBytes || storageAnalysis.total_size,
      )}`
    : storageAnalysisLoading
    ? "載入中..."
    : "尚無資料";
  const isStorageOverLimit = Boolean(
    storageAnalysis &&
      displayStorageLimitBytes > 0 &&
      storageAnalysis.total_size > displayStorageLimitBytes,
  );

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
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <h1>{t("systemSettings.title")}</h1>
        <div className="flex flex-col items-end gap-1">
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="text-[14px]"
              disabled={isRestarting || restartSuccess}
              onClick={() => triggerRestart()}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              {isRestarting ? '重新啟動中...' : '重新啟動系統'}
            </Button>
            <div className="relative">
              {!confirmingShutdown && (
                <Button
                  variant="destructive"
                  className="text-[14px]"
                  disabled={isShuttingDown || shutdownSuccess}
                  onClick={() => setConfirmingShutdown(true)}
                >
                  <Power className="h-4 w-4 mr-2" />
                  {shutdownSuccess ? '已排程關閉' : '停止系統'}
                </Button>
              )}
              {confirmingShutdown && (
                <div className="flex gap-2">
                  <Button
                    variant="destructive"
                    className="text-[14px]"
                    disabled={isShuttingDown}
                    onClick={() => {
                      triggerShutdown();
                      setConfirmingShutdown(false);
                    }}
                  >
                    {isShuttingDown ? '執行中...' : '確認停止'}
                  </Button>
                  <Button
                    variant="outline"
                    className="text-[14px]"
                    onClick={() => setConfirmingShutdown(false)}
                    disabled={isShuttingDown}
                  >
                    取消
                  </Button>
                </div>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end text-xs min-h-[1.5rem]">
            {restartError && <span className="text-destructive">重新啟動失敗</span>}
            {restartSuccess && !restartError && (
              <span className="text-muted-foreground">系統即將重新啟動</span>
            )}
            {shutdownError && <span className="text-destructive">關閉失敗</span>}
            {shutdownSuccess && shutdownData?.scheduled_in_seconds !== undefined && (
              <span className="text-muted-foreground">
                系統將於 {shutdownData.scheduled_in_seconds}s 後關閉
              </span>
            )}
          </div>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="general">{t("systemSettings.tabs.general")}</TabsTrigger>
          <TabsTrigger value="users">{t("systemSettings.tabs.users")}</TabsTrigger>
          <TabsTrigger value="storage">{t("systemSettings.tabs.storage")}</TabsTrigger>
          <TabsTrigger value="security">{t("systemSettings.tabs.security")}</TabsTrigger>
          <TabsTrigger value="backup">{t("systemSettings.tabs.backup")}</TabsTrigger>
          <TabsTrigger value="performance">
            {t("systemSettings.tabs.performance")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                {t("systemSettings.general.title")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="system-name">
                    {t("systemSettings.fields.systemName")}
                  </Label>
                  <Input 
                    id="system-name" 
                    value={systemConfig.general.systemName}
                    onChange={(event) => handleGeneralInputChange("systemName", event.target.value)}
                    placeholder={t("systemSettings.fields.systemNamePlaceholder")} 
                  />
                </div>
                <div>
                  <Label htmlFor="timezone">
                    {t("systemSettings.fields.timezone")}
                  </Label>
                  <Select
                    value={systemConfig.general.timezone}
                    onValueChange={handleTimezoneChange}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {timezoneOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="language">
                    {t("systemSettings.fields.language")}
                  </Label>
                  <Select value={systemConfig.general.language} onValueChange={handleLanguageChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {languageOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                
              </div>

              <div className="flex flex-col items-end gap-2">
                {saveHint && (
                  <span
                    className={`text-sm ${
                      saveHint.isError ? "text-destructive" : "text-muted-foreground"
                    }`}
                  >
                    {t(saveHint.key)}
                  </span>
                )}
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleResetGeneral} disabled={isGeneralSaving}>
                    {t("systemSettings.actions.reset")}
                  </Button>
                  <Button onClick={handleSaveGeneral} disabled={isGeneralSaving}>
                    {isGeneralSaving
                      ? t("systemSettings.actions.saving")
                      : t("systemSettings.actions.save")}
                  </Button>
                </div>
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
                    value={systemConfig.storage.videoRetention}
                    onChange={(event) => handleStorageNumberChange("videoRetention", event.target.value)}
                    placeholder="30" 
                  />
                </div>
                <div>
                  <Label htmlFor="alert-retention">警報保存期限 (天)</Label>
                  <Input 
                    id="alert-retention" 
                    type="number"
                    value={systemConfig.storage.alertRetention}
                    onChange={(event) => handleStorageNumberChange("alertRetention", event.target.value)}
                    placeholder="90" 
                  />
                </div>
                <div>
                  <Label htmlFor="log-retention">日誌保存期限 (天)</Label>
                  <Input 
                    id="log-retention" 
                    type="number"
                    value={systemConfig.storage.logRetention}
                    onChange={(event) => handleStorageNumberChange("logRetention", event.target.value)}
                    placeholder="180" 
                  />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="auto-cleanup">自動清理過期檔案</Label>
                  <Switch
                    id="auto-cleanup"
                    checked={systemConfig.storage.autoCleanup}
                    onCheckedChange={(checked) => handleStorageInputChange("autoCleanup", checked)}
                  />
                </div>
                <div>
                  <Label htmlFor="storage-limit">儲存空間上限 (TB)</Label>
                  <Input 
                    id="storage-limit" 
                    type="number"
                    step="0.1"
                    value={systemConfig.storage.storageLimit}
                    onChange={(event) => handleStorageNumberChange("storageLimit", event.target.value)}
                    placeholder="5.0" 
                  />
                </div>
                <div>
                  <Label htmlFor="storage-warning">存儲空間警告閾值 (%)</Label>
                  <Input 
                    id="storage-warning" 
                    type="number"
                    value={systemConfig.storage.storageWarning}
                    onChange={(event) => handleStorageNumberChange("storageWarning", event.target.value)}
                    placeholder="80" 
                  />
                </div>
              </div>

              <div className="space-y-3">
                <h4>當前存儲狀態</h4>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>總存儲使用量</span>
                    <span>{storageUsageSummary}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                    <div className="flex h-2 bg-gray-200 rounded-full overflow-hidden dark:bg-gray-700">
                      {storageSegments.map((segment, index) => (
                        <div
                          key={segment.label}
                          className={`${segment.color} transition-all duration-300 ease-in-out`}
                          style={{ width: `${storageSegmentPercents[index] ?? 0}%` }}
                        />
                      ))}
                    </div>
                  </div>
                  {storageAnalysisError && (
                    <p className="text-xs text-destructive mt-2">{storageAnalysisError}</p>
                  )}
                  {isStorageOverLimit && (
                    <p className="text-xs text-destructive mt-2">
                      已超過設定的儲存空間上限，請調整清理策略或擴充容量。
                    </p>
                  )}
                  <div className="grid gap-2 mt-2 text-xs text-muted-foreground md:grid-cols-3">
                    {storageSegments.map((segment) => (
                      <div className="flex items-center gap-2" key={segment.label}>
                        <div className={`w-3 h-3 rounded-sm ${segment.color}`}></div>
                        {segment.label}: {storageAnalysis ? formatBytes(segment.value) : "--"}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex flex-col items-end gap-2">
                {storageSaveHint && (
                  <span
                    className={`text-sm ${
                      storageSaveHint.isError ? "text-destructive" : "text-muted-foreground"
                    }`}
                  >
                    {storageSaveHint.message}
                  </span>
                )}
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={handleResetStorage} disabled={isStorageSaving}>
                    重置
                  </Button>
                  <Button onClick={handleSaveStorage} disabled={isStorageSaving}>
                    {isStorageSaving ? "儲存中..." : "儲存設定"}
                  </Button>
                </div>
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
                  <Select
                    value={backupForm.backup_type}
                    onValueChange={(value) =>
                      handleBackupFormChange("backup_type", value as DatabaseBackupSettingsPayload["backup_type"])
                    }
                  >
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
                    value={backupForm.backup_location}
                    onChange={(event) => handleBackupFormChange("backup_location", event.target.value)}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="auto-db-backup">啟用自動備份</Label>
                  <p className="text-sm text-muted-foreground">定期自動備份資料庫</p>
                </div>
                <Switch
                  id="auto-db-backup"
                  checked={backupForm.auto_backup_enabled}
                  onCheckedChange={(checked) => handleBackupFormChange("auto_backup_enabled", checked)}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="backup-frequency">備份頻率</Label>
                  <Select
                    value={backupForm.backup_frequency}
                    onValueChange={(value) =>
                      handleBackupFormChange("backup_frequency", value as DatabaseBackupSettingsPayload["backup_frequency"])
                    }
                  >
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
                    value={backupForm.retention_days}
                    onChange={(event) => handleBackupFormChange("retention_days", Number(event.target.value) || 0)}
                  />
                </div>
              </div>

              <div className="space-y-3">
                <h4>資料庫狀態</h4>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="p-3 border rounded-lg">
                    <p className="text-sm text-muted-foreground">資料庫大小</p>
                    <p className="text-lg font-medium">
                      {backupStatsLoading ? <Skeleton className="h-6 w-20" /> : formatBytes(backupInfo?.database_size_bytes)}
                    </p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <p className="text-sm text-muted-foreground">總記錄數</p>
                    <p className="text-lg font-medium">
                      {backupStatsLoading ? (
                        <Skeleton className="h-6 w-24" />
                      ) : (
                        Math.max(0, backupInfo?.total_record_estimate ?? 0).toLocaleString()
                      )}
                    </p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <p className="text-sm text-muted-foreground">最後備份</p>
                    <p className="text-lg font-medium">
                      {backupStatsLoading ? <Skeleton className="h-6 w-28" /> : formatBackupDate(backupInfo?.last_backup_time)}
                    </p>
                  </div>
                </div>
                {backupInfo?.recent_backups?.length ? (
                  <div className="rounded-lg border p-3 text-sm text-muted-foreground">
                    <p className="font-medium mb-2 text-foreground">最近備份</p>
                    <div className="space-y-1">
                      {backupInfo.recent_backups.map((file) => (
                        <div key={file.name} className="flex justify-between">
                          <span>{file.name}</span>
                          <span>{formatBytes(file.size)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="flex flex-col items-end gap-2">
                {backupMessage && (
                  <span
                    className={`text-sm ${backupMessage.isError ? "text-destructive" : "text-muted-foreground"}`}
                  >
                    {backupMessage.text}
                  </span>
                )}
                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" onClick={handleBackupSettingsSave} disabled={isSavingBackupSettings}>
                    {isSavingBackupSettings ? "儲存中..." : "儲存設定"}
                  </Button>
                  <Button onClick={() => showDisabledFeatureNotice("系統備份功能目前尚未啟用")}>
                    <Download className="h-4 w-4 mr-2" />
                    立即備份
                  </Button>
                  <Button variant="outline" onClick={handleRestoreClick} disabled={isRestoringBackup}>
                    <Upload className="h-4 w-4 mr-2" />
                    {isRestoringBackup ? "還原中..." : "還原備份"}
                  </Button>
                </div>
                <input
                  type="file"
                  ref={restoreInputRef}
                  className="hidden"
                  accept=".sql"
                  onChange={handleRestoreFileChange}
                />
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
                        value={clearConfirmText}
                        onChange={(event) => setClearConfirmText(event.target.value)}
                      />
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="understand-risk"
                        className="rounded"
                        checked={clearAcknowledge}
                        onChange={(event) => setClearAcknowledge(event.target.checked)}
                      />
                      <Label htmlFor="understand-risk" className="text-sm">
                        我理解此操作的風險並同意繼續
                      </Label>
                    </div>

                    {clearMessage && (
                      <p
                        className={`text-sm ${
                          clearMessage.isError ? "text-destructive" : "text-muted-foreground"
                        }`}
                      >
                        {clearMessage.text}
                      </p>
                    )}

                    <Button
                      variant="destructive"
                      disabled={isClearDatabaseDisabled}
                      onClick={handleClearDatabase}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      {clearDatabaseMutation.isPending ? "清空中..." : "清空資料庫"}
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

                <Button className="w-full" onClick={() => showDisabledFeatureNotice("系統備份功能目前尚未啟用")}>
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
                    <Button
                      variant="outline"
                      className="mt-2"
                      onClick={() => showDisabledFeatureNotice("備份還原功能目前尚未啟用")}
                    >
                      選擇檔案
                    </Button>
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
        <Dialog open={disabledFeatureNotice.open} onOpenChange={handleDisabledFeatureNoticeChange}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>功能未啟用</DialogTitle>
              <DialogDescription>
                {disabledFeatureNotice.message || "此功能目前尚未啟用"}
              </DialogDescription>
            </DialogHeader>
            <div className="flex justify-end">
              <Button onClick={() => handleDisabledFeatureNoticeChange(false)}>了解</Button>
            </div>
          </DialogContent>
        </Dialog>
      </Tabs>
    </div>
  );
}
