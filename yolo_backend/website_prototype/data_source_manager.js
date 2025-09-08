/**
 * 資料來源管理 JavaScript 模組
 * 專門處理攝影機和影片檔案的管理功能
 */

// 動態檢測 API 基礎地址
function getAPIBaseURL() {
    const currentHost = window.location.hostname;
    const currentPort = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');
    
    // 如果是本機訪問
    if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
        return `http://localhost:8001`;
    }
    // 如果是 Radmin 網絡訪問
    else if (currentHost === '26.86.64.166') {
        return `http://26.86.64.166:8001`;
    }
    // 其他情況使用當前的 host 和端口
    else {
        return `${window.location.protocol}//${currentHost}:8001`;
    }
}

const API_BASE = getAPIBaseURL();

// 資料來源管理類
class DataSourceManager {
    constructor() {
        this.dataSources = [];
        this.initialize();
    }

    async initialize() {
        await this.loadDataSources();
        this.setupEventListeners();
        this.updateStatistics();
    }

    setupEventListeners() {
        // 新增攝影機按鈕
        document.getElementById('addCameraBtn')?.addEventListener('click', () => {
            this.showAddCameraModal();
        });

        // 新增影片檔案按鈕
        document.getElementById('addVideoBtn')?.addEventListener('click', () => {
            this.showAddVideoModal();
        });

        // 上傳影片按鈕
        document.getElementById('uploadVideoBtn')?.addEventListener('click', () => {
            this.showUploadVideoModal();
        });

        // 自動掃描攝影機按鈕
        document.getElementById('scanCameraBtn')?.addEventListener('click', () => {
            this.scanCameras();
        });

        // 重新整理按鈕
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            this.loadDataSources();
        });

        // 檔案上傳處理
        this.setupFileUpload();
    }

    async loadDataSources() {
        console.log('🔄 開始載入資料來源...');
        
        // 顯示載入狀態
        this.showLoadingState();
        
        try {
            // 設定 15 秒超時
            const controller = new AbortController();
            const timeoutId = setTimeout(() => {
                controller.abort();
                console.error('❌ 載入資料來源超時 (15秒)');
            }, 15000);

            const response = await fetch(`${API_BASE}/api/v1/frontend/data-sources`, {
                signal: controller.signal,
                headers: {
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                this.dataSources = await response.json();
                console.log(`✅ 成功載入 ${this.dataSources.length} 個資料來源`);
                this.renderDataSources();
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('❌ 載入資料來源失敗:', error);
            
            if (error.name === 'AbortError') {
                this.showTimeoutError();
            } else {
                this.showLoadingError(error);
            }
        } finally {
            this.hideLoadingState();
        }
    }

    showLoadingState() {
        const loadingHtml = `
            <div class="loading-indicator text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">載入中...</span>
                </div>
                <p class="mt-2 text-muted">正在載入資料來源...</p>
            </div>
        `;
        
        document.getElementById('cameraList').innerHTML = loadingHtml;
        document.getElementById('videoList').innerHTML = loadingHtml;
    }

    hideLoadingState() {
        document.querySelectorAll('.loading-indicator').forEach(el => el.remove());
    }

    showTimeoutError() {
        const errorHtml = `
            <div class="alert alert-warning" role="alert">
                <h6><i class="fas fa-clock"></i> 載入超時</h6>
                <p>載入資料來源超過 15 秒，可能是網絡問題或服務器忙碌。</p>
                <div class="mt-2">
                    <button class="btn btn-outline-primary btn-sm" onclick="dataSourceManager.loadDataSources()">
                        <i class="fas fa-sync"></i> 重試載入
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" onclick="location.reload()">
                        <i class="fas fa-redo"></i> 重新載入頁面
                    </button>
                </div>
            </div>
        `;
        
        document.getElementById('cameraList').innerHTML = errorHtml;
        document.getElementById('videoList').innerHTML = errorHtml;
    }

    showLoadingError(error) {
        const errorHtml = `
            <div class="alert alert-danger" role="alert">
                <h6><i class="fas fa-exclamation-triangle"></i> 載入失敗</h6>
                <p>無法載入資料來源清單: ${error.message}</p>
                <div class="mt-2">
                    <button class="btn btn-outline-danger btn-sm" onclick="dataSourceManager.loadDataSources()">
                        <i class="fas fa-sync"></i> 重試載入
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" onclick="location.reload()">
                        <i class="fas fa-redo"></i> 重新載入頁面
                    </button>
                </div>
            </div>
        `;
        
        document.getElementById('cameraList').innerHTML = errorHtml;
        document.getElementById('videoList').innerHTML = errorHtml;
    }

    renderDataSources() {
        const cameras = this.dataSources.filter(source => source.source_type === 'camera');
        const videos = this.dataSources.filter(source => 
            source.source_type === 'video' || source.source_type === 'video_file');

        this.renderCameras(cameras);
        this.renderVideos(videos);
        this.updateStatistics();
    }

    updateStatistics() {
        const cameras = this.dataSources.filter(source => source.source_type === 'camera');
        const videos = this.dataSources.filter(source => 
            source.source_type === 'video' || source.source_type === 'video_file');
        const active = this.dataSources.filter(source => source.status === 'active');
        const errors = this.dataSources.filter(source => source.status === 'error');

        document.getElementById('cameraCount').textContent = cameras.length;
        document.getElementById('videoCount').textContent = videos.length;
        document.getElementById('activeCount').textContent = active.length;
        document.getElementById('errorCount').textContent = errors.length;
    }

    renderCameras(cameras) {
        const container = document.getElementById('cameraList');
        if (!container) return;

        if (cameras.length === 0) {
            container.innerHTML = `
                <div class="text-muted text-center py-5">
                    <i class="fas fa-info-circle fa-2x"></i>
                    <p class="mt-2">目前沒有設定攝影機</p>
                </div>
            `;
            return;
        }

        container.innerHTML = cameras.map(camera => `
            <div class="source-item" data-source-id="${camera.id}">
                <div class="source-info">
                    <div class="source-name">
                        <i class="fas fa-video text-primary me-2"></i>
                        ${camera.name || '未命名攝影機'}
                    </div>
                    <div class="source-details">
                        <small class="text-muted">設備路徑: ${camera.source_path}</small>
                        <span class="badge bg-${camera.status === 'active' ? 'success' : 'secondary'} ms-2">
                            ${camera.status === 'active' ? '運行中' : '已停止'}
                        </span>
                    </div>
                </div>
                <div class="source-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="dataSourceManager.testConnection(${camera.id})">
                        <i class="fas fa-play me-1"></i>測試
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="dataSourceManager.editDataSource(${camera.id})">
                        <i class="fas fa-edit me-1"></i>編輯
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="dataSourceManager.deleteDataSource(${camera.id})">
                        <i class="fas fa-trash me-1"></i>刪除
                    </button>
                </div>
            </div>
        `).join('');
    }

    renderVideos(videos) {
        const container = document.getElementById('videoList');
        if (!container) return;

        if (videos.length === 0) {
            container.innerHTML = `
                <div class="text-muted text-center py-5">
                    <i class="fas fa-info-circle fa-2x"></i>
                    <p class="mt-2">目前沒有影片檔案</p>
                </div>
            `;
            return;
        }

        container.innerHTML = videos.map(video => `
            <div class="source-item" data-source-id="${video.id}">
                <div class="source-info">
                    <div class="source-name">
                        <i class="fas fa-file-video text-info me-2"></i>
                        ${video.name || '未命名影片'}
                    </div>
                    <div class="source-details">
                        <small class="text-muted">檔案路徑: ${video.source_path}</small>
                        <span class="badge bg-${video.status === 'active' ? 'success' : 'secondary'} ms-2">
                            ${video.status === 'active' ? '可用' : '不可用'}
                        </span>
                    </div>
                </div>
                <div class="source-actions">
                    <button class="btn btn-sm btn-success" onclick="dataSourceManager.startAnalysis(${video.id})" title="開始分析">
                        <i class="fas fa-search me-1"></i>分析
                    </button>
                    <button class="btn btn-sm btn-outline-primary" onclick="dataSourceManager.testConnection(${video.id})">
                        <i class="fas fa-play me-1"></i>檢查
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="dataSourceManager.editDataSource(${video.id})">
                        <i class="fas fa-edit me-1"></i>編輯
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="dataSourceManager.deleteDataSource(${video.id})">
                        <i class="fas fa-trash me-1"></i>刪除
                    </button>
                </div>
            </div>
        `).join('');
    }

    showAddCameraModal() {
        const modal = new bootstrap.Modal(document.getElementById('addSourceModal'));
        document.getElementById('modalTitle').textContent = '新增攝影機';
        document.getElementById('sourceTypeField').value = 'camera';
        document.getElementById('sourceForm').reset();
        modal.show();
    }

    showAddVideoModal() {
        const modal = new bootstrap.Modal(document.getElementById('addSourceModal'));
        document.getElementById('modalTitle').textContent = '新增影片檔案';
        document.getElementById('sourceTypeField').value = 'video';
        document.getElementById('sourceForm').reset();
        modal.show();
    }

    showUploadVideoModal() {
        const modal = new bootstrap.Modal(document.getElementById('uploadVideoModal'));
        modal.show();
    }

    async scanCameras() {
        try {
            this.showNotification('正在掃描可用的攝影機...', 'info');
            
            // 使用新的強制探測掃描API，提高成功率
            const response = await fetch(`${API_BASE}/api/v1/cameras/scan?force_probe=true&retries=5&warmup_frames=15`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });

            console.log('API 回應狀態:', response.status, response.statusText);

            if (response.ok) {
                const result = await response.json();
                console.log('完整API回應:', result);
                
                const cameraCount = result.available_indices?.length || 0;
                const detailedCameras = result.devices || result.cameras || [];
                
                console.log('解析結果:');
                console.log('- 可用索引:', result.available_indices);
                console.log('- 詳細攝像頭:', detailedCameras);
                console.log('- 攝像頭數量:', cameraCount);
                
                if (cameraCount > 0) {
                    this.showNotification(`掃描完成！發現 ${cameraCount} 個可用攝影機: [${result.available_indices.join(', ')}]`, 'success');
                    
                    // 檢查 cameraList 元素是否存在
                    const cameraListDiv = document.getElementById('cameraList');
                    if (!cameraListDiv) {
                        console.error('找不到 cameraList 元素！');
                        this.showNotification('界面錯誤：找不到攝像頭列表容器', 'error');
                        return;
                    }
                    
                    console.log('準備渲染攝像頭結果...');
                    // 更新攝影機列表顯示
                    this.renderCameraResults(detailedCameras, result.available_indices);
                    console.log('攝像頭結果渲染完成');
                } else {
                    this.showNotification('掃描完成，但沒有發現可用的攝影機。請確認攝影機已連接且未被其他程式使用。', 'warning');
                    this.renderCameraResults([], []);
                }
            } else {
                const errorText = await response.text();
                console.error('API 錯誤回應:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
        } catch (error) {
            console.error('掃描攝影機失敗:', error);
            this.showNotification('掃描失敗: ' + error.message, 'error');
            this.renderCameraResults([], []);
        }
    }

    renderCameraResults(cameras, availableIndices) {
        console.log('renderCameraResults 被調用');
        console.log('- cameras 參數:', cameras);
        console.log('- availableIndices 參數:', availableIndices);
        
        const cameraListDiv = document.getElementById('cameraList');
        if (!cameraListDiv) {
            console.error('找不到 cameraList 元素！');
            return;
        }

        console.log('cameraList 元素存在，準備渲染...');

        if (availableIndices.length === 0) {
            console.log('沒有可用攝像頭，顯示警告');
            cameraListDiv.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>未發現攝影機</strong>
                    <p class="mb-0 mt-2">請確認：</p>
                    <ul class="mb-0 mt-2">
                        <li>攝影機已連接並開啟</li>
                        <li>沒有其他應用程式正在使用攝影機</li>
                        <li>攝影機驅動程式已正確安裝</li>
                    </ul>
                </div>
            `;
            return;
        }

        console.log(`準備顯示 ${cameras.length} 個攝像頭...`);

        // 顯示發現的攝影機
        const cameraCards = cameras.map(camera => {
            console.log('處理攝像頭:', camera);
            return `
            <div class="camera-item border rounded p-3 mb-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="camera-info">
                        <h6 class="mb-2">
                            <i class="fas fa-video text-primary me-2"></i>
                            攝影機 ${camera.index}
                        </h6>
                        <div class="camera-details">
                            <span class="badge bg-${camera.frame_ok ? 'success' : 'danger'} me-2">
                                ${camera.frame_ok ? '✅ 可用' : '❌ 無法讀取'}
                            </span>
                            <span class="badge bg-info me-2">${camera.backend || 'Unknown'}</span>
                            ${camera.width && camera.height ? 
                                `<span class="badge bg-secondary">${camera.width}x${camera.height}</span>` : 
                                '<span class="badge bg-secondary">解析度未知</span>'
                            }
                        </div>
                        <small class="text-muted mt-1 d-block">
                            來源: ${camera.source || 'normal'} | 後端: ${camera.backend || 'Default'}
                        </small>
                    </div>
                    <div class="camera-actions">
                        ${camera.frame_ok ? `
                            <button class="btn btn-sm btn-primary me-2" onclick="dataSourceManager.testCameraPreview(${camera.index})">
                                <i class="fas fa-video"></i> 預覽
                            </button>
                            <button class="btn btn-sm btn-success" onclick="dataSourceManager.addCameraToList(${camera.index}, '攝影機 ${camera.index}')">
                                <i class="fas fa-plus"></i> 添加
                            </button>
                        ` : `
                            <button class="btn btn-sm btn-secondary" disabled>
                                <i class="fas fa-times"></i> 不可用
                            </button>
                        `}
                    </div>
                </div>
            </div>
        `;
        });

        const html = cameraCards.join('');
        console.log('生成的 HTML:', html);
        
        cameraListDiv.innerHTML = html;
        console.log('攝像頭結果已更新到 DOM');
    }

    async testCameraPreview(cameraIndex) {
        try {
            this.showNotification(`正在啟動攝影機 ${cameraIndex} 預覽...`, 'info');
            
            // 使用實時串流 API
            const streamUrl = `${API_BASE}/api/v1/frontend/cameras/${cameraIndex}/stream?t=${Date.now()}`;
            
            // 在新窗口開啟純粹的影片預覽
            const previewWindow = window.open('', `camera_${cameraIndex}_preview`, 'width=800,height=600,resizable=yes');
            
            if (previewWindow) {
                previewWindow.document.write(`
                    <html>
                        <head>
                            <title>攝影機 ${cameraIndex} - 預覽</title>
                            <style>
                                body {
                                    margin: 0;
                                    padding: 0;
                                    background: #000;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    width: 100vw;
                                    height: 100vh;
                                    overflow: hidden;
                                }
                                .stream-video {
                                    max-width: 100%;
                                    max-height: 100%;
                                    object-fit: contain;
                                    display: block;
                                }
                            </style>
                        </head>
                        <body>
                            <img class="stream-video" src="${streamUrl}" alt="攝影機預覽">
                        </body>
                    </html>
                `);
                previewWindow.document.close();
                
                this.showNotification(`攝影機 ${cameraIndex} 預覽已開啟`, 'success');
            } else {
                this.showNotification('無法開啟預覽視窗，請檢查瀏覽器彈窗設定', 'warning');
            }
            
        } catch (error) {
            console.error('啟動預覽失敗:', error);
            this.showNotification('預覽啟動失敗: ' + error.message, 'error');
        }
    }

    async addCameraToList(cameraIndex, cameraName) {
        try {
            // 創建簡化的數據結構，確保符合後端要求
            const formData = {
                name: cameraName || `攝影機 ${cameraIndex}`,
                source_type: "camera",
                config: {
                    device_id: parseInt(cameraIndex) // 確保是數字類型
                }
            };

            console.log('🎯 準備添加攝影機，數據:', formData);
            await this.saveDataSource(formData);
            this.showNotification(`攝影機 ${cameraIndex} 已添加到資料來源列表`, 'success');
        } catch (error) {
            console.error('添加攝影機失敗:', error);
            this.showNotification('添加攝影機失敗: ' + error.message, 'error');
        }
    }

    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('videoFileInput');

        // 拖放處理
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('drag-over');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('drag-over');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('drag-over');
                const files = e.dataTransfer.files;
                this.handleFileUpload(files);
            });
        }

        // 檔案選擇處理
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFileUpload(e.target.files);
            });
        }
    }

    async handleFileUpload(files) {
        if (!files || files.length === 0) return;

        const progressDiv = document.getElementById('uploadProgress');
        const progressBar = progressDiv.querySelector('.progress-bar');
        const statusText = progressDiv.querySelector('.upload-status');

        progressDiv.style.display = 'block';

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            // 檢查檔案類型
            if (!file.type.startsWith('video/')) {
                this.showNotification(`${file.name} 不是有效的影片檔案`, 'error');
                continue;
            }

            statusText.textContent = `正在上傳 ${file.name}...`;
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('source_type', 'video');
                formData.append('name', file.name);

                const response = await fetch(`${API_BASE}/api/v1/frontend/data-sources/upload/video`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    progressBar.style.width = `${((i + 1) / files.length) * 100}%`;
                    this.showNotification(`${file.name} 上傳成功`, 'success');
                    
                    // 立即刷新資料來源列表以顯示新上傳的檔案
                    await this.loadDataSources();
                } else {
                    throw new Error(`上傳失敗: HTTP ${response.status}`);
                }
            } catch (error) {
                console.error('檔案上傳失敗:', error);
                this.showNotification(`${file.name} 上傳失敗: ${error.message}`, 'error');
            }
        }

        statusText.textContent = '上傳完成';
        await this.loadDataSources();
        
        // 隱藏進度條
        setTimeout(() => {
            progressDiv.style.display = 'none';
            progressBar.style.width = '0%';
            
            // 安全地隱藏模態框
            const modalElement = document.getElementById('uploadVideoModal');
            if (modalElement) {
                const modalInstance = bootstrap.Modal.getInstance(modalElement);
                if (modalInstance) {
                    modalInstance.hide();
                } else {
                    const newModalInstance = new bootstrap.Modal(modalElement);
                    newModalInstance.hide();
                }
            }
        }, 2000);
    }

    async saveDataSource(formData) {
        try {
            console.log('🚀 發送數據到服務器:', JSON.stringify(formData, null, 2));
            
            const response = await fetch(`${API_BASE}/api/v1/frontend/data-sources`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            console.log('📨 服務器回應狀態:', response.status);

            if (response.ok) {
                this.showNotification('資料來源已成功建立', 'success');
                await this.loadDataSources();
                
                // 安全地隱藏模態框
                const modalElement = document.getElementById('addSourceModal');
                if (modalElement) {
                    const modalInstance = bootstrap.Modal.getInstance(modalElement);
                    if (modalInstance) {
                        modalInstance.hide();
                    } else {
                        // 如果沒有實例，嘗試創建並隱藏
                        const newModalInstance = new bootstrap.Modal(modalElement);
                        newModalInstance.hide();
                    }
                }
            } else {
                const error = await response.json();
                console.error('❌ 服務器錯誤回應:', error);
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('保存資料來源失敗:', error);
            this.showNotification('保存失敗: ' + error.message, 'error');
        }
    }

    async testConnection(sourceId) {
        try {
            const response = await fetch(`${API_BASE}/api/v1/frontend/data-sources/${sourceId}/test`, {
                method: 'POST'
            });

            if (response.ok) {
                const result = await response.json();
                // 檢查 status 屬性而不是 success
                const isSuccess = result.status === 'success';
                this.showNotification(
                    isSuccess ? '連接測試成功: ' + result.message : '連接測試失敗: ' + result.message,
                    isSuccess ? 'success' : 'error'
                );
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('測試連接失敗:', error);
            this.showNotification('測試失敗: ' + error.message, 'error');
        }
    }

    async deleteDataSource(sourceId) {
        if (!confirm('確定要刪除這個資料來源嗎？')) return;

        try {
            const response = await fetch(`${API_BASE}/api/v1/frontend/data-sources/${sourceId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showNotification('資料來源已刪除', 'success');
                await this.loadDataSources();
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('刪除資料來源失敗:', error);
            this.showNotification('刪除失敗: ' + error.message, 'error');
        }
    }

    showNotification(message, type = 'info') {
        // 創建通知元素
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
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
        }, 5000);
    }

    // 開始分析功能
    async startAnalysis(sourceId) {
        try {
            // 獲取資料來源詳細資訊
            const response = await fetch(`${API_BASE}/api/v1/frontend/data-sources`);
            const sources = await response.json();
            const source = sources.find(s => s.id === sourceId);
            
            if (!source) {
                this.showNotification('找不到指定的資料來源', 'error');
                return;
            }

            if (source.source_type !== 'video_file' && source.source_type !== 'video') {
                this.showNotification('只能分析影片檔案', 'warning');
                return;
            }

            // 顯示分析配置模態框
            this.showAnalysisModal(source);
            
        } catch (error) {
            console.error('啟動分析失敗:', error);
            this.showNotification('啟動分析失敗: ' + error.message, 'error');
        }
    }

    // 顯示分析配置模態框
    showAnalysisModal(source) {
        // 創建模態框HTML
        const modalHtml = `
            <div class="modal fade" id="analysisModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">🎬 開始影片分析 - ${source.name}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>📊 檢測參數</h6>
                                    <div class="mb-3">
                                        <label class="form-label">信心度閾值</label>
                                        <div class="d-flex align-items-center">
                                            <input type="range" class="form-range me-2" id="confidenceSlider" 
                                                   min="0.1" max="0.9" step="0.01" value="0.5">
                                            <span id="confidenceValue">50%</span>
                                        </div>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">IoU閾值</label>
                                        <div class="d-flex align-items-center">
                                            <input type="range" class="form-range me-2" id="iouSlider" 
                                                   min="0.1" max="0.9" step="0.01" value="0.45">
                                            <span id="iouValue">45%</span>
                                        </div>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">最大檢測數</label>
                                        <input type="number" class="form-control" id="maxDetections" 
                                               value="1000" min="10" max="10000">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h6>⚙️ 輸出設定</h6>
                                    <div class="mb-3">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="saveImages" checked>
                                            <label class="form-check-label" for="saveImages">
                                                保存檢測圖片
                                            </label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="saveVideo">
                                            <label class="form-check-label" for="saveVideo">
                                                保存檢測影片
                                            </label>
                                        </div>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">輸出格式</label>
                                        <select class="form-select" id="outputFormat">
                                            <option value="json">JSON 格式</option>
                                            <option value="csv">CSV 格式</option>
                                            <option value="xml">XML 格式</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">影像尺寸</label>
                                        <select class="form-select" id="imageSize">
                                            <option value="320">320x320 (快速)</option>
                                            <option value="416">416x416 (平衡)</option>
                                            <option value="640" selected>640x640 (標準)</option>
                                            <option value="736">736x736 (高精度)</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="startAnalysisBtn">
                                <i class="fas fa-play"></i> 開始分析
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除現有模態框並添加新的
        const existingModal = document.getElementById('analysisModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = new bootstrap.Modal(document.getElementById('analysisModal'));
        
        // 設置滑桿事件
        document.getElementById('confidenceSlider').addEventListener('input', (e) => {
            document.getElementById('confidenceValue').textContent = Math.round(e.target.value * 100) + '%';
        });
        
        document.getElementById('iouSlider').addEventListener('input', (e) => {
            document.getElementById('iouValue').textContent = Math.round(e.target.value * 100) + '%';
        });
        
        // 設置開始分析按鈕事件
        document.getElementById('startAnalysisBtn').addEventListener('click', () => {
            this.executeAnalysis(source, modal);
        });
        
        modal.show();
    }

    // 執行分析
    async executeAnalysis(source, modal) {
        try {
            const modalElement = document.getElementById('analysisModal');
            const options = {
                confidence: parseFloat(modalElement.querySelector('#confidenceSlider').value),
                iou: parseFloat(modalElement.querySelector('#iouSlider').value),
                maxDetections: parseInt(modalElement.querySelector('#maxDetections').value),
                saveImages: modalElement.querySelector('#saveImages').checked,
                saveVideo: modalElement.querySelector('#saveVideo').checked,
                outputFormat: modalElement.querySelector('#outputFormat').value,
                imageSize: parseInt(modalElement.querySelector('#imageSize').value)
            };

            // 創建分析任務配置 - 匹配後端 TaskCreate 模型
            const analysisConfig = {
                name: `影片分析 - ${source.name}`,
                task_type: 'batch',
                camera_id: String(source.id), // 確保轉換為字符串
                model_name: 'yolov11s',
                confidence: options.confidence,
                iou_threshold: options.iou,
                description: `對影片檔案 "${source.name}" 進行 YOLO 分析 (最大檢測:${options.maxDetections}, 影像尺寸:${options.imageSize}, 輸出格式:${options.outputFormat})`
            };

            // 關閉模態框
            modal.hide();

            console.log('📤 發送分析配置:', analysisConfig);

            // 使用新的影片分析 API
            let response;
            
            if (source.source_type === 'video_file' && source.config.path) {
                // 對於伺服器上的影片檔案，直接傳遞檔案路徑
                const formData = new FormData();
                
                // 創建一個空的檔案物件，但在伺服器端會使用 source.config.path
                const dummyFile = new File([''], source.name, { type: 'video/mp4' });
                formData.append('file', dummyFile);
                formData.append('source_id', source.id);
                formData.append('file_path', source.config.path);  // 傳遞實際檔案路徑

                response = await fetch(`${API_BASE}/api/v2/analysis/video`, {
                    method: 'POST',
                    body: formData
                });
            } else {
                throw new Error('不支援的檔案類型或檔案路徑無效');
            }

            console.log('📥 API 回應狀態:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('📥 API 錯誤回應:', errorText);
                let errorMessage = `HTTP ${response.status}`;
                try {
                    const errorData = JSON.parse(errorText);
                    errorMessage = errorData.detail || errorData.message || errorMessage;
                    if (errorData.detail && typeof errorData.detail === 'object') {
                        // 處理驗證錯誤
                        if (Array.isArray(errorData.detail)) {
                            errorMessage = errorData.detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join(', ');
                        }
                    }
                } catch (e) {
                    errorMessage = errorText || errorMessage;
                }
                throw new Error(`分析任務創建失敗: ${errorMessage}`);
            }

            const result = await response.json();
            
            this.showNotification(`✅ 分析任務已啟動！任務ID: ${result.task_id || result.id}`, 'success');
            
            // 顯示進度提示
            this.showAnalysisProgress(result.task_id || result.id);
            
        } catch (error) {
            console.error('執行分析失敗:', error);
            this.showNotification(`❌ 分析執行失敗: ${error.message}`, 'error');
        }
    }

    // 顯示分析進度
    showAnalysisProgress(taskId) {
        this.showNotification(`🔄 分析進行中... 您可以在主控台查看進度`, 'info');
        
        // 可選：跳轉到主控台頁面
        setTimeout(() => {
            if (confirm('是否跳轉到主控台查看分析進度？')) {
                window.location.href = '../index.html#dashboard';
            }
        }, 2000);
    }
}

// 初始化資料來源管理器
let dataSourceManager;
document.addEventListener('DOMContentLoaded', () => {
    dataSourceManager = new DataSourceManager();
});

// 表單提交處理
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('sourceForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const data = {
                name: formData.get('name'),
                source_type: formData.get('source_type'),
                source_path: formData.get('source_path'),
                description: formData.get('description')
            };
            await dataSourceManager.saveDataSource(data);
        });
    }
});
