/**
 * YOLOv11 數位雙生分析系統 - 前端主要邏輯
 * 處理API請求和使用者介面互動
 */

// API 配置 - 動態偵測環境
const getAPIBaseURL = () => {
    const currentHost = window.location.hostname;
    if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
        return 'http://localhost:8000/api/v1';
    } else {
        return `http://${currentHost}:8000/api/v1`;
    }
};

const API_BASE_URL = getAPIBaseURL();

// API 請求函數
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const finalOptions = { ...defaultOptions, ...options };

    try {
        const response = await fetch(url, finalOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API 請求失敗 (${endpoint}):`, error);
        showNotification(`API 請求失敗: ${error.message}`, 'error');
        throw error;
    }
}

// 載入系統統計
async function loadSystemStats() {
    try {
        const stats = await apiRequest('/frontend/stats');
        updateSystemStats(stats);
    } catch (error) {
        console.error('載入系統統計失敗:', error);
        // 使用模擬數據作為後備
        updateSystemStats({
            cpu_usage: 0,
            memory_usage: 0,
            gpu_usage: 0,
            active_tasks: 0,
            active_cameras: 0,
            total_detections: 0,
            uptime: '00:00:00'
        });
    }
}

// 載入任務列表
async function loadTasks() {
    try {
        const tasks = await apiRequest('/frontend/tasks');
        updateTaskList(tasks);
    } catch (error) {
        console.error('載入任務列表失敗:', error);
        updateTaskList([]);
    }
}

// 載入攝影機列表
async function loadCameras() {
    try {
        const cameras = await apiRequest('/frontend/cameras');
        updateCameraGrid(cameras);
    } catch (error) {
        console.error('載入攝影機列表失敗:', error);
        updateCameraGrid([]);
    }
}

// 載入分析數據
async function loadAnalytics(timeRange = '1h') {
    try {
        const analytics = await apiRequest(`/frontend/analytics?time_range=${timeRange}`);
        updateAnalyticsCharts(analytics);
    } catch (error) {
        console.error('載入分析數據失敗:', error);
        // 使用空數據
        updateAnalyticsCharts({
            detection_count: [],
            object_distribution: {},
            hourly_trend: [],
            camera_activity: {}
        });
    }
}

// 創建任務
async function createTask(taskData) {
    try {
        const task = await apiRequest('/frontend/tasks', {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
        
        showNotification('任務創建成功', 'success');
        loadTasks(); // 重新載入任務列表
        return task;
    } catch (error) {
        console.error('創建任務失敗:', error);
        throw error;
    }
}

// 啟動任務
async function startTask(taskId) {
    try {
        await apiRequest(`/frontend/tasks/${taskId}/start`, {
            method: 'POST'
        });
        
        showNotification('任務啟動成功', 'success');
        loadTasks(); // 重新載入任務列表
    } catch (error) {
        console.error('啟動任務失敗:', error);
        throw error;
    }
}

// 停止任務
async function stopTask(taskId) {
    try {
        await apiRequest(`/frontend/tasks/${taskId}/stop`, {
            method: 'POST'
        });
        
        showNotification('任務停止成功', 'success');
        loadTasks(); // 重新載入任務列表
    } catch (error) {
        console.error('停止任務失敗:', error);
        throw error;
    }
}

// 掃描攝影機
async function scanCameras() {
    try {
        showNotification('正在掃描攝影機...', 'info');
        
        await apiRequest('/frontend/cameras/scan', {
            method: 'POST'
        });
        
        showNotification('攝影機掃描完成', 'success');
        loadCameras(); // 重新載入攝影機列表
    } catch (error) {
        console.error('掃描攝影機失敗:', error);
        throw error;
    }
}

// 切換攝影機狀態
async function toggleCamera(cameraId) {
    try {
        const result = await apiRequest(`/frontend/cameras/${cameraId}/toggle`, {
            method: 'POST'
        });
        
        showNotification(`攝影機已${result.active ? '啟動' : '停止'}`, 'success');
        loadCameras(); // 重新載入攝影機列表
        
        // 如果攝影機啟動，開始WebSocket連接
        if (result.active) {
            connectCameraStream(cameraId);
        } else {
            disconnectCameraStream(cameraId);
        }
    } catch (error) {
        console.error('切換攝影機狀態失敗:', error);
        throw error;
    }
}

// 更新系統統計顯示
function updateSystemStats(stats) {
    const elements = {
        cpu: document.getElementById('cpu-usage'),
        memory: document.getElementById('memory-usage'),
        gpu: document.getElementById('gpu-usage'),
        tasks: document.getElementById('active-tasks'),
        cameras: document.getElementById('active-cameras'),
        detections: document.getElementById('total-detections'),
        uptime: document.getElementById('system-uptime')
    };

    if (elements.cpu) elements.cpu.textContent = `${stats.cpu_usage}%`;
    if (elements.memory) elements.memory.textContent = `${stats.memory_usage}%`;
    if (elements.gpu) elements.gpu.textContent = `${stats.gpu_usage}%`;
    if (elements.tasks) elements.tasks.textContent = stats.active_tasks;
    if (elements.cameras) elements.cameras.textContent = stats.active_cameras;
    if (elements.detections) elements.detections.textContent = stats.total_detections.toLocaleString();
    if (elements.uptime) elements.uptime.textContent = stats.uptime;

    // 更新進度條
    updateProgressBar('cpu-progress', stats.cpu_usage);
    updateProgressBar('memory-progress', stats.memory_usage);
    updateProgressBar('gpu-progress', stats.gpu_usage);
}

// 更新進度條
function updateProgressBar(id, value) {
    const progressBar = document.getElementById(id);
    if (progressBar) {
        progressBar.style.width = `${value}%`;
        
        // 根據使用率調整顏色
        if (value > 80) {
            progressBar.className = 'progress-bar bg-danger';
        } else if (value > 60) {
            progressBar.className = 'progress-bar bg-warning';
        } else {
            progressBar.className = 'progress-bar bg-success';
        }
    }
}

// 更新任務列表
function updateTaskList(tasks) {
    const container = document.getElementById('task-list');
    if (!container) return;

    container.innerHTML = '';

    tasks.forEach(task => {
        const taskElement = document.createElement('div');
        taskElement.className = 'task-item card mb-2';
        
        const statusClass = {
            'running': 'text-success',
            'completed': 'text-primary',
            'pending': 'text-warning',
            'failed': 'text-danger'
        }[task.status] || 'text-secondary';

        taskElement.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="card-title mb-1">${task.name}</h6>
                    <span class="badge ${statusClass}">${getStatusText(task.status)}</span>
                </div>
                <div class="progress mb-2" style="height: 6px;">
                    <div class="progress-bar" style="width: ${task.progress}%"></div>
                </div>
                <div class="d-flex justify-content-between">
                    <small class="text-muted">進度: ${task.progress}%</small>
                    <div class="task-actions">
                        ${task.status === 'running' ? 
                            `<button class="btn btn-sm btn-outline-danger" onclick="stopTask('${task.id}')">停止</button>` :
                            `<button class="btn btn-sm btn-outline-success" onclick="startTask('${task.id}')">啟動</button>`
                        }
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(taskElement);
    });
}

// 更新攝影機網格
function updateCameraGrid(cameras) {
    const container = document.getElementById('camera-grid');
    if (!container) return;

    container.innerHTML = '';

    cameras.forEach(camera => {
        const cameraElement = document.createElement('div');
        cameraElement.className = 'col-md-4 mb-3';
        
        const statusClass = camera.active ? 'text-success' : 'text-secondary';
        const statusText = camera.active ? '運行中' : '離線';

        cameraElement.innerHTML = `
            <div class="card camera-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="card-title">${camera.name}</h6>
                        <span class="badge ${statusClass}">${statusText}</span>
                    </div>
                    <p class="card-text">
                        <small class="text-muted">ID: ${camera.id}</small><br>
                        <small class="text-muted">FPS: ${camera.fps || 0}</small>
                    </p>
                    <div class="camera-preview">
                        ${camera.active ? 
                            `<div id="camera-stream-${camera.id}" class="stream-container">
                                <div class="detection-overlay"></div>
                            </div>` :
                            '<div class="no-signal">無信號</div>'
                        }
                    </div>
                    <div class="mt-2">
                        <button class="btn btn-sm ${camera.active ? 'btn-outline-danger' : 'btn-outline-success'}" 
                                onclick="toggleCamera('${camera.id}')">
                            ${camera.active ? '停止' : '啟動'}
                        </button>
                        <button class="btn btn-sm btn-outline-info ms-1" 
                                onclick="testCamera('${camera.id}')">
                            測試
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(cameraElement);
    });
}

