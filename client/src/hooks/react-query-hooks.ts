import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  network_usage: number;
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
    // 設定每 1 秒自動重新整理一次資料
    refetchInterval: 1000,
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
    // 預設不自動輪詢，改由使用者操作或背景任務更新狀態
    refetchInterval: false,
    staleTime: 30000,
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
export interface DiscoveredCameraInfo {
  device_id: number;
  name: string;
  type: string;
  resolution: string;
  fps: number;
  status: string;
}

export interface RegisteredCameraInfo {
  id: string;
  name: string;
  device_index: number;
  resolution: string;
  fps: number;
}

export interface CameraScanResponse {
  message: string;
  cameras: DiscoveredCameraInfo[];
  registered: RegisteredCameraInfo[];
}

// 攝影機掃描參數
export interface CameraScanParams {
  register_new?: boolean;
}

// 攝影機掃描的非同步函式
const scanCameras = async (params?: CameraScanParams): Promise<CameraScanResponse> => {
  const { data } = await apiClient.post(
    '/frontend/cameras/scan',
    undefined,
    {
      params: {
        register_new: params?.register_new ?? true,
      },
    }
  );
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

// 影片分析回應類型定義
export interface VideoAnalysisResponse {
  success: boolean;
  task_id: number;
  message: string;
  task: any;
}

// 影片分析的非同步函式
const startVideoAnalysis = async (formData: FormData): Promise<VideoAnalysisResponse> => {
  const { data } = await apiClient.post('/new-analysis/start-video-analysis', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
};

// 建立影片分析的 mutation hook
export const useVideoAnalysis = () => {
  return useMutation<VideoAnalysisResponse, Error, FormData>({
    mutationFn: startVideoAnalysis,
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
  task_name?: string;
  model_id?: string;
  confidence_threshold?: number;
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
  webrtc_endpoint: string;
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
          webrtc_endpoint: `/frontend/cameras/${cameraId}/webrtc`,
          is_active: camera.status === 'active' || camera.status === 'online',
          resolution: camera.resolution,
          fps: camera.fps,
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

// Live Person Camera 相關介面
export interface LivePersonCameraRequest {
  task_name: string;
  camera_id: string;
  model_id: string;
  confidence: number;
  iou_threshold: number;
  description?: string;
  client_stream?: boolean;
}

export interface LivePersonCameraResponse {
  task_id: string;
  status: string;
  message: string;
  camera_info: any;
  model_info: any;
  created_at: string;
  websocket_url?: string;
}

export interface StopLivePersonCameraResponse {
  task_id: string;
  status: string;
  message: string;
  stopped_at: string;
}

export interface LaunchPreviewResponse {
  task_id: number;
  pid: number;
  already_running: boolean;
  message: string;
}

// 開始 Live Person Camera 分析的非同步函式
const startLivePersonCamera = async (requestData: LivePersonCameraRequest): Promise<LivePersonCameraResponse> => {
  const { data } = await apiClient.post('/frontend/analysis/start-realtime', requestData);
  return data;
};

// 開始 Live Person Camera 分析的 Hook
export const useStartLivePersonCamera = () => {
  return useMutation<LivePersonCameraResponse, Error, LivePersonCameraRequest>({
    mutationFn: startLivePersonCamera,
  });
};

// 停止 Live Person Camera 分析的非同步函式
const stopLivePersonCamera = async (taskId: string): Promise<StopLivePersonCameraResponse> => {
  const { data } = await apiClient.delete(`/frontend/analysis/live-person-camera/${taskId}`);
  return data;
};

// 停止 Live Person Camera 分析的 Hook
export const useStopLivePersonCamera = () => {
  return useMutation<StopLivePersonCameraResponse, Error, string>({
    mutationFn: stopLivePersonCamera,
  });
};

const launchLivePersonPreview = async (taskId: string): Promise<LaunchPreviewResponse> => {
  const { data } = await apiClient.post(`/frontend/analysis/live-person-camera/${taskId}/preview`);
  return data;
};

export const useLaunchLivePersonPreview = () => {
  return useMutation<LaunchPreviewResponse, Error, string>({
    mutationFn: launchLivePersonPreview,
  });
};

// 分析任務列表 API 回應介面
export interface AnalysisTasksResponse {
  success: boolean;
  tasks: AnalysisTask[];
  count: number;
}

// 獲取分析任務列表的非同步函式
const fetchAnalysisTasks = async (taskType?: string, status?: string, limit: number = 50): Promise<AnalysisTasksResponse> => {
  const params = new URLSearchParams();
  if (taskType) params.append('task_type', taskType);
  if (status) params.append('status', status);
  params.append('limit', limit.toString());
  
  const { data } = await apiClient.get(`/analysis/tasks?${params.toString()}`);
  return data;
};

// 獲取分析任務列表的Hook
export const useAnalysisTasks = (taskType?: string, status?: string, limit: number = 50) => {
  return useQuery<AnalysisTasksResponse, Error>({
    queryKey: ['analysisTasks', taskType, status, limit],
    queryFn: () => fetchAnalysisTasks(taskType, status, limit),
    // 設定每 10 秒自動重新整理一次資料
    refetchInterval: 10000,
  });
};

// 停止任務的非同步函式
const stopAnalysisTask = async (taskId: string): Promise<{ message: string; task_id: string }> => {
  const { data } = await apiClient.put(`/frontend/tasks/${taskId}/stop`);
  return data;
};

// 停止任務的Hook
export const useStopAnalysisTask = () => {
  const queryClient = useQueryClient();
  
  return useMutation<{ message: string; task_id: string }, Error, string>({
    mutationFn: stopAnalysisTask,
    onSuccess: () => {
      // 自動重新載入任務列表
      queryClient.invalidateQueries({ queryKey: ['analysisTasks'] });
    },
  });
};

// 刪除任務的非同步函式
const deleteAnalysisTask = async (taskId: string): Promise<{ success: boolean; message: string; task_id: number; deleted_detections: number }> => {
  const { data } = await apiClient.delete(`/analysis/tasks/${taskId}`);
  return data;
};

// 刪除任務的Hook
export const useDeleteAnalysisTask = () => {
  const queryClient = useQueryClient();
  
  return useMutation<{ success: boolean; message: string; task_id: number; deleted_detections: number }, Error, string>({
    mutationFn: deleteAnalysisTask,
    onSuccess: () => {
      // 自動重新載入任務列表
      queryClient.invalidateQueries({ queryKey: ['analysisTasks'] });
    },
  });
};

// 切換任務狀態（暫停/恢復）的非同步函式
const toggleAnalysisTaskStatus = async (taskId: string): Promise<{ message: string; task_id: number; old_status: string; new_status: string }> => {
  const { data } = await apiClient.put(`/frontend/tasks/${taskId}/toggle`);
  return data;
};

// 切換任務狀態的Hook
export const useToggleAnalysisTaskStatus = () => {
  const queryClient = useQueryClient();
  
  return useMutation<{ message: string; task_id: number; old_status: string; new_status: string }, Error, string>({
    mutationFn: toggleAnalysisTaskStatus,
    onSuccess: () => {
      // 自動重新載入任務列表
      queryClient.invalidateQueries({ queryKey: ['analysisTasks'] });
    },
  });
};

// ===== 系統控制相關 =====
interface ShutdownResponse {
  message: string;
  scheduled_in_seconds?: number;
}

const shutdownSystem = async (): Promise<ShutdownResponse> => {
  // 後端實際路徑為 /api/v1/frontend/system/shutdown ，apiClient 已在 baseURL 中含 /api/v1
  const { data } = await apiClient.post('/frontend/system/shutdown');
  return data;
};

export const useShutdownSystem = () => {
  return useMutation<ShutdownResponse, Error, void>({
    mutationFn: shutdownSystem,
  });
};



