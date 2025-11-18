import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  Camera,
  Search,
  AlertTriangle,
  Settings,
  Database,
  Monitor,
  ChevronRight,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from "./ui/sidebar";
import { useLanguage } from "../lib/language";
import { useTimezone } from "../lib/timezone";

interface AppSidebarProps {
  currentPage: string;
  onPageChange: (page: string) => void;
}

const menuGroups = [
  {
    titleKey: "sidebar.group.systemMonitoring",
    items: [
      {
        titleKey: "sidebar.item.dashboard",
        icon: Monitor,
        id: "dashboard",
      },
      {
        titleKey: "sidebar.item.cameraControl",
        icon: Camera,
        id: "camera-control",
      },
    ],
  },
  {
    titleKey: "sidebar.group.analytics",
    items: [
      {
        titleKey: "sidebar.item.detectionAnalysis",
        icon: Search,
        id: "detection-analysis",
      },
      {
        titleKey: "sidebar.item.statisticalAnalysis",
        icon: BarChart3,
        id: "statistical-analysis",
      },
    ],
  },
  {
    titleKey: "sidebar.group.data",
    items: [
      {
        titleKey: "sidebar.item.recordQuery",
        icon: Database,
        id: "record-query",
      },
      {
        titleKey: "sidebar.item.alertManagement",
        icon: AlertTriangle,
        id: "alert-management",
      },
    ],
  },
  {
    titleKey: "sidebar.group.settings",
    items: [
      {
        titleKey: "sidebar.item.systemSettings",
        icon: Settings,
        id: "system-settings",
      },
    ],
  },
];

export function AppSidebar({ currentPage, onPageChange }: AppSidebarProps) {
  const { t, language } = useLanguage();
  const { timezone } = useTimezone();
  const [currentTime, setCurrentTime] = useState(() => new Date());

  useEffect(() => {
    const timer = window.setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const { timeLabel, dateLabel } = useMemo(() => {
    const timeLabel = currentTime.toLocaleTimeString(language, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      timeZone: timezone,
    });
    const dateLabel = currentTime.toLocaleDateString(language, {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
      timeZone: timezone,
    });
    return { timeLabel, dateLabel };
  }, [currentTime, language, timezone]);

  return (
    <Sidebar>
      <SidebarHeader className="p-4">
        <div className="flex items-center gap-2">
          <Camera className="h-8 w-8 text-primary" />
          <div>
            <h2 className="font-semibold">{t("sidebar.brand.title")}</h2>
            <p className="text-sm text-muted-foreground">
              {t("sidebar.brand.subtitle")}
            </p>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {menuGroups.map((group) => (
          <SidebarGroup key={group.titleKey}>
            <SidebarGroupLabel>{t(group.titleKey)}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      onClick={() => onPageChange(item.id)}
                      isActive={currentPage === item.id}
                      className="w-full justify-start"
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{t(item.titleKey)}</span>
                      <ChevronRight className="h-4 w-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter className="border-t p-4">
        <p className="text-xs text-muted-foreground mb-1">
          {t("sidebar.clock.title")}
        </p>
        <p className="text-lg font-semibold leading-none">{timeLabel}</p>
        <p className="text-xs text-muted-foreground">{dateLabel}</p>
      </SidebarFooter>
    </Sidebar>
  );
}
