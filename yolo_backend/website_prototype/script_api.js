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
                return 'ws://localhost:8001/ws/system-stats';
            } else {
                return `ws://${currentHost}:8001/ws/system-stats`;
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
    static async request(method, endpoint, params = {}) {
        let url = `${API_CONFIG.baseURL}/api/v1${endpoint}`;
        
        const defaultOptions = {
            method: method.toUpperCase(),
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };

        // 處理GET請求的查詢參數
        if (method.toUpperCase() === 'GET' && params && Object.keys(params).length > 0) {
            const queryString = new URLSearchParams(params).toString();
            url += `?${queryString}`;
        }
        
        // 處理POST/PUT請求的body
        if (['POST', 'PUT', 'PATCH'].includes(method.toUpperCase()) && params) {
            defaultOptions.body = JSON.stringify(params);
        }
        
        try {
            const response = await fetch(url, defaultOptions);
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
        return this.request('GET', `/health`);
    }

    // 獲取系統統計
    static async getSystemStats() {
        return this.request('GET', `/frontend/stats`);
    }

    // 任務管理 API
    static async getTasks() {
        return this.request('GET', `/frontend/tasks`);
    }

    static async createTask(taskData) {
        return this.request('POST', `/frontend/tasks`, taskData);
    }

    static async startTask(taskId) {
        return this.request('POST', `/frontend/tasks/${taskId}/start`);
    }

    static async stopTask(taskId) {
        return this.request('POST', `/frontend/tasks/${taskId}/stop`);
    }

    static async deleteTask(taskId) {
        return this.request('DELETE', `/frontend/tasks/${taskId}`);
    }

    // 攝影機管理 API
    static async getCameras() {
        return this.request('GET', `/frontend/cameras`);
    }

    static async scanCameras() {
        return this.request('POST', `/frontend/cameras/scan`);
    }

    static async refreshCameras() {
        return this.request('POST', `/frontend/cameras/refresh`);
    }

    static async testCamera(cameraId) {
        return this.request('POST', `/frontend/cameras/${cameraId}/test`);
    }

    static async getCameraPreview(cameraIndex) {
        const url = `${API_CONFIG.baseURL}/api/v1/frontend/cameras/${cameraIndex}/preview`;
        return fetch(url, {
            method: 'GET',
            headers: {
                'Cache-Control': 'no-cache'
            }
        });
    }

    static getCameraStreamUrl(cameraIndex) {
        return `${API_CONFIG.baseURL}/api/v1/frontend/cameras/${cameraIndex}/stream`;
    }

    // 分析與統計 API
    static async getAnalytics(period = '24h') {
        return this.request('GET', `/frontend/analytics`, { period });
    }

    static async exportData(format = 'json') {
        return this.request('GET', `/frontend/export`, { format });
    }

    // YOLO 模型管理 API
    static async getAvailableModels() {
        return this.request('GET', `/frontend/models`);
    }

    static async getCurrentModel() {
        return this.request('GET', `/frontend/models/current`);
    }

    static async loadModel(modelId) {
        return this.request('POST', `/frontend/models/load`, { model_id: modelId });
    }

    static async unloadModel(modelId) {
        return this.request('POST', `/frontend/models/unload`, { model_id: modelId });
    }

    static async getModelConfig() {
        return this.request('GET', `/frontend/models/config`);
    }

    static async updateModelConfig(config) {
        return this.request('PUT', `/frontend/models/config`, config);
    }

    // 系統配置 API
    static async getConfig() {
        return this.request('GET', `/frontend/config`);
    }

    static async updateConfig(configData) {
        return this.request('PUT', `/frontend/config`, configData);
    }

    // 通知顯示
    static showNotification(message, type = 'info') {
        // 創建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 20px;
            background: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#51cf66' : '#74c0fc'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease;
            max-width: 300px;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);

        // 自動移除
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
}

// 添加通知樣式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

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
            // 如果已有連接且狀態正常，不重複連接
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                console.log('WebSocket 已經連接');
                return;
            }

            // 關閉舊連接
            if (this.ws) {
                this.ws.close();
            }

            this.ws = new WebSocket(API_CONFIG.endpoints.websocket);
            
            this.ws.onopen = () => {
                console.log('WebSocket 連接成功');
                AppState.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
                APIClient.showNotification('即時監控連接成功', 'success');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('解析 WebSocket 消息失敗:', error);
                }
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket 連接關閉', event.code, event.reason);
                AppState.isConnected = false;
                this.updateConnectionStatus(false);
                
                // 只有在非正常關閉時才嘗試重連
                if (event.code !== 1000) {
                    this.attemptReconnect();
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket 錯誤:', error);
                AppState.isConnected = false;
                this.updateConnectionStatus(false);
            };

        } catch (error) {
            console.error('WebSocket 連接失敗:', error);
            APIClient.showNotification('即時監控連接失敗', 'error');
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'User disconnected');
            this.ws = null;
        }
        AppState.isConnected = false;
        this.updateConnectionStatus(false);
    }

    handleMessage(data) {
        switch(data.type) {
            case 'system_stats':
                AppState.systemStats = data.data;
                DashboardManager.updateStats(data.data);
                break;
            case 'task_update':
                TaskManager.updateTaskInUI(data.data);
                break;
            case 'camera_status':
                CameraManager.updateCameraInUI(data.data);
                break;
            case 'detection_result':
                AnalyticsManager.addDetectionResult(data.data);
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
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`嘗試重新連接... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                if (!AppState.isConnected) {
                    this.connect();
                }
            }, this.reconnectInterval);
        } else {
            console.log('達到最大重連次數，停止重連');
            APIClient.showNotification('即時監控連接失敗，請重新整理頁面', 'error');
        }
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
        
        console.log('NavigationManager 初始化:', {
            navLinksCount: navLinks.length,
            contentSectionsCount: contentSections.length,
            hasBreadcrumb: !!breadcrumb
        });
        
        // 檢查每個導航連結的結構
        navLinks.forEach((link, index) => {
            const hasParent = !!link.parentElement;
            const hasSpan = !!link.querySelector('span');
            console.log(`導航連結 ${index}:`, {
                hasParent,
                hasSpan,
                href: link.getAttribute('href'),
                dataSection: link.getAttribute('data-section')
            });
        });
        
        navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const targetSection = this.getAttribute('data-section');
                const href = this.getAttribute('href');
                
                console.log('導航連結被點擊:', {
                    targetSection,
                    href,
                    linkText: this.querySelector('span')?.textContent
                });
                
                // 如果連結指向外部頁面或文件，讓瀏覽器正常處理
                if (href && (href.endsWith('.html') || 
                    href.startsWith('http') || 
                    href.startsWith('/website/') ||
                    href.includes('data_source'))) {
                    console.log('允許導航到外部頁面:', href);
                    return; // 不阻止預設行為
                }
                
                // 對內部錨點導航進行特殊處理
                if (href && href.startsWith('#') && targetSection) {
                    e.preventDefault();
                    console.log('處理內部導航:', targetSection);
                    
                    // 使用統一的分頁切換方法
                    NavigationManager.switchToSection(targetSection);
                } else {
                    console.log('不符合內部導航條件，讓瀏覽器處理');
                }
            });
        });

        // 側邊欄切換
        NavigationManager.initSidebarToggle();
        
        // 系統停止功能
        NavigationManager.initSystemShutdown();
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

    static initSystemShutdown() {
        console.log('🔧 初始化停止系統功能...');
        
        const shutdownBtn = document.querySelector('.system-shutdown');
        
        if (!shutdownBtn) {
            console.error('❌ 找不到停止系統按鈕元素');
            return;
        }
        
        console.log('✅ 找到停止系統按鈕:', shutdownBtn);
        
        // 移除之前的事件監聽器（如果存在）
        const existingHandler = shutdownBtn._shutdownHandler;
        if (existingHandler) {
            shutdownBtn.removeEventListener('click', existingHandler);
            console.log('🗑️ 移除舊的事件監聽器');
        }
        
        // 確保按鈕可以點擊
        shutdownBtn.style.pointerEvents = 'auto';
        shutdownBtn.style.cursor = 'pointer';
        shutdownBtn.style.zIndex = '9999';
        shutdownBtn.style.position = 'relative';
        
        // 添加視覺調試
        console.log('🎯 按鈕CSS屬性檢查:');
        console.log('  pointerEvents:', getComputedStyle(shutdownBtn).pointerEvents);
        console.log('  cursor:', getComputedStyle(shutdownBtn).cursor);
        console.log('  zIndex:', getComputedStyle(shutdownBtn).zIndex);
        console.log('  position:', getComputedStyle(shutdownBtn).position);
        
        // 添加hover測試
        shutdownBtn.addEventListener('mouseenter', function() {
            console.log('🖱️ 滑鼠進入停止按鈕');
        });
        
        shutdownBtn.addEventListener('mouseleave', function() {
            console.log('🖱️ 滑鼠離開停止按鈕');
        });
        
        // 創建新的事件處理器
        const shutdownHandler = async function(event) {
            console.log('🔴 停止系統按鈕被點擊');
            event.preventDefault();
            event.stopPropagation();
            
            // 顯示確認對話框
            const confirmed = confirm(
                '您確定要停止系統嗎？\n\n' +
                '這將關閉整個YOLOv11分析系統，\n' +
                '所有正在執行的任務都會被終止。\n\n' +
                '點擊確定繼續，或取消返回。'
            );
            
            if (!confirmed) {
                console.log('⏹️ 用戶取消停止操作');
                return;
            }
            
            try {
                console.log('🚀 開始停止系統...');
                
                // 顯示停止中的狀態
                const icon = this.querySelector('i');
                const span = this.querySelector('span');
                const originalContent = { icon: icon.className, text: span.textContent };
                
                icon.className = 'fas fa-spinner fa-spin';
                span.textContent = '停止中...';
                this.style.pointerEvents = 'none';
                
                console.log('📡 發送停止請求到服務器...');
                
                // 發送停止請求 - 使用完整的API URL
                const shutdownURL = `${API_CONFIG.baseURL}/api/v1/frontend/system/shutdown`;
                console.log('🌐 停止API URL:', shutdownURL);
                
                const response = await fetch(shutdownURL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                console.log('📨 服務器回應:', response.status);
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('✅ 停止請求成功:', result);
                    
                    // 顯示成功訊息
                    span.textContent = '已停止';
                    icon.className = 'fas fa-check';
                    
                    // 簡單的提示訊息，不跳轉頁面
                    setTimeout(() => {
                        alert('✅ 系統已安全停止\n\n重新啟動請執行: python start.py');
                    }, 1000);
                    
                } else {
                    throw new Error(`停止失敗: ${response.status}`);
                }
                
            } catch (error) {
                console.error('❌ 停止系統失敗:', error);
                
                // 恢復按鈕狀態
                icon.className = originalContent.icon;
                span.textContent = originalContent.text;
                this.style.pointerEvents = 'auto';
                
                alert('停止系統失敗：' + error.message);
            }
        };
        
        // 保存事件處理器的引用，以便後續移除
        shutdownBtn._shutdownHandler = shutdownHandler;
        
        // 添加多種事件監聽器以確保可點擊（瀏覽器相容性）
        shutdownBtn.addEventListener('click', shutdownHandler, { passive: false });
        shutdownBtn.addEventListener('touchstart', shutdownHandler, { passive: false }); // 觸控支援
        shutdownBtn.addEventListener('mousedown', function(e) {
            console.log('🖱️ 滑鼠按下事件');
        }, { passive: false }); // 滑鼠按下
        
        // Chrome 特別支援 - 簡化版本
        shutdownBtn.onclick = function(e) {
            console.log('🔥 Chrome兼容 - onclick屬性觸發');
            e.preventDefault();
            e.stopPropagation();
            shutdownHandler.call(this, e);
            return false;
        };
        
        // 確保Chrome事件正確觸發
        shutdownBtn.addEventListener('click', function(e) {
            console.log('🔥 Chrome兼容 - addEventListener click觸發');
        }, true);
        
        console.log('✅ 停止系統事件監聽器已綁定');
        
        // Chrome瀏覽器特別處理
        if (navigator.userAgent.includes('Chrome')) {
            console.log('🌐 偵測到Chrome瀏覽器，啟用兼容模式');
            
            // 強制重新應用樣式
            shutdownBtn.style.display = 'flex';
            shutdownBtn.style.cursor = 'pointer';
            shutdownBtn.style.pointerEvents = 'auto';
            shutdownBtn.style.touchAction = 'manipulation';
            
            // 添加Chrome專用的點擊處理
            shutdownBtn.setAttribute('role', 'button');
            shutdownBtn.setAttribute('tabindex', '0');
            
            // 鍵盤支援（Chrome有時需要）
            shutdownBtn.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    console.log('⌨️ Chrome鍵盤事件觸發');
                    e.preventDefault();
                    shutdownHandler.call(this, e);
                }
            });
        }
        
        // 強制測試按鈕是否可見且可點擊
        const rect = shutdownBtn.getBoundingClientRect();
        console.log('📏 按鈕位置信息:', {
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height,
            visible: rect.width > 0 && rect.height > 0
        });
        
        // 添加額外的測試事件
        shutdownBtn.addEventListener('mouseenter', function() {
            console.log('🖱️ 鼠標進入停止按鈕');
        });
        
        // 全局測試函數
        window.testShutdownButton = function() {
            console.log('🧪 手動測試停止按鈕');
            shutdownHandler();
        };
        
        // 全局API測試函數
        window.testShutdownAPI = async function() {
            console.log('🧪 直接測試停止API');
            const shutdownURL = `${API_CONFIG.baseURL}/api/v1/frontend/system/shutdown`;
            console.log('🌐 測試URL:', shutdownURL);
            
            try {
                const response = await fetch(shutdownURL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                console.log('📨 API回應狀態:', response.status);
                const result = await response.json();
                console.log('📨 API回應內容:', result);
                return result;
            } catch (error) {
                console.error('❌ API測試失敗:', error);
                return null;
            }
        };
        
        // 全局強制點擊測試
        window.forceClickShutdown = function() {
            console.log('🔨 強制點擊停止按鈕');
            const btn = document.querySelector('.system-shutdown');
            if (btn) {
                console.log('✅ 找到按鈕，模擬點擊');
                btn.click();
                // 也嘗試觸發自定義事件
                btn.dispatchEvent(new Event('click', { bubbles: true }));
            } else {
                console.error('❌ 找不到按鈕');
            }
        };
        
        // 全局按鈕診斷
        window.diagnoseShutdownButton = function() {
            const btn = document.querySelector('.system-shutdown');
            if (!btn) {
                console.error('❌ 找不到停止按鈕');
                return;
            }
            
            console.log('🔍 按鈕診斷信息:');
            console.log('  元素:', btn);
            console.log('  顯示狀態:', getComputedStyle(btn).display);
            console.log('  可見性:', getComputedStyle(btn).visibility);
            console.log('  透明度:', getComputedStyle(btn).opacity);
            console.log('  指標事件:', getComputedStyle(btn).pointerEvents);
            console.log('  z-index:', getComputedStyle(btn).zIndex);
            
            const rect = btn.getBoundingClientRect();
            console.log('  位置:', rect);
            console.log('  父元素:', btn.parentElement);
            
            // 檢查是否被其他元素覆蓋
            const elementAtPoint = document.elementFromPoint(
                rect.left + rect.width / 2,
                rect.top + rect.height / 2
            );
            console.log('  該位置的最上層元素:', elementAtPoint);
            console.log('  是否是按鈕本身:', elementAtPoint === btn);
        };
    }
    
    static handleInitialHash() {
        const hash = window.location.hash.replace('#', '');
        if (hash) {
            console.log('初始 hash 處理:', hash);
            NavigationManager.switchToSection(hash);
        } else {
            console.log('無初始 hash，載入預設分頁');
            // 沒有 hash 則切換到預設頁面（儀表板）並更新 URL
            NavigationManager.switchToSection('dashboard');
        }
    }
    
    static handleHashChange() {
        const hash = window.location.hash.replace('#', '');
        console.log('Hash 變化:', hash);
        if (hash) {
            // 只有當新的 hash 與當前活躍分頁不同時才切換
            if (hash !== AppState.activeSection) {
                NavigationManager.switchToSectionWithoutURLUpdate(hash);
            }
        } else {
            // 如果 hash 被清空，回到預設分頁
            if (AppState.activeSection !== 'dashboard') {
                NavigationManager.switchToSectionWithoutURLUpdate('dashboard');
            }
        }
    }
    
    static switchToSectionWithoutURLUpdate(sectionName) {
        console.log('切換到分頁（不更新URL）:', sectionName);
        
        // 移除所有活躍狀態
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // 找到對應的導航項目並激活
        const navLink = document.querySelector(`[data-section="${sectionName}"]`);
        if (navLink && navLink.parentElement) {
            navLink.parentElement.classList.add('active');
            
            // 更新麵包屑
            const breadcrumb = document.querySelector('.current-page');
            const linkText = navLink.querySelector('span');
            if (breadcrumb && linkText) {
                breadcrumb.textContent = linkText.textContent;
            }
        }
        
        // 顯示對應的內容區塊
        const targetElement = document.getElementById(sectionName);
        if (targetElement) {
            targetElement.classList.add('active');
            AppState.activeSection = sectionName;
            
            // 不更新 URL，因為這是由 hash 變化觸發的
            
            // 載入對應區塊的數據
            NavigationManager.loadSectionData(sectionName);
        } else {
            console.warn(`找不到分頁: ${sectionName}`);
        }
    }
    
    static switchToSection(sectionName) {
        console.log('切換到分頁:', sectionName);
        
        // 移除所有活躍狀態
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // 找到對應的導航項目並激活
        const navLink = document.querySelector(`[data-section="${sectionName}"]`);
        if (navLink && navLink.parentElement) {
            navLink.parentElement.classList.add('active');
            
            // 更新麵包屑
            const breadcrumb = document.querySelector('.current-page');
            const linkText = navLink.querySelector('span');
            if (breadcrumb && linkText) {
                breadcrumb.textContent = linkText.textContent;
            }
        }
        
        // 顯示對應的內容區塊
        const targetElement = document.getElementById(sectionName);
        if (targetElement) {
            targetElement.classList.add('active');
            AppState.activeSection = sectionName;
            
            // 統一更新 URL fragment（所有分頁切換都會更新網址）
            const newHash = `#${sectionName}`;
            if (window.location.hash !== newHash) {
                // 使用 pushState 而不是直接修改 hash，避免觸發 hashchange 事件
                window.history.pushState(null, null, newHash);
                console.log('已更新網址:', newHash);
            }
            
            // 載入對應區塊的數據
            NavigationManager.loadSectionData(sectionName);
        } else {
            console.warn(`找不到分頁: ${sectionName}，載入預設頁面`);
            // 如果找不到對應分頁，載入預設頁面
            NavigationManager.switchToSection('dashboard');
        }
    }

    static async loadSectionData(section) {
        try {
            // 確保系統停止功能在每個分頁都正常工作
            NavigationManager.initSystemShutdown();
            
            console.log('載入分頁數據:', section);
            
            switch(section) {
                case 'dashboard':
                    await DashboardManager.loadData();
                    break;
                case 'ai-engine':
                    // 重新初始化 YOLO 管理器以確保事件正確綁定
                    if (window.yoloManager) {
                        window.yoloManager.init();
                    }
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
                case 'data-management':
                    await window.DataManager.loadDataManagement();
                    break;
                case 'config':
                    await ConfigManager.loadConfig();
                    break;
                default:
                    console.log('未知分頁，載入預設數據');
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
        } catch (error) {
            console.error('載入儀表板數據失敗:', error);
            APIClient.showNotification('無法載入系統統計數據', 'error');
        }
    }

    static updateStats(stats) {
        // 更新統計卡片
        const statElements = {
            'cpu-usage': stats.cpu_usage.toFixed(1) + '%',
            'memory-usage': stats.memory_usage.toFixed(1) + '%',
            'gpu-usage': stats.gpu_usage !== undefined ? stats.gpu_usage.toFixed(1) + '%' : 'N/A',
            'active-tasks': stats.active_tasks.toString(),
            'total-detections': stats.total_detections.toString()
        };

        Object.entries(statElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });

        // 更新系統狀態指示器
        const statusElement = document.querySelector('.system-status');
        if (statusElement) {
            // 根據系統負載判斷狀態
            const cpuHigh = stats.cpu_usage > 80;
            const memoryHigh = stats.memory_usage > 85;
            const isHealthy = !cpuHigh && !memoryHigh;
            
            const status = isHealthy ? '正常運行' : '負載較高';
            const statusClass = isHealthy ? 'status-good' : 'status-warning';
            statusElement.innerHTML = `<span class="${statusClass}">${status}</span>`;
        }

        // 更新進度條
        this.updateProgressBars(stats);
    }

    static updateProgressBars(stats) {
        // 更新 CPU 進度條
        const cpuBar = document.querySelector('.cpu-progress .progress-bar');
        if (cpuBar) {
            cpuBar.style.width = `${stats.cpu_usage}%`;
            cpuBar.className = `progress-bar ${this.getProgressBarClass(stats.cpu_usage)}`;
        }

        // 更新記憶體進度條
        const memoryBar = document.querySelector('.memory-progress .progress-bar');
        if (memoryBar) {
            memoryBar.style.width = `${stats.memory_usage}%`;
            memoryBar.className = `progress-bar ${this.getProgressBarClass(stats.memory_usage)}`;
        }

        // 更新 GPU 進度條（如果有的話）
        const gpuBar = document.querySelector('.gpu-progress .progress-bar');
        if (gpuBar && stats.gpu_usage !== undefined) {
            gpuBar.style.width = `${stats.gpu_usage}%`;
            gpuBar.className = `progress-bar ${this.getProgressBarClass(stats.gpu_usage)}`;
        }
    }

    static getProgressBarClass(usage) {
        if (usage < 50) return 'bg-success';
        if (usage < 75) return 'bg-warning';
        return 'bg-danger';
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
            APIClient.showNotification('無法載入任務列表', 'error');
            this.renderTasks([]); // 顯示空列表
        }
    }

    static renderTasks(tasks) {
        const container = document.getElementById('tasks-container');
        if (!container) return;

        if (tasks.length === 0) {
            container.innerHTML = '<p>暫無任務</p>';
            return;
        }

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
            APIClient.showNotification('無法載入攝影機列表', 'error');
            this.renderCameras([]); // 顯示空列表
        }
    }

    static async scanCameras() {
        try {
            APIClient.showNotification('正在快速掃描攝影機...', 'info');
            const result = await APIClient.scanCameras();
            APIClient.showNotification(result.message, 'success');
            
            // 立即重新載入攝影機列表
            await this.loadCameras();
        } catch (error) {
            console.error('掃描攝影機失敗:', error);
            APIClient.showNotification('攝影機掃描失敗', 'error');
        }
    }

    static renderCameras(cameras) {
        const container = document.getElementById('cameras-container');
        if (!container) return;

        if (cameras.length === 0) {
            container.innerHTML = `
                <div class="no-cameras">
                    <p>未檢測到攝影機</p>
                    <button onclick="CameraManager.scanCameras()" class="btn btn-primary">
                        <i class="fas fa-search"></i> 快速掃描攝影機
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = cameras.map((camera, index) => `
            <div class="camera-card" data-camera-id="${camera.id || index}">
                <div class="camera-preview">
                    <div class="camera-placeholder" id="camera-preview-${index}">
                        <i class="fas fa-video"></i>
                        <span>攝影機 ${index}</span>
                    </div>
                    <div class="camera-status ${camera.status === 'active' ? 'active' : 'inactive'}"></div>
                </div>
                <div class="camera-info">
                    <h3>${camera.name || `攝影機 ${index}`}</h3>
                    <p><strong>解析度:</strong> ${camera.resolution || camera.width + 'x' + camera.height}</p>
                    <p><strong>狀態:</strong> ${this.getStatusText(camera.status)}</p>
                    <p><strong>後端:</strong> ${camera.backend || 'DEFAULT'}</p>
                </div>
                <div class="camera-actions">
                    <button onclick="CameraManager.testCamera('${camera.id || index}')" class="btn btn-primary">測試</button>
                    <button onclick="CameraManager.showPreview(${index})" class="btn btn-success">
                        <i class="fas fa-play"></i> 實時預覽
                    </button>
                    <button onclick="CameraManager.openFullStream(${index})" class="btn btn-secondary">
                        <i class="fas fa-external-link-alt"></i> 全螢幕
                    </button>
                </div>
            </div>
        `).join('');

        // 如果有攝影機但沒有顯示掃描按鈕，添加一個
        container.innerHTML += `
            <div class="scan-actions">
                <button onclick="CameraManager.scanCameras()" class="btn btn-outline">
                    <i class="fas fa-refresh"></i> 重新掃描
                </button>
            </div>
        `;
    }

    static async showPreview(cameraIndex) {
        try {
            const previewContainer = document.getElementById(`camera-preview-${cameraIndex}`);
            if (!previewContainer) return;

            // 顯示載入狀態
            previewContainer.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 啟動實時預覽...';

            // 直接使用MJPEG串流顯示實時影片
            const streamUrl = APIClient.getCameraStreamUrl(cameraIndex);
            
            previewContainer.innerHTML = `
                <img src="${streamUrl}" 
                     alt="攝影機 ${cameraIndex} 實時預覽" 
                     style="width: 100%; height: 100%; object-fit: cover;"
                     onload="CameraManager.handleStreamSuccess(${cameraIndex})"
                     onerror="CameraManager.handleStreamError(${cameraIndex})">
                <div class="stream-controls">
                    <button onclick="CameraManager.stopPreview(${cameraIndex})" class="btn btn-small btn-danger">
                        <i class="fas fa-stop"></i> 停止預覽
                    </button>
                </div>
            `;
            
            APIClient.showNotification(`攝影機 ${cameraIndex} 實時預覽已啟動`, 'success');
            
        } catch (error) {
            console.error('實時預覽啟動失敗:', error);
            const previewContainer = document.getElementById(`camera-preview-${cameraIndex}`);
            if (previewContainer) {
                previewContainer.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>預覽啟動失敗</span>
                `;
            }
            APIClient.showNotification(`攝影機 ${cameraIndex} 實時預覽啟動失敗`, 'error');
        }
    }

    static stopPreview(cameraIndex) {
        const previewContainer = document.getElementById(`camera-preview-${cameraIndex}`);
        if (previewContainer) {
            previewContainer.innerHTML = `
                <div class="camera-placeholder">
                    <i class="fas fa-video"></i>
                    <span>攝影機 ${cameraIndex}</span>
                </div>
            `;
        }
        APIClient.showNotification(`攝影機 ${cameraIndex} 預覽已停止`, 'info');
    }

    static handleStreamSuccess(cameraIndex) {
        console.log(`攝影機 ${cameraIndex} 串流載入成功`);
    }

    static startStream(cameraIndex) {
        // 這個函數現在用於向後相容，重定向到showPreview
        this.showPreview(cameraIndex);
    }

    static openFullStream(cameraIndex) {
        try {
            const streamUrl = APIClient.getCameraStreamUrl(cameraIndex);
            
            // 在新視窗開啟全螢幕串流
            const newWindow = window.open('', `camera_${cameraIndex}_fullscreen`, 
                'width=800,height=600,resizable=yes,scrollbars=no,toolbar=no,menubar=no');
            
            if (newWindow) {
                newWindow.document.write(`
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>攝影機 ${cameraIndex} - 全螢幕預覽</title>
                        <style>
                            body {
                                margin: 0;
                                padding: 0;
                                background: #000;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                height: 100vh;
                                font-family: Arial, sans-serif;
                            }
                            img {
                                max-width: 100%;
                                max-height: 100%;
                                object-fit: contain;
                            }
                            .controls {
                                position: absolute;
                                top: 10px;
                                right: 10px;
                                background: rgba(0,0,0,0.7);
                                color: white;
                                padding: 10px;
                                border-radius: 5px;
                            }
                            .error {
                                color: white;
                                text-align: center;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="controls">
                            <span>攝影機 ${cameraIndex} | </span>
                            <button onclick="window.close()" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">關閉</button>
                        </div>
                        <img src="${streamUrl}" 
                             alt="攝影機 ${cameraIndex} 全螢幕串流"
                             onerror="this.style.display='none'; document.body.innerHTML='<div class=error>無法載入攝影機串流</div>'">
                    </body>
                    </html>
                `);
                newWindow.document.close();
                
                APIClient.showNotification(`攝影機 ${cameraIndex} 全螢幕預覽已開啟`, 'success');
            } else {
                APIClient.showNotification('無法開啟新視窗，請檢查瀏覽器彈窗設定', 'warning');
            }
        } catch (error) {
            console.error('全螢幕串流開啟失敗:', error);
            APIClient.showNotification(`攝影機 ${cameraIndex} 全螢幕串流開啟失敗`, 'error');
        }
    }

    static handleStreamError(cameraIndex) {
        const previewContainer = document.getElementById(`camera-preview-${cameraIndex}`);
        if (previewContainer) {
            previewContainer.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <span>串流中斷</span>
            `;
        }
        APIClient.showNotification(`攝影機 ${cameraIndex} 串流中斷`, 'warning');
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
        APIClient.showNotification('攝影機串流功能開發中', 'info');
    }

    static updateCameraInUI(cameraData) {
        const cameraCard = document.querySelector(`[data-camera-id="${cameraData.id}"]`);
        if (cameraCard) {
            const statusElement = cameraCard.querySelector('.camera-status');
            statusElement.className = `camera-status ${cameraData.status === 'active' ? 'active' : 'inactive'}`;
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
        const statusElement = document.getElementById('analytics-status');
        if (statusElement) {
            statusElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 載入中...';
        }
        
        // 重置統計數字
        ['totalDetections', 'personCount', 'vehicleCount', 'alertCount'].forEach(id => {
            const element = document.getElementById(id);
            if (element) element.textContent = '-';
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
        console.log('新檢測結果:', result);
    }

    static async exportData(format) {
        try {
            await APIClient.exportData(format);
            APIClient.showNotification(`數據已匯出為 ${format.toUpperCase()} 格式`, 'success');
        } catch (error) {
            APIClient.showNotification('數據匯出失敗', 'error');
        }
    }
}

// ============================
// 數據管理
// ============================

class DataManager {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalRecords = 0;
        this.selectedRecords = new Set();
        this.filters = {
            timeRange: 'all',
            objectType: '',
            confidenceMin: 0,
            confidenceMax: 1,
            startDate: null,
            endDate: null
        };
    }

    static async loadDataManagement() {
        try {
            const dataManager = new DataManager();
            await dataManager.loadStatistics();
            await dataManager.loadDetectionResults();
            await dataManager.loadStorageAnalysis();
            await dataManager.loadQuickStats();
            dataManager.setupEventListeners();
        } catch (error) {
            console.error('載入數據管理失敗:', error);
            APIClient.showNotification('載入數據管理失敗', 'error');
        }
    }

    async loadStatistics() {
        try {
            const stats = await APIClient.request('GET', '/frontend/stats');
            
            // 更新統計卡片
            document.getElementById('total-records').textContent = stats.total_records || '0';
            document.getElementById('detection-count').textContent = stats.detection_count || '0';
            document.getElementById('days-active').textContent = stats.days_active || '0';
            document.getElementById('storage-size').textContent = this.formatFileSize(stats.storage_size || 0);
        } catch (error) {
            console.error('載入統計數據失敗:', error);
        }
    }

    async loadQuickStats() {
        try {
            const stats = await APIClient.request('GET', '/frontend/quick-stats');
            
            // 更新快速統計
            const todayElement = document.getElementById('today-detections');
            const avgConfidenceElement = document.getElementById('avg-confidence');
            const commonObjectElement = document.getElementById('most-common-object');
            const trackingContinuityElement = document.getElementById('tracking-continuity');
            
            if (todayElement) todayElement.textContent = stats.today_detections || '0';
            if (avgConfidenceElement) avgConfidenceElement.textContent = `${(stats.avg_confidence * 100).toFixed(1)}%`;
            if (commonObjectElement) commonObjectElement.textContent = stats.most_common_object || 'N/A';
            if (trackingContinuityElement) trackingContinuityElement.textContent = `${stats.tracking_continuity || 0}%`;
        } catch (error) {
            console.error('載入快速統計失敗:', error);
        }
    }

    async loadStorageAnalysis() {
        try {
            const analysis = await APIClient.request('GET', '/frontend/storage-analysis');
            
            // 更新存儲分析顯示
            const detectionSizeElement = document.getElementById('storage-detection-size');
            const videoSizeElement = document.getElementById('storage-video-size');
            const logSizeElement = document.getElementById('storage-log-size');
            const totalSizeElement = document.getElementById('storage-total-size');
            const freeSpaceElement = document.getElementById('storage-free-space');
            
            if (detectionSizeElement) detectionSizeElement.textContent = this.formatFileSize(analysis.detection_size || 0);
            if (videoSizeElement) videoSizeElement.textContent = this.formatFileSize(analysis.video_size || 0);
            if (logSizeElement) logSizeElement.textContent = this.formatFileSize(analysis.log_size || 0);
            if (totalSizeElement) totalSizeElement.textContent = this.formatFileSize(analysis.total_size || 0);
            if (freeSpaceElement) freeSpaceElement.textContent = this.formatFileSize(analysis.free_space || 0);
            
            // 如果有圖表容器，更新圖表
            this.updateStorageChart(analysis);
        } catch (error) {
            console.error('載入存儲分析失敗:', error);
        }
    }

    updateStorageChart(analysis) {
        const chartCanvas = document.getElementById('storage-chart');
        if (!chartCanvas) return;
        
        // 使用 Chart.js 創建圖表（如果已載入）
        if (typeof Chart !== 'undefined') {
            new Chart(chartCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['檢測數據', '視頻文件', '日誌文件'],
                    datasets: [{
                        data: [
                            analysis.detection_size || 0,
                            analysis.video_size || 0,
                            analysis.log_size || 0
                        ],
                        backgroundColor: [
                            '#007bff',
                            '#28a745',
                            '#ffc107'
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
    }

    async loadDetectionResults(page = 1) {
        try {
            this.currentPage = page;
            const params = {
                page: page,
                limit: this.pageSize,
                ...this.getFilterParams()
            };

            const response = await APIClient.request('GET', '/frontend/detection-results', params);
            
            this.totalRecords = response.total || 0;
            this.renderDetectionResults(response.results || []);
            this.renderPagination();
            this.updateDataInfo();
        } catch (error) {
            console.error('載入檢測結果失敗:', error);
            document.getElementById('data-results-table').innerHTML = `
                <tr>
                    <td colspan="10" class="text-center text-danger">
                        <i class="fas fa-exclamation-triangle"></i> 載入失敗
                    </td>
                </tr>
            `;
        }
    }

    renderDetectionResults(results) {
        const tableBody = document.getElementById('data-results-table');
        
        if (results.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="10" class="text-center text-muted">
                        <i class="fas fa-inbox"></i> 沒有符合條件的記錄
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = results.map(result => `
            <tr data-id="${result.id}">
                <td>
                    <input type="checkbox" class="record-checkbox" value="${result.id}" 
                           onchange="DataManager.instance.toggleRecordSelection(${result.id})">
                </td>
                <td>${result.id}</td>
                <td>
                    <div>${this.formatDateTime(result.timestamp)}</div>
                    <small class="text-muted">${this.formatTime(result.timestamp)}</small>
                </td>
                <td>
                    <span class="badge bg-primary">${result.object_chinese || result.object_type}</span>
                </td>
                <td>
                    <code class="small">${result.object_id || 'N/A'}</code>
                </td>
                <td>
                    <div class="progress" style="height: 6px;">
                        <div class="progress-bar ${this.getConfidenceColor(result.confidence)}" 
                             style="width: ${(result.confidence * 100)}%"></div>
                    </div>
                    <small>${(result.confidence * 100).toFixed(1)}%</small>
                </td>
                <td>
                    <small>
                        中心: (${result.center_x?.toFixed(0) || 'N/A'}, ${result.center_y?.toFixed(0) || 'N/A'})<br>
                        ${result.width?.toFixed(0) || 'N/A'} × ${result.height?.toFixed(0) || 'N/A'}
                    </small>
                </td>
                <td>
                    <small>${(result.area || 0).toFixed(0)} px²</small>
                </td>
                <td>
                    <span class="badge bg-secondary">${result.zone_chinese || result.zone || 'N/A'}</span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary btn-xs" 
                                onclick="DataManager.instance.viewRecord(${result.id})" title="查看詳情">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-xs" 
                                onclick="DataManager.instance.deleteRecord(${result.id})" title="刪除">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    renderPagination() {
        const totalPages = Math.ceil(this.totalRecords / this.pageSize);
        const pagination = document.getElementById('data-pagination');
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let paginationHTML = '';
        
        // 上一頁
        paginationHTML += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="DataManager.instance.loadDetectionResults(${this.currentPage - 1})">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;

        // 頁碼
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);

        if (startPage > 1) {
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="DataManager.instance.loadDetectionResults(1)">1</a>
                </li>
            `;
            if (startPage > 2) {
                paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="DataManager.instance.loadDetectionResults(${i})">${i}</a>
                </li>
            `;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="DataManager.instance.loadDetectionResults(${totalPages})">${totalPages}</a>
                </li>
            `;
        }

        // 下一頁
        paginationHTML += `
            <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="DataManager.instance.loadDetectionResults(${this.currentPage + 1})">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;

        pagination.innerHTML = paginationHTML;
    }

    updateDataInfo() {
        const start = (this.currentPage - 1) * this.pageSize + 1;
        const end = Math.min(this.currentPage * this.pageSize, this.totalRecords);
        
        document.getElementById('data-page-start').textContent = start;
        document.getElementById('data-page-end').textContent = end;
        document.getElementById('data-total-count').textContent = this.totalRecords;
    }

    async loadStorageAnalysis() {
        try {
            const storage = await APIClient.request('GET', '/frontend/storage-analysis');
            
            // 更新儲存空間分析
            this.updateStorageBar('detection-storage', 'detection-storage-text', 
                                 storage.detection_size, storage.total_size);
            this.updateStorageBar('video-storage', 'video-storage-text', 
                                 storage.video_size, storage.total_size);
            this.updateStorageBar('log-storage', 'log-storage-text', 
                                 storage.log_size, storage.total_size);
        } catch (error) {
            console.error('載入儲存分析失敗:', error);
        }
    }

    updateStorageBar(barId, textId, size, totalSize) {
        const percentage = totalSize > 0 ? (size / totalSize * 100) : 0;
        document.getElementById(barId).style.width = `${percentage}%`;
        document.getElementById(textId).textContent = this.formatFileSize(size);
    }

    async loadQuickStats() {
        try {
            const quickStats = await APIClient.request('GET', '/frontend/quick-stats');
            
            document.getElementById('today-detections').textContent = quickStats.today_detections || '0';
            document.getElementById('avg-confidence').textContent = 
                quickStats.avg_confidence ? (quickStats.avg_confidence * 100).toFixed(1) + '%' : 'N/A';
            document.getElementById('most-common-object').textContent = 
                quickStats.most_common_object || 'N/A';
            document.getElementById('peak-hours').textContent = 
                quickStats.peak_hours || 'N/A';

            // 更新品質指標
            this.updateQualityIndicator('high-confidence', quickStats.high_confidence_percentage || 0);
            this.updateQualityIndicator('tracking-continuity', quickStats.tracking_continuity || 0);
        } catch (error) {
            console.error('載入快速統計失敗:', error);
        }
    }

    updateQualityIndicator(type, percentage) {
        const bar = document.getElementById(`${type}-bar`);
        const text = document.getElementById(`${type}-text`);
        
        if (bar && text) {
            bar.style.width = `${percentage}%`;
            text.textContent = `${percentage.toFixed(1)}%`;
        }
    }

    setupEventListeners() {
        // 時間範圍變更
        document.getElementById('data-time-range').addEventListener('change', (e) => {
            const customRange = document.getElementById('custom-date-range');
            if (e.target.value === 'custom') {
                customRange.style.display = 'block';
            } else {
                customRange.style.display = 'none';
            }
        });
    }

    getFilterParams() {
        const params = {};
        
        if (this.filters.objectType) {
            params.object_type = this.filters.objectType;
        }
        
        if (this.filters.confidenceMin > 0) {
            params.confidence_min = this.filters.confidenceMin;
        }
        
        if (this.filters.confidenceMax < 1) {
            params.confidence_max = this.filters.confidenceMax;
        }

        // 時間範圍處理
        const now = new Date();
        switch (this.filters.timeRange) {
            case 'today':
                params.start_date = new Date(now.setHours(0, 0, 0, 0)).toISOString();
                break;
            case 'week':
                params.start_date = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
                break;
            case 'month':
                params.start_date = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
                break;
            case 'custom':
                if (this.filters.startDate) params.start_date = this.filters.startDate;
                if (this.filters.endDate) params.end_date = this.filters.endDate;
                break;
        }

        return params;
    }

    static applyFilters() {
        const instance = DataManager.instance || new DataManager();
        
        // 獲取篩選條件
        instance.filters.timeRange = document.getElementById('data-time-range').value;
        instance.filters.objectType = document.getElementById('data-object-type').value;
        instance.filters.confidenceMin = parseFloat(document.getElementById('confidence-min').value) || 0;
        instance.filters.confidenceMax = parseFloat(document.getElementById('confidence-max').value) || 1;
        
        if (instance.filters.timeRange === 'custom') {
            instance.filters.startDate = document.getElementById('start-date').value;
            instance.filters.endDate = document.getElementById('end-date').value;
        }

        // 重新載入數據
        instance.loadDetectionResults(1);
    }

    static resetFilters() {
        // 重置表單
        document.getElementById('data-time-range').value = 'all';
        document.getElementById('data-object-type').value = '';
        document.getElementById('confidence-min').value = '0';
        document.getElementById('confidence-max').value = '1';
        document.getElementById('start-date').value = '';
        document.getElementById('end-date').value = '';
        document.getElementById('custom-date-range').style.display = 'none';

        // 重新載入數據
        const instance = DataManager.instance || new DataManager();
        instance.filters = {
            timeRange: 'all',
            objectType: '',
            confidenceMin: 0,
            confidenceMax: 1,
            startDate: null,
            endDate: null
        };
        instance.loadDetectionResults(1);
    }

    static toggleSelectAll() {
        const selectAll = document.getElementById('select-all-data');
        const checkboxes = document.querySelectorAll('.record-checkbox');
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAll.checked;
            const id = parseInt(checkbox.value);
            if (selectAll.checked) {
                DataManager.instance.selectedRecords.add(id);
            } else {
                DataManager.instance.selectedRecords.delete(id);
            }
        });
    }

    toggleRecordSelection(id) {
        if (this.selectedRecords.has(id)) {
            this.selectedRecords.delete(id);
        } else {
            this.selectedRecords.add(id);
        }

        // 更新全選狀態
        const allCheckboxes = document.querySelectorAll('.record-checkbox');
        const checkedBoxes = document.querySelectorAll('.record-checkbox:checked');
        const selectAll = document.getElementById('select-all-data');
        
        selectAll.indeterminate = checkedBoxes.length > 0 && checkedBoxes.length < allCheckboxes.length;
        selectAll.checked = checkedBoxes.length === allCheckboxes.length;
    }

    static async exportData(format) {
        try {
            const instance = DataManager.instance || new DataManager();
            const selectedIds = Array.from(instance.selectedRecords);
            
            const params = {
                format: format,
                ...instance.getFilterParams()
            };

            if (selectedIds.length > 0) {
                params.ids = selectedIds.join(',');
            }

            // 創建下載連結
            const queryString = new URLSearchParams(params).toString();
            const downloadUrl = `${API_CONFIG.baseURL}/api/v1/frontend/export-data?${queryString}`;
            
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `detection_results_${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            APIClient.showNotification(`數據已匯出為 ${format.toUpperCase()} 格式`, 'success');
        } catch (error) {
            console.error('匯出數據失敗:', error);
            APIClient.showNotification('數據匯出失敗', 'error');
        }
    }

    async viewRecord(id) {
        try {
            const record = await APIClient.request('GET', `/frontend/detection-results/${id}`);
            this.showRecordModal(record);
        } catch (error) {
            console.error('載入記錄詳情失敗:', error);
            APIClient.showNotification('載入記錄詳情失敗', 'error');
        }
    }

    showRecordModal(record) {
        // 創建模態對話框顯示記錄詳情
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">檢測記錄詳情 - ${record.id}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>基本資訊</h6>
                                <table class="table table-sm">
                                    <tr><td>記錄ID:</td><td>${record.id}</td></tr>
                                    <tr><td>時間戳:</td><td>${this.formatDateTime(record.timestamp)}</td></tr>
                                    <tr><td>物件類型:</td><td>${record.object_chinese || record.object_type}</td></tr>
                                    <tr><td>物件ID:</td><td>${record.object_id || 'N/A'}</td></tr>
                                    <tr><td>信心度:</td><td>${(record.confidence * 100).toFixed(2)}%</td></tr>
                                </table>
                            </div>
                            <div class="col-md-6">
                                <h6>位置資訊</h6>
                                <table class="table table-sm">
                                    <tr><td>中心座標:</td><td>(${record.center_x?.toFixed(2)}, ${record.center_y?.toFixed(2)})</td></tr>
                                    <tr><td>寬度:</td><td>${record.width?.toFixed(2)} px</td></tr>
                                    <tr><td>高度:</td><td>${record.height?.toFixed(2)} px</td></tr>
                                    <tr><td>面積:</td><td>${record.area?.toFixed(2)} px²</td></tr>
                                    <tr><td>區域:</td><td>${record.zone_chinese || record.zone || 'N/A'}</td></tr>
                                </table>
                            </div>
                        </div>
                        ${record.velocity_x !== undefined ? `
                        <div class="row mt-3">
                            <div class="col-md-12">
                                <h6>運動資訊</h6>
                                <table class="table table-sm">
                                    <tr><td>X方向速度:</td><td>${record.velocity_x?.toFixed(2)} px/s</td></tr>
                                    <tr><td>Y方向速度:</td><td>${record.velocity_y?.toFixed(2)} px/s</td></tr>
                                    <tr><td>移動速度:</td><td>${record.speed?.toFixed(2)} px/s</td></tr>
                                    <tr><td>移動方向:</td><td>${record.direction_chinese || record.direction || 'N/A'}</td></tr>
                                </table>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">關閉</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    async deleteRecord(id) {
        if (!confirm('確定要刪除這筆記錄嗎？此操作無法復原。')) {
            return;
        }

        try {
            await APIClient.request('DELETE', `/frontend/detection-results/${id}`);
            APIClient.showNotification('記錄已刪除', 'success');
            this.loadDetectionResults(this.currentPage);
        } catch (error) {
            console.error('刪除記錄失敗:', error);
            APIClient.showNotification('刪除記錄失敗', 'error');
        }
    }

    static async backupDatabase() {
        try {
            const link = document.createElement('a');
            link.href = `${API_CONFIG.baseURL}/api/v1/frontend/backup-database`;
            link.download = `database_backup_${new Date().toISOString().split('T')[0]}.sql`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            APIClient.showNotification('資料庫備份已開始下載', 'success');
        } catch (error) {
            console.error('備份資料庫失敗:', error);
            APIClient.showNotification('備份資料庫失敗', 'error');
        }
    }

    static async optimizeDatabase() {
        if (!confirm('資料庫優化可能需要幾分鐘時間，期間系統效能可能受影響。確定要繼續嗎？')) {
            return;
        }

        try {
            await APIClient.request('POST', '/frontend/optimize-database');
            APIClient.showNotification('資料庫優化完成', 'success');
        } catch (error) {
            console.error('優化資料庫失敗:', error);
            APIClient.showNotification('優化資料庫失敗', 'error');
        }
    }

    static showClearDialog() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">⚠️ 危險操作警告</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="text-danger"><strong>警告：此操作將永久刪除所有檢測記錄！</strong></p>
                        <p>這個操作包括：</p>
                        <ul>
                            <li>所有檢測結果記錄</li>
                            <li>所有行為事件記錄</li>
                            <li>所有分析任務記錄</li>
                        </ul>
                        <p>請輸入 <code>DELETE</code> 確認：</p>
                        <input type="text" class="form-control" id="clearConfirmText" placeholder="輸入 DELETE">
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-danger" onclick="DataManager.confirmClearDatabase()">
                            確認清空
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    static async confirmClearDatabase() {
        const confirmText = document.getElementById('clearConfirmText').value;
        
        if (confirmText !== 'DELETE') {
            APIClient.showNotification('確認文字不正確', 'error');
            return;
        }

        try {
            await APIClient.request('POST', '/frontend/clear-database');
            APIClient.showNotification('資料庫已清空', 'success');
            
            // 關閉模態對話框
            const modal = document.querySelector('.modal.show');
            if (modal) {
                bootstrap.Modal.getInstance(modal).hide();
            }
            
            // 重新載入數據
            if (DataManager.instance) {
                DataManager.instance.loadDetectionResults(1);
                DataManager.instance.loadStatistics();
            }
        } catch (error) {
            console.error('清空資料庫失敗:', error);
            APIClient.showNotification('清空資料庫失敗', 'error');
        }
    }

    // 工具方法
    formatDateTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleDateString('zh-TW');
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('zh-TW');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getConfidenceColor(confidence) {
        if (confidence >= 0.8) return 'bg-success';
        if (confidence >= 0.6) return 'bg-warning';
        return 'bg-danger';
    }

    // 實例方法（供 HTML 調用）
    async applyFilters() {
        await this.loadDetectionResults(1);
    }

    async resetFilters() {
        this.filters = {
            timeRange: 'all',
            objectType: '',
            confidenceMin: 0,
            confidenceMax: 1,
            startDate: null,
            endDate: null
        };
        
        // 重置表單
        document.getElementById('time-range').value = 'all';
        document.getElementById('object-type').value = '';
        document.getElementById('confidence-min').value = 0;
        document.getElementById('confidence-max').value = 1;
        document.getElementById('start-date').value = '';
        document.getElementById('end-date').value = '';
        
        await this.loadDetectionResults(1);
    }

    async exportData(format) {
        try {
            const params = {
                format: format,
                ...this.getFilterParams()
            };
            
            const response = await APIClient.request('GET', '/frontend/export-data', params);
            
            // 創建下載鏈接
            const blob = new Blob([response], { type: this.getContentType(format) });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `detection_results.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            APIClient.showNotification(`已導出為 ${format.toUpperCase()} 格式`, 'success');
        } catch (error) {
            console.error('導出失敗:', error);
            APIClient.showNotification('導出失敗', 'error');
        }
    }

    async toggleSelectAll() {
        const checkbox = document.getElementById('select-all');
        const isChecked = checkbox.checked;
        
        const recordCheckboxes = document.querySelectorAll('input[name="selected-records"]');
        recordCheckboxes.forEach(cb => {
            cb.checked = isChecked;
            if (isChecked) {
                this.selectedRecords.add(cb.value);
            } else {
                this.selectedRecords.delete(cb.value);
            }
        });
        
        this.updateSelectionInfo();
    }

    async backupDatabase() {
        try {
            const response = await APIClient.request('POST', '/frontend/backup-database');
            APIClient.showNotification('資料庫備份完成', 'success');
        } catch (error) {
            console.error('備份失敗:', error);
            APIClient.showNotification('備份失敗', 'error');
        }
    }

    async optimizeDatabase() {
        try {
            await APIClient.request('POST', '/frontend/optimize-database');
            APIClient.showNotification('資料庫優化完成', 'success');
        } catch (error) {
            console.error('優化失敗:', error);
            APIClient.showNotification('優化失敗', 'error');
        }
    }

    async showClearDialog() {
        // 調用靜態方法
        DataManager.showClearDialog();
    }

    // 工具方法
    getContentType(format) {
        switch (format) {
            case 'csv': return 'text/csv';
            case 'json': return 'application/json';
            case 'excel': return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
            default: return 'text/plain';
        }
    }

    getFilterParams() {
        const params = {};
        
        if (this.filters.timeRange !== 'all') {
            params.time_range = this.filters.timeRange;
        }
        if (this.filters.objectType) {
            params.object_type = this.filters.objectType;
        }
        if (this.filters.confidenceMin > 0) {
            params.confidence_min = this.filters.confidenceMin;
        }
        if (this.filters.confidenceMax < 1) {
            params.confidence_max = this.filters.confidenceMax;
        }
        if (this.filters.startDate) {
            params.start_date = this.filters.startDate;
        }
        if (this.filters.endDate) {
            params.end_date = this.filters.endDate;
        }
        
        return params;
    }

    updateSelectionInfo() {
        const count = this.selectedRecords.size;
        const info = document.getElementById('selection-info');
        if (info) {
            info.textContent = count > 0 ? `已選擇 ${count} 項` : '';
        }
    }

    updateDataInfo() {
        const info = document.getElementById('data-info');
        if (info) {
            const start = (this.currentPage - 1) * this.pageSize + 1;
            const end = Math.min(start + this.pageSize - 1, this.totalRecords);
            info.textContent = `顯示 ${start}-${end}，共 ${this.totalRecords} 項`;
        }
    }

    setupEventListeners() {
        // 實現事件監聽器設置
        const timeRange = document.getElementById('time-range');
        const objectType = document.getElementById('object-type');
        const confidenceMin = document.getElementById('confidence-min');
        const confidenceMax = document.getElementById('confidence-max');
        const startDate = document.getElementById('start-date');
        const endDate = document.getElementById('end-date');
        
        if (timeRange) timeRange.addEventListener('change', (e) => {
            this.filters.timeRange = e.target.value;
        });
        
        if (objectType) objectType.addEventListener('change', (e) => {
            this.filters.objectType = e.target.value;
        });
        
        if (confidenceMin) confidenceMin.addEventListener('change', (e) => {
            this.filters.confidenceMin = parseFloat(e.target.value);
        });
        
        if (confidenceMax) confidenceMax.addEventListener('change', (e) => {
            this.filters.confidenceMax = parseFloat(e.target.value);
        });
        
        if (startDate) startDate.addEventListener('change', (e) => {
            this.filters.startDate = e.target.value;
        });
        
        if (endDate) endDate.addEventListener('change', (e) => {
            this.filters.endDate = e.target.value;
        });
    }
}

// 創建全局實例
DataManager.instance = null;

// ============================
// YOLO 模型管理
// ============================

class YOLOModelManager {
    constructor() {
        this.currentModel = null;
        this.models = [
            {
                name: 'YOLOv11n',
                id: 'yolov11n',
                params: '2.6M',
                speed: 'Fast',
                accuracy: 'Good',
                status: 'unloaded',
                available: true,  // 預設為可用，會被API更新
                speedBar: 90,
                accuracyBar: 75,
                sizeBar: 20
            },
            {
                name: 'YOLOv11s',
                id: 'yolov11s',
                params: '9.4M',
                speed: 'Fast',
                accuracy: 'Good',
                status: 'loaded',
                available: true,  // 預設為可用，會被API更新
                speedBar: 85,
                accuracyBar: 80,
                sizeBar: 35
            },
            {
                name: 'YOLOv11m',
                id: 'yolov11m',
                params: '20.1M',
                speed: 'Medium',
                accuracy: 'Better',
                status: 'unloaded',
                available: true,  // 預設為可用，會被API更新
                speedBar: 70,
                accuracyBar: 85,
                sizeBar: 50
            },
            {
                name: 'YOLOv11l',
                id: 'yolov11l',
                params: '25.3M',
                speed: 'Medium',
                accuracy: 'Better',
                status: 'unloaded',
                available: true,  // 預設為可用，會被API更新
                speedBar: 60,
                accuracyBar: 88,
                sizeBar: 65
            },
            {
                name: 'YOLOv11x',
                id: 'yolov11x',
                params: '56.9M',
                speed: 'Slow',
                accuracy: 'Best',
                status: 'unloaded',
                available: true,  // 預設為可用，會被API更新
                speedBar: 45,
                accuracyBar: 92,
                sizeBar: 85
            }
        ];
        this.config = {
            confidence: 0.5,
            iou: 0.45,
            imageSize: 640
        };
        this.init();
    }

    async init() {
        console.log('YOLOModelManager 初始化開始'); // 調試用
        this.renderConfig();
        this.bindEvents();
        
        // 先從 API 載入模型狀態，再渲染
        await this.refreshModelsFromAPI();
        
        // 從 API 載入配置
        this.loadConfigFromAPI();
        
        console.log('YOLOModelManager 初始化完成'); // 調試用
    }

    renderModels() {
        const container = document.querySelector('.yolo-model-selector');
        if (!container) {
            console.error('❌ 找不到 .yolo-model-selector 容器');
            return;
        }

        console.log('🔄 渲染模型，模型數量:', this.models.length); // 調試用
        
        container.innerHTML = this.models.map(model => {
            console.log(`🔍 模型 ${model.id}: available=${model.available}, status=${model.status}`); // 調試用
            return `
            <div class="yolo-model-card ${model.status === 'loaded' ? 'active' : ''} ${!model.available ? 'unavailable' : ''}" 
                 data-model-id="${model.id}">
                <div class="model-header">
                    <h3 class="model-name">${model.name}</h3>
                    <span class="model-status ${model.status}">
                        ${model.status === 'loaded' ? '已載入' : 
                          model.status === 'unavailable' ? '檔案不存在' : '未載入'}
                    </span>
                </div>
                <div class="model-details">
                    <div class="model-detail-item">
                        <span class="detail-label">參數量</span>
                        <span class="detail-value">${model.params}</span>
                    </div>
                    <div class="model-detail-item">
                        <span class="detail-label">速度</span>
                        <span class="detail-value">${model.speed}</span>
                    </div>
                </div>
                <div class="model-performance">
                    <div class="performance-label">速度</div>
                    <div class="performance-indicator">
                        <div class="performance-bar speed" style="width: ${model.speedBar}%"></div>
                    </div>
                </div>
                <div class="model-performance">
                    <div class="performance-label">精度</div>
                    <div class="performance-indicator">
                        <div class="performance-bar accuracy" style="width: ${model.accuracyBar}%"></div>
                    </div>
                </div>
                <div class="model-performance">
                    <div class="performance-label">大小</div>
                    <div class="performance-indicator">
                        <div class="performance-bar size" style="width: ${model.sizeBar}%"></div>
                    </div>
                </div>
                <div class="model-actions">
                    ${!model.available ? 
                        `<button class="model-action-btn" disabled>
                            <i class="fas fa-exclamation-triangle"></i> 檔案不存在
                        </button>` :
                        (model.status === 'loaded' ? 
                            `<button class="model-action-btn unload" data-action="unload" data-model="${model.id}">
                                <i class="fas fa-stop"></i> 卸載
                            </button>` : 
                            `<button class="model-action-btn load" data-action="load" data-model="${model.id}">
                                <i class="fas fa-play"></i> 載入
                            </button>`
                        )
                    }
                </div>
            </div>
        `;
        }).join('');
        
        console.log('✅ 模型渲染完成'); // 調試用
    }

    renderConfig() {
        // 更新滑桿顯示值
        this.updateSliderDisplay('confidence', this.config.confidence);
        this.updateSliderDisplay('iou', this.config.iou);
        
        // 設置滑桿值
        const confidenceSlider = document.getElementById('confidence-slider');
        const iouSlider = document.getElementById('iou-slider');
        
        if (confidenceSlider) confidenceSlider.value = this.config.confidence;
        if (iouSlider) iouSlider.value = this.config.iou;
        
        // 設置圖像大小選擇
        const imageSizeOptions = document.querySelectorAll('.size-option');
        imageSizeOptions.forEach(option => {
            if (parseInt(option.dataset.size) === this.config.imageSize) {
                option.classList.add('active');
            } else {
                option.classList.remove('active');
            }
        });
    }

    bindEvents() {
        // 移除舊的事件監聽器（如果存在）
        document.removeEventListener('click', this.handleDocumentClick);
        
        // 創建綁定的事件處理器
        this.handleDocumentClick = this.handleDocumentClick.bind(this);
        
        // 添加新的事件監聽器
        document.addEventListener('click', this.handleDocumentClick);

        // 滑桿事件
        const confidenceSlider = document.getElementById('confidence-slider');
        const iouSlider = document.getElementById('iou-slider');
        
        if (confidenceSlider) {
            confidenceSlider.removeEventListener('input', this.handleConfidenceChange);
            this.handleConfidenceChange = (e) => {
                this.config.confidence = parseFloat(e.target.value);
                this.updateSliderDisplay('confidence', this.config.confidence);
            };
            confidenceSlider.addEventListener('input', this.handleConfidenceChange);
        }
        
        if (iouSlider) {
            iouSlider.removeEventListener('input', this.handleIouChange);
            this.handleIouChange = (e) => {
                this.config.iou = parseFloat(e.target.value);
                this.updateSliderDisplay('iou', this.config.iou);
            };
            iouSlider.addEventListener('input', this.handleIouChange);
        }
    }

    handleDocumentClick(e) {
        // 模型載入/卸載按鈕
        if (e.target.closest('.model-action-btn:not([disabled])')) {
            e.preventDefault();
            e.stopPropagation();
            
            const btn = e.target.closest('.model-action-btn');
            const action = btn.dataset.action;
            const modelId = btn.dataset.model;
            
            console.log('按鈕點擊:', action, modelId); // 調試用
            
            if (action === 'load') {
                this.loadModel(modelId);
            } else if (action === 'unload') {
                this.unloadModel(modelId);
            }
            return;
        }
        
        // 模型卡片選擇（但不包括按鈕區域）
        if (e.target.closest('.yolo-model-card') && !e.target.closest('.model-actions')) {
            const card = e.target.closest('.yolo-model-card');
            const modelId = card.dataset.modelId;
            console.log('模型卡片點擊:', modelId); // 調試用
            this.selectModel(modelId);
            return;
        }

        // 圖像大小選擇事件
        if (e.target.closest('.size-option')) {
            const option = e.target.closest('.size-option');
            const size = parseInt(option.dataset.size);
            
            // 移除所有活躍狀態
            document.querySelectorAll('.size-option').forEach(opt => opt.classList.remove('active'));
            // 添加活躍狀態
            option.classList.add('active');
            
            this.config.imageSize = size;
            return;
        }

        // 配置按鈕事件
        if (e.target.closest('.config-btn.apply')) {
            this.applyConfig();
            return;
        }
        
        if (e.target.closest('.config-btn.reset')) {
            this.resetConfig();
            return;
        }
    }

    selectModel(modelId) {
        console.log('selectModel 被調用，modelId:', modelId); // 調試用
        
        // 只有未載入的模型可以選擇
        const model = this.models.find(m => m.id === modelId);
        if (model && model.status === 'unloaded') {
            // 移除其他選中狀態
            document.querySelectorAll('.yolo-model-card').forEach(card => {
                if (card.dataset.modelId !== modelId) {
                    card.classList.remove('selected');
                }
            });
            
            // 切換選中狀態
            const card = document.querySelector(`[data-model-id="${modelId}"]`);
            if (card) {
                card.classList.toggle('selected');
                console.log('模型選中狀態已切換:', modelId); // 調試用
            }
        } else {
            console.log('模型無法選擇:', model ? model.status : '模型不存在'); // 調試用
        }
    }

    async loadModel(modelId) {
        const model = this.models.find(m => m.id === modelId);
        if (!model) return;

        try {
            // 顯示載入狀態
            this.setModelLoading(modelId, true);
            
            // 實際的 API 調用
            await APIClient.loadModel(modelId);
            
            // 先卸載其他模型
            this.models.forEach(m => {
                if (m.id !== modelId) {
                    m.status = 'unloaded';
                }
            });
            
            // 載入選中的模型
            model.status = 'loaded';
            this.currentModel = modelId;
            
            // 重新渲染
            this.renderModels();
            
            APIClient.showNotification(`模型 ${model.name} 載入成功`, 'success');
        } catch (error) {
            console.error('載入模型失敗:', error);
            APIClient.showNotification(`模型 ${model.name} 載入失敗: ${error.message}`, 'error');
        } finally {
            this.setModelLoading(modelId, false);
        }
    }

    async unloadModel(modelId) {
        const model = this.models.find(m => m.id === modelId);
        if (!model) return;

        try {
            // 顯示卸載狀態
            this.setModelLoading(modelId, true);
            
            // 實際的 API 調用
            await APIClient.unloadModel(modelId);
            
            model.status = 'unloaded';
            if (this.currentModel === modelId) {
                this.currentModel = null;
            }
            
            // 重新渲染
            this.renderModels();
            
            APIClient.showNotification(`模型 ${model.name} 卸載成功`, 'success');
        } catch (error) {
            console.error('卸載模型失敗:', error);
            APIClient.showNotification(`模型 ${model.name} 卸載失敗: ${error.message}`, 'error');
        } finally {
            this.setModelLoading(modelId, false);
        }
    }

    setModelLoading(modelId, loading) {
        const card = document.querySelector(`[data-model-id="${modelId}"]`);
        if (card) {
            const button = card.querySelector('.model-action-btn');
            if (button) {
                button.disabled = loading;
                if (loading) {
                    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 處理中...';
                }
            }
        }
    }

    updateSliderDisplay(type, value) {
        const displayElement = document.getElementById(`${type}-value`);
        if (displayElement) {
            // value 已經是 0.0-1.0 的範圍，直接轉換為百分比
            displayElement.textContent = Math.round(value * 100) + '%';
        }
    }

    async applyConfig() {
        try {
            // 實際的 API 調用
            await APIClient.updateModelConfig(this.config);
            
            APIClient.showNotification('配置應用成功', 'success');
        } catch (error) {
            console.error('應用配置失敗:', error);
            APIClient.showNotification(`配置應用失敗: ${error.message}`, 'error');
        }
    }

    async loadConfigFromAPI() {
        try {
            const config = await APIClient.getModelConfig();
            this.config = { ...this.config, ...config };
            this.renderConfig();
        } catch (error) {
            console.error('載入配置失敗:', error);
            // 使用默認配置
        }
    }

    async refreshModelsFromAPI() {
        try {
            console.log('🔄 開始從API刷新模型狀態...'); // 調試用
            const response = await APIClient.getAvailableModels();
            console.log('📡 API響應:', response); // 調試用
            
            // 更新本地模型數據
            if (response.models && Array.isArray(response.models)) {
                console.log(`✅ 找到 ${response.models.length} 個模型`); // 調試用
                
                // 合併 API 數據與本地模型數據
                this.models.forEach(localModel => {
                    const apiModel = response.models.find(m => m.id === localModel.id);
                    if (apiModel) {
                        localModel.status = apiModel.status;
                        localModel.available = apiModel.available;
                        localModel.file_path = apiModel.file_path;
                        localModel.actual_size_mb = apiModel.actual_size_mb;
                        console.log(`🔄 更新模型 ${localModel.id}: ${apiModel.available ? '可用' : '不可用'}`);
                    } else {
                        localModel.available = false;
                        localModel.status = 'unavailable';
                        console.log(`❌ 模型 ${localModel.id}: API中未找到`);
                    }
                });
                
                // 設置當前載入的模型
                if (response.current_model) {
                    this.currentModel = response.current_model;
                    console.log(`🎯 當前模型: ${response.current_model}`); // 調試用
                }
            }
            
            this.renderModels();
            console.log('✅ 模型刷新完成'); // 調試用
        } catch (error) {
            console.error('❌ 刷新模型狀態失敗:', error);
            // 如果 API 失敗，至少渲染本地數據
            this.renderModels();
        }
    }

    resetConfig() {
        // 重置為默認值
        this.config = {
            confidence: 0.5,
            iou: 0.45,
            imageSize: 640
        };
        
        this.renderConfig();
        APIClient.showNotification('配置已重置為默認值', 'info');
    }

    // 獲取當前配置
    getConfig() {
        return { ...this.config };
    }

    // 設置配置
    setConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.renderConfig();
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
                if (config && config[key] !== undefined) {
                    input.value = config[key];
                }
            });
        }
    }

    static async saveConfig() {
        const form = document.getElementById('config-form');
        if (!form) return;
        
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
        if (!modelSelect) return;
        
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

// 全局 YOLO 管理器實例
window.yoloManager = null;

document.addEventListener('DOMContentLoaded', function() {
    // 檢查外部資源載入狀態
    const checkExternalResources = () => {
        let resourceErrors = 0;
        
        // 檢查 Bootstrap 是否載入
        if (typeof window.bootstrap === 'undefined') {
            console.warn('⚠️ Bootstrap 未載入，可能是網絡問題');
            resourceErrors++;
        }
        
        // 檢查 Chart.js 是否載入
        if (typeof window.Chart === 'undefined') {
            console.warn('⚠️ Chart.js 未載入，可能是網絡問題');
            resourceErrors++;
        }
        
        if (resourceErrors > 0) {
            console.warn(`⚠️ 檢測到 ${resourceErrors} 個外部資源載入失敗`);
            console.info('💡 建議使用離線版本: /website/index_offline.html');
            
            // 顯示通知給用戶
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #ff9800;
                color: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 10000;
                max-width: 300px;
                font-size: 14px;
            `;
            notification.innerHTML = `
                <strong>網絡連接問題</strong><br>
                部分資源無法載入，如有問題請使用
                <a href="/website/index_offline.html" style="color: #fff; text-decoration: underline;">離線版本</a>
                <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; color: white; cursor: pointer;">&times;</button>
            `;
            document.body.appendChild(notification);
            
            // 5秒後自動移除通知
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        }
    };
    
    // 延遲檢查，給外部資源時間載入
    setTimeout(checkExternalResources, 2000);
    
    // 初始化導航
    NavigationManager.init();
    
    // 初始化 YOLO 管理器 (異步)
    window.yoloManager = new YOLOModelManager();
    
    // 暫時禁用WebSocket連接
    // 建立 WebSocket 連接
    // const wsManager = new WebSocketManager();
    // AppState.websocket = wsManager;
    // wsManager.connect();
    
    // 頁面卸載時關閉 WebSocket 連接
    window.addEventListener('beforeunload', function() {
        if (AppState.websocket) {
            AppState.websocket.disconnect();
        }
    });
    
    // 檢查後端連接
    APIClient.checkHealth()
        .then(() => {
            APIClient.showNotification('後端連接成功', 'success');
            // 檢查URL hash並載入對應分頁
            NavigationManager.handleInitialHash();
        })
        .catch(() => {
            APIClient.showNotification('無法連接到後端服務', 'error');
            // 即使後端連接失敗，也處理URL hash
            NavigationManager.handleInitialHash();
        });
    
    // 監聽瀏覽器前進/後退按鈕
    window.addEventListener('hashchange', function() {
        NavigationManager.handleHashChange();
    });
    
    // 定期更新系統狀態（只在連接成功且 WebSocket 不可用時）
    setInterval(async () => {
        if (AppState.activeSection === 'dashboard' && !AppState.isConnected) {
            try {
                const stats = await APIClient.getSystemStats();
                DashboardManager.updateStats(stats);
            } catch (error) {
                console.error('定期更新系統狀態失敗:', error);
            }
        }
    }, 10000); // WebSocket 斷開時每 10 秒用 API 更新
});

