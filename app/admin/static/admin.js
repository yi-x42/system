/**
 * YOLOv11 後台管理系統 JavaScript - 增強版
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
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initCharts();
        this.loadSystemStatus();
        this.loadYoloConfig();
        this.loadAvailableModels();
        this.loadFileList();
        this.loadNetworkStatus();
        this.loadLogs();
        
        // 每 5 秒更新一次系統狀態
        setInterval(() => this.loadSystemStatus(), 5000);
        // 每 30 秒更新一次網絡狀態
        setInterval(() => this.loadNetworkStatus(), 30000);
        // 更新時間
        setInterval(() => this.updateTime(), 1000);
    }

    setupEventListeners() {
        // 側邊欄切換
        document.getElementById('sidebar-toggle').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('-translate-x-full');
        });

        document.getElementById('sidebar-close').addEventListener('click', () => {
            document.getElementById('sidebar').classList.add('-translate-x-full');
        });

        // 導航項目點擊
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const target = item.getAttribute('href').substring(1);
                this.showPanel(target);
                
                // 更新導航狀態
                document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('bg-gray-800'));
                item.classList.add('bg-gray-800');
                
                // 更新頁面標題
                const titles = {
                    'dashboard': '系統監控',
                    'yolo-config': 'YOLO 配置',
                    'file-manager': '檔案管理',
                    'analytics': '資料分析',
                    'network': '網絡狀態',
                    'logs': '系統日誌'
                };
                document.getElementById('page-title').textContent = titles[target] || '系統監控';
            });
        });

        // YOLO 配置相關事件
        this.setupYoloConfigEvents();
        
        // 檔案上傳
        document.getElementById('file-upload')?.addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files[0]);
        });

        // YOLO 配置表單
        document.getElementById('yolo-config-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveYoloConfig();
        });
    }

    setupYoloConfigEvents() {
        // 滑桿同步
        const confidenceSlider = document.getElementById('confidence-slider');
        const confidenceInput = document.getElementById('confidence-threshold');
        const iouSlider = document.getElementById('iou-slider');
        const iouInput = document.getElementById('iou-threshold');

        if (confidenceSlider && confidenceInput) {
            confidenceSlider.addEventListener('input', (e) => {
                confidenceInput.value = e.target.value;
            });
            confidenceInput.addEventListener('input', (e) => {
                confidenceSlider.value = e.target.value;
            });
        }

        if (iouSlider && iouInput) {
            iouSlider.addEventListener('input', (e) => {
                iouInput.value = e.target.value;
            });
            iouInput.addEventListener('input', (e) => {
                iouSlider.value = e.target.value;
            });
        }

        // 重新整理模型按鈕
        document.getElementById('refresh-models')?.addEventListener('click', () => {
            this.loadAvailableModels();
        });

        // 重置配置按鈕
        document.getElementById('reset-config')?.addEventListener('click', () => {
            this.resetYoloConfig();
        });
    }

    initCharts() {
        // 系統資源趨勢圖（面積圖）
        const systemCtx = document.getElementById('systemChart')?.getContext('2d');
        if (systemCtx) {
            this.systemChart = new Chart(systemCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'CPU %',
                            data: [],
                            borderColor: 'rgb(59, 130, 246)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: '記憶體 %',
                            data: [],
                            borderColor: 'rgb(34, 197, 94)',
                            backgroundColor: 'rgba(34, 197, 94, 0.1)',
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: 'GPU %',
                            data: [],
                            borderColor: 'rgb(168, 85, 247)',
                            backgroundColor: 'rgba(168, 85, 247, 0.1)',
                            fill: true,
                            tension: 0.4
                        }
                    ]
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
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }

        // 資源分佈圓餅圖
        const pieCtx = document.getElementById('resourcePieChart')?.getContext('2d');
        if (pieCtx) {
            this.resourcePieChart = new Chart(pieCtx, {
                type: 'doughnut',
                data: {
                    labels: ['已使用', '可用'],
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: [
                            'rgb(239, 68, 68)',
                            'rgb(34, 197, 94)'
                        ],
                        borderWidth: 2
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

        // 記憶體詳細圖（長條圖）
        const memoryCtx = document.getElementById('memoryChart')?.getContext('2d');
        if (memoryCtx) {
            this.memoryChart = new Chart(memoryCtx, {
                type: 'bar',
                data: {
                    labels: ['實體記憶體', '虛擬記憶體', '交換記憶體'],
                    datasets: [{
                        label: '使用率 %',
                        data: [0, 0, 0],
                        backgroundColor: [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(34, 197, 94, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        borderColor: [
                            'rgb(59, 130, 246)',
                            'rgb(34, 197, 94)',
                            'rgb(251, 191, 36)'
                        ],
                        borderWidth: 1
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

        // 網絡活動圖（折線圖）
        const networkCtx = document.getElementById('networkChart')?.getContext('2d');
        if (networkCtx) {
            this.networkChart = new Chart(networkCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: '上傳 (KB/s)',
                            data: [],
                            borderColor: 'rgb(239, 68, 68)',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: '下載 (KB/s)',
                            data: [],
                            borderColor: 'rgb(34, 197, 94)',
                            backgroundColor: 'rgba(34, 197, 94, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
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
    }
                this.switchPanel(item.getAttribute('href').substring(1));
                
                // 更新活動狀態
                document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
            });
        });

        // YOLO 配置表單提交
        document.getElementById('yolo-config-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveYoloConfig();
        });

        // 檔案上傳
        document.getElementById('file-upload').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.uploadFile(e.target.files[0]);
            }
        });
    }

    switchPanel(panelName) {
        // 隱藏所有面板
        document.querySelectorAll('.content-panel').forEach(panel => {
            panel.classList.add('hidden');
        });

        // 顯示目標面板
        const targetPanel = document.getElementById(panelName + '-content');
        if (targetPanel) {
            targetPanel.classList.remove('hidden');
        }

        // 更新頁面標題
        const titles = {
            'dashboard': '系統監控',
            'yolo-config': 'YOLO 配置',
            'file-manager': '檔案管理',
            'analytics': '資料分析',
            'network': '網絡狀態',
            'logs': '系統日誌'
        };
        
        document.getElementById('page-title').textContent = titles[panelName] || '系統監控';
    }

    initCharts() {
        // 系統資源趨勢圖
        const systemCtx = document.getElementById('systemChart').getContext('2d');
        this.systemChart = new Chart(systemCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CPU (%)',
                        data: [],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: '記憶體 (%)',
                        data: [],
                        borderColor: 'rgb(16, 185, 129)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'GPU (%)',
                        data: [],
                        borderColor: 'rgb(139, 92, 246)',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.1
                    }
                ]
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

        // 網絡流量圖
        const networkCtx = document.getElementById('networkChart').getContext('2d');
        this.networkChart = new Chart(networkCtx, {
            type: 'bar',
            data: {
                labels: ['發送', '接收'],
                datasets: [{
                    label: '流量 (MB)',
                    data: [0, 0],
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(34, 197, 94, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/admin/api/system/status');
            const data = await response.json();

            // 更新指標卡片
            document.getElementById('cpu-usage').textContent = `${data.cpu.percent.toFixed(1)}%`;
            document.getElementById('memory-usage').textContent = `${data.memory.percent.toFixed(1)}%`;
            document.getElementById('gpu-usage').textContent = `${data.gpu.load.toFixed(1)}%`;
            document.getElementById('disk-usage').textContent = `${data.disk.percent.toFixed(1)}%`;

            // 更新圖表數據
            const now = new Date().toLocaleTimeString();
            this.systemData.labels.push(now);
            this.systemData.cpu.push(data.cpu.percent);
            this.systemData.memory.push(data.memory.percent);
            this.systemData.gpu.push(data.gpu.load);

            // 限制數據點數量
            if (this.systemData.labels.length > 20) {
                this.systemData.labels.shift();
                this.systemData.cpu.shift();
                this.systemData.memory.shift();
                this.systemData.gpu.shift();
            }

            // 更新圖表
            this.systemChart.data.labels = this.systemData.labels;
            this.systemChart.data.datasets[0].data = this.systemData.cpu;
            this.systemChart.data.datasets[1].data = this.systemData.memory;
            this.systemChart.data.datasets[2].data = this.systemData.gpu;
            this.systemChart.update('none');

            // 更新網絡圖表
            this.networkChart.data.datasets[0].data = [
                (data.network.bytes_sent / (1024 * 1024)).toFixed(2),
                (data.network.bytes_recv / (1024 * 1024)).toFixed(2)
            ];
            this.networkChart.update('none');

        } catch (error) {
            console.error('載入系統狀態失敗:', error);
        }
    }

    async loadYoloConfig() {
        try {
            const response = await fetch('/admin/api/yolo/config');
            const config = await response.json();

            document.getElementById('model-path').value = config.model_path;
            document.getElementById('device').value = config.device;
            document.getElementById('confidence-threshold').value = config.confidence_threshold;
            document.getElementById('iou-threshold').value = config.iou_threshold;
            document.getElementById('max-file-size').value = config.max_file_size;
            document.getElementById('allowed-extensions').value = config.allowed_extensions.join(',');

        } catch (error) {
            console.error('載入 YOLO 配置失敗:', error);
        }
    }

    async saveYoloConfig() {
        try {
            const formData = new FormData(document.getElementById('yolo-config-form'));
            
            const response = await fetch('/admin/api/yolo/config', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.showNotification('配置儲存成功', 'success');
            } else {
                this.showNotification('配置儲存失敗', 'error');
            }

        } catch (error) {
            console.error('儲存 YOLO 配置失敗:', error);
            this.showNotification('配置儲存失敗', 'error');
        }
    }

    async loadFileList(path = '.') {
        try {
            const response = await fetch(`/admin/api/files/list?path=${encodeURIComponent(path)}`);
            const data = await response.json();

            this.currentPath = data.current_path;
            document.getElementById('current-path').textContent = data.current_path;

            const fileList = document.getElementById('file-list');
            fileList.innerHTML = '';

            // 返回上級目錄選項
            if (data.parent_path) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center cursor-pointer" onclick="adminDashboard.loadFileList('${data.parent_path}')">
                            <i class="fas fa-folder mr-2 text-yellow-500"></i>
                            <span class="text-blue-600 hover:underline">..</span>
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">目錄</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">-</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">-</td>
                `;
                fileList.appendChild(row);
            }

            // 檔案和目錄列表
            data.items.forEach(item => {
                const row = document.createElement('tr');
                const icon = item.type === 'directory' ? 'fa-folder' : 'fa-file';
                const iconColor = item.type === 'directory' ? 'text-yellow-500' : 'text-gray-500';
                const size = item.type === 'directory' ? '-' : this.formatFileSize(item.size);
                
                row.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center ${item.type === 'directory' ? 'cursor-pointer' : ''}" 
                             ${item.type === 'directory' ? `onclick="adminDashboard.loadFileList('${item.path}')"` : ''}>
                            <i class="fas ${icon} mr-2 ${iconColor}"></i>
                            <span class="${item.type === 'directory' ? 'text-blue-600 hover:underline' : ''}">${item.name}</span>
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.type === 'directory' ? '目錄' : '檔案'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${size}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${new Date(item.modified).toLocaleString()}</td>
                `;
                fileList.appendChild(row);
            });

        } catch (error) {
            console.error('載入檔案列表失敗:', error);
        }
    }

    async uploadFile(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('target_path', this.currentPath);

            const response = await fetch('/admin/api/files/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.showNotification('檔案上傳成功', 'success');
                this.loadFileList(this.currentPath);
            } else {
                this.showNotification('檔案上傳失敗', 'error');
            }

        } catch (error) {
            console.error('上傳檔案失敗:', error);
            this.showNotification('檔案上傳失敗', 'error');
        }
    }

    async loadNetworkStatus() {
        try {
            const response = await fetch('/admin/api/radmin/status');
            const data = await response.json();

            const statusElement = document.getElementById('connection-status');
            const icon = statusElement.querySelector('i');
            const text = statusElement.querySelector('span');

            if (data.radmin_connected) {
                icon.className = 'fas fa-circle status-online mr-2';
                text.textContent = '已連接';
            } else {
                icon.className = 'fas fa-circle status-offline mr-2';
                text.textContent = '未連接';
            }

            // 更新網絡面板
            const networkInfo = document.getElementById('network-info');
            networkInfo.innerHTML = `
                <div class="space-y-4">
                    <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <span>Radmin 網絡狀態</span>
                        <span class="${data.radmin_connected ? 'status-online' : 'status-offline'}">
                            ${data.radmin_connected ? '已連接' : '未連接'}
                        </span>
                    </div>
                    <div class="p-4 bg-gray-50 rounded-lg">
                        <h4 class="font-medium mb-2">網絡介面</h4>
                        ${data.network_interfaces.map(iface => 
                            `<div class="text-sm text-gray-600">${iface.interface}: ${iface.ip}</div>`
                        ).join('')}
                    </div>
                </div>
            `;

        } catch (error) {
            console.error('載入網絡狀態失敗:', error);
        }
    }

    async loadLogs() {
        try {
            const response = await fetch('/admin/api/logs/list?lines=50');
            const data = await response.json();

            const logContent = document.getElementById('log-content');
            logContent.innerHTML = data.logs.map(log => 
                `<div class="mb-1">${this.escapeHtml(log)}</div>`
            ).join('');

            // 滾動到底部
            logContent.scrollTop = logContent.scrollHeight;

        } catch (error) {
            console.error('載入日誌失敗:', error);
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    updateTime() {
        const now = new Date();
        document.getElementById('current-time').textContent = now.toLocaleString();
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        } text-white`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            document.body.removeChild(notification);
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 初始化管理面板
let adminDashboard;
document.addEventListener('DOMContentLoaded', () => {
    adminDashboard = new AdminDashboard();
});
