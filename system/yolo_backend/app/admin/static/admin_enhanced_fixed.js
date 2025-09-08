/**
 * YOLOv11 後台管理系統 JavaScript - 修復版
 */

class AdminDashboard {
    constructor() {
        this.systemChart = null;
        this.resourcePieChart = null;
        this.memoryChart = null;
        this.networkChart = null;
        this.currentPath = '.';
        this.selectedModel = null;
        this.availableModels = null;
        this.systemData = {
            labels: [],
            cpu: [],
            memory: [],
            gpu: []
        };
        
        // 攝影機管理相關狀態
        this.cameraList = [];
        this.currentCamera = null;
        this.previewStream = null;
        this.previewInterval = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupFileManagerEvents();
        this.setupApiTestEvents();
        this.setupCameraManagerEvents();
        this.initCharts();
        this.loadSystemStatus();
        this.loadYoloConfig();
        this.loadAvailableModels();
        this.loadFileList();
        this.loadCameraList();
        this.loadNetworkStatus();
        this.loadLogs();
        this.checkApiStatus();
        
        // 每 5 秒更新一次系統狀態
        setInterval(() => this.loadSystemStatus(), 5000);
        // 每 30 秒更新一次網絡狀態
        setInterval(() => this.loadNetworkStatus(), 30000);
        // 更新時間
        setInterval(() => this.updateTime(), 1000);
    }

