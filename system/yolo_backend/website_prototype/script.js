// ============================
// 配置與常量
// ============================

// API 基礎網址配置 - 動態偵測環境
const API_CONFIG = {
    get baseURL() {
        const currentHost = window.location.hostname;
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
            return 'http://localhost:8001';
        } else {
            return `http://${currentHost}:8001`;
        }
    },
    endpoints: {
        health: '/api/v1/health',
        frontend: '/api/v1/frontend',
        analysis: '/api/v1/new_analysis',
        get websocket() {
            const currentHost = window.location.hostname;
            if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
                return 'ws://localhost:8001/ws';
            } else {
                return `ws://${currentHost}:8001/ws`;
            }
        }
    }
};

// 全局狀態管理
const AppState = {
    isConnected: false,
    currentTheme: localStorage.getItem('theme') || 'light',
    websocket: null,
    activeSection: 'dashboard',
    systemStats: null,
    tasks: [],
    cameras: []
};

// ============================
// API 調用函數
// ============================

class APIClient {
    static async request(endpoint, options = {}) {
        const url = `${API_CONFIG.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };
        
        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API 請求失敗:', error);
            this.showNotification('API 請求失敗: ' + error.message, 'error');
            throw error;
        }
    }

    // 系統健康檢查
    static async checkHealth() {
        return this.request(API_CONFIG.endpoints.health);
    }

    // 獲取系統統計
    static async getSystemStats() {
        return this.request(`${API_CONFIG.endpoints.frontend}/stats`);
    }

    // 任務管理 API
    static async getTasks() {
        return this.request(`${API_CONFIG.endpoints.frontend}/tasks`);
    }

    static async createTask(taskData) {
        return this.request(`${API_CONFIG.endpoints.frontend}/tasks`, {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
    }

    static async startTask(taskId) {
        return this.request(`${API_CONFIG.endpoints.frontend}/tasks/${taskId}/start`, {
            method: 'POST'
        });
    }

    static async stopTask(taskId) {
        return this.request(`${API_CONFIG.endpoints.frontend}/tasks/${taskId}/stop`, {
            method: 'POST'
        });
    }

    static async deleteTask(taskId) {
        return this.request(`${API_CONFIG.endpoints.frontend}/tasks/${taskId}`, {
            method: 'DELETE'
        });
    }

    // 攝影機管理 API
    static async getCameras() {
        return this.request(`${API_CONFIG.endpoints.frontend}/cameras`);
    }

    static async refreshCameras() {
        return this.request(`${API_CONFIG.endpoints.frontend}/cameras/refresh`, {
            method: 'POST'
        });
    }

    static async testCamera(cameraId) {
        return this.request(`${API_CONFIG.endpoints.frontend}/cameras/${cameraId}/test`, {
            method: 'POST'
        });
    }

    // 分析與統計 API
    static async getAnalytics(period = '24h') {
        return this.request(`${API_CONFIG.endpoints.frontend}/analytics?period=${period}`);
    }

    static async exportData(format = 'json') {
        return this.request(`${API_CONFIG.endpoints.frontend}/export?format=${format}`);
    }

    // 模型管理 API
    static async getModels() {
        return this.request(`${API_CONFIG.endpoints.frontend}/models`);
    }

    static async loadModel(modelName) {
        return this.request(`${API_CONFIG.endpoints.frontend}/models/load`, {
            method: 'POST',
            body: JSON.stringify({ model_name: modelName })
        });
    }

    // 系統配置 API
    static async getConfig() {
        return this.request(`${API_CONFIG.endpoints.frontend}/config`);
    }

    static async updateConfig(configData) {
        return this.request(`${API_CONFIG.endpoints.frontend}/config`, {
            method: 'PUT',
            body: JSON.stringify(configData)
        });
    }

    // 通知顯示
    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(notification);

        setTimeout(() => notification.remove(), 5000);
    }
}

// ============================
// WebSocket 連接管理
// ============================

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 5000;
    }

    connect() {
        try {
            console.log('嘗試建立 WebSocket 連接...');
            this.ws = new WebSocket(API_CONFIG.endpoints.websocket);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket 連接成功');
                AppState.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };

            this.ws.onclose = () => {
                console.log('⚠️ WebSocket 連接關閉');
                AppState.isConnected = false;
                this.updateConnectionStatus(false);
                // 暫時禁用自動重連，避免持續錯誤
                // this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.warn('⚠️ WebSocket 無法連接（這是正常的，系統將使用 API 模式）:', error);
                AppState.isConnected = false;
                this.updateConnectionStatus(false);
            };

        } catch (error) {
            console.warn('⚠️ WebSocket 連接失敗，將使用 API 模式:', error);
            AppState.isConnected = false;
            this.updateConnectionStatus(false);
        }
    }

    handleMessage(data) {
        switch(data.type) {
            case 'system_stats':
                AppState.systemStats = data.data;
                this.updateDashboard();
                break;
            case 'task_update':
                this.updateTaskStatus(data.data);
                break;
            case 'camera_status':
                this.updateCameraStatus(data.data);
                break;
            case 'detection_result':
                this.updateDetectionResults(data.data);
                break;
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.querySelector('.connection-status');
        if (statusElement) {
            statusElement.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
            statusElement.innerHTML = `
                <i class="fas fa-${connected ? 'wifi' : 'wifi-slash'}"></i>
                ${connected ? '已連線' : '未連線'}
            `;
        }
    }

    attemptReconnect() {
        // 暫時禁用自動重連，避免持續的連接嘗試
        console.log('ℹ️ WebSocket 自動重連已禁用，系統將使用 API 模式');
        return;
        
        /* 原始重連邏輯（已禁用）
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`嘗試重新連接... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectInterval);
        } else {
            console.log('⚠️ WebSocket 重連嘗試已達上限，切換至 API 模式');
        }
        */
    }

    updateDashboard() {
        if (AppState.activeSection === 'dashboard' && AppState.systemStats) {
            DashboardManager.updateStats(AppState.systemStats);
        }
    }

    updateTaskStatus(taskData) {
        TaskManager.updateTaskInUI(taskData);
    }

    updateCameraStatus(cameraData) {
        CameraManager.updateCameraInUI(cameraData);
    }

    updateDetectionResults(resultData) {
        AnalyticsManager.addDetectionResult(resultData);
    }
}

// ============================
// 導航管理
// ============================

