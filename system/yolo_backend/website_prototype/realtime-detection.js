/**
 * 即時辨識功能 JavaScript
 * 處理 WebSocket 連接、檢測控制和結果顯示
 */

class RealtimeDetectionManager {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.isDetecting = false;
        this.detectionCount = 0;
        this.objectCount = 0;
        this.fpsCount = 0;
        this.lastFpsUpdate = Date.now();
        this.fpsCounter = 0;
        
        this.API_BASE = window.API_CONFIG ? window.API_CONFIG.baseURL : 'http://26.86.64.166:8001/api/v1';
        this.WS_URL = window.API_CONFIG ? window.API_CONFIG.websocketURL : 'ws://26.86.64.166:8001/ws/detection';
        
        this.initializeElements();
        this.attachEventListeners();
        this.autoConnect();
    }
    
    initializeElements() {
        // WebSocket 狀態
        this.wsStatus = document.getElementById('websocket-status');
        this.wsStatusText = document.getElementById('ws-status-text');
        
        // 控制元素
        this.cameraSelect = document.getElementById('camera-select');
        this.detectionStatus = document.getElementById('detection-status');
        this.startBtn = document.getElementById('start-detection-btn');
        this.stopBtn = document.getElementById('stop-detection-btn');
        this.refreshBtn = document.getElementById('refresh-status-btn');
        
        // 統計元素
        this.detectionCountEl = document.getElementById('detection-count');
        this.objectCountEl = document.getElementById('object-count');
        this.fpsCountEl = document.getElementById('fps-count');
        
        // 結果顯示元素
        this.latestResult = document.getElementById('latest-result');
        this.historyList = document.getElementById('detection-history-list');
        this.clearResultsBtn = document.getElementById('clear-results-btn');
        
        // 日誌元素
        this.systemLog = document.getElementById('system-log');
        this.clearLogBtn = document.getElementById('clear-log-btn');
        
        // 載入可用攝影機
        this.loadAvailableCameras();
    }
    
    async loadAvailableCameras() {
        if (!this.cameraSelect) return;
        
        try {
            this.addLog('🔍 掃描可用攝影機...');
            
            // 調用攝影機掃描 API
            const response = await fetch('/api/v1/cameras/scan?max_index=6&warmup_frames=1&force_probe=false');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // 清空現有選項
            this.cameraSelect.innerHTML = '';
            
            if (data.available_indices && data.available_indices.length > 0) {
                // 添加可用的攝影機
                data.available_indices.forEach(index => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = `攝影機 ${index}`;
                    this.cameraSelect.appendChild(option);
                });
                
                this.addLog(`✅ 找到 ${data.available_indices.length} 個可用攝影機: ${data.available_indices.join(', ')}`, 'success');
            } else {
                // 沒有找到攝影機
                const option = document.createElement('option');
                option.value = '';
                option.textContent = '未找到可用攝影機';
                option.disabled = true;
                this.cameraSelect.appendChild(option);
                
                this.addLog('⚠️ 未找到可用攝影機', 'warning');
            }
            
        } catch (error) {
            this.addLog(`❌ 攝影機掃描失敗: ${error.message}`, 'error');
            
            // 如果掃描失敗，提供預設選項
            this.cameraSelect.innerHTML = '';
            for (let i = 0; i < 4; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = `攝影機 ${i} (未驗證)`;
                this.cameraSelect.appendChild(option);
            }
        }
    }
    
    attachEventListeners() {
        if (this.startBtn) {
            this.startBtn.addEventListener('click', () => this.startDetection());
        }
        
        if (this.stopBtn) {
            this.stopBtn.addEventListener('click', () => this.stopDetection());
        }
        
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.refreshStatus());
        }
        
        if (this.clearResultsBtn) {
            this.clearResultsBtn.addEventListener('click', () => this.clearResults());
        }
        
        if (this.clearLogBtn) {
            this.clearLogBtn.addEventListener('click', () => this.clearLog());
        }
    }
    
    addLog(message, type = 'info') {
        if (!this.systemLog) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        logEntry.innerHTML = `
            <span class="timestamp">[${timestamp}]</span>
            <span class="message">${message}</span>
        `;
        
        this.systemLog.appendChild(logEntry);
        this.systemLog.scrollTop = this.systemLog.scrollHeight;
    }
    
    updateWebSocketStatus(status, message) {
        if (!this.wsStatus || !this.wsStatusText) return;
        
        this.wsStatus.className = `alert alert-${status}`;
        this.wsStatusText.textContent = message;
        
        if (status === 'success') {
            this.wsStatus.classList.add('connected');
            this.wsStatus.classList.remove('disconnected', 'connecting');
        } else if (status === 'danger') {
            this.wsStatus.classList.add('disconnected');
            this.wsStatus.classList.remove('connected', 'connecting');
        } else if (status === 'warning') {
            this.wsStatus.classList.add('connecting');
            this.wsStatus.classList.remove('connected', 'disconnected');
        }
    }
    
    autoConnect() {
        this.addLog('🔄 自動連接 WebSocket...');
        this.connectWebSocket();
    }
    
    connectWebSocket() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.addLog('⚠️ WebSocket 已經連接', 'warning');
            return;
        }
        
        this.addLog('🔄 正在連接 WebSocket...');
        this.updateWebSocketStatus('warning', '正在連接...');
        
        try {
            this.ws = new WebSocket(this.WS_URL);
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.addLog('✅ WebSocket 連接成功！', 'success');
                this.updateWebSocketStatus('success', '已連接');
            };
            
            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };
            
            this.ws.onclose = () => {
                this.isConnected = false;
                this.addLog('🔌 WebSocket 連接已斷開', 'warning');
                this.updateWebSocketStatus('danger', '連接已斷開');
                
                // 5秒後自動重連
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.addLog('🔄 嘗試重新連接...', 'info');
                        this.connectWebSocket();
                    }
                }, 5000);
            };
            
            this.ws.onerror = (error) => {
                this.addLog(`❌ WebSocket 錯誤: ${error}`, 'error');
                this.updateWebSocketStatus('danger', '連接錯誤');
            };
            
        } catch (error) {
            this.addLog(`❌ WebSocket 連接失敗: ${error.message}`, 'error');
            this.updateWebSocketStatus('danger', '連接失敗');
        }
    }
    
    handleWebSocketMessage(event) {
        this.fpsCounter++;
        const now = Date.now();
        
        // 計算 FPS
        if (now - this.lastFpsUpdate >= 1000) {
            this.fpsCount = this.fpsCounter;
            this.fpsCounter = 0;
            this.lastFpsUpdate = now;
            this.updateStats();
        }
        
        try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'detection_result') {
                this.handleDetectionResult(data);
            } else {
                this.addLog(`📨 收到訊息: ${data.type}`, 'info');
            }
            
        } catch (error) {
            this.addLog(`❌ 解析訊息失敗: ${error.message}`, 'error');
        }
    }
    
    handleDetectionResult(data) {
        this.detectionCount++;
        
        // 統計檢測到的物件數量
        if (data.detections && data.detections.length > 0) {
            this.objectCount += data.detections.length;
            this.addLog(`🎯 檢測到 ${data.detections.length} 個物件: ${data.detections.map(d => d.class_name).join(', ')}`, 'success');
        }
        
        this.updateStats();
        this.updateLatestResult(data);
        this.addToHistory(data);
    }
    
    updateStats() {
        if (this.detectionCountEl) this.detectionCountEl.textContent = this.detectionCount;
        if (this.objectCountEl) this.objectCountEl.textContent = this.objectCount;
        if (this.fpsCountEl) this.fpsCountEl.textContent = this.fpsCount;
    }
    
    updateLatestResult(data) {
        if (!this.latestResult) return;
        
        const objectsDetected = data.detections ? data.detections.length : 0;
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        
        let objectsHtml = '';
        if (data.detections && data.detections.length > 0) {
            objectsHtml = data.detections.map(detection => 
                `<span class="object-tag">
                    ${detection.class_name}
                    <span class="confidence-score">${(detection.confidence * 100).toFixed(1)}%</span>
                </span>`
            ).join('');
        }
        
        this.latestResult.innerHTML = `
            <div class="detection-item">
                <div class="detection-meta">
                    <span><strong>檢測 #${this.detectionCount}</strong></span>
                    <span>${timestamp}</span>
                </div>
                <div class="detection-info">
                    <p><strong>📹 攝影機:</strong> ${data.camera_index}</p>
                    <p><strong>🔢 物件數量:</strong> ${objectsDetected}</p>
                    ${objectsDetected > 0 ? 
                        `<div class="detected-objects">
                            <strong>🎯 檢測物件:</strong><br>
                            ${objectsHtml}
                        </div>` : 
                        '<p><strong>❌ 未檢測到物件</strong></p>'
                    }
                </div>
            </div>
        `;
    }
    
    addToHistory(data) {
        if (!this.historyList) return;
        
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        const objectsDetected = data.detections ? data.detections.length : 0;
        
        const historyItem = document.createElement('div');
        historyItem.className = 'detection-item mb-2';
        historyItem.innerHTML = `
            <div class="detection-meta">
                <span>#${this.detectionCount}</span>
                <span>${timestamp}</span>
            </div>
            <div class="detection-summary">
                <small>攝影機 ${data.camera_index} - ${objectsDetected} 個物件</small>
            </div>
        `;
        
        // 插入到最前面
        this.historyList.insertBefore(historyItem, this.historyList.firstChild);
        
        // 限制歷史記錄數量（最多保留 20 條）
        while (this.historyList.children.length > 20) {
            this.historyList.removeChild(this.historyList.lastChild);
        }
    }
    
    async apiCall(url, method = 'GET', body = null) {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            
            if (body) {
                options.body = JSON.stringify(body);
            }
            
            this.addLog(`🔄 API 調用: ${method} ${url.replace(this.API_BASE, '')}`);
            const response = await fetch(url, options);
            const data = await response.json();
            
            if (response.ok) {
                this.addLog(`✅ API 調用成功`, 'success');
                return data;
            } else {
                this.addLog(`❌ API 調用失敗: ${response.status} - ${data.error || data.detail || '未知錯誤'}`, 'error');
                return null;
            }
        } catch (error) {
            this.addLog(`❌ API 調用錯誤: ${error.message}`, 'error');
            return null;
        }
    }
    
    async startDetection() {
        if (!this.cameraSelect) return;
        
        const cameraIndex = this.cameraSelect.value;
        this.addLog(`🚀 正在啟動攝影機 ${cameraIndex} 的即時檢測...`);
        
        const result = await this.apiCall(`${this.API_BASE}/realtime/start/${cameraIndex}`, 'POST');
        
        if (result) {
            this.isDetecting = true;
            this.updateDetectionStatus('檢測中', 'warning');
            this.updateButtons();
            this.addLog(`✅ 即時檢測已啟動，任務ID: ${result.task_id}`, 'success');
        }
    }
    
    async stopDetection() {
        if (!this.cameraSelect) return;
        
        const cameraIndex = this.cameraSelect.value;
        this.addLog(`⏹️ 正在停止攝影機 ${cameraIndex} 的即時檢測...`);
        
        const result = await this.apiCall(`${this.API_BASE}/realtime/stop/${cameraIndex}`, 'POST');
        
        if (result) {
            this.isDetecting = false;
            this.updateDetectionStatus('已停止', 'secondary');
            this.updateButtons();
            this.addLog(`✅ 即時檢測已停止，總檢測數: ${result.total_detections}`, 'success');
        }
    }
    
    async refreshStatus() {
        if (!this.cameraSelect) return;
        
        const cameraIndex = this.cameraSelect.value;
        this.addLog(`📊 檢查攝影機 ${cameraIndex} 的檢測狀態...`);
        
        const result = await this.apiCall(`${this.API_BASE}/realtime/status/${cameraIndex}`);
        
        if (result) {
            this.isDetecting = result.running;
            
            if (result.running) {
                this.updateDetectionStatus('檢測中', 'warning');
                this.addLog(`✅ 檢測狀態: 運行中`, 'success');
                this.addLog(`📋 任務ID: ${result.task_id}, 檢測數量: ${result.detection_count}`, 'info');
            } else {
                this.updateDetectionStatus('未檢測', 'secondary');
                this.addLog(`ℹ️ 檢測狀態: 未運行`, 'info');
            }
            
            this.updateButtons();
        }
    }
    
    updateDetectionStatus(text, badgeClass) {
        if (this.detectionStatus) {
            this.detectionStatus.textContent = text;
            this.detectionStatus.className = `badge bg-${badgeClass}`;
        }
    }
    
    updateButtons() {
        if (this.startBtn && this.stopBtn) {
            this.startBtn.disabled = this.isDetecting;
            this.stopBtn.disabled = !this.isDetecting;
        }
    }
    
    clearResults() {
        if (this.latestResult) {
            this.latestResult.innerHTML = `
                <div class="no-detection">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <p class="text-muted">等待檢測結果...</p>
                </div>
            `;
        }
        
        if (this.historyList) {
            this.historyList.innerHTML = '';
        }
        
        this.detectionCount = 0;
        this.objectCount = 0;
        this.updateStats();
        
        this.addLog('🧹 檢測結果已清空', 'info');
    }
    
    clearLog() {
        if (this.systemLog) {
            this.systemLog.innerHTML = `
                <div class="log-entry">
                    <span class="timestamp">[系統]</span>
                    <span class="message">日誌已清空</span>
                </div>
            `;
        }
    }
}

// 當頁面載入且即時辨識頁面被激活時初始化
let realtimeManager = null;

// 監聽頁面切換事件
document.addEventListener('DOMContentLoaded', function() {
    // 監聽導航點擊
    const navLinks = document.querySelectorAll('.nav-link[data-section]');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            const section = this.getAttribute('data-section');
            if (section === 'realtime-detection') {
                // 延遲初始化，確保DOM已渲染
                setTimeout(() => {
                    if (!realtimeManager) {
                        realtimeManager = new RealtimeDetectionManager();
                    }
                }, 100);
            }
        });
    });
});

// 如果直接訪問即時辨識頁面
if (window.location.hash === '#realtime-detection') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(() => {
            if (!realtimeManager) {
                realtimeManager = new RealtimeDetectionManager();
            }
        }, 500);
    });
}