// 更新分析圖表
function updateAnalyticsCharts(data) {
    // 這裡需要整合圖表庫 (如 Chart.js)
    console.log('更新分析圖表:', data);
    
    // 示例：更新檢測數量圖表
    if (data.detection_count && typeof Chart !== 'undefined') {
        updateDetectionChart(data.detection_count);
    }
    
    // 示例：更新物件分布圖表
    if (data.object_distribution) {
        updateObjectDistributionChart(data.object_distribution);
    }
}

// 更新檢測結果顯示
function updateDetectionDisplay(cameraId, detectionData) {
    const container = document.getElementById(`camera-stream-${cameraId}`);
    if (!container) return;

    const overlay = container.querySelector('.detection-overlay');
    if (!overlay) return;

    // 清除之前的檢測框
    overlay.innerHTML = '';

    // 添加新的檢測框
    detectionData.detections.forEach(detection => {
        const bbox = document.createElement('div');
        bbox.className = 'detection-bbox';
        bbox.style.left = `${detection.bbox[0]}px`;
        bbox.style.top = `${detection.bbox[1]}px`;
        bbox.style.width = `${detection.bbox[2] - detection.bbox[0]}px`;
        bbox.style.height = `${detection.bbox[3] - detection.bbox[1]}px`;
        
        const label = document.createElement('div');
        label.className = 'detection-label';
        label.textContent = `${detection.class_name} (${(detection.confidence * 100).toFixed(1)}%)`;
        
        bbox.appendChild(label);
        overlay.appendChild(bbox);
    });
}

