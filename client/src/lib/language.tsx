import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

export const languageOptions = [
  { value: "zh-TW", label: "繁體中文" },
  { value: "zh-CN", label: "簡體中文" },
  { value: "en-US", label: "English (US)" },
  { value: "ja-JP", label: "日本語" },
  { value: "ko-KR", label: "한국어" },
  { value: "th-TH", label: "ภาษาไทย" },
  { value: "vi-VN", label: "Tiếng Việt" },
  { value: "id-ID", label: "Bahasa Indonesia" },
  { value: "es-ES", label: "Español" },
] as const;

export type LanguageCode = (typeof languageOptions)[number]["value"];

export const DEFAULT_LANGUAGE: LanguageCode = "zh-TW";
const LANGUAGE_STORAGE_KEY = "systemLanguage";

type LanguageContextValue = {
  language: LanguageCode;
  setLanguage: (language: LanguageCode) => void;
  t: (key: string) => string;
};

const translationTable: Partial<Record<LanguageCode, Record<string, string>>> = {
  "zh-TW": {
    "sidebar.brand.title": "智慧偵測系統",
    "sidebar.brand.subtitle": "監控管理平台",
    "sidebar.group.systemMonitoring": "系統監控",
    "sidebar.group.analytics": "分析與統計",
    "sidebar.group.data": "數據管理",
    "sidebar.group.settings": "系統配置",
    "sidebar.item.dashboard": "儀表板",
    "sidebar.item.cameraControl": "攝影機控制中心",
    "sidebar.item.detectionAnalysis": "任務配置",
    "sidebar.item.statisticalAnalysis": "統計分析",
    "sidebar.item.recordQuery": "紀錄查詢",
    "sidebar.item.alertManagement": "警報管理",
    "sidebar.item.systemSettings": "系統設定",
    "systemSettings.title": "系統設定",
    "systemSettings.general.title": "一般系統設定",
    "systemSettings.fields.systemName": "系統名稱",
    "systemSettings.fields.systemNamePlaceholder": "輸入系統名稱",
    "systemSettings.fields.timezone": "時區",
    "systemSettings.fields.language": "系統語言",
    "systemSettings.actions.reset": "重置",
    "systemSettings.actions.save": "儲存設定",
    "systemSettings.actions.saving": "儲存中...",
    "systemSettings.messages.saved": "設定已儲存",
    "systemSettings.messages.saveError": "儲存失敗，請稍後再試",
    "systemSettings.messages.reset": "已恢復預設值",
    "systemSettings.tabs.general": "一般設定",
    "systemSettings.tabs.users": "用戶管理",
    "systemSettings.tabs.storage": "存儲設定",
    "systemSettings.tabs.security": "資料庫管理",
    "systemSettings.tabs.backup": "備份還原",
    "systemSettings.tabs.performance": "效能監控",
  },
  "zh-CN": {
    "sidebar.brand.title": "智慧检测系统",
    "sidebar.brand.subtitle": "监控管理平台",
    "sidebar.group.systemMonitoring": "系统监控",
    "sidebar.group.analytics": "分析与统计",
    "sidebar.group.data": "数据管理",
    "sidebar.group.settings": "系统配置",
    "sidebar.item.dashboard": "仪表板",
    "sidebar.item.cameraControl": "摄像机控制中心",
    "sidebar.item.detectionAnalysis": "任务配置",
    "sidebar.item.statisticalAnalysis": "统计分析",
    "sidebar.item.recordQuery": "记录查询",
    "sidebar.item.alertManagement": "警报管理",
    "sidebar.item.systemSettings": "系统设置",
    "systemSettings.title": "系统设置",
    "systemSettings.general.title": "一般系统设置",
    "systemSettings.fields.systemName": "系统名称",
    "systemSettings.fields.systemNamePlaceholder": "输入系统名称",
    "systemSettings.fields.timezone": "时区",
    "systemSettings.fields.language": "系统语言",
    "systemSettings.actions.reset": "重置",
    "systemSettings.actions.save": "保存设置",
    "systemSettings.actions.saving": "保存中...",
    "systemSettings.messages.saved": "设置已保存",
    "systemSettings.messages.saveError": "保存失败，请稍后再试",
    "systemSettings.messages.reset": "已恢复默认值",
    "systemSettings.tabs.general": "常规设置",
    "systemSettings.tabs.users": "用户管理",
    "systemSettings.tabs.storage": "存储设置",
    "systemSettings.tabs.security": "数据库管理",
    "systemSettings.tabs.backup": "备份还原",
    "systemSettings.tabs.performance": "性能监控",
  },
  "en-US": {
    "sidebar.brand.title": "Smart Detection System",
    "sidebar.brand.subtitle": "Monitoring Console",
    "sidebar.group.systemMonitoring": "System Monitoring",
    "sidebar.group.analytics": "Analytics & Reports",
    "sidebar.group.data": "Data Management",
    "sidebar.group.settings": "System Settings",
    "sidebar.item.dashboard": "Dashboard",
    "sidebar.item.cameraControl": "Camera Control",
    "sidebar.item.detectionAnalysis": "Task Configuration",
    "sidebar.item.statisticalAnalysis": "Statistics",
    "sidebar.item.recordQuery": "Record Query",
    "sidebar.item.alertManagement": "Alert Management",
    "sidebar.item.systemSettings": "System Settings",
    "systemSettings.title": "System Settings",
    "systemSettings.general.title": "General Configuration",
    "systemSettings.fields.systemName": "System Name",
    "systemSettings.fields.systemNamePlaceholder": "Enter a system name",
    "systemSettings.fields.timezone": "Time Zone",
    "systemSettings.fields.language": "System Language",
    "systemSettings.actions.reset": "Reset",
    "systemSettings.actions.save": "Save Settings",
    "systemSettings.actions.saving": "Saving...",
    "systemSettings.messages.saved": "Settings saved",
    "systemSettings.messages.saveError": "Unable to save, please try again",
    "systemSettings.messages.reset": "Restored defaults",
    "systemSettings.tabs.general": "General",
    "systemSettings.tabs.users": "Users",
    "systemSettings.tabs.storage": "Storage",
    "systemSettings.tabs.security": "Database",
    "systemSettings.tabs.backup": "Backup & Restore",
    "systemSettings.tabs.performance": "Performance",
  },
  "ja-JP": {
    "sidebar.brand.title": "スマート検知システム",
    "sidebar.brand.subtitle": "監視管理プラットフォーム",
    "sidebar.group.systemMonitoring": "システム監視",
    "sidebar.group.analytics": "分析と統計",
    "sidebar.group.data": "データ管理",
    "sidebar.group.settings": "システム設定",
    "sidebar.item.dashboard": "ダッシュボード",
    "sidebar.item.cameraControl": "カメラ制御",
    "sidebar.item.detectionAnalysis": "タスク設定",
    "sidebar.item.statisticalAnalysis": "統計分析",
    "sidebar.item.recordQuery": "記録検索",
    "sidebar.item.alertManagement": "アラート管理",
    "sidebar.item.systemSettings": "システム設定",
    "systemSettings.title": "システム設定",
    "systemSettings.general.title": "一般システム設定",
    "systemSettings.fields.systemName": "システム名",
    "systemSettings.fields.systemNamePlaceholder": "システム名を入力",
    "systemSettings.fields.timezone": "タイムゾーン",
    "systemSettings.fields.language": "システム言語",
    "systemSettings.actions.reset": "リセット",
    "systemSettings.actions.save": "設定を保存",
    "systemSettings.actions.saving": "保存中...",
    "systemSettings.messages.saved": "設定を保存しました",
    "systemSettings.messages.saveError": "保存に失敗しました。後でもう一度お試しください",
    "systemSettings.messages.reset": "既定値に戻しました",
    "systemSettings.tabs.general": "一般設定",
    "systemSettings.tabs.users": "ユーザー管理",
    "systemSettings.tabs.storage": "ストレージ設定",
    "systemSettings.tabs.security": "データベース管理",
    "systemSettings.tabs.backup": "バックアップと復元",
    "systemSettings.tabs.performance": "パフォーマンス監視",
  },
  "ko-KR": {
    "sidebar.brand.title": "스마트 감지 시스템",
    "sidebar.brand.subtitle": "모니터링 관리 플랫폼",
    "sidebar.group.systemMonitoring": "시스템 모니터링",
    "sidebar.group.analytics": "분석 및 통계",
    "sidebar.group.data": "데이터 관리",
    "sidebar.group.settings": "시스템 설정",
    "sidebar.item.dashboard": "대시보드",
    "sidebar.item.cameraControl": "카메라 제어",
    "sidebar.item.detectionAnalysis": "작업 구성",
    "sidebar.item.statisticalAnalysis": "통계 분석",
    "sidebar.item.recordQuery": "기록 조회",
    "sidebar.item.alertManagement": "알림 관리",
    "sidebar.item.systemSettings": "시스템 설정",
    "systemSettings.title": "시스템 설정",
    "systemSettings.general.title": "일반 시스템 설정",
    "systemSettings.fields.systemName": "시스템 이름",
    "systemSettings.fields.systemNamePlaceholder": "시스템 이름을 입력하세요",
    "systemSettings.fields.timezone": "시간대",
    "systemSettings.fields.language": "시스템 언어",
    "systemSettings.actions.reset": "초기화",
    "systemSettings.actions.save": "설정 저장",
    "systemSettings.actions.saving": "저장 중...",
    "systemSettings.messages.saved": "설정이 저장되었습니다",
    "systemSettings.messages.saveError": "저장에 실패했습니다. 잠시 후 다시 시도하세요",
    "systemSettings.messages.reset": "기본값으로 복원되었습니다",
    "systemSettings.tabs.general": "일반 설정",
    "systemSettings.tabs.users": "사용자 관리",
    "systemSettings.tabs.storage": "스토리지 설정",
    "systemSettings.tabs.security": "데이터베이스 관리",
    "systemSettings.tabs.backup": "백업 및 복구",
    "systemSettings.tabs.performance": "성능 모니터링",
  },
  "th-TH": {
    "sidebar.brand.title": "ระบบตรวจจับอัจฉริยะ",
    "sidebar.brand.subtitle": "แพลตฟอร์มจัดการการเฝ้าระวัง",
    "sidebar.group.systemMonitoring": "การเฝ้าระวังระบบ",
    "sidebar.group.analytics": "การวิเคราะห์และสถิติ",
    "sidebar.group.data": "การจัดการข้อมูล",
    "sidebar.group.settings": "การตั้งค่าระบบ",
    "sidebar.item.dashboard": "แดชบอร์ด",
    "sidebar.item.cameraControl": "ศูนย์ควบคุมกล้อง",
    "sidebar.item.detectionAnalysis": "ตั้งค่างาน",
    "sidebar.item.statisticalAnalysis": "การวิเคราะห์สถิติ",
    "sidebar.item.recordQuery": "ค้นหาบันทึก",
    "sidebar.item.alertManagement": "จัดการแจ้งเตือน",
    "sidebar.item.systemSettings": "ตั้งค่าระบบ",
    "systemSettings.title": "ตั้งค่าระบบ",
    "systemSettings.general.title": "การตั้งค่าทั่วไป",
    "systemSettings.fields.systemName": "ชื่อระบบ",
    "systemSettings.fields.systemNamePlaceholder": "กรอกชื่อระบบ",
    "systemSettings.fields.timezone": "โซนเวลา",
    "systemSettings.fields.language": "ภาษาของระบบ",
    "systemSettings.actions.reset": "รีเซ็ต",
    "systemSettings.actions.save": "บันทึกการตั้งค่า",
    "systemSettings.actions.saving": "กำลังบันทึก...",
    "systemSettings.messages.saved": "บันทึกการตั้งค่าแล้ว",
    "systemSettings.messages.saveError": "บันทึกไม่สำเร็จ โปรดลองใหม่อีกครั้ง",
    "systemSettings.messages.reset": "คืนค่าเป็นค่าเริ่มต้นแล้ว",
    "systemSettings.tabs.general": "ทั่วไป",
    "systemSettings.tabs.users": "จัดการผู้ใช้",
    "systemSettings.tabs.storage": "การตั้งค่าที่เก็บข้อมูล",
    "systemSettings.tabs.security": "จัดการฐานข้อมูล",
    "systemSettings.tabs.backup": "สำรองและกู้คืน",
    "systemSettings.tabs.performance": "ติดตามประสิทธิภาพ",
  },
  "vi-VN": {
    "sidebar.brand.title": "Hệ thống Giám sát Thông minh",
    "sidebar.brand.subtitle": "Nền tảng quản lý giám sát",
    "sidebar.group.systemMonitoring": "Giám sát hệ thống",
    "sidebar.group.analytics": "Phân tích & Thống kê",
    "sidebar.group.data": "Quản lý dữ liệu",
    "sidebar.group.settings": "Cấu hình hệ thống",
    "sidebar.item.dashboard": "Bảng điều khiển",
    "sidebar.item.cameraControl": "Điều khiển camera",
    "sidebar.item.detectionAnalysis": "Cấu hình nhiệm vụ",
    "sidebar.item.statisticalAnalysis": "Phân tích thống kê",
    "sidebar.item.recordQuery": "Tra cứu bản ghi",
    "sidebar.item.alertManagement": "Quản lý cảnh báo",
    "sidebar.item.systemSettings": "Cài đặt hệ thống",
    "systemSettings.title": "Cài đặt hệ thống",
    "systemSettings.general.title": "Cấu hình chung",
    "systemSettings.fields.systemName": "Tên hệ thống",
    "systemSettings.fields.systemNamePlaceholder": "Nhập tên hệ thống",
    "systemSettings.fields.timezone": "Múi giờ",
    "systemSettings.fields.language": "Ngôn ngữ hệ thống",
    "systemSettings.actions.reset": "Đặt lại",
    "systemSettings.actions.save": "Lưu cài đặt",
    "systemSettings.actions.saving": "Đang lưu...",
    "systemSettings.messages.saved": "Đã lưu cài đặt",
    "systemSettings.messages.saveError": "Lưu thất bại, vui lòng thử lại sau",
    "systemSettings.messages.reset": "Đã khôi phục mặc định",
    "systemSettings.tabs.general": "Chung",
    "systemSettings.tabs.users": "Quản lý người dùng",
    "systemSettings.tabs.storage": "Cài đặt lưu trữ",
    "systemSettings.tabs.security": "Quản lý cơ sở dữ liệu",
    "systemSettings.tabs.backup": "Sao lưu & Khôi phục",
    "systemSettings.tabs.performance": "Theo dõi hiệu năng",
  },
  "id-ID": {
    "sidebar.brand.title": "Sistem Deteksi Cerdas",
    "sidebar.brand.subtitle": "Platform manajemen pemantauan",
    "sidebar.group.systemMonitoring": "Pemantauan Sistem",
    "sidebar.group.analytics": "Analitik & Statistik",
    "sidebar.group.data": "Manajemen Data",
    "sidebar.group.settings": "Konfigurasi Sistem",
    "sidebar.item.dashboard": "Dasbor",
    "sidebar.item.cameraControl": "Kontrol Kamera",
    "sidebar.item.detectionAnalysis": "Konfigurasi Tugas",
    "sidebar.item.statisticalAnalysis": "Analisis Statistik",
    "sidebar.item.recordQuery": "Pencarian Rekaman",
    "sidebar.item.alertManagement": "Manajemen Peringatan",
    "sidebar.item.systemSettings": "Pengaturan Sistem",
    "systemSettings.title": "Pengaturan Sistem",
    "systemSettings.general.title": "Konfigurasi Umum",
    "systemSettings.fields.systemName": "Nama Sistem",
    "systemSettings.fields.systemNamePlaceholder": "Masukkan nama sistem",
    "systemSettings.fields.timezone": "Zona Waktu",
    "systemSettings.fields.language": "Bahasa Sistem",
    "systemSettings.actions.reset": "Atur Ulang",
    "systemSettings.actions.save": "Simpan Pengaturan",
    "systemSettings.actions.saving": "Menyimpan...",
    "systemSettings.messages.saved": "Pengaturan tersimpan",
    "systemSettings.messages.saveError": "Gagal menyimpan, coba lagi",
    "systemSettings.messages.reset": "Telah kembali ke default",
    "systemSettings.tabs.general": "Umum",
    "systemSettings.tabs.users": "Manajemen Pengguna",
    "systemSettings.tabs.storage": "Pengaturan Penyimpanan",
    "systemSettings.tabs.security": "Manajemen Basis Data",
    "systemSettings.tabs.backup": "Cadangan & Pemulihan",
    "systemSettings.tabs.performance": "Pemantauan Kinerja",
  },
};

const LanguageContext = createContext<LanguageContextValue>({
  language: DEFAULT_LANGUAGE,
  setLanguage: () => undefined,
  t: (key: string) => key,
});

const getInitialLanguage = (): LanguageCode => {
  if (typeof window === "undefined") {
    return DEFAULT_LANGUAGE;
  }
  const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY) as LanguageCode | null;
  return stored ?? DEFAULT_LANGUAGE;
};

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [language, setLanguageState] = useState<LanguageCode>(getInitialLanguage);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
      document.documentElement.lang = language;
    }
  }, [language]);

  const setLanguage = useCallback((value: LanguageCode) => {
    setLanguageState(value);
  }, []);

  const translate = useCallback(
    (key: string) => {
      const candidates: LanguageCode[] = [language, "en-US", DEFAULT_LANGUAGE];
      for (const candidate of candidates) {
        const table = translationTable[candidate];
        if (table && table[key]) {
          return table[key];
        }
      }
      return key;
    },
    [language],
  );

  const contextValue = useMemo(
    () => ({
      language,
      setLanguage,
      t: translate,
    }),
    [language, setLanguage, translate],
  );

  return (
    <LanguageContext.Provider value={contextValue}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
