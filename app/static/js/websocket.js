/**
 * WebSocket 連接管理器
 * 處理與後端的即時通訊
 */

class WebSocketManager {
    constructor() {
        this.connections = new Map();
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
        this.reconnectAttempts = new Map();
        this.listeners = new Map();
    }

    /**
     * 連接WebSocket
     * @param {string} endpoint - WebSocket端點
     * @param {string} id - 連接ID
     * @param {Function} onMessage - 消息處理回調
     * @param {Function} onError - 錯誤處理回調
     */
    connect(endpoint, id, onMessage, onError) {
        // 動態偵測 WebSocket 地址
        const currentHost = window.location.hostname;
        const wsHost = currentHost === 'localhost' || currentHost === '127.0.0.1' 
            ? 'localhost:8000' 
            : `${currentHost}:8000`;
        
        const wsUrl = `ws://${wsHost}${endpoint}`;
        console.log(`[WebSocket] 連接到: ${wsUrl}`);

        try {
            const ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                console.log(`[WebSocket] ${id} 連接成功`);
                this.connections.set(id, ws);
                this.reconnectAttempts.set(id, 0);
                
                // 發送連接成功事件
                this.emit('connected', { id, endpoint });
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log(`[WebSocket] ${id} 收到消息:`, data);
                    
                    if (onMessage) {
                        onMessage(data);
                    }
                    
                    // 發送消息事件
                    this.emit('message', { id, data });
                } catch (error) {
                    console.error(`[WebSocket] ${id} 解析消息失敗:`, error);
                }
            };

            ws.onclose = (event) => {
                console.log(`[WebSocket] ${id} 連接關閉:`, event.code, event.reason);
                this.connections.delete(id);
                
                // 自動重連
                this.reconnect(endpoint, id, onMessage, onError);
            };

            ws.onerror = (error) => {
                console.error(`[WebSocket] ${id} 錯誤:`, error);
                
                if (onError) {
                    onError(error);
                }
                
                // 發送錯誤事件
                this.emit('error', { id, error });
            };

        } catch (error) {
            console.error(`[WebSocket] ${id} 創建失敗:`, error);
            if (onError) {
                onError(error);
            }
        }
    }

    /**
     * 重新連接
     */
    reconnect(endpoint, id, onMessage, onError) {
        const attempts = this.reconnectAttempts.get(id) || 0;
        const delay = Math.min(this.reconnectDelay * Math.pow(2, attempts), this.maxReconnectDelay);
        
        console.log(`[WebSocket] ${id} 將在 ${delay}ms 後重連 (嘗試 ${attempts + 1})`);
        
        setTimeout(() => {
            this.reconnectAttempts.set(id, attempts + 1);
            this.connect(endpoint, id, onMessage, onError);
        }, delay);
    }

    /**
     * 發送消息
     */
    send(id, message) {
        const ws = this.connections.get(id);
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(message));
            return true;
        }
        console.warn(`[WebSocket] ${id} 未連接，無法發送消息`);
        return false;
    }

    /**
     * 斷開連接
     */
    disconnect(id) {
        const ws = this.connections.get(id);
        if (ws) {
            ws.close();
            this.connections.delete(id);
            this.reconnectAttempts.delete(id);
            console.log(`[WebSocket] ${id} 手動斷開連接`);
        }
    }

    /**
     * 斷開所有連接
     */
    disconnectAll() {
        this.connections.forEach((ws, id) => {
            this.disconnect(id);
        });
    }

    /**
     * 添加事件監聽器
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
     * 移除事件監聽器
     */
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * 發送事件
     */
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`[WebSocket] 事件回調錯誤 (${event}):`, error);
                }
            });
        }
    }

    /**
     * 獲取連接狀態
     */
    getConnectionStatus(id) {
        const ws = this.connections.get(id);
        if (!ws) return 'disconnected';
        
        switch (ws.readyState) {
            case WebSocket.CONNECTING: return 'connecting';
            case WebSocket.OPEN: return 'connected';
            case WebSocket.CLOSING: return 'closing';
            case WebSocket.CLOSED: return 'disconnected';
            default: return 'unknown';
        }
    }

    /**
     * 獲取所有連接狀態
     */
    getAllConnectionStatus() {
        const status = {};
        this.connections.forEach((ws, id) => {
            status[id] = this.getConnectionStatus(id);
        });
        return status;
    }
}

