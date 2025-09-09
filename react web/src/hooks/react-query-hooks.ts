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

// 影片上傳回應介面
export interface VideoUploadResponse {
  message: string;
  source_id: number;
  file_path: string;
  original_name: string;
  size: number;
  video_info: {
    duration: number;
    fps: number;
    resolution: string;
    frame_count: number;
  };
}

// 影片上傳的非同步函式
const uploadVideo = async (formData: FormData): Promise<VideoUploadResponse> => {
  const { data } = await apiClient.post('/frontend/data-sources/upload/video', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
};

// 建立影片上傳的 mutation hook
export const useVideoUpload = () => {
  return useMutation<VideoUploadResponse, Error, FormData>({
    mutationFn: uploadVideo,
  });
};

// YOLO 模型清單型別
export interface YoloModelFileInfo {
  id: string;
  name: string;
  modelType: string;
  parameterCount: string;
  fileSize: string;
  status: string;
  size: number;
  created_at: number;
  modified_at: number;
  path: string;
}

// 取得 YOLO 模型清單
const fetchYoloModelList = async (): Promise<YoloModelFileInfo[]> => {
  const { data } = await apiClient.get('/frontend/models/list');
  return data;
};

export const useYoloModelList = () => {
  return useQuery<YoloModelFileInfo[], Error>({
    queryKey: ['yoloModelList'],
    queryFn: fetchYoloModelList,
    refetchOnWindowFocus: false,
  });
};

// 模型狀態切換
const toggleModelStatus = async (modelId: string): Promise<any> => {
  const { data } = await apiClient.post(`/frontend/models/${modelId}/toggle`);
  return data;
};

export const useToggleModelStatus = () => {
  return useMutation({
    mutationFn: toggleModelStatus,
  });
};

// 取得已啟用的模型清單（供其他功能使用）
const fetchActiveModels = async (): Promise<YoloModelFileInfo[]> => {
  const { data } = await apiClient.get('/frontend/models/active');
  return data;
};

export const useActiveModels = () => {
  return useQuery<YoloModelFileInfo[], Error>({
    queryKey: ['activeModels'],
    queryFn: fetchActiveModels,
    refetchOnWindowFocus: false,
  });
};

// 分析任務相關介面
export interface AnalysisTaskRequest {
  task_type: 'video_file' | 'realtime_camera';
  source_info: {
    file_path?: string;
    original_filename?: string;
    confidence_threshold?: number;
    camera_index?: number;
  };
  source_width?: number;
  source_height?: number;
  source_fps?: number;
}

export interface AnalysisTask {
  id: number;
  task_type: string;
  status: string;
  source_info: any;
  source_width?: number;
  source_height?: number;
  source_fps?: number;
  start_time?: string;
  end_time?: string;
  created_at: string;
}

export interface CreateAnalysisTaskResponse {
  success: boolean;
  task_id: number;
  message: string;
  task: AnalysisTask;
}

// 創建分析任務的非同步函式
const createAnalysisTask = async (taskData: AnalysisTaskRequest): Promise<CreateAnalysisTaskResponse> => {
  const { data } = await apiClient.post('/tasks/create', taskData);
  return data;
};

// 創建分析任務的 mutation hook
export const useCreateAnalysisTask = () => {
  return useMutation<CreateAnalysisTaskResponse, Error, AnalysisTaskRequest>({
    mutationFn: createAnalysisTask,
  });
};