    setupEventListeners() {
        // 側邊欄切換
        const sidebarToggle = document.getElementById('sidebar-toggle');
        const sidebarClose = document.getElementById('sidebar-close');
        
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                document.getElementById('sidebar').classList.toggle('-translate-x-full');
            });
        }

        if (sidebarClose) {
            sidebarClose.addEventListener('click', () => {
                document.getElementById('sidebar').classList.add('-translate-x-full');
            });
        }

        // 導航項目切換
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const target = item.getAttribute('href').substring(1);
                this.showSection(target);
                
                // 更新活動狀態
                document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
            });
        });

        // YOLO 配置表單
        const yoloForm = document.getElementById('yolo-config-form');
        if (yoloForm) {
            yoloForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveYoloConfig();
            });
        }

        // 檔案上傳
        const fileUpload = document.getElementById('file-upload');
        if (fileUpload) {
            fileUpload.addEventListener('change', (e) => {
                this.uploadFile(e.target.files[0]);
            });
        }

        // 重新整理模型按鈕
        const refreshModelsBtn = document.getElementById('refresh-models');
        if (refreshModelsBtn) {
            refreshModelsBtn.addEventListener('click', () => {
                this.loadAvailableModels();
            });
        }

        // 重置配置按鈕
        const resetConfigBtn = document.getElementById('reset-config');
        if (resetConfigBtn) {
            resetConfigBtn.addEventListener('click', () => {
                this.resetYoloConfig();
            });
        }

        // 範圍滑桿值更新
        const confidenceSlider = document.getElementById('confidence');
        const iouSlider = document.getElementById('iou');
        
        if (confidenceSlider) {
            confidenceSlider.addEventListener('input', (e) => {
                const valueSpan = document.getElementById('confidence-value');
                if (valueSpan) valueSpan.textContent = e.target.value;
            });
        }
        
        if (iouSlider) {
            iouSlider.addEventListener('input', (e) => {
                const valueSpan = document.getElementById('iou-value');
                if (valueSpan) valueSpan.textContent = e.target.value;
            });
        }
    }

    showSection(sectionId) {
        console.log('Switching to section:', sectionId);
        
        // 隱藏所有面板
        document.querySelectorAll('.section').forEach(section => {
            section.classList.add('hidden');
        });
        
        // 顯示目標面板
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            console.log('Showing section:', sectionId);
        } else {
            console.error('Section not found:', sectionId);
        }
        
        // 特殊處理
        if (sectionId === 'dashboard') {
            this.loadSystemStatus();
        } else if (sectionId === 'yolo-config') {
            this.loadYoloConfig();
            this.loadAvailableModels();
        } else if (sectionId === 'file-manager') {
            this.loadFileList(this.currentPath);
        }
    }

    updateTime() {
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.textContent = new Date().toLocaleString('zh-TW');
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/admin/api/system/status');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            this.updateSystemMetrics(data);
            this.updateSystemChart(data);
        } catch (error) {
            console.error('載入系統狀態失敗:', error);
            // 顯示錯誤狀態
            this.showErrorState();
        }
    }

    showErrorState() {
        const cpuElement = document.getElementById('cpu-usage');
        const memoryElement = document.getElementById('memory-usage');
        const gpuElement = document.getElementById('gpu-usage');
        
        if (cpuElement) cpuElement.textContent = 'Error';
        if (memoryElement) memoryElement.textContent = 'Error';
        if (gpuElement) gpuElement.textContent = 'Error';
    }

    updateSystemMetrics(data) {
        console.log('Updating system metrics:', data);
        
        const cpuElement = document.getElementById('cpu-usage');
        const memoryElement = document.getElementById('memory-usage');
        const gpuElement = document.getElementById('gpu-usage');
        
        if (cpuElement && data.cpu) {
            cpuElement.textContent = `${Math.round(data.cpu.percent)}%`;
        }
        if (memoryElement && data.memory) {
            memoryElement.textContent = `${Math.round(data.memory.percent)}%`;
        }
        if (gpuElement) {
            if (data.gpu && data.gpu.name && data.gpu.name !== '未檢測到 GPU') {
                gpuElement.textContent = `${Math.round(data.gpu.load || 0)}%`;
            } else {
                gpuElement.textContent = 'N/A';
            }
        }
    }

    initCharts() {
        this.initSystemChart();
        this.initResourcePieChart();
        this.initMemoryChart();
        this.initNetworkChart();
    }

    initSystemChart() {
        const ctx = document.getElementById('system-chart');
        if (!ctx) return;

        this.systemChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CPU',
                        data: [],
                        borderColor: '#00f5ff',
                        backgroundColor: 'rgba(0, 245, 255, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Memory',
                        data: [],
                        borderColor: '#39ff14',
                        backgroundColor: 'rgba(57, 255, 20, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'GPU',
                        data: [],
                        borderColor: '#bf00ff',
                        backgroundColor: 'rgba(191, 0, 255, 0.1)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { color: '#ffffff' }
                    },
                    x: {
                        ticks: { color: '#ffffff' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                }
            }
        });
    }

    initResourcePieChart() {
        const ctx = document.getElementById('resource-chart');
        if (!ctx) return;

        this.resourceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['CPU', 'Memory', 'GPU'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#00f5ff', '#39ff14', '#bf00ff'],
                    borderColor: '#1a1a2e',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                }
            }
        });
    }

    initMemoryChart() {
        const ctx = document.getElementById('memory-chart');
        if (!ctx) return;

        this.memoryChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['已使用', '可用'],
                datasets: [{
                    label: '記憶體 (GB)',
                    data: [0, 0],
                    backgroundColor: ['#ff1493', '#39ff14'],
                    borderColor: ['#ff1493', '#39ff14'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#ffffff' }
                    },
                    x: {
                        ticks: { color: '#ffffff' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                }
            }
        });
    }

    initNetworkChart() {
        const ctx = document.getElementById('network-chart');
        if (!ctx) return;

        this.networkChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '下載',
                        data: [],
                        borderColor: '#00f5ff',
                        backgroundColor: 'rgba(0, 245, 255, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: '上傳',
                        data: [],
                        borderColor: '#ff1493',
                        backgroundColor: 'rgba(255, 20, 147, 0.1)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#ffffff' }
                    },
                    x: {
                        ticks: { color: '#ffffff' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                }
            }
        });
    }

    updateSystemChart(data) {
        if (!this.systemChart) return;

        const now = new Date().toLocaleTimeString();
        
        // 限制資料點數量
        if (this.systemData.labels.length >= 20) {
            this.systemData.labels.shift();
            this.systemData.cpu.shift();
            this.systemData.memory.shift();
            this.systemData.gpu.shift();
        }
        
        this.systemData.labels.push(now);
        this.systemData.cpu.push(data.cpu ? data.cpu.percent : 0);
        this.systemData.memory.push(data.memory ? data.memory.percent : 0);
        this.systemData.gpu.push(data.gpu ? (data.gpu.load || 0) : 0);
        
        this.systemChart.data.labels = this.systemData.labels;
        this.systemChart.data.datasets[0].data = this.systemData.cpu;
        this.systemChart.data.datasets[1].data = this.systemData.memory;
        this.systemChart.data.datasets[2].data = this.systemData.gpu;
        
        this.systemChart.update('none');
    }

    async loadYoloConfig() {
        try {
            const response = await fetch('/admin/api/yolo/config');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const config = await response.json();
            
            const confidenceInput = document.getElementById('confidence');
            const iouInput = document.getElementById('iou');
            const maxDetInput = document.getElementById('max-det');
            const deviceSelect = document.getElementById('device');
            
            if (confidenceInput) confidenceInput.value = config.confidence_threshold || 0.25;
            if (iouInput) iouInput.value = config.iou_threshold || 0.7;
            if (maxDetInput) maxDetInput.value = config.max_det || 1000;
            if (deviceSelect) deviceSelect.value = config.device || 'auto';
            
            // 更新顯示值
            const confidenceValue = document.getElementById('confidence-value');
            const iouValue = document.getElementById('iou-value');
            if (confidenceValue) confidenceValue.textContent = config.confidence_threshold || 0.25;
            if (iouValue) iouValue.textContent = config.iou_threshold || 0.7;
            
            // 更新模型選擇
            const selectedModelElement = document.getElementById('selected-model');
            if (selectedModelElement && config.model_path) {
                selectedModelElement.value = config.model_path;
                // 同時更新顯示文字
                const modelDisplayElement = document.querySelector('.model-name');
                if (modelDisplayElement) {
                    modelDisplayElement.textContent = config.model_path;
                }
            }
            
        } catch (error) {
            console.error('載入 YOLO 配置失敗:', error);
        }
    }

    async loadAvailableModels() {
        try {
            const response = await fetch('/admin/api/yolo/models');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            // 後端返回 official_models 和 custom_models
            this.availableModels = [...(data.official_models || []), ...(data.custom_models || [])];
            this.renderModelCards();
        } catch (error) {
            console.error('載入可用模型失敗:', error);
            this.availableModels = [];
            this.renderModelCards();
        }
    }

    renderModelCards() {
        const officialContainer = document.getElementById('official-models');
        const customContainer = document.getElementById('custom-models');
        
        if (!officialContainer || !customContainer) return;

        // 清空容器
        officialContainer.innerHTML = '';
        customContainer.innerHTML = '';
        
        // 從後端 API 獲取的模型資料
        const officialModels = this.availableModels.filter(model => !model.custom);
        const customModels = this.availableModels.filter(model => model.custom);
        
        // 渲染官方模型
        if (officialModels.length === 0) {
            officialContainer.innerHTML = '<p class="text-gray-400 text-center">正在載入模型列表...</p>';
        } else {
            officialModels.forEach(model => {
                const card = this.createModelCard(model, model.exists || false, true);
                officialContainer.appendChild(card);
            });
        }
        
        // 渲染自定義模型
        if (customModels.length === 0) {
            customContainer.innerHTML = '<p class="text-gray-400 text-center">暫無自定義模型</p>';
        } else {
            customModels.forEach(model => {
                const card = this.createModelCard(model, true, false);
                customContainer.appendChild(card);
            });
        }
    }

    createModelCard(model, isDownloaded, isOfficial) {
        const card = document.createElement('div');
        const modelFileName = model.file || model.name;
        card.className = `model-card p-4 cursor-pointer border-2 border-gray-600 rounded-lg hover:border-cyan-400 transition-all duration-300 ${this.selectedModel?.file === modelFileName ? 'border-cyan-400 bg-cyan-900 bg-opacity-20' : ''}`;
        
        card.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <h4 class="font-bold text-cyan-100 text-sm">${model.name || modelFileName}</h4>
                <span class="text-xs px-2 py-1 rounded ${isDownloaded ? 'bg-green-600' : 'bg-gray-600'} text-white">
                    ${isDownloaded ? '已下載' : '未下載'}
                </span>
            </div>
            <p class="text-xs text-gray-300 mb-2">${model.description || '模型檔案'}</p>
            <div class="text-xs text-cyan-400">
                大小: ${model.actual_size || model.size || 'Unknown'}
            </div>
            ${!isDownloaded ? '<button class="mt-2 w-full py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700">下載模型</button>' : ''}
        `;
        
        card.addEventListener('click', (e) => {
            e.preventDefault();
            if (!isDownloaded) {
                this.downloadModel(model);
            } else {
                this.selectModel(model, card);
            }
        });
        
        return card;
    }

    selectModel(model, cardElement) {
        this.selectedModel = model;
        
        // 更新UI - 移除所有選中狀態
        document.querySelectorAll('.model-card').forEach(card => {
            card.classList.remove('border-cyan-400', 'bg-cyan-900', 'bg-opacity-20');
            card.classList.add('border-gray-600');
        });
        
        // 添加選中狀態到當前卡片
        if (cardElement) {
            cardElement.classList.remove('border-gray-600');
            cardElement.classList.add('border-cyan-400', 'bg-cyan-900', 'bg-opacity-20');
        }
        
        // 更新選中模型輸入框 - 使用檔案名稱
        const selectedModelInput = document.getElementById('selected-model');
        if (selectedModelInput) {
            selectedModelInput.value = model.file || model.name;
        }
        
        // 更新顯示的模型名稱
        const modelDisplayElement = document.querySelector('.model-name');
        if (modelDisplayElement) {
            modelDisplayElement.textContent = model.file || model.name;
        }
        
        console.log('選擇模型:', model.file || model.name);
        
        console.log('已選擇模型:', model.name);
    }

    async downloadModel(model) {
        try {
            const response = await fetch(`/admin/api/yolo/download/${model.name}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                console.log(`模型 ${model.name} 下載完成`);
                this.loadAvailableModels(); // 重新載入模型列表
            } else {
                console.error(`模型 ${model.name} 下載失敗`);
            }
        } catch (error) {
            console.error('下載模型失敗:', error);
        }
    }

    async saveYoloConfig() {
        try {
            const formData = {
                confidence: parseFloat(document.getElementById('confidence').value),
                iou: parseFloat(document.getElementById('iou').value),
                max_det: parseInt(document.getElementById('max-det').value),
                device: document.getElementById('device').value,
                model_path: document.getElementById('selected-model').value
            };

            const response = await fetch('/admin/api/yolo/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                console.log('YOLO 配置保存成功');
                alert('配置保存成功！');
            } else {
                console.error('保存配置失敗');
                alert('保存配置失敗！');
            }
        } catch (error) {
            console.error('保存配置失敗:', error);
            alert('保存配置失敗：' + error.message);
        }
    }

    resetYoloConfig() {
        // 重置為預設值
        document.getElementById('confidence').value = 0.25;
        document.getElementById('iou').value = 0.45;
        document.getElementById('max-det').value = 1000;
        document.getElementById('device').value = 'auto';
        document.getElementById('selected-model').value = '';
        
        // 更新顯示值
        const confidenceValue = document.getElementById('confidence-value');
        const iouValue = document.getElementById('iou-value');
        if (confidenceValue) confidenceValue.textContent = '0.25';
        if (iouValue) iouValue.textContent = '0.45';
        
        // 清除模型選擇
        document.querySelectorAll('.model-card').forEach(card => {
            card.classList.remove('border-cyan-400', 'bg-cyan-900', 'bg-opacity-20');
            card.classList.add('border-gray-600');
        });
        
        this.selectedModel = null;
        console.log('配置已重置為預設值');
    }

    async loadFileList(path = '') {
        try {
            // 如果路徑是 "." 則發送空字符串
            const cleanPath = path === '.' ? '' : path;
            const response = await fetch(`/admin/api/files?path=${encodeURIComponent(cleanPath)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.currentPath = data.current_path;
            this.renderFileList(data);
            this.updateBreadcrumb(data.current_path);
        } catch (error) {
            console.error('載入檔案列表失敗:', error);
            this.showFileError('載入檔案列表失敗: ' + error.message);
        }
    }

    renderFileList(data) {
        const container = document.getElementById('file-list');
        if (!container) return;

        container.innerHTML = '';
        
        const allItems = [...data.directories, ...data.files];
        
        if (allItems.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-400 py-8">
                    <i class="fas fa-folder-open text-4xl mb-4"></i>
                    <p>此資料夾是空的</p>
                </div>
            `;
            return;
        }

        allItems.forEach(item => {
            const row = document.createElement('div');
            row.className = 'file-row grid grid-cols-5 gap-4 p-3 border border-gray-600 rounded-md hover:border-cyan-400 hover:bg-gray-800 transition-all duration-300 cursor-pointer';
            
            const isDirectory = item.type === 'directory';
            const icon = this.getFileIcon(item);
            const size = isDirectory ? '--' : this.formatFileSize(item.size);
            const modified = item.modified ? new Date(item.modified * 1000).toLocaleString() : '--';
            
            row.innerHTML = `
                <div class="flex items-center">
                    <i class="${icon} mr-3 text-cyan-400"></i>
                    <span class="text-cyan-100 truncate">${item.name}</span>
                </div>
                <div class="text-gray-300">${isDirectory ? '資料夾' : this.getFileType(item.extension)}</div>
                <div class="text-gray-300">${size}</div>
                <div class="text-gray-300 text-sm">${modified}</div>
                <div class="flex space-x-2">
                    ${isDirectory ? `
                        <button class="open-folder text-blue-400 hover:text-blue-300" title="開啟">
                            <i class="fas fa-folder-open"></i>
                        </button>
                    ` : `
                        <button class="download-file text-green-400 hover:text-green-300" title="下載">
                            <i class="fas fa-download"></i>
                        </button>
                    `}
                    ${!item.is_parent ? `
                        <button class="delete-item text-red-400 hover:text-red-300" title="刪除">
                            <i class="fas fa-trash"></i>
                        </button>
                    ` : ''}
                </div>
            `;
            
            // 添加事件監聽器
            if (isDirectory) {
                const openBtn = row.querySelector('.open-folder');
                if (openBtn) {
                    openBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.openFolder(item.path);
                    });
                }
                
                // 雙擊開啟資料夾
                row.addEventListener('dblclick', () => {
                    this.openFolder(item.path);
                });
            } else {
                const downloadBtn = row.querySelector('.download-file');
                if (downloadBtn) {
                    downloadBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.downloadFile(item.path);
                    });
                }
            }
            
            // 刪除按鈕
            const deleteBtn = row.querySelector('.delete-item');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deleteItem(item.path, item.name, isDirectory);
                });
            }
            
            container.appendChild(row);
        });
    }

    getFileIcon(item) {
        if (item.type === 'directory') {
            return item.is_parent ? 'fas fa-level-up-alt' : 'fas fa-folder';
        }
        
        const ext = item.extension?.toLowerCase();
        switch (ext) {
            case '.py': return 'fab fa-python text-yellow-400';
            case '.js': return 'fab fa-js-square text-yellow-400';
            case '.html': return 'fab fa-html5 text-orange-400';
            case '.css': return 'fab fa-css3-alt text-blue-400';
            case '.json': return 'fas fa-brackets-curly text-green-400';
            case '.txt': case '.md': return 'fas fa-file-text text-gray-400';
            case '.jpg': case '.jpeg': case '.png': case '.gif': return 'fas fa-image text-purple-400';
            case '.mp4': case '.avi': case '.mov': return 'fas fa-video text-red-400';
            case '.pdf': return 'fas fa-file-pdf text-red-400';
            case '.zip': case '.rar': case '.7z': return 'fas fa-file-archive text-yellow-400';
            case '.pt': case '.pth': return 'fas fa-brain text-cyan-400';
            default: return 'fas fa-file text-gray-400';
        }
    }

    getFileType(extension) {
        if (!extension) return '檔案';
        const ext = extension.toLowerCase();
        const types = {
            '.py': 'Python 檔案',
            '.js': 'JavaScript 檔案',
            '.html': 'HTML 檔案',
            '.css': 'CSS 檔案',
            '.json': 'JSON 檔案',
            '.txt': '文字檔案',
            '.md': 'Markdown 檔案',
            '.jpg': '圖片檔案',
            '.jpeg': '圖片檔案',
            '.png': '圖片檔案',
            '.gif': '圖片檔案',
            '.mp4': '影片檔案',
            '.avi': '影片檔案',
            '.mov': '影片檔案',
            '.pdf': 'PDF 檔案',
            '.zip': '壓縮檔案',
            '.rar': '壓縮檔案',
            '.7z': '壓縮檔案',
            '.pt': 'PyTorch 模型',
            '.pth': 'PyTorch 模型'
        };
        return types[ext] || '檔案';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    updateBreadcrumb(path) {
        const breadcrumb = document.getElementById('breadcrumb');
        if (!breadcrumb) return;
        
        if (!path) {
            breadcrumb.innerHTML = '<span class="text-cyan-400">根目錄</span>';
            return;
        }
        
        const parts = path.split(/[\\/]/).filter(part => part);
        let currentPath = '';
        let html = '<span class="breadcrumb-item text-cyan-400 cursor-pointer" data-path="">根目錄</span>';
        
        parts.forEach((part, index) => {
            currentPath += (currentPath ? '/' : '') + part;
            html += ' <span class="text-gray-400">/</span> ';
            html += `<span class="breadcrumb-item text-cyan-400 cursor-pointer" data-path="${currentPath}">${part}</span>`;
        });
        
        breadcrumb.innerHTML = html;
        
        // 添加點擊事件
        breadcrumb.querySelectorAll('.breadcrumb-item').forEach(item => {
            item.addEventListener('click', () => {
                const targetPath = item.dataset.path;
                this.loadFileList(targetPath);
            });
        });
    }

    openFolder(path) {
        this.loadFileList(path);
    }

    downloadFile(path) {
        const link = document.createElement('a');
        link.href = `/admin/api/files/download?path=${encodeURIComponent(path)}`;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    async deleteItem(path, name, isDirectory) {
        const itemType = isDirectory ? '資料夾' : '檔案';
        if (!confirm(`確定要刪除${itemType} "${name}" 嗎？此操作無法復原。`)) {
            return;
        }
        
        try {
            const response = await fetch(`/admin/api/files/delete?path=${encodeURIComponent(path)}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            if (result.success) {
                this.showFileSuccess(result.message);
                this.loadFileList(this.currentPath); // 重新載入當前目錄
            } else {
                this.showFileError(result.message);
            }
        } catch (error) {
            console.error('刪除失敗:', error);
            this.showFileError('刪除失敗: ' + error.message);
        }
    }

    setupFileManagerEvents() {
        // 重新整理按鈕
        const refreshBtn = document.getElementById('refresh-files');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadFileList(this.currentPath);
            });
        }
        
        // 新建資料夾按鈕
        const createFolderBtn = document.getElementById('create-folder-btn');
        if (createFolderBtn) {
            createFolderBtn.addEventListener('click', () => {
                this.showCreateFolderDialog();
            });
        }
        
        // 檔案上傳
        const fileUpload = document.getElementById('file-upload');
        if (fileUpload) {
            fileUpload.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.uploadFiles(e.target.files);
                }
            });
        }
    }

    showCreateFolderDialog() {
        const folderName = prompt('請輸入資料夾名稱:');
        if (folderName && folderName.trim()) {
            this.createFolder(folderName.trim());
        }
    }

    async createFolder(name) {
        try {
            const formData = new FormData();
            formData.append('name', name);
            formData.append('path', this.currentPath || '');
            
            const response = await fetch('/admin/api/files/create-folder', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            if (result.success) {
                this.showFileSuccess(result.message);
                this.loadFileList(this.currentPath); // 重新載入當前目錄
            } else {
                this.showFileError(result.message);
            }
        } catch (error) {
            console.error('建立資料夾失敗:', error);
            this.showFileError('建立資料夾失敗: ' + error.message);
        }
    }

    async uploadFiles(files) {
        for (const file of files) {
            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('path', this.currentPath || '');
                
                const response = await fetch('/admin/api/files/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                if (result.success) {
                    this.showFileSuccess(result.message);
                } else {
                    this.showFileError(result.message);
                }
            } catch (error) {
                console.error('上傳檔案失敗:', error);
                this.showFileError(`上傳 ${file.name} 失敗: ${error.message}`);
            }
        }
        
        // 重新載入檔案列表
        this.loadFileList(this.currentPath);
        
        // 清空檔案輸入
        const fileUpload = document.getElementById('file-upload');
        if (fileUpload) {
            fileUpload.value = '';
        }
    }

    showFileSuccess(message) {
        this.showNotification(message, 'success');
    }

    showFileError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification p-4 rounded-lg shadow-lg border-l-4 text-white max-w-sm transform transition-all duration-300 ease-in-out translate-x-full opacity-0`;
        
        switch (type) {
            case 'success':
                notification.classList.add('bg-green-800', 'border-green-400');
                break;
            case 'error':
                notification.classList.add('bg-red-800', 'border-red-400');
                break;
            case 'warning':
                notification.classList.add('bg-yellow-800', 'border-yellow-400');
                break;
            default:
                notification.classList.add('bg-blue-800', 'border-blue-400');
        }

        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        notification.innerHTML = `
            <div class="flex items-start">
                <i class="${icons[type]} mr-3 mt-1 text-lg"></i>
                <div class="flex-1">
                    <p class="text-sm font-medium">${message}</p>
                </div>
                <button class="ml-2 text-white hover:text-gray-300" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        container.appendChild(notification);

        // 動畫顯示
        setTimeout(() => {
            notification.classList.remove('translate-x-full', 'opacity-0');
        }, 100);

        // 自動移除 (5秒後)
        setTimeout(() => {
            notification.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, 5000);
    }

    async loadNetworkStatus() {
        try {
            const response = await fetch('/admin/api/network/status');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.updateNetworkInfo(data);
        } catch (error) {
            console.error('載入網絡狀態失敗:', error);
        }
    }

    updateNetworkInfo(data) {
        const statusElement = document.getElementById('network-status');
        if (statusElement) {
            statusElement.textContent = data.radmin_connected ? '已連接' : '未連接';
            statusElement.className = data.radmin_connected ? 'text-green-400' : 'text-red-400';
        }
    }

    async loadLogs() {
        try {
            const response = await fetch('/admin/api/logs/list?lines=50');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.renderLogs(data.logs || []);
        } catch (error) {
            console.error('載入日誌失敗:', error);
            this.renderLogs([]);
        }
    }

    renderLogs(logs) {
        const container = document.getElementById('logs-container');
        if (!container) return;

        container.innerHTML = '';
        
        if (!logs || logs.length === 0) {
            container.innerHTML = '<p class="text-gray-400">暫無日誌</p>';
            return;
        }

        logs.forEach(log => {
            const logDiv = document.createElement('div');
            logDiv.className = 'log-entry mb-4 p-3 bg-gray-800 rounded-md';
            logDiv.innerHTML = `
                <h4 class="text-cyan-100 font-bold mb-2">${log.file}</h4>
                <pre class="text-sm text-gray-300 whitespace-pre-wrap">${log.content}</pre>
            `;
            container.appendChild(logDiv);
        });
    }

    async uploadFile(file) {
        if (!file) return;

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/admin/api/files/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                console.log('檔案上傳成功');
                this.loadFileList(); // 重新載入檔案列表
                alert('檔案上傳成功！');
            } else {
                console.error('檔案上傳失敗');
                alert('檔案上傳失敗！');
            }
        } catch (error) {
            console.error('上傳檔案失敗:', error);
            alert('上傳檔案失敗：' + error.message);
        }
    }

    // ===================== API 測試功能 =====================

    setupApiTestEvents() {
        // API 端點選擇變更
        const apiEndpoint = document.getElementById('api-endpoint');
        if (apiEndpoint) {
            apiEndpoint.addEventListener('change', (e) => {
                const customInput = document.getElementById('custom-endpoint-input');
                if (e.target.value === 'custom') {
                    customInput.classList.remove('hidden');
                } else {
                    customInput.classList.add('hidden');
                }
            });
        }

        // API 測試按鈕
        const testApiBtn = document.getElementById('test-api-btn');
        if (testApiBtn) {
            testApiBtn.addEventListener('click', () => {
                this.executeApiTest();
            });
        }

        // 快速測試按鈕
        document.querySelectorAll('.quick-test-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const endpoint = btn.dataset.endpoint;
                this.quickApiTest(endpoint);
            });
        });
    }

    async checkApiStatus() {
        try {
            const response = await fetch('/api/v1/health');
            const statusElement = document.getElementById('api-status');
            if (statusElement) {
                if (response.ok) {
                    statusElement.textContent = '正常運行';
                    statusElement.className = 'text-green-300 text-sm';
                } else {
                    statusElement.textContent = '異常狀態';
                    statusElement.className = 'text-red-300 text-sm';
                }
            }
        } catch (error) {
            const statusElement = document.getElementById('api-status');
            if (statusElement) {
                statusElement.textContent = '連接失敗';
                statusElement.className = 'text-red-300 text-sm';
            }
        }
    }

    async executeApiTest() {
        const endpointSelect = document.getElementById('api-endpoint');
        const customEndpoint = document.getElementById('custom-endpoint');
        const httpMethod = document.getElementById('http-method');
        const requestBody = document.getElementById('request-body');
        const responseOutput = document.getElementById('response-output');
        const responseHeaders = document.getElementById('response-headers');
        const responseStatus = document.getElementById('response-status');

        let endpoint;
        if (endpointSelect.value === 'custom') {
            endpoint = customEndpoint.value;
        } else {
            endpoint = endpointSelect.value;
        }

        if (!endpoint) {
            alert('請選擇或輸入 API 端點');
            return;
        }

        // 更新 UI 狀態
        const testBtn = document.getElementById('test-api-btn');
        const originalText = testBtn.innerHTML;
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>測試中...';
        testBtn.disabled = true;

        responseOutput.textContent = '執行中...';
        responseStatus.textContent = '請求中';
        responseStatus.className = 'px-2 py-1 rounded text-xs font-medium bg-yellow-600 text-white';

        try {
            const options = {
                method: httpMethod.value,
                headers: {
                    'Content-Type': 'application/json',
                }
            };

            // 如果是 POST/PUT 請求且有請求體
            if (['POST', 'PUT'].includes(httpMethod.value) && requestBody.value.trim()) {
                try {
                    options.body = JSON.stringify(JSON.parse(requestBody.value));
                } catch (e) {
                    throw new Error('請求體 JSON 格式錯誤');
                }
            }

            const startTime = Date.now();
            const response = await fetch(endpoint, options);
            const endTime = Date.now();
            const duration = endTime - startTime;

            // 處理回應狀態
            const statusClass = response.ok ? 'bg-green-600' : 'bg-red-600';
            responseStatus.textContent = `${response.status} ${response.statusText} (${duration}ms)`;
            responseStatus.className = `px-2 py-1 rounded text-xs font-medium ${statusClass} text-white`;

            // 顯示回應標頭
            const headers = {};
            for (let [key, value] of response.headers.entries()) {
                headers[key] = value;
            }
            responseHeaders.textContent = JSON.stringify(headers, null, 2);

            // 處理回應內容
            const contentType = response.headers.get('content-type');
            let responseData;

            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json();
                responseOutput.textContent = JSON.stringify(responseData, null, 2);
            } else {
                responseData = await response.text();
                responseOutput.textContent = responseData;
            }

        } catch (error) {
            responseStatus.textContent = '錯誤';
            responseStatus.className = 'px-2 py-1 rounded text-xs font-medium bg-red-600 text-white';
            responseOutput.textContent = `錯誤: ${error.message}`;
            responseHeaders.textContent = '無法獲取標頭';
        }

        // 恢復按鈕狀態
        testBtn.innerHTML = originalText;
        testBtn.disabled = false;
    }

    async quickApiTest(endpoint) {
        // 設置表單值
        const endpointSelect = document.getElementById('api-endpoint');
        const customEndpoint = document.getElementById('custom-endpoint');
        const customInput = document.getElementById('custom-endpoint-input');

        // 檢查是否為預設端點
        const option = Array.from(endpointSelect.options).find(opt => opt.value === endpoint);
        if (option) {
            endpointSelect.value = endpoint;
            customInput.classList.add('hidden');
        } else {
            endpointSelect.value = 'custom';
            customEndpoint.value = endpoint;
            customInput.classList.remove('hidden');
        }

        // 設置為 GET 請求
        const httpMethod = document.getElementById('http-method');
        httpMethod.value = 'GET';

        // 清空請求體
        const requestBody = document.getElementById('request-body');
        requestBody.value = '';

        // 切換到 API 文件面板
        this.showSection('api-docs');
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        document.querySelector('a[href="#api-docs"]').classList.add('active');

        // 執行測試
        setTimeout(() => {
            this.executeApiTest();
        }, 100);
    }

    // ==================== 攝影機管理功能 ====================
    
    setupCameraManagerEvents() {
        // 攝影機類型切換
        const cameraType = document.getElementById('camera-type');
        if (cameraType) {
            cameraType.addEventListener('change', (e) => {
                this.updateCameraConfigUI(e.target.value);
            });
        }

        // 掃描攝影機
        const scanCamerasBtn = document.getElementById('scan-cameras');
        if (scanCamerasBtn) {
            scanCamerasBtn.addEventListener('click', () => {
                this.scanCameras();
            });
        }

        // 新增攝影機
        const addCameraBtn = document.getElementById('add-camera');
        if (addCameraBtn) {
            addCameraBtn.addEventListener('click', () => {
                this.clearCameraForm();
            });
        }

        // 攝影機配置表單
        const cameraForm = document.getElementById('camera-config-form');
        if (cameraForm) {
            cameraForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveCameraConfig();
            });
        }

        // 測試攝影機連接
        const testCameraBtn = document.getElementById('test-camera');
        if (testCameraBtn) {
            testCameraBtn.addEventListener('click', () => {
                this.testCameraConnection();
            });
        }

        // 開始預覽
        const startPreviewBtn = document.getElementById('start-preview');
        if (startPreviewBtn) {
            startPreviewBtn.addEventListener('click', () => {
                this.startCameraPreview();
            });
        }

        // 停止預覽
        const stopPreviewBtn = document.getElementById('stop-preview');
        if (stopPreviewBtn) {
            stopPreviewBtn.addEventListener('click', () => {
                this.stopCameraPreview();
            });
        }

        // 截圖
        const captureFrameBtn = document.getElementById('capture-frame');
        if (captureFrameBtn) {
            captureFrameBtn.addEventListener('click', () => {
                this.captureFrame();
            });
        }

        // 瀏覽影片檔案
        const browseVideoBtn = document.getElementById('browse-video-file');
        if (browseVideoBtn) {
            browseVideoBtn.addEventListener('click', () => {
                this.browseVideoFile();
            });
        }

        // 初始化攝影機類型配置
        this.updateCameraConfigUI('usb');
        this.loadCameraList();
    }

    updateCameraConfigUI(type) {
        const usbConfig = document.getElementById('usb-config');
        const networkConfig = document.getElementById('network-config');
        const fileConfig = document.getElementById('file-config');

        // 隱藏所有配置區塊
        [usbConfig, networkConfig, fileConfig].forEach(element => {
            if (element) element.classList.add('hidden');
        });

        // 顯示相應的配置區塊
        switch (type) {
            case 'usb':
                if (usbConfig) usbConfig.classList.remove('hidden');
                break;
            case 'rtsp':
            case 'ip':
                if (networkConfig) networkConfig.classList.remove('hidden');
                break;
            case 'file':
                if (fileConfig) fileConfig.classList.remove('hidden');
                break;
        }
    }

    async scanCameras() {
        const scanBtn = document.getElementById('scan-cameras');
        const originalText = scanBtn.innerHTML;
        
        try {
            scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>掃描中...';
            scanBtn.disabled = true;

            console.log('開始掃描攝影機...');
            
            const response = await fetch('/admin/api/cameras/scan', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const data = await response.json();
                console.log('掃描結果:', data);
                
                // 更新 USB 設備下拉選單
                this.updateAvailableCameras(data.cameras);
                
                // 創建臨時攝影機狀態卡片顯示掃描結果
                this.displayScanResults(data.cameras);
                
                // 成功通知已在 updateAvailableCameras 中處理
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || '掃描失敗');
            }
        } catch (error) {
            console.error('掃描攝影機失敗:', error);
            this.showNotification('掃描攝影機失敗: ' + error.message, 'error');
        } finally {
            scanBtn.innerHTML = originalText;
            scanBtn.disabled = false;
        }
    }

    displayScanResults(cameras) {
        const cardsContainer = document.getElementById('camera-status-cards');
        if (!cardsContainer) return;

        // 清空現有卡片
        cardsContainer.innerHTML = '';

        if (cameras.length === 0) {
            cardsContainer.innerHTML = `
                <div class="col-span-full text-center text-gray-400 py-8">
                    <i class="fas fa-video-slash text-4xl mb-2"></i>
                    <p>未找到可用攝影機</p>
                    <p class="text-sm mt-2">請檢查設備連接和權限設定</p>
                </div>
            `;
            return;
        }

        // 顯示掃描到的攝影機
        cameras.forEach(camera => {
            const card = document.createElement('div');
            card.className = 'tech-card p-4 cursor-pointer hover:border-cyan-400/50 transition-all duration-300';
            card.onclick = () => this.selectScannedCamera(camera);
            
            card.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <h4 class="text-cyan-100 font-medium">${camera.name}</h4>
                    <i class="fas fa-video text-green-400"></i>
                </div>
                <div class="text-sm text-cyan-300">${camera.type} (索引 ${camera.index})</div>
                <div class="text-xs text-gray-400 mt-1">${camera.width}x${camera.height}@${camera.fps}fps</div>
                <div class="text-xs text-cyan-300 mt-1">後端: ${camera.backend_name || 'Default'}</div>
                <div class="flex items-center justify-between mt-3">
                    <span class="text-xs text-green-400">可用</span>
                    <button class="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors" 
                            onclick="event.stopPropagation(); dashboard.useScannedCamera(${camera.index}, '${camera.name}')">
                        使用此攝影機
                    </button>
                </div>
            `;
            
            cardsContainer.appendChild(card);
        });
    }

    selectScannedCamera(camera) {
        console.log('選擇攝影機:', camera);
        
        // 自動填入攝影機配置
        document.getElementById('camera-name').value = camera.name;
        document.getElementById('camera-type').value = 'usb';
        document.getElementById('usb-device').value = camera.index;
        document.getElementById('camera-width').value = camera.width;
        document.getElementById('camera-height').value = camera.height;
        document.getElementById('camera-fps').value = camera.fps;
        
        // 更新配置 UI
        this.updateCameraConfigUI('usb');
        
        this.showNotification(`已選擇攝影機: ${camera.name}`, 'info');
    }

    useScannedCamera(cameraIndex, cameraName) {
        // 快速配置並測試攝影機
        const formData = {
            name: cameraName,
            type: 'usb',
            source: cameraIndex,
            width: 640,
            height: 480,
            fps: 30,
            auto_start: false
        };
        
        // 填入表單
        document.getElementById('camera-name').value = formData.name;
        document.getElementById('camera-type').value = formData.type;
        document.getElementById('usb-device').value = formData.source;
        document.getElementById('camera-width').value = formData.width;
        document.getElementById('camera-height').value = formData.height;
        document.getElementById('camera-fps').value = formData.fps;
        
        this.updateCameraConfigUI('usb');
        
        // 自動測試連接
        this.testCameraConnection();
    }

    updateAvailableCameras(cameras) {
        const usbDevice = document.getElementById('usb-device');
        if (usbDevice) {
            usbDevice.innerHTML = '';
            
            // 添加默認選項
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = '請選擇攝影機...';
            usbDevice.appendChild(defaultOption);
            
            // 添加掃描到的攝影機
            cameras.forEach((camera) => {
                const option = document.createElement('option');
                option.value = camera.index;
                option.textContent = camera.name || `攝影機 ${camera.index}`;
                usbDevice.appendChild(option);
            });
            
            // 顯示掃描結果通知
            if (cameras.length > 0) {
                this.showNotification(`掃描完成！找到 ${cameras.length} 個可用攝影機`, 'success');
            } else {
                this.showNotification('未找到可用攝影機，請檢查設備連接和權限設定', 'warning');
            }
        }
    }

    async saveCameraConfig() {
        const formData = this.getCameraFormData();
        
        try {
            const response = await fetch('/admin/api/cameras', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification('攝影機配置已保存', 'success');
                this.loadCameraList();
                this.clearCameraForm();
            } else {
                const error = await response.json();
                throw new Error(error.detail || '保存失敗');
            }
        } catch (error) {
            console.error('保存攝影機配置失敗:', error);
            this.showNotification('保存失敗: ' + error.message, 'error');
        }
    }

    getCameraFormData() {
        const type = document.getElementById('camera-type').value;
        const formData = {
            name: document.getElementById('camera-name').value,
            type: type,
            width: parseInt(document.getElementById('camera-width').value),
            height: parseInt(document.getElementById('camera-height').value),
            fps: parseInt(document.getElementById('camera-fps').value),
            auto_start: document.getElementById('auto-start').checked
        };

        switch (type) {
            case 'usb':
                formData.source = parseInt(document.getElementById('usb-device').value);
                break;
            case 'rtsp':
            case 'ip':
                formData.source = document.getElementById('camera-url').value;
                formData.username = document.getElementById('camera-username').value;
                formData.password = document.getElementById('camera-password').value;
                break;
            case 'file':
                formData.source = document.getElementById('video-file-path').value;
                break;
        }

        return formData;
    }

    async testCameraConnection() {
        const formData = this.getCameraFormData();
        const testBtn = document.getElementById('test-camera');
        const originalText = testBtn.innerHTML;
        
        try {
            testBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>測試中...';
            testBtn.disabled = true;

            const response = await fetch('/admin/api/cameras/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.showNotification('攝影機連接測試成功', 'success');
                    this.updateCameraStatus('已連接');
                } else {
                    throw new Error(data.message || '連接失敗');
                }
            } else {
                throw new Error('測試失敗');
            }
        } catch (error) {
            console.error('測試攝影機連接失敗:', error);
            this.showNotification('連接測試失敗: ' + error.message, 'error');
            this.updateCameraStatus('連接失敗');
        } finally {
            testBtn.innerHTML = originalText;
            testBtn.disabled = false;
        }
    }

    async startCameraPreview() {
        if (!this.currentCamera) {
            this.showNotification('請先選擇或配置攝影機', 'warning');
            return;
        }

        try {
            const response = await fetch(`/admin/api/cameras/${this.currentCamera.id}/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                this.showNotification('攝影機預覽已啟動', 'success');
                this.startPreviewPolling();
                this.updateCameraStatus('預覽中');
            } else {
                throw new Error('啟動預覽失敗');
            }
        } catch (error) {
            console.error('啟動攝影機預覽失敗:', error);
            this.showNotification('啟動預覽失敗: ' + error.message, 'error');
        }
    }

    async stopCameraPreview() {
        if (!this.currentCamera) {
            return;
        }

        try {
            const response = await fetch(`/admin/api/cameras/${this.currentCamera.id}/stop`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                this.showNotification('攝影機預覽已停止', 'success');
                this.stopPreviewPolling();
                this.updateCameraStatus('已停止');
            } else {
                throw new Error('停止預覽失敗');
            }
        } catch (error) {
            console.error('停止攝影機預覽失敗:', error);
            this.showNotification('停止預覽失敗: ' + error.message, 'error');
        }
    }

    startPreviewPolling() {
        this.stopPreviewPolling(); // 確保沒有重複的輪詢
        
        this.previewInterval = setInterval(async () => {
            try {
                const response = await fetch(`/admin/api/cameras/${this.currentCamera.id}/frame`);
                if (response.ok) {
                    const blob = await response.blob();
                    const imageUrl = URL.createObjectURL(blob);
                    
                    const previewVideo = document.getElementById('preview-video');
                    const previewCanvas = document.getElementById('preview-canvas');
                    
                    if (previewCanvas) {
                        const ctx = previewCanvas.getContext('2d');
                        const img = new Image();
                        img.onload = () => {
                            previewCanvas.width = img.width;
                            previewCanvas.height = img.height;
                            ctx.drawImage(img, 0, 0);
                            URL.revokeObjectURL(imageUrl);
                        };
                        img.src = imageUrl;
                        
                        previewCanvas.classList.remove('hidden');
                        if (previewVideo) previewVideo.classList.add('hidden');
                    }
                }
            } catch (error) {
                console.error('獲取攝影機幀失敗:', error);
            }
        }, 100); // 100ms 間隔，約 10 FPS
    }

    stopPreviewPolling() {
        if (this.previewInterval) {
            clearInterval(this.previewInterval);
            this.previewInterval = null;
        }
        
        const previewVideo = document.getElementById('preview-video');
        const previewCanvas = document.getElementById('preview-canvas');
        
        if (previewVideo) previewVideo.classList.add('hidden');
        if (previewCanvas) previewCanvas.classList.add('hidden');
    }

    async captureFrame() {
        if (!this.currentCamera) {
            this.showNotification('請先啟動攝影機預覽', 'warning');
            return;
        }

        try {
            const response = await fetch(`/admin/api/cameras/${this.currentCamera.id}/capture`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(`截圖已保存: ${data.filename}`, 'success');
            } else {
                throw new Error('截圖失敗');
            }
        } catch (error) {
            console.error('截圖失敗:', error);
            this.showNotification('截圖失敗: ' + error.message, 'error');
        }
    }

    browseVideoFile() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'video/*,.mp4,.avi,.mov,.mkv,.wmv,.flv,.webm';
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (file) {
                // 顯示檔案選擇狀態
                const pathInput = document.getElementById('video-file-path');
                pathInput.value = `正在上傳: ${file.name}`;
                pathInput.disabled = true;
                
                try {
                    // 創建 FormData 上傳檔案
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    // 上傳檔案
                    const response = await fetch('/api/v1/frontend/data-sources/upload/video', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        pathInput.value = result.file_path;
                        pathInput.disabled = false;
                        this.showNotification(`影片檔案 ${file.name} 上傳成功`, 'success');
                    } else {
                        const error = await response.json();
                        throw new Error(error.detail || '上傳失敗');
                    }
                } catch (error) {
                    console.error('影片檔案上傳失敗:', error);
                    pathInput.value = '';
                    pathInput.disabled = false;
                    this.showNotification(`影片檔案上傳失敗: ${error.message}`, 'error');
                }
            }
        };
        input.click();
    }

    async loadCameraList() {
        try {
            const response = await fetch('/admin/api/cameras');
            if (response.ok) {
                const data = await response.json();
                this.cameraList = data.cameras;
                this.renderCameraList();
                this.renderCameraStatusCards();
            }
        } catch (error) {
            console.error('載入攝影機列表失敗:', error);
        }
    }

    renderCameraList() {
        const cameraListElement = document.getElementById('camera-list');
        if (!cameraListElement) return;

        cameraListElement.innerHTML = '';

        this.cameraList.forEach(camera => {
            const row = document.createElement('tr');
            row.className = 'border-b border-gray-700 hover:bg-gray-800/50';
            
            const statusClass = camera.status === 'active' ? 'text-green-400' : 
                               camera.status === 'error' ? 'text-red-400' : 'text-gray-400';
            
            row.innerHTML = `
                <td class="py-3 text-cyan-100">${camera.name}</td>
                <td class="py-3 text-cyan-200">${this.getCameraTypeDisplay(camera.type)}</td>
                <td class="py-3 text-cyan-200 truncate max-w-xs">${camera.source}</td>
                <td class="py-3">
                    <span class="px-2 py-1 rounded text-xs ${statusClass}">
                        ${this.getCameraStatusDisplay(camera.status)}
                    </span>
                </td>
                <td class="py-3">
                    <div class="flex space-x-2">
                        <button onclick="dashboard.editCamera('${camera.id}')" class="text-blue-400 hover:text-blue-300">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="dashboard.selectCamera('${camera.id}')" class="text-green-400 hover:text-green-300">
                            <i class="fas fa-play"></i>
                        </button>
                        <button onclick="dashboard.deleteCamera('${camera.id}')" class="text-red-400 hover:text-red-300">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            
            cameraListElement.appendChild(row);
        });
    }

    renderCameraStatusCards() {
        const cardsContainer = document.getElementById('camera-status-cards');
        if (!cardsContainer) return;

        cardsContainer.innerHTML = '';

        this.cameraList.forEach(camera => {
            const card = document.createElement('div');
            card.className = 'tech-card p-4 cursor-pointer hover:border-cyan-400/50 transition-all duration-300';
            card.onclick = () => this.selectCamera(camera.id);
            
            const statusColor = camera.status === 'active' ? 'text-green-400' : 
                               camera.status === 'error' ? 'text-red-400' : 'text-gray-400';
            
            card.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <h4 class="text-cyan-100 font-medium">${camera.name}</h4>
                    <i class="fas fa-video ${statusColor}"></i>
                </div>
                <div class="text-sm text-cyan-300">${this.getCameraTypeDisplay(camera.type)}</div>
                <div class="text-xs text-gray-400 mt-1 truncate">${camera.source}</div>
                <div class="flex items-center justify-between mt-3">
                    <span class="text-xs ${statusColor}">${this.getCameraStatusDisplay(camera.status)}</span>
                    ${camera.status === 'active' ? '<div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>' : ''}
                </div>
            `;
            
            cardsContainer.appendChild(card);
        });

        if (this.cameraList.length === 0) {
            cardsContainer.innerHTML = `
                <div class="col-span-full text-center text-gray-400 py-8">
                    <i class="fas fa-video-slash text-4xl mb-2"></i>
                    <p>尚未配置任何攝影機</p>
                </div>
            `;
        }
    }

    getCameraTypeDisplay(type) {
        const types = {
            'usb': 'USB 攝影機',
            'rtsp': 'RTSP 串流',
            'ip': 'IP 攝影機',
            'file': '影片檔案'
        };
        return types[type] || type;
    }

    getCameraStatusDisplay(status) {
        const statuses = {
            'active': '運行中',
            'inactive': '已停止',
            'error': '錯誤',
            'connecting': '連接中'
        };
        return statuses[status] || status;
    }

    selectCamera(cameraId) {
        this.currentCamera = this.cameraList.find(c => c.id === cameraId);
        if (this.currentCamera) {
            this.loadCameraToForm(this.currentCamera);
            this.showNotification(`已選擇攝影機: ${this.currentCamera.name}`, 'info');
        }
    }

    loadCameraToForm(camera) {
        document.getElementById('camera-name').value = camera.name;
        document.getElementById('camera-type').value = camera.type;
        document.getElementById('camera-width').value = camera.width;
        document.getElementById('camera-height').value = camera.height;
        document.getElementById('camera-fps').value = camera.fps;
        document.getElementById('auto-start').checked = camera.auto_start;

        this.updateCameraConfigUI(camera.type);

        switch (camera.type) {
            case 'usb':
                document.getElementById('usb-device').value = camera.source;
                break;
            case 'rtsp':
            case 'ip':
                document.getElementById('camera-url').value = camera.source;
                document.getElementById('camera-username').value = camera.username || '';
                document.getElementById('camera-password').value = camera.password || '';
                break;
            case 'file':
                document.getElementById('video-file-path').value = camera.source;
                break;
        }
    }

    async editCamera(cameraId) {
        const camera = this.cameraList.find(c => c.id === cameraId);
        if (camera) {
            this.currentCamera = camera;
            this.loadCameraToForm(camera);
            // 切換到攝影機管理面板
            this.showSection('camera-manager');
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            document.querySelector('a[href="#camera-manager"]').classList.add('active');
        }
    }

    async deleteCamera(cameraId) {
        if (!confirm('確定要刪除這個攝影機配置嗎？')) {
            return;
        }

        try {
            const response = await fetch(`/admin/api/cameras/${cameraId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                this.showNotification('攝影機配置已刪除', 'success');
                this.loadCameraList();
                if (this.currentCamera && this.currentCamera.id === cameraId) {
                    this.currentCamera = null;
                    this.clearCameraForm();
                }
            } else {
                throw new Error('刪除失敗');
            }
        } catch (error) {
            console.error('刪除攝影機失敗:', error);
            this.showNotification('刪除失敗: ' + error.message, 'error');
        }
    }

    clearCameraForm() {
        document.getElementById('camera-config-form').reset();
        document.getElementById('camera-width').value = '640';
        document.getElementById('camera-height').value = '480';
        document.getElementById('camera-fps').value = '30';
        this.updateCameraConfigUI('usb');
        this.currentCamera = null;
    }

    updateCameraStatus(status) {
        const statusElement = document.getElementById('camera-status');
        if (statusElement) {
            statusElement.textContent = status;
        }
    }
}

// =============================================================================
// 資料庫管理功能
// =============================================================================

// 全域變數
let currentPage = 1;
let currentTable = 'analysis_records';
let totalPages = 1;
let isLoading = false;
let searchSuggestions = {};
let searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');

// 重新整理資料庫統計
async function refreshDatabaseStats() {
    try {
        console.log('刷新資料庫統計...');
        
        const response = await fetch('/admin/api/database/stats');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const stats = await response.json();
        
        // 更新統計卡片
        document.getElementById('analysisRecordCount').textContent = stats.analysis_records.toLocaleString();
        document.getElementById('detectionResultCount').textContent = stats.detection_results.toLocaleString();
        document.getElementById('behaviorEventCount').textContent = stats.behavior_events.toLocaleString();
        
        console.log('資料庫統計更新完成:', stats);
        
    } catch (error) {
        console.error('重新整理資料庫統計失敗:', error);
        showAlert('重新整理資料庫統計失敗: ' + error.message, 'error');
    }
}

// 查詢資料表
async function queryTable() {
    if (isLoading) return;
    
    try {
        isLoading = true;
        showLoading(true);
        
        currentTable = document.getElementById('tableSelect').value;
        const limit = parseInt(document.getElementById('limitSelect').value);
        const sortBy = document.getElementById('sortSelect').value;
        const order = document.getElementById('orderSelect').value;
        const search = document.getElementById('searchInput').value.trim();
        
        const offset = (currentPage - 1) * limit;
        
        let url = `/admin/api/database/query/${currentTable}?limit=${limit}&offset=${offset}&order_by=${sortBy}&order_direction=${order}`;
        if (search) {
            url += `&search=${encodeURIComponent(search)}`;
        }
        
        console.log('查詢資料表:', url);
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // 顯示資料表
        displayTableData(result);
        
        // 更新分頁資訊
        updatePaginationInfo(result);
        
        console.log('資料表查詢完成:', result);
        
    } catch (error) {
        console.error('查詢資料表失敗:', error);
        showAlert('查詢資料表失敗: ' + error.message, 'error');
        
        // 顯示錯誤狀態
        const container = document.getElementById('dataTableContainer');
        container.innerHTML = `
            <div class="text-center py-8 text-red-400">
                <i class="fas fa-exclamation-triangle text-4xl mb-4"></i>
                <div>查詢失敗: ${error.message}</div>
            </div>
        `;
    } finally {
        isLoading = false;
        showLoading(false);
    }
}

// 載入搜尋建議
async function loadSearchSuggestions(tableName) {
    try {
        const response = await fetch(`/admin/api/database/search-suggestions/${tableName}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        searchSuggestions = result.suggestions;
        
        // 更新搜尋建議界面
        updateSearchSuggestionsUI();
        updateQuickFilters();
        updateSearchHistory();
        
    } catch (error) {
        console.error('載入搜尋建議失敗:', error);
        searchSuggestions = { common_values: [], status_options: [], type_options: [] };
    }
}

// 更新搜尋建議界面
function updateSearchSuggestionsUI() {
    const suggestionsList = document.getElementById('suggestionsList');
    if (!suggestionsList) return;
    
    let html = '';
    
    // 常見值
    if (searchSuggestions.common_values && searchSuggestions.common_values.length > 0) {
        html += '<div class="px-3 py-1 text-xs text-gray-400 font-medium">常見項目</div>';
        searchSuggestions.common_values.forEach(value => {
            html += `
                <div class="px-3 py-2 hover:bg-gray-700 cursor-pointer text-cyan-100 text-sm suggestion-item" 
                     data-value="${value}">
                    <i class="fas fa-file-alt text-cyan-400 mr-2"></i>${value}
                </div>
            `;
        });
    }
    
    // 類型選項
    if (searchSuggestions.type_options && searchSuggestions.type_options.length > 0) {
        html += '<div class="px-3 py-1 text-xs text-gray-400 font-medium border-t border-gray-700 mt-2 pt-2">類型</div>';
        searchSuggestions.type_options.forEach(type => {
            html += `
                <div class="px-3 py-2 hover:bg-gray-700 cursor-pointer text-cyan-100 text-sm suggestion-item" 
                     data-value="${type}">
                    <i class="fas fa-tag text-green-400 mr-2"></i>${type}
                </div>
            `;
        });
    }
    
    // 狀態選項
    if (searchSuggestions.status_options && searchSuggestions.status_options.length > 0) {
        html += '<div class="px-3 py-1 text-xs text-gray-400 font-medium border-t border-gray-700 mt-2 pt-2">狀態/區域</div>';
        searchSuggestions.status_options.forEach(status => {
            html += `
                <div class="px-3 py-2 hover:bg-gray-700 cursor-pointer text-cyan-100 text-sm suggestion-item" 
                     data-value="${status}">
                    <i class="fas fa-circle text-blue-400 mr-2"></i>${status}
                </div>
            `;
        });
    }
    
    if (html === '') {
        html = '<div class="px-3 py-2 text-gray-400 text-sm">暫無建議</div>';
    }
    
    suggestionsList.innerHTML = html;
    
    // 綁定點擊事件
    suggestionsList.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
            const value = item.getAttribute('data-value');
            document.getElementById('searchInput').value = value;
            document.getElementById('searchSuggestions').classList.add('hidden');
            // 自動執行搜尋
            searchTable();
        });
    });
}

// 更新快捷篩選按鈕
function updateQuickFilters() {
    const quickFilters = document.getElementById('quickFilters');
    if (!quickFilters) return;
    
    let html = '';
    
    // 根據不同資料表提供不同的快捷篩選
    const filters = getQuickFiltersForTable(currentTable);
    
    filters.forEach(filter => {
        html += `
            <button class="quick-filter-btn px-3 py-1 bg-gray-700 hover:bg-cyan-600 text-gray-300 hover:text-white rounded-md text-xs transition-all duration-300"
                    data-value="${filter.value}" data-description="${filter.description}" title="${filter.description}">
                <i class="${filter.icon} mr-1"></i>${filter.label}
            </button>
        `;
    });
    
    quickFilters.innerHTML = html;
    
    // 綁定點擊事件
    quickFilters.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const value = btn.getAttribute('data-value');
            const description = btn.getAttribute('data-description');
            
            document.getElementById('searchInput').value = value;
            // 顯示提示
            showAlert(`已套用篩選: ${description}`, 'info');
            // 自動執行搜尋
            searchTable();
        });
    });
}

// 獲取指定資料表的快捷篩選選項
function getQuickFiltersForTable(tableName) {
    const filters = {
        'analysis_records': [
            { label: '處理中', value: 'processing', icon: 'fas fa-spinner', description: '顯示正在處理的分析任務' },
            { label: '已完成', value: 'completed', icon: 'fas fa-check-circle', description: '顯示已完成的分析任務' },
            { label: '失敗', value: 'failed', icon: 'fas fa-times-circle', description: '顯示處理失敗的分析任務' },
            { label: '影片分析', value: 'detection', icon: 'fas fa-video', description: '顯示影片檢測分析' }
        ],
        'detection_results': [
            { label: '人物', value: 'person', icon: 'fas fa-user', description: '顯示人物檢測結果' },
            { label: '人', value: '人', icon: 'fas fa-user', description: '顯示人物檢測結果（中文）' },
            { label: '車輛', value: 'car', icon: 'fas fa-car', description: '顯示車輛檢測結果' },
            { label: '高信心度', value: '0.8', icon: 'fas fa-thumbs-up', description: '顯示信心度大於80%的檢測' }
        ],
        'behavior_events': [
            { label: '高風險', value: 'high', icon: 'fas fa-exclamation-triangle', description: '顯示高風險事件' },
            { label: '中風險', value: 'medium', icon: 'fas fa-exclamation-circle', description: '顯示中風險事件' },
            { label: '低風險', value: 'low', icon: 'fas fa-info-circle', description: '顯示低風險事件' },
            { label: '進入事件', value: 'enter', icon: 'fas fa-sign-in-alt', description: '顯示進入相關事件' }
        ]
    };
    
    return filters[tableName] || [];
}

// 更新搜尋歷史
function updateSearchHistory() {
    const searchHistoryDiv = document.getElementById('searchHistory');
    const historyList = document.getElementById('historyList');
    
    if (!historyList) return;
    
    if (searchHistory.length === 0) {
        searchHistoryDiv.classList.add('hidden');
        return;
    }
    
    searchHistoryDiv.classList.remove('hidden');
    
    let html = '';
    // 顯示最近的5個搜尋記錄
    searchHistory.slice(0, 5).forEach(search => {
        html += `
            <button class="history-item px-3 py-1 bg-gray-700 hover:bg-purple-600 text-gray-300 hover:text-white rounded-md text-xs transition-all duration-300"
                    data-value="${search}">
                <i class="fas fa-history mr-1"></i>${search}
            </button>
        `;
    });
    
    historyList.innerHTML = html;
    
    // 綁定點擊事件
    historyList.querySelectorAll('.history-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const value = btn.getAttribute('data-value');
            document.getElementById('searchInput').value = value;
            searchTable();
        });
    });
}

// 保存搜尋歷史
function saveSearchHistory(searchTerm) {
    if (!searchTerm || searchTerm.trim() === '') return;
    
    // 移除重複項目
    searchHistory = searchHistory.filter(item => item !== searchTerm);
    // 添加到開頭
    searchHistory.unshift(searchTerm);
    // 只保留最近的10個搜尋
    searchHistory = searchHistory.slice(0, 10);
    
    // 保存到本地存儲
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
    
    // 更新界面
    updateSearchHistory();
}

// 顯示資料表資料
function displayTableData(result) {
    const container = document.getElementById('dataTableContainer');
    
    if (!result.data || result.data.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-gray-400">
                <i class="fas fa-inbox text-4xl mb-4"></i>
                <div>沒有找到資料</div>
            </div>
        `;
        return;
    }
    
    // 構建表格 HTML
    let tableHtml = `
        <table class="w-full text-sm text-left text-gray-300">
            <thead class="text-xs text-gray-400 uppercase bg-gray-800">
                <tr>
    `;
    
    // 表頭
    result.columns.forEach(column => {
        const displayName = getColumnDisplayName(column);
        tableHtml += `<th scope="col" class="px-6 py-3">${displayName}</th>`;
    });
    
    // 新增操作欄
    tableHtml += `<th scope="col" class="px-6 py-3">操作</th>`;
    
    tableHtml += `
                </tr>
            </thead>
            <tbody>
    `;
    
    // 資料行
    result.data.forEach((row, index) => {
        const bgClass = index % 2 === 0 ? 'bg-gray-900' : 'bg-gray-800';
        tableHtml += `<tr class="${bgClass} border-b border-gray-700 hover:bg-gray-700 transition-colors">`;
        
        result.columns.forEach(column => {
            let value = row[column];
            
            // 格式化不同類型的值
            if (value === null || value === undefined || value === '') {
                value = '<span class="text-gray-500">-</span>';
            } else if (column.includes('created_at') || column.includes('updated_at') || column.includes('timestamp')) {
                try {
                    const date = new Date(value);
                    value = date.toLocaleString('zh-TW');
                } catch (e) {
                    // 保持原值
                }
            } else if (typeof value === 'number' && column.includes('confidence')) {
                value = (value * 100).toFixed(2) + '%';
            } else if (typeof value === 'string' && value.length > 50) {
                value = `<span title="${value}">${value.substring(0, 50)}...</span>`;
            }
            
            tableHtml += `<td class="px-6 py-4">${value}</td>`;
        });
        
        // 新增操作按鈕
        tableHtml += `
            <td class="px-6 py-4">
                <button onclick="showItemDetails('${result.table_name}', ${row.id})" 
                        class="px-3 py-1 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-md hover:from-cyan-700 hover:to-blue-700 transition-all duration-300 text-xs">
                    <i class="fas fa-info-circle mr-1"></i>查看詳情
                </button>
            </td>
        `;
        
        tableHtml += '</tr>';
    });
    
    tableHtml += `
            </tbody>
        </table>
    `;
    
    container.innerHTML = tableHtml;
}

// 獲取欄位顯示名稱
function getColumnDisplayName(column) {
    const columnNames = {
        'id': 'ID',
        'created_at': '建立時間',
        'updated_at': '更新時間',
        'video_name': '影片名稱',
        'video_path': '影片路徑',
        'status': '狀態',
        'analysis_type': '分析類型',
        'duration': '影片長度',
        'fps': '幀率',
        'total_frames': '總幀數',
        'total_detections': '檢測總數',
        'object_type': '物件類型',
        'object_chinese': '物件中文',
        'confidence': '信心度',
        'bbox_x1': 'X1',
        'bbox_y1': 'Y1',
        'bbox_x2': 'X2',
        'bbox_y2': 'Y2',
        'center_x': '中心X',
        'center_y': '中心Y',
        'width': '寬度',
        'height': '高度',
        'area': '面積',
        'speed': '速度',
        'direction': '方向',
        'zone': '區域',
        'event_type': '事件類型',
        'timestamp': '時間戳'
    };
    
    return columnNames[column] || column;
}

// 更新分頁資訊
function updatePaginationInfo(result) {
    const paginationContainer = document.getElementById('paginationContainer');
    const pageInfo = document.getElementById('pageInfo');
    const totalCount = document.getElementById('totalCount');
    const currentPageSpan = document.getElementById('currentPageSpan');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const resultInfo = document.getElementById('resultInfo');
    
    const limit = parseInt(document.getElementById('limitSelect').value);
    const startIndex = (result.current_page - 1) * limit + 1;
    const endIndex = Math.min(result.current_page * limit, result.total_count);
    
    totalPages = Math.ceil(result.total_count / limit);
    currentPage = result.current_page;
    
    // 更新資訊
    pageInfo.textContent = `${startIndex}-${endIndex}`;
    totalCount.textContent = result.total_count.toLocaleString();
    currentPageSpan.textContent = currentPage;
    resultInfo.textContent = `顯示 ${result.data.length} 筆記錄，共 ${result.total_count.toLocaleString()} 筆`;
    
    // 更新按鈕狀態
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    
    // 顯示分頁控制
    if (result.total_count > 0) {
        paginationContainer.classList.remove('hidden');
    } else {
        paginationContainer.classList.add('hidden');
    }
}

// 上一頁
function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        queryTable();
    }
}