class NavigationManager {
    static init() {
        const navLinks = document.querySelectorAll('.nav-link');
        const contentSections = document.querySelectorAll('.content-section');
        const breadcrumb = document.querySelector('.breadcrumb .current-page');
        
        navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const targetSection = this.getAttribute('data-section');
                const href = this.getAttribute('href');
                
                // 如果連結指向外部頁面或文件，讓瀏覽器正常處理
                if (href.endsWith('.html') || 
                    href.startsWith('http') || 
                    href.startsWith('/website/') ||
                    href.includes('data_source')) {
                    console.log('允許導航到外部頁面:', href);
                    return; // 不阻止預設行為
                }
                
                // 對內部錨點導航進行特殊處理
                if (href.startsWith('#') && targetSection) {
                    e.preventDefault();
                    console.log('處理內部導航:', targetSection);
                    
                    // 移除所有活躍狀態
                    navLinks.forEach(l => l.parentElement.classList.remove('active'));
                    contentSections.forEach(section => section.classList.remove('active'));
                    
                    // 添加活躍狀態
                    this.parentElement.classList.add('active');
                    
                    // 顯示對應內容區塊
                    const targetElement = document.getElementById(targetSection);
                    if (targetElement) {
                        targetElement.classList.add('active');
                        AppState.activeSection = targetSection;
                        
                        // 更新麵包屑
                        if (breadcrumb) {
                            breadcrumb.textContent = this.querySelector('span').textContent;
                        }
                        
                        // 載入對應區塊的數據
                        NavigationManager.loadSectionData(targetSection);
                    }
                }
            });
        });

        // 側邊欄切換
        NavigationManager.initSidebarToggle();
        
        // 主題切換
        NavigationManager.initThemeToggle();
    }

    static initSidebarToggle() {
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        const sidebar = document.querySelector('.sidebar');
        
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function() {
                sidebar.classList.toggle('show');
            });
        }
        
        // 點擊主內容區域時關閉側邊欄（手機版）
        document.querySelector('.main-content').addEventListener('click', function() {
            if (window.innerWidth <= 1024) {
                sidebar.classList.remove('show');
            }
        });
    }

    static initThemeToggle() {
        const themeToggle = document.querySelector('.theme-toggle');
        
        // 設置初始主題
        document.documentElement.setAttribute('data-theme', AppState.currentTheme);
        
        themeToggle.addEventListener('click', function() {
            AppState.currentTheme = AppState.currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', AppState.currentTheme);
            localStorage.setItem('theme', AppState.currentTheme);
            
            // 更新主題圖示
            const icon = this.querySelector('i');
            icon.className = AppState.currentTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        });
    }

    static async loadSectionData(section) {
        try {
            switch(section) {
                case 'dashboard':
                    await DashboardManager.loadData();
                    break;
                case 'tasks':
                    await TaskManager.loadTasks();
                    break;
                case 'cameras':
                    await CameraManager.loadCameras();
                    break;
                case 'analytics':
                    await AnalyticsManager.loadAnalytics();
                    break;
                case 'config':
                    await ConfigManager.loadConfig();
                    break;
            }
        } catch (error) {
            console.error(`載入 ${section} 數據失敗:`, error);
        }
    }
}

// ============================
// 儀表板管理
// ============================

class DashboardManager {
    static async loadData() {
        try {
            const stats = await APIClient.getSystemStats();
            this.updateStats(stats);
            this.initializeCharts();
        } catch (error) {
            console.error('載入儀表板數據失敗:', error);
        }
    }

    static updateStats(stats) {
        // 更新統計卡片
        const statCards = {
            'cpu-usage': { value: stats.cpu_usage, suffix: '%' },
            'memory-usage': { value: stats.memory_usage, suffix: '%' },
            'active-tasks': { value: stats.active_tasks, suffix: '' },
            'total-detections': { value: stats.total_detections, suffix: '' }
        };

        Object.entries(statCards).forEach(([id, data]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = data.value + data.suffix;
            }
        });

