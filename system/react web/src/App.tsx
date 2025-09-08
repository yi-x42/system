import { useState } from "react";
import { SidebarProvider } from "./components/ui/sidebar";
import { AppSidebar } from "./components/AppSidebar";
import { Dashboard } from "./components/Dashboard";
import { CameraControl } from "./components/CameraControl";
import { DetectionAnalysis } from "./components/DetectionAnalysis";
import { StatisticalAnalysis } from "./components/StatisticalAnalysis";
import { RecordQuery } from "./components/RecordQuery";
import { AlertManagement } from "./components/AlertManagement";
import { SystemSettings } from "./components/SystemSettings";

export default function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");

  const renderPage = () => {
    switch (currentPage) {
      case "dashboard":
        return <Dashboard />;
      case "camera-control":
        return <CameraControl />;
      case "detection-analysis":
        return <DetectionAnalysis />;
      case "statistical-analysis":
        return <StatisticalAnalysis />;
      case "record-query":
        return <RecordQuery />;
      case "alert-management":
        return <AlertManagement />;
      case "system-settings":
        return <SystemSettings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        <AppSidebar currentPage={currentPage} onPageChange={setCurrentPage} />
        <main className="flex-1 p-6 bg-background">
          {renderPage()}
        </main>
      </div>
    </SidebarProvider>
  );
}