/**
 * API 配置 - 自動偵測運行環境
 * 支援本機開發和 Radmin 網絡環境
 */

class APIConfig {
    constructor() {
        this.currentHost = window.location.hostname;
        this.currentPort = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');
        this.apiPort = '8001'; // API 服務端口
        
        // 初始化 API 基礎 URL
        this.initializeAPI();
    }

    initializeAPI() {
        // 自動偵測 API 基礎 URL
        if (this.currentHost === 'localhost' || this.currentHost === '127.0.0.1') {
            // 本機開發環境
            this.baseURL = `http://localhost:${this.apiPort}`;
            this.websocketURL = `ws://localhost:${this.apiPort}`;
        } else {
            // Radmin 網絡或其他遠程環境
            this.baseURL = `http://${this.currentHost}:${this.apiPort}`;
            this.websocketURL = `ws://${this.currentHost}:${this.apiPort}`;
        }
        
        console.log('🔧 API 配置初始化:');
        console.log(`   當前主機: ${this.currentHost}`);
        console.log(`   API 基礎 URL: ${this.baseURL}`);
        console.log(`   WebSocket URL: ${this.websocketURL}`);
    }

    getAPIBaseURL() {
        return this.baseURL;
    }

    getWebSocketURL() {
        return this.websocketURL;
    }

    // 構建完整的 API URL
    buildAPIURL(endpoint) {
        // 確保 endpoint 以 / 開頭
        if (!endpoint.startsWith('/')) {
            endpoint = '/' + endpoint;
        }
        return this.baseURL + endpoint;
    }

    // 構建 WebSocket URL
    buildWebSocketURL(endpoint) {
        // 確保 endpoint 以 / 開頭
        if (!endpoint.startsWith('/')) {
            endpoint = '/' + endpoint;
        }
        return this.websocketURL + endpoint;
    }

    // 通用 fetch 包裝器
    async fetch(endpoint, options = {}) {
        const url = this.buildAPIURL(endpoint);
        
        // 設置默認 headers
        const defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };

        // 合併 headers
        const headers = { ...defaultHeaders, ...(options.headers || {}) };
        
        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return response;
        } catch (error) {
            console.error(`❌ API 請求失敗 [${endpoint}]:`, error);
            throw error;
        }
    }

    // GET 請求
    async get(endpoint, params = {}) {
        const baseUrl = this.buildAPIURL(endpoint);
        const url = new URL(baseUrl);
        
        // 添加查詢參數
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== null) {
                url.searchParams.append(key, params[key]);
            }
        });
        
        return fetch(url.toString(), {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });
    }

    // POST 請求
    async post(endpoint, data = {}) {
        return this.fetch(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT 請求
    async put(endpoint, data = {}) {
        return this.fetch(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // DELETE 請求
    async delete(endpoint) {
        return this.fetch(endpoint, {
            method: 'DELETE'
        });
    }

    // FormData POST 請求（用於文件上傳）
    async postFormData(endpoint, formData) {
        return this.fetch(endpoint, {
            method: 'POST',
            body: formData,
            headers: {} // 讓瀏覽器自動設置 Content-Type
        });
    }

    // WebSocket 連接
    createWebSocket(endpoint) {
        const url = this.buildWebSocketURL(endpoint);
        console.log(`🔌 建立 WebSocket 連接: ${url}`);
        return new WebSocket(url);
    }

    // 檢查 API 連通性
    async checkAPIHealth() {
        try {
            const response = await this.get('/api/v1/health');
            const data = await response.json();
            console.log('✅ API 健康檢查通過:', data);
            return true;
        } catch (error) {
            console.error('❌ API 健康檢查失敗:', error);
            return false;
        }
    }

    // 環境資訊
    getEnvironmentInfo() {
        return {
            host: this.currentHost,
            port: this.currentPort,
            apiBaseURL: this.baseURL,
            websocketURL: this.websocketURL,
            isLocal: this.currentHost === 'localhost' || this.currentHost === '127.0.0.1',
            isRadmin: this.currentHost.startsWith('26.86.64.')
        };
    }
}

// 創建全局 API 實例
window.apiConfig = new APIConfig();

// 為了向後兼容，也導出一些常用的配置
window.API_BASE_URL = window.apiConfig.getAPIBaseURL();
window.WEBSOCKET_BASE_URL = window.apiConfig.getWebSocketURL();

// 在控制台顯示配置資訊
console.log('🌐 YOLOv11 系統 API 配置:', window.apiConfig.getEnvironmentInfo());