        // 更新系統狀態
        const statusElement = document.querySelector('.system-status');
        if (statusElement) {
            const status = stats.system_healthy ? '正常運行' : '異常';
            const statusClass = stats.system_healthy ? 'status-good' : 'status-warning';
            statusElement.innerHTML = `<span class="${statusClass}">${status}</span>`;
        }
    }

    static initializeCharts() {
        // CPU 使用率圖表
        const cpuCtx = document.getElementById('cpuChart');
        if (cpuCtx && !cpuCtx.chart) {
            cpuCtx.chart = new Chart(cpuCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU 使用率',
                        data: [],
                        borderColor: '#6c5ce7',
                        backgroundColor: 'rgba(108, 92, 231, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }

        // 記憶體使用率圖表
        const memoryCtx = document.getElementById('memoryChart');
        if (memoryCtx && !memoryCtx.chart) {
            memoryCtx.chart = new Chart(memoryCtx, {
                type: 'doughnut',
                data: {
                    labels: ['已使用', '可用'],
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ['#6c5ce7', '#ddd']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }

    static updateCharts(data) {
        // 更新 CPU 圖表
        const cpuChart = document.getElementById('cpuChart')?.chart;
        if (cpuChart) {
            const now = new Date().toLocaleTimeString();
            cpuChart.data.labels.push(now);
            cpuChart.data.datasets[0].data.push(data.cpu_usage);
            
            // 保持最近 20 個數據點
            if (cpuChart.data.labels.length > 20) {
                cpuChart.data.labels.shift();
                cpuChart.data.datasets[0].data.shift();
            }
            cpuChart.update();
        }

        // 更新記憶體圖表
        const memoryChart = document.getElementById('memoryChart')?.chart;
        if (memoryChart) {
            memoryChart.data.datasets[0].data = [data.memory_usage, 100 - data.memory_usage];
            memoryChart.update();
        }
    }
}

// ============================
// 任務管理
// ============================

class TaskManager {
    static async loadTasks() {
        try {
            const tasks = await APIClient.getTasks();
            AppState.tasks = tasks;
            this.renderTasks(tasks);
        } catch (error) {
            console.error('載入任務失敗:', error);
        }
    }

    static renderTasks(tasks) {
        const container = document.getElementById('tasks-container');
        if (!container) return;

        container.innerHTML = tasks.map(task => `
            <div class="task-card" data-task-id="${task.id}">
                <div class="task-header">
                    <h3>${task.name}</h3>
                    <span class="status-badge status-${task.status}">${this.getStatusText(task.status)}</span>
                </div>
                <div class="task-details">
                    <p><strong>類型:</strong> ${this.getTypeText(task.type)}</p>
                    <p><strong>進度:</strong> ${task.progress}%</p>
                    <p><strong>創建時間:</strong> ${new Date(task.created_at).toLocaleString()}</p>
                </div>
                <div class="task-actions">
                    ${task.status === 'created' || task.status === 'stopped' ? 
                        `<button onclick="TaskManager.startTask('${task.id}')" class="btn btn-primary">啟動</button>` : ''}
                    ${task.status === 'running' ? 
                        `<button onclick="TaskManager.stopTask('${task.id}')" class="btn btn-warning">停止</button>` : ''}
                    <button onclick="TaskManager.deleteTask('${task.id}')" class="btn btn-danger">刪除</button>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${task.progress}%"></div>
                </div>
            </div>
        `).join('');
    }

    static async createTask() {
        const modal = document.getElementById('create-task-modal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    static async submitCreateTask() {
        const form = document.getElementById('create-task-form');
        const formData = new FormData(form);
        
        const taskData = {
            name: formData.get('task-name'),
            type: formData.get('task-type'),
            config: {
                model: formData.get('model'),
                confidence: parseFloat(formData.get('confidence')),
                source: formData.get('source')
            }
        };

        try {
            await APIClient.createTask(taskData);
            this.closeCreateTaskModal();
            await this.loadTasks();
            APIClient.showNotification('任務創建成功', 'success');
        } catch (error) {
            APIClient.showNotification('任務創建失敗', 'error');
        }
    }

    static closeCreateTaskModal() {
        const modal = document.getElementById('create-task-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    static async startTask(taskId) {
        try {
            await APIClient.startTask(taskId);
            await this.loadTasks();
            APIClient.showNotification('任務啟動成功', 'success');
        } catch (error) {
            APIClient.showNotification('任務啟動失敗', 'error');
        }
    }

    static async stopTask(taskId) {
        try {
            await APIClient.stopTask(taskId);
            await this.loadTasks();
            APIClient.showNotification('任務停止成功', 'success');
        } catch (error) {
            APIClient.showNotification('任務停止失敗', 'error');
        }
    }

    static async deleteTask(taskId) {
        if (confirm('確定要刪除這個任務嗎？')) {
            try {
                await APIClient.deleteTask(taskId);
                await this.loadTasks();
                APIClient.showNotification('任務刪除成功', 'success');
            } catch (error) {
                APIClient.showNotification('任務刪除失敗', 'error');
            }
        }
    }

    static updateTaskInUI(taskData) {
        const taskCard = document.querySelector(`[data-task-id="${taskData.id}"]`);
        if (taskCard) {
            // 更新狀態標籤
            const statusBadge = taskCard.querySelector('.status-badge');
            statusBadge.className = `status-badge status-${taskData.status}`;
            statusBadge.textContent = this.getStatusText(taskData.status);
            
            // 更新進度條
            const progressFill = taskCard.querySelector('.progress-fill');
            progressFill.style.width = `${taskData.progress}%`;
            
            // 更新進度文字
            const progressText = taskCard.querySelector('.task-details p:nth-child(2)');
            progressText.innerHTML = `<strong>進度:</strong> ${taskData.progress}%`;
        }
    }

    static getStatusText(status) {
        const statusMap = {
            'created': '已創建',
            'running': '運行中',
            'stopped': '已停止',
            'completed': '已完成',
            'error': '錯誤'
        };
        return statusMap[status] || status;
    }

    static getTypeText(type) {
        const typeMap = {
            'realtime': '即時檢測',
            'batch': '批次處理',
            'training': '模型訓練'
        };
        return typeMap[type] || type;
    }
}

// ============================
// 攝影機管理
// ============================

class CameraManager {
    static async loadCameras() {
        try {
            const cameras = await APIClient.getCameras();
            AppState.cameras = cameras;
            this.renderCameras(cameras);
        } catch (error) {
            console.error('載入攝影機失敗:', error);
        }
    }

    static renderCameras(cameras) {
        const container = document.getElementById('cameras-container');
        if (!container) return;

        container.innerHTML = cameras.map(camera => `
            <div class="camera-card" data-camera-id="${camera.id}">
                <div class="camera-preview">
                    <img src="data:image/svg+xml;base64,${btoa('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="75"><rect width="100" height="75" fill="#ddd"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#999">攝影機 ${camera.id}</text></svg>')}" alt="攝影機預覽">
                    <div class="camera-status ${camera.status === 'active' ? 'active' : 'inactive'}"></div>
                </div>
                <div class="camera-info">
                    <h3>${camera.name}</h3>
                    <p><strong>解析度:</strong> ${camera.resolution}</p>
                    <p><strong>狀態:</strong> ${this.getStatusText(camera.status)}</p>
                </div>
                <div class="camera-actions">
                    <button onclick="CameraManager.testCamera('${camera.id}')" class="btn btn-primary">測試</button>
                    <button onclick="CameraManager.startStream('${camera.id}')" class="btn btn-success">開始串流</button>
                </div>
            </div>
        `).join('');
    }

    static async refreshCameras() {
        try {
            await APIClient.refreshCameras();
            await this.loadCameras();
            APIClient.showNotification('攝影機列表已刷新', 'success');
        } catch (error) {
            APIClient.showNotification('刷新攝影機失敗', 'error');
        }
    }

    static async testCamera(cameraId) {
        try {
            const result = await APIClient.testCamera(cameraId);
            APIClient.showNotification(result.message, result.success ? 'success' : 'error');
        } catch (error) {
            APIClient.showNotification('攝影機測試失敗', 'error');
        }
    }

    static startStream(cameraId) {
        // 實現攝影機串流功能
        APIClient.showNotification('攝影機串流功能開發中', 'info');
    }

    static updateCameraInUI(cameraData) {
        const cameraCard = document.querySelector(`[data-camera-id="${cameraData.id}"]`);
        if (cameraCard) {
            const statusElement = cameraCard.querySelector('.camera-status');
            statusElement.className = `camera-status ${cameraData.status === 'active' ? 'active' : 'inactive'}`;
            
            const statusText = cameraCard.querySelector('.camera-info p:last-child');
            statusText.innerHTML = `<strong>狀態:</strong> ${this.getStatusText(cameraData.status)}`;
        }
    }

    static getStatusText(status) {
        const statusMap = {
            'active': '運行中',
            'inactive': '未連接',
            'error': '錯誤'
        };
        return statusMap[status] || status;
    }
}

// ============================
// 分析管理
// ============================

class AnalyticsManager {
    static currentPeriod = '24h';
    static charts = {};

    static async loadAnalytics() {
        try {
            this.showLoadingState();
            const analytics = await APIClient.getAnalytics(this.currentPeriod);
            this.renderAnalytics(analytics);
            this.initializeAnalyticsCharts(analytics);
            this.updateAnalyticsStatus('success', '數據載入成功');
        } catch (error) {
            console.error('載入分析數據失敗:', error);
            this.showErrorState(error.message);
            this.updateAnalyticsStatus('error', '數據載入失敗: ' + error.message);
        }
    }

    static showLoadingState() {
        // 顯示加載狀態
        document.getElementById('analytics-status').innerHTML = 
            '<i class="fas fa-spinner fa-spin"></i> 載入中...';
        
        // 重置統計數字
        ['totalDetections', 'personCount', 'vehicleCount', 'alertCount'].forEach(id => {
            const element = document.getElementById(id);
            if (element) element.textContent = '-';
        });

        // 顯示圖表加載狀態
        ['trend-chart-loading', 'category-chart-loading', 'heatmap-loading', 'time-analysis-loading'].forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'block';
        });
    }

    static showErrorState(errorMessage) {
        // 顯示錯誤狀態
        ['trend-chart-error', 'category-chart-error', 'heatmap-error', 'time-analysis-error'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.style.display = 'block';
                element.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${errorMessage}`;
            }
        });

        // 隱藏加載狀態
        ['trend-chart-loading', 'category-chart-loading', 'heatmap-loading', 'time-analysis-loading'].forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'none';
        });
    }

    static updateAnalyticsStatus(type, message) {
        const statusElement = document.getElementById('analytics-status');
        if (statusElement) {
            if (type === 'success') {
                statusElement.innerHTML = `<i class="fas fa-check-circle text-success"></i> ${message}`;
            } else if (type === 'error') {
                statusElement.innerHTML = `<i class="fas fa-exclamation-triangle text-danger"></i> ${message}`;
            }
        }
    }

    static renderAnalytics(data) {
        try {
            // 更新統計數字
            const totalDetections = Object.values(data.detection_counts || {}).reduce((a, b) => a + b, 0);
            const personCount = data.category_distribution?.person || 0;
            const vehicleCount = (data.category_distribution?.car || 0) + (data.category_distribution?.truck || 0);
            const alertCount = data.detection_counts?.anomaly || 0;

            const stats = {
                'totalDetections': totalDetections.toLocaleString(),
                'personCount': personCount.toLocaleString(),
                'vehicleCount': vehicleCount.toLocaleString(),
                'alertCount': alertCount.toLocaleString()
            };

            Object.entries(stats).forEach(([id, value]) => {
                const element = document.getElementById(id);
                if (element) {
                    element.textContent = value;
                }
            });

            // 載入檢測結果列表
            this.loadDetectionResults();

        } catch (error) {
            console.error('渲染分析數據失敗:', error);
        }
    }

    static initializeAnalyticsCharts(data) {
        // 隱藏加載狀態
        ['trend-chart-loading', 'category-chart-loading', 'heatmap-loading', 'time-analysis-loading'].forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'none';
        });

        // 隱藏錯誤狀態
        ['trend-chart-error', 'category-chart-error', 'heatmap-error', 'time-analysis-error'].forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'none';
        });

        try {
            // 檢測類型分布圖
            const detectionCtx = document.getElementById('detectionChart');
            if (detectionCtx) {
                if (this.charts.detectionChart) {
                    this.charts.detectionChart.destroy();
                }
                
                const categoryData = data.category_distribution || {};
                const categoryLabels = Object.keys(categoryData);
                const categoryValues = Object.values(categoryData);
                const categoryColors = ['#6c5ce7', '#74b9ff', '#fd79a8', '#55a3ff', '#00b894', '#fdcb6e'];

                this.charts.detectionChart = new Chart(detectionCtx, {
                    type: 'pie',
                    data: {
                        labels: categoryLabels.length > 0 ? categoryLabels : ['暫無數據'],
                        datasets: [{
                            data: categoryValues.length > 0 ? categoryValues : [1],
                            backgroundColor: categoryLabels.length > 0 ? categoryColors.slice(0, categoryLabels.length) : ['#ddd']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }

            // 時間趨勢圖
            const trendCtx = document.getElementById('trendChart');
            if (trendCtx) {
                if (this.charts.trendChart) {
                    this.charts.trendChart.destroy();
                }
                
                const hourlyData = data.hourly_trend || [];
                const trendLabels = hourlyData.map(item => item.hour);
                const trendValues = hourlyData.map(item => item.total);

                this.charts.trendChart = new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: trendLabels.length > 0 ? trendLabels : ['00:00', '06:00', '12:00', '18:00'],
                        datasets: [{
                            label: '檢測數量',
                            data: trendValues.length > 0 ? trendValues : [0, 0, 0, 0],
                            borderColor: '#6c5ce7',
                            backgroundColor: 'rgba(108, 92, 231, 0.1)',
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        plugins: {
                            legend: {
                                display: false
                            }
                        }
                    }
                });
            }

            // 類別分布圖（環形圖）
            const categoryCtx = document.getElementById('categoryChart');
            if (categoryCtx) {
                if (this.charts.categoryChart) {
                    this.charts.categoryChart.destroy();
                }
                
                const categoryData = data.category_distribution || {};
                const categoryLabels = Object.keys(categoryData);
                const categoryValues = Object.values(categoryData);
                const categoryColors = ['#6c5ce7', '#74b9ff', '#fd79a8', '#55a3ff', '#00b894', '#fdcb6e'];

                this.charts.categoryChart = new Chart(categoryCtx, {
                    type: 'doughnut',
                    data: {
                        labels: categoryLabels.length > 0 ? categoryLabels : ['暫無數據'],
                        datasets: [{
                            data: categoryValues.length > 0 ? categoryValues : [1],
                            backgroundColor: categoryLabels.length > 0 ? categoryColors.slice(0, categoryLabels.length) : ['#ddd']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }

            // 熱力圖（簡化版，使用檢測密度）
            const heatmapCtx = document.getElementById('heatmapChart');
            if (heatmapCtx) {
                if (this.charts.heatmapChart) {
                    this.charts.heatmapChart.destroy();
                }
                
                const detectionCounts = data.detection_counts || {};
                const heatmapLabels = Object.keys(detectionCounts);
                const heatmapValues = Object.values(detectionCounts);

                this.charts.heatmapChart = new Chart(heatmapCtx, {
                    type: 'bar',
                    data: {
                        labels: heatmapLabels.length > 0 ? heatmapLabels : ['暫無數據'],
                        datasets: [{
                            label: '檢測次數',
                            data: heatmapValues.length > 0 ? heatmapValues : [0],
                            backgroundColor: '#74b9ff',
                            borderColor: '#0984e3',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        plugins: {
                            legend: {
                                display: false
                            }
                        }
                    }
                });
            }

        } catch (error) {
            console.error('初始化圖表失敗:', error);
            this.showErrorState('圖表載入失敗');
        }
    }

    static async loadDetectionResults() {
        try {
            const response = await fetch(`${API_CONFIG.baseURL}/api/v1/frontend/detection-results?limit=50`);
            if (!response.ok) throw new Error('載入檢測結果失敗');
            
            const results = await response.json();
            this.renderDetectionResultsTable(results);
        } catch (error) {
            console.error('載入檢測結果失敗:', error);
            const tableElement = document.getElementById('detection-results-table');
            if (tableElement) {
                tableElement.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-danger">
                            <i class="fas fa-exclamation-triangle"></i> 載入檢測結果失敗: ${error.message}
                        </td>
                    </tr>
                `;
            }
        }
    }

    static renderDetectionResultsTable(results) {
        const tableElement = document.getElementById('detection-results-table');
        if (!tableElement) return;

        if (!results || results.length === 0) {
            tableElement.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        <i class="fas fa-info-circle"></i> 暫無檢測結果
                    </td>
                </tr>
            `;
            return;
        }

        const tableRows = results.map(result => {
            const timestamp = new Date(result.timestamp).toLocaleString('zh-TW');
            const confidence = Math.round(result.confidence * 100);
            const statusClass = result.confidence > 0.8 ? 'success' : result.confidence > 0.6 ? 'warning' : 'danger';
            
            return `
                <tr>
                    <td>${timestamp}</td>
                    <td>攝像頭 ${result.camera_id || 'N/A'}</td>
                    <td>${result.object_type || '未知'}</td>
                    <td>
                        <span class="badge bg-${statusClass}">${confidence}%</span>
                    </td>
                    <td>
                        <span class="badge bg-${result.status === 'completed' ? 'success' : 'secondary'}">
                            ${result.status === 'completed' ? '已完成' : '處理中'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="showDetectionDetail('${result.id}')">
                            <i class="fas fa-eye"></i> 詳情
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        tableElement.innerHTML = tableRows;
    }

    static setPeriod(period) {
        this.currentPeriod = period;
        
        // 更新按鈕狀態
        document.querySelectorAll('[data-period]').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-period="${period}"]`)?.classList.add('active');
        
        // 重新載入數據
        this.loadAnalytics();
    }

    static addDetectionResult(result) {
        // 實時更新檢測結果
        console.log('新檢測結果:', result);
    }

    static async exportData(format) {
        try {
            const data = await APIClient.exportData(format);
            APIClient.showNotification(`數據已匯出為 ${format.toUpperCase()} 格式`, 'success');
        } catch (error) {
            APIClient.showNotification('數據匯出失敗', 'error');
        }
    }
}

// ============================
// 配置管理
// ============================

class ConfigManager {
    static async loadConfig() {
        try {
            const config = await APIClient.getConfig();
            this.renderConfig(config);
        } catch (error) {
            console.error('載入配置失敗:', error);
        }
    }

    static renderConfig(config) {
        // 渲染配置表單
        const form = document.getElementById('config-form');
        if (form) {
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => {
                const key = input.name;
                if (config[key] !== undefined) {
                    input.value = config[key];
                }
            });
        }
    }

    static async saveConfig() {
        const form = document.getElementById('config-form');
        const formData = new FormData(form);
        const config = {};
        
        for (let [key, value] of formData.entries()) {
            config[key] = value;
        }

        try {
            await APIClient.updateConfig(config);
            APIClient.showNotification('配置保存成功', 'success');
        } catch (error) {
            APIClient.showNotification('配置保存失敗', 'error');
        }
    }

    static async loadModel() {
        const modelSelect = document.getElementById('model-select');
        const modelName = modelSelect.value;
        
        if (!modelName) {
            APIClient.showNotification('請選擇模型', 'warning');
            return;
        }

        try {
            await APIClient.loadModel(modelName);
            APIClient.showNotification('模型載入成功', 'success');
        } catch (error) {
            APIClient.showNotification('模型載入失敗', 'error');
        }
    }
}

// ============================
// 應用程式初始化
// ============================

document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有管理器
    NavigationManager.init();
    
    // 建立 WebSocket 連接
    const wsManager = new WebSocketManager();
    AppState.websocket = wsManager;
    wsManager.connect();
    
    // 檢查後端連接
    APIClient.checkHealth()
        .then(() => {
            APIClient.showNotification('後端連接成功', 'success');
            // 載入默認頁面數據
            DashboardManager.loadData();
        })
        .catch(() => {
            APIClient.showNotification('無法連接到後端服務', 'error');
        });
    
    // 定期更新系統狀態
    setInterval(async () => {
        if (AppState.activeSection === 'dashboard') {
            try {
                const stats = await APIClient.getSystemStats();
                DashboardManager.updateCharts(stats);
            } catch (error) {
                console.error('更新系統狀態失敗:', error);
            }
        }
    }, 5000);
});

// ============================
// 全局函數（供 HTML 調用）
// ============================

// 任務相關
window.createTask = () => TaskManager.createTask();
window.submitCreateTask = () => TaskManager.submitCreateTask();
window.closeCreateTaskModal = () => TaskManager.closeCreateTaskModal();

// 攝影機相關
window.refreshCameras = () => CameraManager.refreshCameras();

// 分析相關
window.exportData = (format) => AnalyticsManager.exportData(format);

// 配置相關
window.saveConfig = () => ConfigManager.saveConfig();
window.loadModel = () => ConfigManager.loadModel();

// 主題切換功能（如果存在主題切換按鈕）
const themeToggle = document.querySelector('.theme-toggle');
if (themeToggle) {
    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-theme');
        const icon = this.querySelector('i');
        if (document.body.classList.contains('dark-theme')) {
            icon.className = 'fas fa-sun';
        } else {
            icon.className = 'fas fa-moon';
        }
    });
}

// 初始化其他UI功能
function initializeUIFeatures() {
    // 滑動條功能
    const sliders = document.querySelectorAll('.config-slider');
    sliders.forEach(slider => {
        const valueDisplay = slider.parentElement.querySelector('.slider-value');
        
        slider.addEventListener('input', function() {
            valueDisplay.textContent = this.value + '%';
        });
    });
    
    // 模型選擇器
    const modelOptions = document.querySelectorAll('.model-option');
    modelOptions.forEach(option => {
        option.addEventListener('click', function() {
            modelOptions.forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // 分頁標籤切換
    const tabBtns = document.querySelectorAll('.tab-btn');
    const cameraTab = document.getElementById('camera-tab-content');
    const videoTab = document.getElementById('video-tab-content');
    tabBtns.forEach((btn, idx) => {
        btn.addEventListener('click', function() {
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            if (idx === 0) {
                cameraTab.style.display = 'block';
                videoTab.style.display = 'none';
            } else {
                cameraTab.style.display = 'none';
                videoTab.style.display = 'block';
            }
        });
    });
    
    // 搜尋功能
    const searchInput = document.querySelector('.search-box input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            console.log('搜尋:', searchTerm);
        });
    }
    
    // 通知點擊
    const notifications = document.querySelector('.notifications');
    if (notifications) {
        notifications.addEventListener('click', function() {
            showNotificationPanel();
        });
    }
    
    // 用戶選單點擊
    const userMenu = document.querySelector('.user-menu');
    if (userMenu) {
        userMenu.addEventListener('click', function() {
            showUserMenu();
        });
    }
    
    // 快速操作按鈕
    const quickActionBtns = document.querySelectorAll('.quick-action-btn');
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.querySelector('span').textContent;
            handleQuickAction(action);
        });
    });
    
    // 攝影機操作按鈕
    const cameraActionBtns = document.querySelectorAll('.camera-actions .btn-icon');
    cameraActionBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const icon = this.querySelector('i');
            if (icon.classList.contains('fa-play')) {
                handleCameraPlay(this);
            } else if (icon.classList.contains('fa-cog')) {
                handleCameraConfig(this);
            }
        });
    });
    
    // 初始化圖表
    initializeCharts();
    
    // 初始化即時數據更新
    startRealTimeUpdates();
}

// 圖表初始化
function initializeCharts() {
    const ctx = document.getElementById('performanceChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
                datasets: [{
                    label: 'CPU 使用率',
                    data: [20, 35, 45, 60, 55, 40, 30],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4
                }, {
                    label: 'GPU 使用率',
                    data: [10, 25, 70, 85, 75, 65, 45],
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// 即時數據更新
function startRealTimeUpdates() {
    setInterval(() => {
        updateSystemStats();
        updateDetectionList();
    }, 5000); // 每5秒更新一次
}

// 更新系統統計
function updateSystemStats() {
    // 模擬數據更新
    const cpuStat = document.querySelector('.stat-icon.cpu').parentElement.querySelector('.stat-value');
    const memoryStat = document.querySelector('.stat-icon.memory').parentElement.querySelector('.stat-value');
    const gpuStat = document.querySelector('.stat-icon.gpu').parentElement.querySelector('.stat-value');
    const tasksStat = document.querySelector('.stat-icon.tasks').parentElement.querySelector('.stat-value');
    
    if (cpuStat) {
        const newValue = Math.floor(Math.random() * 30) + 30; // 30-60%
        cpuStat.textContent = newValue + '%';
        animateStatCard(cpuStat.parentElement.parentElement);
    }
    
    if (memoryStat) {
        const newValue = (Math.random() * 4 + 6).toFixed(1); // 6.0-10.0GB
        memoryStat.textContent = newValue + 'GB';
    }
    
    if (gpuStat) {
        const newValue = Math.floor(Math.random() * 40) + 50; // 50-90%
        gpuStat.textContent = newValue + '%';
    }
    
    if (tasksStat) {
        const newValue = Math.floor(Math.random() * 10) + 8; // 8-18
        tasksStat.textContent = newValue;
    }
}

// 更新檢測列表
function updateDetectionList() {
    // 模擬新的檢測結果
    const detectionList = document.querySelector('.detection-list');
    if (detectionList && Math.random() > 0.7) { // 30% 機率更新
        const newDetection = createDetectionItem();
        detectionList.insertBefore(newDetection, detectionList.firstChild);
        
        // 限制列表長度
        if (detectionList.children.length > 5) {
            detectionList.removeChild(detectionList.lastChild);
        }
    }
}

// 創建檢測項目
function createDetectionItem() {
    const item = document.createElement('div');
    item.className = 'detection-item';
    item.style.opacity = '0';
    item.style.transform = 'translateY(-10px)';
    
    const objectCount = Math.floor(Math.random() * 5) + 1;
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];
    
    item.innerHTML = `
        <div class="detection-thumb">
            <div style="background: linear-gradient(135deg, ${randomColor}, ${randomColor}aa); width: 60px; height: 40px; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; font-weight: bold;">IMG</div>
        </div>
        <div class="detection-info">
            <div class="detection-title">檢測到 ${objectCount} 個物件</div>
            <div class="detection-time">剛剛</div>
        </div>
        <div class="detection-status">
            <span class="status-badge success">完成</span>
        </div>
    `;
    
    // 動畫效果
    setTimeout(() => {
        item.style.transition = 'all 0.3s ease-out';
        item.style.opacity = '1';
        item.style.transform = 'translateY(0)';
    }, 10);
    
    return item;
}

// 統計卡片動畫
function animateStatCard(card) {
    card.style.transform = 'scale(1.02)';
    setTimeout(() => {
        card.style.transform = 'scale(1)';
    }, 200);
}

// 通知面板
function showNotificationPanel() {
    // 創建通知面板
    const panel = document.createElement('div');
    panel.className = 'notification-panel';
    panel.innerHTML = `
        <div class="notification-header">
            <h3>通知</h3>
            <button class="close-btn">&times;</button>
        </div>
        <div class="notification-content">
            <div class="notification-item">
                <i class="fas fa-info-circle text-info"></i>
                <div>
                    <div class="notification-title">系統更新</div>
                    <div class="notification-text">YOLOv11 模型已更新至最新版本</div>
                    <div class="notification-time">2 分鐘前</div>
                </div>
            </div>
            <div class="notification-item">
                <i class="fas fa-exclamation-triangle text-warning"></i>
                <div>
                    <div class="notification-title">儲存空間警告</div>
                    <div class="notification-text">儲存空間使用率已達 85%</div>
                    <div class="notification-time">10 分鐘前</div>
                </div>
            </div>
            <div class="notification-item">
                <i class="fas fa-check-circle text-success"></i>
                <div>
                    <div class="notification-title">分析完成</div>
                    <div class="notification-text">影片分析任務已完成</div>
                    <div class="notification-time">1 小時前</div>
                </div>
            </div>
        </div>
    `;
    
    // 添加樣式和事件
    document.body.appendChild(panel);
    
    // 關閉按鈕事件
    panel.querySelector('.close-btn').addEventListener('click', () => {
        panel.remove();
    });
    
    // 點擊外部關閉
    panel.addEventListener('click', (e) => {
        if (e.target === panel) {
            panel.remove();
        }
    });
}

// 用戶選單
function showUserMenu() {
    console.log('顯示用戶選單');
    // 實現用戶選單功能
}

// 快速操作處理
function handleQuickAction(action) {
    console.log('執行快速操作:', action);
    
    // 顯示操作回饋
    showToast(`正在執行: ${action}`, 'info');
    
    // 模擬操作延遲
    setTimeout(() => {
        showToast(`${action} 完成！`, 'success');
    }, 2000);
}

// 攝影機操作
function handleCameraPlay(button) {
    const icon = button.querySelector('i');
    if (icon.classList.contains('fa-play')) {
        icon.className = 'fas fa-pause';
        showToast('攝影機已開始串流', 'success');
    } else {
        icon.className = 'fas fa-play';
        showToast('攝影機已停止串流', 'info');
    }
}

function handleCameraConfig(button) {
    showToast('開啟攝影機配置', 'info');
}

// 提示訊息
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // 添加樣式
    toast.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease-out;
    `;
    
    // 設置顏色
    const colors = {
        info: '#3b82f6',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444'
    };
    toast.style.backgroundColor = colors[type] || colors.info;
    
    document.body.appendChild(toast);
    
    // 顯示動畫
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 10);
    
    // 自動消失
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// 響應式處理
window.addEventListener('resize', function() {
    const sidebar = document.querySelector('.sidebar');
    if (window.innerWidth > 1024) {
        sidebar.classList.remove('show');
    }
});

// 鍵盤快捷鍵
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K 快速搜尋
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-box input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // ESC 關閉側邊欄（手機版）
    if (e.key === 'Escape') {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.remove('show');
    }
});

// ===== 第二階段功能：任務排程系統 =====

// 任務數據
const tasks = [
    {
        id: 'task_001',
        name: '前門監控分析',
        type: 'realtime',
        status: 'running',
        progress: 75,
        camera: '前門攝影機',
        startTime: new Date(Date.now() - 3600000),
        model: 'YOLOv11s'
    },
    {
        id: 'task_002',
        name: '停車場車輛計數',
        type: 'scheduled',
        status: 'pending',
        progress: 0,
        camera: '停車場攝影機',
        startTime: new Date(Date.now() + 1800000),
        model: 'YOLOv11m'
    },
    {
        id: 'task_003',
        name: '影片批次分析',
        type: 'batch',
        status: 'completed',
        progress: 100,
        camera: 'Video File',
        startTime: new Date(Date.now() - 7200000),
        model: 'YOLOv11l'
    }
];

// 快速任務創建
function createQuickTask(type) {
    console.log(`創建 ${type} 任務`);
    
    const taskNames = {
        'realtime': '即時監控任務',
        'batch': '批次處理任務',
        'scheduled': '排程任務',
        'event': '事件觸發任務'
    };
    
    // 模擬創建任務
    const newTask = {
        id: `task_${Date.now()}`,
        name: taskNames[type] || '新任務',
        type: type,
        status: 'pending',
        progress: 0,
        camera: '預設攝影機',
        startTime: new Date(),
        model: 'YOLOv11s'
    };
    
    tasks.unshift(newTask);
    updateTaskStats();
    renderActiveTasks();
    
    // 顯示成功消息
    showNotification(`${taskNames[type]} 已創建`, 'success');
}

// 更新任務統計
function updateTaskStats() {
    const runningTasks = tasks.filter(t => t.status === 'running').length;
    const pendingTasks = tasks.filter(t => t.status === 'pending').length;
    const completedTasks = tasks.filter(t => t.status === 'completed').length;
    const failedTasks = tasks.filter(t => t.status === 'failed').length;
    
    const runningEl = document.getElementById('runningTasks');
    const pendingEl = document.getElementById('pendingTasks');
    const completedEl = document.getElementById('completedTasks');
    const failedEl = document.getElementById('failedTasks');
    
    if (runningEl) runningEl.textContent = runningTasks;
    if (pendingEl) pendingEl.textContent = pendingTasks;
    if (completedEl) completedEl.textContent = completedTasks;
    if (failedEl) failedEl.textContent = failedTasks;
}

// 渲染執行中任務
function renderActiveTasks() {
    const container = document.getElementById('activeTasksList');
    if (!container) return;
    
    const activeTasks = tasks.filter(t => t.status === 'running' || t.status === 'pending');
    
    container.innerHTML = activeTasks.map(task => `
        <div class="task-item">
            <div class="task-item-header">
                <div class="task-item-title">${task.name}</div>
                <div class="task-item-status task-status-${task.status}">
                    ${getStatusText(task.status)}
                </div>
            </div>
            <div class="task-item-details">
                <small class="text-muted">
                    <i class="fas fa-camera"></i> ${task.camera} | 
                    <i class="fas fa-brain"></i> ${task.model} | 
                    <i class="fas fa-clock"></i> ${formatTime(task.startTime)}
                </small>
            </div>
            <div class="task-progress">
                <div class="task-progress-bar" style="width: ${task.progress}%"></div>
            </div>
            <div class="task-actions mt-2">
                <button class="btn btn-sm btn-outline-primary" onclick="viewTaskDetails('${task.id}')">
                    <i class="fas fa-eye"></i> 查看
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="stopTask('${task.id}')">
                    <i class="fas fa-stop"></i> 停止
                </button>
            </div>
        </div>
    `).join('');
}

// 獲取狀態文字
function getStatusText(status) {
    const statusMap = {
        'running': '執行中',
        'pending': '等待中',
        'completed': '已完成',
        'failed': '失敗'
    };
    return statusMap[status] || status;
}

// 格式化時間
function formatTime(date) {
    return date.toLocaleTimeString('zh-TW', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 刷新執行中任務
function refreshActiveTasks() {
    // 模擬更新任務進度
    tasks.forEach(task => {
        if (task.status === 'running' && task.progress < 100) {
            task.progress = Math.min(100, task.progress + Math.random() * 10);
            if (task.progress >= 100) {
                task.status = 'completed';
            }
        }
    });
    
    updateTaskStats();
    renderActiveTasks();
}

// 查看任務詳情
function viewTaskDetails(taskId) {
    const task = tasks.find(t => t.id === taskId);
    if (task) {
        alert(`任務詳情：\n名稱：${task.name}\n狀態：${getStatusText(task.status)}\n進度：${task.progress}%`);
    }
}

// 停止任務
function stopTask(taskId) {
    const taskIndex = tasks.findIndex(t => t.id === taskId);
    if (taskIndex !== -1) {
        tasks[taskIndex].status = 'stopped';
        updateTaskStats();
        renderActiveTasks();
        showNotification('任務已停止', 'warning');
    }
}

// ===== 第二階段功能：多攝影機管理 =====

// 攝影機群組數據
const cameraGroups = [
    { id: 'group_1', name: '主要出入口', cameras: ['cam_001', 'cam_002'], count: 2 },
    { id: 'group_2', name: '停車區域', cameras: ['cam_003', 'cam_004', 'cam_005'], count: 3 },
    { id: 'group_3', name: '公共區域', cameras: ['cam_006'], count: 1 }
];

// 攝影機數據
const cameras = [
    { id: 'cam_001', name: '前門攝影機', status: 'online', type: 'USB', resolution: '1920x1080' },
    { id: 'cam_002', name: '後門攝影機', status: 'offline', type: 'Network', resolution: '1280x720' },
    { id: 'cam_003', name: '停車場東側', status: 'online', type: 'Network', resolution: '1920x1080' },
    { id: 'cam_004', name: '停車場西側', status: 'online', type: 'Network', resolution: '1920x1080' },
    { id: 'cam_005', name: '停車場南側', status: 'online', type: 'Network', resolution: '1280x720' },
    { id: 'cam_006', name: '大廳攝影機', status: 'online', type: 'USB', resolution: '1920x1080' }
];

// 當前網格布局
let currentGridLayout = '2x2';

// 創建攝影機群組
function createCameraGroup() {
    const groupName = prompt('請輸入群組名稱：');
    if (groupName) {
        const newGroup = {
            id: `group_${Date.now()}`,
            name: groupName,
            cameras: [],
            count: 0
        };
        cameraGroups.push(newGroup);
        renderCameraGroups();
        showNotification(`攝影機群組 "${groupName}" 已創建`, 'success');
    }
}

// 渲染攝影機群組
function renderCameraGroups() {
    const container = document.getElementById('cameraGroups');
    if (!container) return;
    
    container.innerHTML = cameraGroups.map(group => `
        <div class="camera-group-item" onclick="selectCameraGroup('${group.id}')">
            <div class="camera-group-name">${group.name}</div>
            <div class="camera-group-count">${group.count} 個攝影機</div>
        </div>
    `).join('');
}

// 選擇攝影機群組
function selectCameraGroup(groupId) {
    const group = cameraGroups.find(g => g.id === groupId);
    if (group) {
        console.log(`選擇群組：${group.name}`);
        showNotification(`已選擇群組：${group.name}`, 'info');
    }
}

// 改變網格布局
function changeGridLayout(layout) {
    currentGridLayout = layout;
    const container = document.getElementById('cameraGridDisplay');
    if (!container) return;
    
    // 移除舊的布局類別
    container.classList.remove('camera-grid-2x2', 'camera-grid-3x3', 'camera-grid-4x4');
    // 添加新的布局類別
    container.classList.add(`camera-grid-${layout}`);
    
    renderCameraGrid();
    showNotification(`網格布局已切換為 ${layout}`, 'info');
}

// 渲染攝影機網格
function renderCameraGrid() {
    const container = document.getElementById('cameraGridDisplay');
    if (!container) return;
    
    const maxCameras = currentGridLayout === '2x2' ? 4 : 
                      currentGridLayout === '3x3' ? 9 : 16;
    
    const displayCameras = cameras.slice(0, maxCameras);
    
    container.innerHTML = displayCameras.map((camera, index) => `
        <div class="camera-grid-item ${camera.status === 'online' ? 'active' : ''}" data-camera="${camera.id}">
            <div class="camera-grid-placeholder">
                <i class="fas fa-video"></i>
            </div>
            <div class="camera-grid-overlay">
                <div class="camera-grid-name">${camera.name}</div>
            </div>
            <div class="camera-grid-status ${camera.status}"></div>
            <div class="camera-grid-controls">
                <button class="camera-control-btn" onclick="toggleCamera('${camera.id}')">
                    <i class="fas fa-${camera.status === 'online' ? 'pause' : 'play'}"></i>
                </button>
                <button class="camera-control-btn" onclick="configCamera('${camera.id}')">
                    <i class="fas fa-cog"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// 切換攝影機狀態
function toggleCamera(cameraId) {
    const camera = cameras.find(c => c.id === cameraId);
    if (camera) {
        camera.status = camera.status === 'online' ? 'offline' : 'online';
        renderCameraGrid();
        renderCameraGroups();
        showNotification(`攝影機 ${camera.name} 已${camera.status === 'online' ? '啟動' : '停止'}`, 
                        camera.status === 'online' ? 'success' : 'warning');
    }
}

// 配置攝影機
function configCamera(cameraId) {
    const camera = cameras.find(c => c.id === cameraId);
    if (camera) {
        alert(`配置攝影機：${camera.name}\n類型：${camera.type}\n解析度：${camera.resolution}`);
    }
}

// 啟動所有攝影機
function startAllCameras() {
    cameras.forEach(camera => {
        camera.status = 'online';
    });
    renderCameraGrid();
    renderCameraGroups();
    showNotification('所有攝影機已啟動', 'success');
}

// 停止所有攝影機
function stopAllCameras() {
    cameras.forEach(camera => {
        camera.status = 'offline';
    });
    renderCameraGrid();
    renderCameraGroups();
    showNotification('所有攝影機已停止', 'warning');
}

// ===== 第二階段功能：統計分析增強 =====

// 初始化增強圖表
function initEnhancedCharts() {
    // 趨勢分析圖表
    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: Array.from({length: 24}, (_, i) => `${i}:00`),
                datasets: [{
                    label: '人員檢測',
                    data: Array.from({length: 24}, () => Math.floor(Math.random() * 100)),
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4
                }, {
                    label: '車輛檢測',
                    data: Array.from({length: 24}, () => Math.floor(Math.random() * 50)),
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // 物件類型分布圖表
    const categoryCtx = document.getElementById('categoryChart');
    if (categoryCtx) {
        new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: ['人員', '車輛', '自行車', '其他'],
                datasets: [{
                    data: [45, 30, 15, 10],
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#4BC0C0'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // 時段分析圖表
    const timeCtx = document.getElementById('timeAnalysisChart');
    if (timeCtx) {
        new Chart(timeCtx, {
            type: 'bar',
            data: {
                labels: ['00-06', '06-12', '12-18', '18-24'],
                datasets: [{
                    label: '活動強度',
                    data: [20, 80, 100, 60],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
}

// 顯示通知功能增強
function showNotification(message, type = 'info') {
    // 創建通知元素
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // 自動移除通知
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

// 分析頁面專用函數
function setAnalyticsPeriod(period) {
    AnalyticsManager.setPeriod(period);
}

function showDetectionDetail(detectionId) {
    // 顯示檢測詳情模態框
    fetch(`${API_CONFIG.baseURL}/api/v1/frontend/detection-results/${detectionId}`)
        .then(response => {
            if (!response.ok) throw new Error('載入檢測詳情失敗');
            return response.json();
        })
        .then(data => {
            const modalContent = `
                <div class="modal fade" id="detectionDetailModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">檢測詳情</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <p><strong>時間:</strong> ${new Date(data.timestamp).toLocaleString('zh-TW')}</p>
                                        <p><strong>攝像頭:</strong> ${data.camera_id || 'N/A'}</p>
                                        <p><strong>物件類型:</strong> ${data.object_type || '未知'}</p>
                                        <p><strong>信心度:</strong> ${Math.round(data.confidence * 100)}%</p>
                                    </div>
                                    <div class="col-md-6">
                                        <p><strong>狀態:</strong> ${data.status === 'completed' ? '已完成' : '處理中'}</p>
                                        <p><strong>處理時間:</strong> ${data.processing_time || 'N/A'}ms</p>
                                        <p><strong>檢測區域:</strong> ${data.bbox ? `${data.bbox}` : 'N/A'}</p>
                                    </div>
                                </div>
                                ${data.image_url ? `<div class="mt-3"><img src="${data.image_url}" class="img-fluid" alt="檢測圖像"></div>` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 移除現有模態框並添加新的
            const existingModal = document.getElementById('detectionDetailModal');
            if (existingModal) existingModal.remove();
            
            document.body.insertAdjacentHTML('beforeend', modalContent);
            
            // 顯示模態框
            const modal = new bootstrap.Modal(document.getElementById('detectionDetailModal'));
            modal.show();
        })
        .catch(error => {
            console.error('載入檢測詳情失敗:', error);
            showNotification('載入檢測詳情失敗: ' + error.message, 'danger');
        });
}

function exportAnalyticsData(format) {
    AnalyticsManager.exportData(format);
}

// 分析頁面相關函數
function refreshAnalytics() {
    AnalyticsManager.loadAnalytics();
}

function exportDetectionResults() {
    exportAnalyticsData('csv');
}

function refreshDetectionResults() {
    AnalyticsManager.loadDetectionResults();
}

// 注意：主要初始化邏輯已移至 script_api.js
// 以下函數保留供向後兼容

// 導航初始化（已移至 script_api.js）
function initNavigation() {
    console.log('✓ 導航功能由 script_api.js 處理');
}

// 主題切換初始化（已移至 script_api.js）
function initThemeToggle() {
    console.log('✓ 主題切換由 script_api.js 處理');
}