// 顯示通知
function showNotification(message, type = 'info') {
    // 創建通知元素
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.innerHTML = `
        <span>${message}</span>
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    // 添加到通知容器
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // 自動移除通知
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// 獲取狀態文字
function getStatusText(status) {
    const statusTexts = {
        'running': '運行中',
        'completed': '已完成',
        'pending': '等待中',
        'failed': '失敗',
        'stopped': '已停止'
    };
    return statusTexts[status] || status;
}

// 測試攝影機
async function testCamera(cameraId) {
    try {
        const result = await apiRequest(`/frontend/cameras/${cameraId}/test`);
        
        if (result.success) {
            showNotification('攝影機測試成功', 'success');
        } else {
            showNotification(`攝影機測試失敗: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('測試攝影機失敗:', error);
        showNotification('攝影機測試失敗', 'error');
    }
}

// 初始化函數
function initializeApp() {
    console.log('初始化 YOLOv11 系統...');
    
    // 載入初始數據
    loadSystemStats();
    loadTasks();
    loadCameras();
    loadAnalytics();
    
    // 初始化WebSocket連接
    if (typeof initializeWebSocketConnections === 'function') {
        initializeWebSocketConnections();
    }
    
    // 設置定期更新
    setInterval(loadSystemStats, 30000); // 每30秒更新系統統計
    setInterval(loadTasks, 10000); // 每10秒更新任務
    setInterval(loadCameras, 15000); // 每15秒更新攝影機
    
    console.log('系統初始化完成');
}

// DOM 載入完成後初始化
document.addEventListener('DOMContentLoaded', initializeApp);

// 導出函數供全局使用
window.loadSystemStats = loadSystemStats;
window.loadTasks = loadTasks;
window.loadCameras = loadCameras;
window.loadAnalytics = loadAnalytics;
window.createTask = createTask;
window.startTask = startTask;
window.stopTask = stopTask;
window.scanCameras = scanCameras;
window.toggleCamera = toggleCamera;
window.testCamera = testCamera;
window.showNotification = showNotification;
