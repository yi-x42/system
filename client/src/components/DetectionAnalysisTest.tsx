import React from "react";

export function DetectionAnalysisTest() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">任務配置測試</h1>
      <div className="bg-gray-100 p-4 rounded">
        <p>如果您看到這個頁面，表示基本的組件渲染是正常的。</p>
        <p>測試時間: {new Date().toLocaleString()}</p>
      </div>
    </div>
  );
}