// 創建全局WebSocket管理器實例
const wsManager = new WebSocketManager();

// 系統統計WebSocket
function connectSystemStats() {
    wsManager.connect(
        '/ws/system-stats',
        'system-stats',
        (data) => {
            if (data.type === 'system_stats') {
                updateSystemStats(data.data);
            }
        },
        (error) => {
            console.error('系統統計WebSocket錯誤:', error);
            showNotification('系統統計連接失敗', 'error');
        }
    );
}

// 任務更新WebSocket
function connectTaskUpdates() {
    wsManager.connect(
        '/ws/task-updates',
        'task-updates',
        (data) => {
            if (data.type === 'task_update') {
                updateTaskList(data.active_tasks);
                updateTaskStats(data.stats);
            }
        },
        (error) => {
            console.error('任務更新WebSocket錯誤:', error);
            showNotification('任務更新連接失敗', 'error');
        }
    );
}

// 分析數據WebSocket
function connectAnalytics() {
    wsManager.connect(
        '/ws/analytics',
        'analytics',
        (data) => {
            if (data.type === 'analytics_update') {
                updateAnalyticsCharts(data.data);
            }
        },
        (error) => {
            console.error('分析數據WebSocket錯誤:', error);
            showNotification('分析數據連接失敗', 'error');
        }
    );
}

// 攝影機檢測WebSocket
function connectCameraStream(cameraId) {
    wsManager.connect(
        `/ws/detection/${cameraId}`,
        `camera-${cameraId}`,
        (data) => {
            if (data.type === 'detection') {
                updateDetectionDisplay(cameraId, data);
            } else if (data.type === 'error') {
                console.error(`攝影機 ${cameraId} 錯誤:`, data.message);
                showNotification(`攝影機 ${cameraId} 錯誤: ${data.message}`, 'error');
            }
        },
        (error) => {
            console.error(`攝影機 ${cameraId} WebSocket錯誤:`, error);
            showNotification(`攝影機 ${cameraId} 連接失敗`, 'error');
        }
    );
}

// 斷開攝影機檢測WebSocket
function disconnectCameraStream(cameraId) {
    wsManager.disconnect(`camera-${cameraId}`);
}

// 初始化所有WebSocket連接
function initializeWebSocketConnections() {
    console.log('[WebSocket] 初始化連接...');
    
    // 連接系統統計
    connectSystemStats();
    
    // 連接任務更新
    connectTaskUpdates();
    
    // 連接分析數據
    connectAnalytics();
    
    // 監聽連接狀態變化
    wsManager.on('connected', (data) => {
        console.log(`[WebSocket] ${data.id} 連接成功`);
        updateConnectionStatus(data.id, 'connected');
    });
    
    wsManager.on('error', (data) => {
        console.error(`[WebSocket] ${data.id} 連接錯誤`);
        updateConnectionStatus(data.id, 'error');
    });
}

// 更新連接狀態顯示
function updateConnectionStatus(connectionId, status) {
    const statusElement = document.querySelector(`[data-connection="${connectionId}"]`);
    if (statusElement) {
        statusElement.className = `connection-status status-${status}`;
        statusElement.textContent = getStatusText(status);
    }
}

// 獲取狀態文字
function getStatusText(status) {
    const statusTexts = {
        'connected': '已連接',
        'connecting': '連接中',
        'disconnected': '已斷開',
        'error': '連接錯誤'
    };
    return statusTexts[status] || status;
}

// 清理WebSocket連接
function cleanupWebSocketConnections() {
    console.log('[WebSocket] 清理所有連接...');
    wsManager.disconnectAll();
}

// 頁面卸載時清理連接
window.addEventListener('beforeunload', cleanupWebSocketConnections);

// 導出給全局使用
window.wsManager = wsManager;
window.initializeWebSocketConnections = initializeWebSocketConnections;
window.connectCameraStream = connectCameraStream;
window.disconnectCameraStream = disconnectCameraStream;
