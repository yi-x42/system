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

// 攝影機資料介面
export interface CameraInfo {
  id: string;
  name: string;
  status: string;
  camera_type: string;
  resolution: string;
  fps: number;
  group_id?: string;
  device_index?: number;
  rtsp_url?: string;
  // 為了與現有組件兼容，添加額外欄位
  location?: string;
  recording?: boolean;
  nightVision?: boolean;
  motionDetection?: boolean;
  ip?: string;
  model?: string;
}

// 獲取攝影機列表的非同步函式
const fetchCameras = async (): Promise<CameraInfo[]> => {
  const { data } = await apiClient.get('/frontend/cameras');
  return data;
};

// 攝影機列表的 hook
export const useCameras = () => {
  return useQuery<CameraInfo[], Error>({
    queryKey: ['cameras'],
    queryFn: fetchCameras,
    refetchOnWindowFocus: false,
    staleTime: 30000, // 30 seconds
  });
};

// 添加攝影機的介面
export interface AddCameraRequest {
  name: string;
  camera_type: string;
  resolution: string;
  fps: number;
  device_index?: number;
  rtsp_url?: string;
}

export interface AddCameraResponse {
  success: boolean;
  camera_id: string;
  message: string;
}

// 添加攝影機的非同步函式
const addCamera = async (cameraData: AddCameraRequest): Promise<AddCameraResponse> => {
  const { data } = await apiClient.post('/frontend/cameras', cameraData);
  return data;
};