// 下一頁
function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        queryTable();
    }
}

// 搜尋資料表
function searchTable() {
    const searchTerm = document.getElementById('searchInput').value.trim();
    
    // 保存搜尋歷史
    if (searchTerm) {
        saveSearchHistory(searchTerm);
    }
    
    currentPage = 1; // 重置到第一頁
    queryTable();
}

// 清除搜尋
function clearSearch() {
    document.getElementById('searchInput').value = '';
    document.getElementById('searchSuggestions').classList.add('hidden');
    currentPage = 1;
    queryTable();
}

// 匯出資料庫資料
async function exportDatabaseData() {
    try {
        const table = document.getElementById('tableSelect').value;
        
        showAlert('正在匯出資料，請稍候...', 'info');
        
        const response = await fetch(`/admin/api/database/export/${table}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // 下載檔案
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${table}_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showAlert('資料匯出完成！', 'success');
        
    } catch (error) {
        console.error('匯出資料失敗:', error);
        showAlert('匯出資料失敗: ' + error.message, 'error');
    }
}

// 清理舊資料
async function clearOldData() {
    if (!confirm('確定要刪除 30 天前的舊資料嗎？此操作無法復原！')) {
        return;
    }
    
    try {
        showAlert('正在清理舊資料，請稍候...', 'info');
        
        const response = await fetch('/admin/api/database/cleanup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ days: 30 })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        showAlert(`清理完成！刪除了 ${result.deleted_detections} 筆檢測結果，${result.deleted_behaviors} 筆行為事件，${result.deleted_analysis} 筆分析記錄`, 'success');
        
        // 重新整理統計資訊
        refreshDatabaseStats();
        
    } catch (error) {
        console.error('清理舊資料失敗:', error);
        showAlert('清理舊資料失敗: ' + error.message, 'error');
    }
}

// 刪除所有資料
async function clearAllDatabase() {
    if (!confirm('⚠️ 警告：此操作將永久刪除所有資料庫中的資料！\n\n您確定要繼續嗎？此操作無法復原！')) {
        return;
    }
    
    // 二次確認
    if (!confirm('最後確認：您真的要刪除所有資料嗎？\n\n建議先建立備份！')) {
        return;
    }
    
    try {
        showAlert('正在刪除所有資料，請稍候...', 'info');
        
        const response = await fetch('/admin/api/database/clear-all', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        showAlert('所有資料已成功刪除！', 'success');
        
        // 重新整理統計資料
        refreshDatabaseStats();
        
    } catch (error) {
        console.error('刪除所有資料失敗:', error);
        showAlert('刪除所有資料失敗: ' + error.message, 'error');
    }
}

// 備份資料庫
async function backupDatabase() {
    try {
        showAlert('正在建立資料庫備份，請稍候...', 'info');
        
        const response = await fetch('/admin/api/database/backup');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        showAlert(`備份完成！檔案: ${result.backup_file}`, 'success');
        
    } catch (error) {
        console.error('備份資料庫失敗:', error);
        showAlert('備份資料庫失敗: ' + error.message, 'error');
    }
}

// 顯示載入狀態
function showLoading(show) {
    const indicator = document.getElementById('loadingIndicator');
    const container = document.getElementById('dataTableContainer');
    
    if (show) {
        indicator.classList.remove('hidden');
        container.classList.add('opacity-50');
    } else {
        indicator.classList.add('hidden');
        container.classList.remove('opacity-50');
    }
}

// 顯示警告訊息
function showAlert(message, type = 'info') {
    // 創建警告元素
    const alertDiv = document.createElement('div');
    alertDiv.className = `fixed top-4 right-4 p-4 rounded-lg text-white z-50 max-w-sm ${getAlertClass(type)}`;
    alertDiv.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${getAlertIcon(type)} mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(alertDiv);
    
    // 自動移除
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// 獲取警告樣式類別
function getAlertClass(type) {
    const classes = {
        'success': 'bg-green-600',
        'error': 'bg-red-600',
        'warning': 'bg-yellow-600',
        'info': 'bg-blue-600'
    };
    return classes[type] || classes.info;
}

// 獲取警告圖示
function getAlertIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

// 顯示項目詳細資訊
async function showItemDetails(tableName, itemId) {
    try {
        console.log(`查看詳細資訊: ${tableName} - ID: ${itemId}`);
        
        // 顯示載入中
        const loadingModal = createModal('載入中...', `
            <div class="text-center py-8">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
                <div class="mt-4 text-cyan-300">正在載入項目詳細資訊...</div>
            </div>
        `);
        document.body.appendChild(loadingModal);
        
        // 發送 API 請求
        const response = await fetch(`/admin/api/database/item-info/${tableName}/${itemId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // 移除載入中視窗
        loadingModal.remove();
        
        // 顯示詳細資訊視窗
        displayItemDetailsModal(result);
        
    } catch (error) {
        console.error('獲取項目詳細資訊失敗:', error);
        
        // 移除載入中視窗
        const loadingModal = document.querySelector('.modal-overlay');
        if (loadingModal) {
            loadingModal.remove();
        }
        
        showAlert(`獲取項目詳細資訊失敗: ${error.message}`, 'error');
    }
}

// 顯示項目詳細資訊模態視窗
function displayItemDetailsModal(result) {
    const { item_data, detailed_info, table_name } = result;
    
    // 構建詳細資訊 HTML
    let modalContent = `
        <div class="max-h-96 overflow-y-auto">
            <!-- 項目基本資訊 -->
            <div class="mb-6">
                <h3 class="text-lg font-bold text-cyan-100 mb-3 flex items-center">
                    <i class="fas fa-info-circle text-cyan-400 mr-2"></i>
                    基本資訊
                </h3>
                <div class="bg-gray-800/50 rounded-lg p-4">
                    <div class="grid grid-cols-2 gap-4 text-sm">
    `;
    
    // 顯示基本資料
    Object.entries(item_data).forEach(([key, value]) => {
        const displayName = getColumnDisplayName(key);
        let displayValue = value;
        
        // 格式化顯示值
        if (value === null || value === undefined || value === '') {
            displayValue = '<span class="text-gray-500">未設定</span>';
        } else if (key.includes('created_at') || key.includes('updated_at') || key.includes('timestamp')) {
            try {
                const date = new Date(value);
                displayValue = date.toLocaleString('zh-TW');
            } catch (e) {
                displayValue = value;
            }
        } else if (typeof value === 'number' && key.includes('confidence')) {
            displayValue = (value * 100).toFixed(2) + '%';
        }
        
        modalContent += `
            <div class="col-span-1">
                <div class="text-gray-400">${displayName}</div>
                <div class="text-cyan-100 font-medium">${displayValue}</div>
            </div>
        `;
    });
    
    modalContent += `
                    </div>
                </div>
            </div>
            
            <!-- 用途說明 -->
            <div class="mb-6">
                <h3 class="text-lg font-bold text-cyan-100 mb-3 flex items-center">
                    <i class="fas fa-lightbulb text-yellow-400 mr-2"></i>
                    ${detailed_info.purpose}
                </h3>
                <div class="bg-gray-800/50 rounded-lg p-4">
                    <p class="text-gray-300 text-sm mb-4">${detailed_info.description}</p>
                    
                    <div class="mb-4">
                        <h4 class="text-cyan-300 font-medium mb-2">主要功能：</h4>
                        <ul class="list-disc list-inside text-gray-300 text-sm space-y-1">
    `;
    
    detailed_info.functionality.forEach(func => {
        modalContent += `<li>${func}</li>`;
    });
    
    modalContent += `
                        </ul>
                    </div>
                    
                    <div>
                        <h4 class="text-cyan-300 font-medium mb-2">使用場景：</h4>
                        <ul class="list-disc list-inside text-gray-300 text-sm space-y-1">
    `;
    
    detailed_info.usage_scenarios.forEach(scenario => {
        modalContent += `<li>${scenario}</li>`;
    });
    
    modalContent += `
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- 關聯資料 -->
            <div class="mb-6">
                <h3 class="text-lg font-bold text-cyan-100 mb-3 flex items-center">
                    <i class="fas fa-link text-green-400 mr-2"></i>
                    關聯資料
                </h3>
                <div class="bg-gray-800/50 rounded-lg p-4">
                    <div class="grid grid-cols-2 gap-4 text-sm">
    `;
    
    Object.entries(detailed_info.related_data).forEach(([key, value]) => {
        const displayName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        modalContent += `
            <div class="col-span-1">
                <div class="text-gray-400">${displayName}</div>
                <div class="text-cyan-100 font-medium">${value}</div>
            </div>
        `;
    });
    
    modalContent += `
                    </div>
                </div>
            </div>
            
            <!-- 欄位說明 -->
            <div>
                <h3 class="text-lg font-bold text-cyan-100 mb-3 flex items-center">
                    <i class="fas fa-list text-purple-400 mr-2"></i>
                    欄位說明
                </h3>
                <div class="bg-gray-800/50 rounded-lg p-4">
                    <div class="space-y-3 text-sm">
    `;
    
    Object.entries(detailed_info.field_explanations).forEach(([field, explanation]) => {
        const displayName = getColumnDisplayName(field);
        modalContent += `
            <div class="border-b border-gray-600 pb-2 last:border-b-0">
                <div class="text-cyan-300 font-medium">${displayName} (${field})</div>
                <div class="text-gray-300 mt-1">${explanation}</div>
            </div>
        `;
    });
    
    modalContent += `
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 創建並顯示模態視窗
    const modal = createModal(`項目詳細資訊 - ${getTableDisplayName(table_name)} #${item_data.id}`, modalContent);
    document.body.appendChild(modal);
}

// 獲取資料表顯示名稱
function getTableDisplayName(tableName) {
    const tableNames = {
        'analysis_records': '分析記錄',
        'detection_results': '檢測結果',
        'behavior_events': '行為事件'
    };
    return tableNames[tableName] || tableName;
}

// 創建模態視窗
function createModal(title, content) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-gray-900 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-screen overflow-hidden">
            <div class="flex items-center justify-between p-6 border-b border-gray-700">
                <h3 class="text-xl font-bold text-cyan-100">${title}</h3>
                <button class="close-modal text-gray-400 hover:text-gray-200">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="p-6">
                ${content}
            </div>
            <div class="flex justify-end p-6 border-t border-gray-700">
                <button class="close-modal px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors">
                    關閉
                </button>
            </div>
        </div>
    `;
    
    // 關閉事件
    modal.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', () => modal.remove());
    });
    
    // 點擊背景關閉
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    return modal;
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing dashboard...');
    
    const dashboard = new AdminDashboard();
    window.dashboard = dashboard; // 用於調試
    
    // 初始化資料庫管理
    if (document.getElementById('database')) {
        console.log('初始化資料庫管理功能...');
        
        // 設置導航點擊事件
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const href = item.getAttribute('href');
                if (href === '#database') {
                    setTimeout(() => {
                        refreshDatabaseStats();
                        // 載入初始搜尋建議
                        loadSearchSuggestions(currentTable);
                    }, 100);
                }
            });
        });
        
        // 初始化智能搜尋功能
        initSmartSearch();
    }
    
    console.log('YOLOv11 後台管理系統已初始化完成');
});

// 初始化智能搜尋功能
function initSmartSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchSuggestions = document.getElementById('searchSuggestions');
    const searchSuggestionsBtn = document.getElementById('searchSuggestionsBtn');
    const tableSelect = document.getElementById('tableSelect');
    
    if (!searchInput || !searchSuggestions || !searchSuggestionsBtn || !tableSelect) {
        console.log('搜尋元素未找到，跳過智能搜尋初始化');
        return;
    }
    
    // 表格切換時重新載入建議
    tableSelect.addEventListener('change', () => {
        currentTable = tableSelect.value;
        loadSearchSuggestions(currentTable);
    });
    
    // 點擊建議按鈕顯示/隱藏建議
    searchSuggestionsBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        searchSuggestions.classList.toggle('hidden');
    });
    
    // 搜尋輸入框獲得焦點時顯示建議
    searchInput.addEventListener('focus', () => {
        searchSuggestions.classList.remove('hidden');
    });
    
    // 按 Enter 鍵執行搜尋
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchTable();
            searchSuggestions.classList.add('hidden');
        }
    });
    
    // 點擊外部隱藏建議
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && 
            !searchSuggestions.contains(e.target) && 
            !searchSuggestionsBtn.contains(e.target)) {
            searchSuggestions.classList.add('hidden');
        }
    });
    
    // 載入初始建議
    loadSearchSuggestions(currentTable);
    
    console.log('智能搜尋功能已初始化');
}