// ============================
// 全局函數（供 HTML 調用）
// ============================

// 攝影機相關
window.refreshCameras = () => CameraManager.refreshCameras();

// 分析相關
window.exportData = (format) => AnalyticsManager.exportData(format);
window.setAnalyticsPeriod = (period) => AnalyticsManager.setPeriod(period);
window.refreshAnalytics = () => AnalyticsManager.loadAnalytics();
window.exportDetectionResults = () => AnalyticsManager.exportData('csv');
window.refreshDetectionResults = () => AnalyticsManager.loadDetectionResults();
window.showDetectionDetail = (detectionId) => {
    console.log('查看檢測詳情:', detectionId);
    // 可以在這裡實現詳情彈窗
};

// 配置相關
window.saveConfig = () => ConfigManager.saveConfig();
window.loadModel = () => ConfigManager.loadModel();

// 數據管理全局實例
let globalDataManager = null;

// 數據管理相關（初始化全局實例）
window.DataManager = {
    async init() {
        if (!globalDataManager) {
            globalDataManager = new DataManager();
        }
        return globalDataManager;
    },
    
    async applyFilters() {
        const manager = await this.init();
        return manager.applyFilters();
    },
    
    async resetFilters() {
        const manager = await this.init();
        return manager.resetFilters();
    },
    
    async exportData(format) {
        const manager = await this.init();
        return manager.exportData(format);
    },
    
    async toggleSelectAll() {
        const manager = await this.init();
        return manager.toggleSelectAll();
    },
    
    async backupDatabase() {
        const manager = await this.init();
        return manager.backupDatabase();
    },
    
    async optimizeDatabase() {
        const manager = await this.init();
        return manager.optimizeDatabase();
    },
    
    async showClearDialog() {
        const manager = await this.init();
        return manager.showClearDialog();
    },
    
    async loadDataManagement() {
        const manager = await this.init();
        await manager.loadStatistics();
        await manager.loadDetectionResults();
        await manager.loadStorageAnalysis();
        await manager.loadQuickStats();
        manager.setupEventListeners();
    }
};
