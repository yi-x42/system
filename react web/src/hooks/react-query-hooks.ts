import { useQuery, useMutation } from '@tanstack/react-query';
import apiClient from '../lib/api';

// 定義從後端 API 回傳的系統統計資料結構
export interface SystemStats {
  total_cameras: number;
  online_cameras: number;
  total_alerts_today: number;
  alerts_vs_yesterday: number;
  active_tasks: number;
  system_uptime_seconds: number;
  storage_usage_gb: number;
  storage_total_gb: number;
  storage_percentage: number;
  model_name: string;
  model_params_m: number;
  avg_inference_ms: number;
  cpu_usage: number;
  memory_usage: number;
  gpu_usage: number;
  gpu_memory_usage: number;
}

// 獲取系統統計資料的非同步函式
const fetchSystemStats = async (): Promise<SystemStats> => {
  const { data } = await apiClient.get('/frontend/stats');
  return data;
};

// 建立一個自訂的 React Query hook 來使用系統統計資料
export const useSystemStats = () => {
  return useQuery<SystemStats, Error>({
    queryKey: ['systemStats'],
    queryFn: fetchSystemStats,
    // 設定每 5 秒自動重新整理一次資料
    refetchInterval: 5000,
  });
};

// 定義攝影機掃描結果的結構
export interface CameraDevice {
  index: number;
  backend?: string;
  frame_ok: boolean;
  width?: number;
  height?: number;
  source?: string;
  attempts?: Array<{
    backend: string;
    opened: boolean;
    frame_ok: boolean;
    width?: number;
    height?: number;
    elapsed_ms: number;
  }>;
}

export interface CameraScanResponse {
  devices: CameraDevice[];
  available_indices: number[];
  count: number;
}

// 攝影機掃描參數
export interface CameraScanParams {
  max_index?: number;
  warmup_frames?: number;
  force_probe?: boolean;
  retries?: number;
}

// 攝影機掃描的非同步函式
const scanCameras = async (params?: CameraScanParams): Promise<CameraScanResponse> => {
  const { data } = await apiClient.get('/cameras/scan', { params });
  return data;
};

// 建立攝影機掃描的 mutation hook
export const useScanCameras = () => {
  return useMutation<CameraScanResponse, Error, CameraScanParams | undefined>({
    mutationFn: scanCameras,
  });
};