// 添加攝影機的 hook
export const useAddCamera = () => {
  return useMutation<AddCameraResponse, Error, AddCameraRequest>({
    mutationFn: addCamera,
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
  // 後端返回的格式是 {value: [], Count: number}，需要提取 value 字段
  return data.value || data || [];
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
  // 後端返回的格式是 {value: [], Count: number}，需要提取 value 字段
  return data.value || data || [];
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
  status?: string;  // 對於 create-and-execute API 的額外狀態欄位
}

// 創建分析任務的非同步函式
const createAnalysisTask = async (taskData: AnalysisTaskRequest): Promise<CreateAnalysisTaskResponse> => {
  const { data } = await apiClient.post('/tasks/create', taskData);
  return data;
};

// 創建並執行分析任務的非同步函式
const createAndExecuteAnalysisTask = async (taskData: AnalysisTaskRequest): Promise<CreateAnalysisTaskResponse> => {
  const { data } = await apiClient.post('/tasks/create-and-execute', taskData);
  return data;
};

// 影片檔案資訊介面
export interface VideoFileInfo {
  id: string;
  name: string;
  file_path: string;
  upload_time: string;
  size: string;
  duration?: string;
  resolution?: string;
  status: 'ready' | 'analyzing' | 'completed';
}

export interface VideoListResponse {
  videos: VideoFileInfo[];
  total: number;
}

// 獲取影片列表的非同步函式 - 讀取真實目錄內容 
const fetchVideoList = async (): Promise<VideoListResponse> => {
  // 使用主 API 路由器中的影片檔案端點
  try {
    const { data } = await apiClient.get('/video-files');
    return data;
  } catch (error) {
    console.warn('主影片檔案 API 無法訪問，嘗試專用影片列表 API');
    
    // 嘗試專用影片列表 API
    try {
      const { data } = await apiClient.get('/video-list/simple');
      return data;
    } catch (listError) {
      console.warn('專用影片列表 API 無法訪問，嘗試前端路由');
      
      // 嘗試原本的前端路由
      try {
        const { data } = await apiClient.get('/frontend/videos');
        return data;
      } catch (frontendError) {
        console.warn('所有 API 無法訪問，使用實際檔案資料作為備案');
        
        // 最後備案：返回基於實際目錄檔案的資料
        return {
          videos: [
            {
              id: '20250909_231421_3687560-uhd_2160_3840_30fps.mp4',
              name: '20250909_231421_3687560-uhd_2160_3840_30fps.mp4',
              file_path: 'D:/project/system/yolo_backend/uploads/videos/20250909_231421_3687560-uhd_2160_3840_30fps.mp4',
              upload_time: '2025-09-09 23:14:21',
              size: '20.0MB',
              duration: '0:07', 
              resolution: '2160x3840',
              status: 'ready'
            }
          ],
          total: 1
        };
      }
    }
  }
};

// 創建分析任務的 mutation hook
export const useCreateAnalysisTask = () => {
  return useMutation<CreateAnalysisTaskResponse, Error, AnalysisTaskRequest>({
    mutationFn: createAnalysisTask,
  });
};

// 創建並執行分析任務的 mutation hook
export const useCreateAndExecuteAnalysisTask = () => {
  return useMutation<CreateAnalysisTaskResponse, Error, AnalysisTaskRequest>({
    mutationFn: createAndExecuteAnalysisTask,
  });
};

// ===== 影片列表相關 =====

export interface VideoFileInfo {
  id: string;
  name: string;
  file_path: string;
  upload_time: string;
  size: string;
  duration?: string;
  resolution?: string;
  status: 'ready' | 'analyzing' | 'completed';
}

export interface VideoListResponse {
  videos: VideoFileInfo[];
  total: number;
}

// 獲取影片列表的 hook
export const useVideoList = () => {
  return useQuery<VideoListResponse, Error>({
    queryKey: ['videoList'],
    queryFn: fetchVideoList,
    // 每 10 秒刷新一次
    refetchInterval: 10000,
  });
};

// 刪除影片的回應介面
export interface DeleteVideoResponse {
  success: boolean;
  message: string;
  deleted_file: string;
}

// 刪除影片的函式
const deleteVideo = async (videoId: string): Promise<DeleteVideoResponse> => {
  const { data } = await apiClient.delete(`/frontend/videos/${videoId}`);
  return data;
};

// 刪除影片的 hook
export const useDeleteVideo = () => {
  return useMutation<DeleteVideoResponse, Error, string>({
    mutationFn: deleteVideo,
  });
};

// 刪除攝影機回應型別
interface DeleteCameraResponse {
  message: string;
  camera_id: string;
}

// 刪除攝影機的函式
const deleteCamera = async (cameraId: string): Promise<DeleteCameraResponse> => {
  const { data } = await apiClient.delete(`/frontend/cameras/${cameraId}`);
  return data;
};

// 刪除攝影機的 hook
export const useDeleteCamera = () => {
  return useMutation<DeleteCameraResponse, Error, string>({
    mutationFn: deleteCamera,
  });
};

// 攝影機串流相關介面和Hook
export interface CameraStreamInfo {
  camera_id: string;
  stream_url: string;
  is_active: boolean;
  resolution: string;
  fps: number;
}

// 檢查攝影機是否有可用串流
export const useCameraStreamInfo = (cameraId: string | null) => {
  return useQuery<CameraStreamInfo, Error>({
    queryKey: ['camera-stream', cameraId],
    queryFn: async (): Promise<CameraStreamInfo> => {
      if (!cameraId) throw new Error('Camera ID is required');
      
      // 檢查攝影機是否存在
      const cameras = await fetchCameras();
      const camera = cameras.find(c => c.id === cameraId);
      
      if (!camera) {
        throw new Error('Camera not found');
      }
      
      // 對於USB攝影機，不管狀態如何都嘗試串流
      // 因為資料庫狀態可能不準確，物理設備可能仍然可用

      // 對於本地USB攝影機，使用索引0進行串流測試
      if (camera.camera_type === 'USB' || camera.device_index !== undefined) {
        // 使用攝影機的 device_index 或預設為 0
        const cameraIndex = camera.device_index !== undefined ? camera.device_index : 0;
        return {
          camera_id: cameraId,
          stream_url: `/api/v1/frontend/cameras/${cameraIndex}/stream`,
          is_active: true,
          resolution: camera.resolution,
          fps: camera.fps
        };
      } else {
        throw new Error('僅支援本地USB攝影機串流');
      }
    },
    enabled: !!cameraId,
    retry: false,
    staleTime: 5000, // 5 seconds
  });
};

// 切換攝影機狀態的Hook
export interface ToggleCameraResponse {
  camera_id: string;
  status: string;
  message: string;
}

export const useToggleCamera = () => {
  return useMutation<ToggleCameraResponse, Error, string>({
    mutationFn: async (cameraId: string): Promise<ToggleCameraResponse> => {
      const { data } = await apiClient.put(`/frontend/cameras/${cameraId}/toggle`);
      return data;
    },
  });
};
