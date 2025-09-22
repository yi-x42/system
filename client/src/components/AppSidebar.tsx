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
} from "./ui/sidebar";

interface AppSidebarProps {
  currentPage: string;
  onPageChange: (page: string) => void;
}

const menuItems = [
  {
    title: "系統監控",
    items: [
      {
        title: "儀表板",
        icon: Monitor,
        id: "dashboard",
      },
      {
        title: "攝影機控制中心",
        icon: Camera,
        id: "camera-control",
      },
    ],
  },
  {
    title: "分析與統計",
    items: [
      {
        title: "任務配置",
        icon: Search,
        id: "detection-analysis",
      },
      {
        title: "統計分析",
        icon: BarChart3,
        id: "statistical-analysis",
      },
    ],
  },
  {
    title: "數據管理",
    items: [
      {
        title: "紀錄查詢",
        icon: Database,
        id: "record-query",
      },
      {
        title: "警報管理",
        icon: AlertTriangle,
        id: "alert-management",
      },
    ],
  },
  {
    title: "系統配置",
    items: [
      {
        title: "系統設定",
        icon: Settings,
        id: "system-settings",
      },
    ],
  },
];

export function AppSidebar({ currentPage, onPageChange }: AppSidebarProps) {
  return (
    <Sidebar>
      <SidebarHeader className="p-4">
        <div className="flex items-center gap-2">
          <Camera className="h-8 w-8 text-primary" />
          <div>
            <h2 className="font-semibold">智慧偵測系統</h2>
            <p className="text-sm text-muted-foreground">監控管理平台</p>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {menuItems.map((group) => (
          <SidebarGroup key={group.title}>
            <SidebarGroupLabel>{group.title}</SidebarGroupLabel>
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
                      <span>{item.title}</span>
                      <ChevronRight className="h-4 w-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
    </Sidebar>
  );
}