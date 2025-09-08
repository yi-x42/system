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
        const fileUpload = document.getElementById('file-upload');
        if (fileUpload) {
            fileUpload.addEventListener('change', (e) => {
                this.handleFileUpload(e.target.files[0]);
            });
        }

        // YOLO 配置表單
        const configForm = document.getElementById('yolo-config-form');
        if (configForm) {
            configForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveYoloConfig();
            });
        }
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
        const refreshButton = document.getElementById('refresh-models');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                this.loadAvailableModels();
            });
        }

        // 重置配置按鈕
        const resetButton = document.getElementById('reset-config');
        if (resetButton) {
            resetButton.addEventListener('click', () => {
                this.resetYoloConfig();
            });
        }
    }

    showPanel(panelName) {
        // 隱藏所有面板
        document.querySelectorAll('.content-panel').forEach(panel => {
            panel.classList.add('hidden');
        });
        
        // 顯示指定面板
        const targetPanel = document.getElementById(`${panelName}-content`);
        if (targetPanel) {
            targetPanel.classList.remove('hidden');
        }
        
        // 如果是 YOLO 配置面板，載入模型
        if (panelName === 'yolo-config') {
            this.loadAvailableModels();
        }
    }

    initCharts() {
        // 系統資源趨勢圖（面積圖）
        const systemCtx = document.getElementById('systemChart');
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
        const pieCtx = document.getElementById('resourcePieChart');
        if (pieCtx) {
            this.resourcePieChart = new Chart(pieCtx, {
                type: 'doughnut',
                data: {
                    labels: ['CPU 使用', 'CPU 空閒', '記憶體使用', '記憶體空閒'],
                    datasets: [{
                        data: [0, 100, 0, 100],
                        backgroundColor: [
                            'rgb(59, 130, 246)',
                            'rgba(59, 130, 246, 0.2)',
                            'rgb(34, 197, 94)',
                            'rgba(34, 197, 94, 0.2)'
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
        const memoryCtx = document.getElementById('memoryChart');
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
        const networkCtx = document.getElementById('networkChart');
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

    async loadSystemStatus() {
        try {
            const response = await fetch('/admin/api/system/status');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
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

            // 限制數據點數量到20個
            if (this.systemData.labels.length > 20) {
                this.systemData.labels.shift();
                this.systemData.cpu.shift();
                this.systemData.memory.shift();
                this.systemData.gpu.shift();
            }

            // 更新趨勢圖
            if (this.systemChart) {
                this.systemChart.data.labels = this.systemData.labels;
                this.systemChart.data.datasets[0].data = this.systemData.cpu;
                this.systemChart.data.datasets[1].data = this.systemData.memory;
                this.systemChart.data.datasets[2].data = this.systemData.gpu;
                this.systemChart.update('none');
            }

            // 更新圓餅圖
            if (this.resourcePieChart) {
                this.resourcePieChart.data.datasets[0].data = [
                    data.cpu.percent,
                    100 - data.cpu.percent,
                    data.memory.percent,
                    100 - data.memory.percent
                ];
                this.resourcePieChart.update('none');
            }

            // 更新記憶體詳細圖
            if (this.memoryChart) {
                this.memoryChart.data.datasets[0].data = [
                    data.memory.percent,
                    data.memory.virtual_percent || 0,
                    data.memory.swap_percent || 0
                ];
                this.memoryChart.update('none');
            }

        } catch (error) {
            console.error('載入系統狀態失敗:', error);
        }
    }

    async loadAvailableModels() {
        try {
            const response = await fetch('/admin/api/yolo/models');
            const data = await response.json();
            this.availableModels = data;
            this.renderModelList();
        } catch (error) {
            console.error('載入模型列表失敗:', error);
        }
    }

    renderModelList() {
        const officialContainer = document.getElementById('official-models');
        const customContainer = document.getElementById('custom-models');

        if (!this.availableModels || !officialContainer || !customContainer) return;

        // 渲染官方模型
        officialContainer.innerHTML = '';
        this.availableModels.official_models.forEach(model => {
            const modelCard = this.createModelCard(model, false);
            officialContainer.appendChild(modelCard);
        });

        // 渲染自定義模型
        customContainer.innerHTML = '';
        if (this.availableModels.custom_models.length === 0) {
            customContainer.innerHTML = '<p class="text-gray-500 col-span-full text-center py-4">尚無自定義模型</p>';
        } else {
            this.availableModels.custom_models.forEach(model => {
                const modelCard = this.createModelCard(model, true);
                customContainer.appendChild(modelCard);
            });
        }
    }

    createModelCard(model, isCustom) {
        const card = document.createElement('div');
        card.className = `border rounded-lg p-4 cursor-pointer transition-all duration-200 ${
            model.exists ? 'border-green-300 bg-green-50 hover:bg-green-100' : 'border-gray-300 bg-gray-50 hover:bg-gray-100'
        }`;

        const statusIcon = model.exists ? 
            '<i class="fas fa-check-circle text-green-500"></i>' : 
            '<i class="fas fa-download text-blue-500"></i>';

        card.innerHTML = `
            <div class="flex items-start justify-between mb-2">
                <h5 class="font-medium text-gray-900">${model.name}</h5>
                ${statusIcon}
            </div>
            <p class="text-sm text-gray-600 mb-2">${model.description}</p>
            <div class="flex justify-between items-center text-xs text-gray-500">
                <span>大小: ${model.actual_size}</span>
                <span>${model.exists ? '已下載' : '未下載'}</span>
            </div>
        `;

        card.addEventListener('click', () => {
            if (model.exists) {
                this.selectModel(model);
            } else {
                this.downloadModel(model);
            }
        });

        return card;
    }

    selectModel(model) {
        this.selectedModel = model;
        const selectedModelInput = document.getElementById('selected-model');
        if (selectedModelInput) {
            selectedModelInput.value = model.file;
        }
        
        // 更新視覺反饋
        document.querySelectorAll('#official-models > div, #custom-models > div').forEach(card => {
            card.classList.remove('ring-2', 'ring-blue-500');
        });
        event.currentTarget.classList.add('ring-2', 'ring-blue-500');
    }

    async downloadModel(model) {
        try {
            const formData = new FormData();
            formData.append('model_file', model.file);
            
            const response = await fetch('/admin/api/yolo/download-model', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (result.success) {
                alert(`模型 ${model.name} 下載成功！`);
                this.loadAvailableModels();
            } else {
                alert(`下載失敗：${result.message}`);
            }
        } catch (error) {
            console.error('下載模型失敗:', error);
            alert('下載過程中發生錯誤');
        }
    }

    async loadYoloConfig() {
        try {
            const response = await fetch('/admin/api/yolo/config');
            const config = await response.json();

            document.getElementById('selected-model').value = config.model_path;
            document.getElementById('device').value = config.device;
            document.getElementById('confidence-threshold').value = config.confidence_threshold;
            document.getElementById('confidence-slider').value = config.confidence_threshold;
            document.getElementById('iou-threshold').value = config.iou_threshold;
            document.getElementById('iou-slider').value = config.iou_threshold;
            document.getElementById('max-file-size').value = config.max_file_size;

        } catch (error) {
            console.error('載入 YOLO 配置失敗:', error);
        }
    }

    async saveYoloConfig() {
        try {
            const formData = new FormData();
            formData.append('model_path', document.getElementById('selected-model').value);
            formData.append('device', document.getElementById('device').value);
            formData.append('confidence_threshold', document.getElementById('confidence-threshold').value);
            formData.append('iou_threshold', document.getElementById('iou-threshold').value);
            formData.append('max_file_size', document.getElementById('max-file-size').value);
            
            // 收集選中的檔案格式
            const selectedFormats = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
                .map(cb => cb.value);
            formData.append('allowed_extensions', selectedFormats.join(','));

            const response = await fetch('/admin/api/yolo/config', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                alert('配置已儲存成功！');
            } else {
                alert('儲存配置失敗');
            }
        } catch (error) {
            console.error('儲存配置失敗:', error);
            alert('儲存過程中發生錯誤');
        }
    }

    resetYoloConfig() {
        document.getElementById('selected-model').value = 'yolo11n.pt';
        document.getElementById('device').value = 'auto';
        document.getElementById('confidence-threshold').value = '0.25';
        document.getElementById('confidence-slider').value = '0.25';
        document.getElementById('iou-threshold').value = '0.7';
        document.getElementById('iou-slider').value = '0.7';
        document.getElementById('max-file-size').value = '50MB';
        
        // 重置複選框
        document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = ['jpg', 'png', 'mp4', 'avi'].includes(cb.value);
        });
    }

    async loadFileList(path = '.') {
        try {
            const response = await fetch(`/admin/api/files/list?path=${encodeURIComponent(path)}`);
            const data = await response.json();

            this.currentPath = path;
            document.getElementById('current-path').textContent = path;

            const tbody = document.getElementById('file-list');
            tbody.innerHTML = '';

            data.files.forEach(file => {
                const row = document.createElement('tr');
                row.className = 'hover:bg-gray-50';
                
                const icon = file.type === 'directory' ? 'fa-folder' : 'fa-file';
                const size = file.type === 'directory' ? '-' : file.size;
                
                row.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center">
                            <i class="fas ${icon} mr-2 text-gray-500"></i>
                            <span class="text-sm text-gray-900">${file.name}</span>
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${file.type}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${size}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${file.modified || '-'}</td>
                `;

                if (file.type === 'directory') {
                    row.style.cursor = 'pointer';
                    row.addEventListener('click', () => {
                        this.loadFileList(file.path);
                    });
                }

                tbody.appendChild(row);
            });
        } catch (error) {
            console.error('載入檔案列表失敗:', error);
        }
    }

    async handleFileUpload(file) {
        if (!file) return;

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/admin/api/files/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                alert('檔案上傳成功！');
                this.loadFileList(this.currentPath);
            } else {
                alert('檔案上傳失敗');
            }
        } catch (error) {
            console.error('上傳檔案失敗:', error);
            alert('上傳過程中發生錯誤');
        }
    }

    async loadNetworkStatus() {
        try {
            const response = await fetch('/admin/api/radmin/status');
            const data = await response.json();

            const networkInfo = document.getElementById('network-info');
            if (networkInfo) {
                networkInfo.innerHTML = `
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span>Radmin IP:</span>
                            <span class="font-mono">${data.radmin_ip || '26.86.64.166'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>連接狀態:</span>
                            <span class="text-green-600">已連接</span>
                        </div>
                        <div class="flex justify-between">
                            <span>服務端口:</span>
                            <span class="font-mono">8001</span>
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('載入網絡狀態失敗:', error);
        }
    }

    async loadLogs() {
        try {
            const response = await fetch('/admin/api/logs/list?lines=50');
            const data = await response.json();

            const logContent = document.getElementById('log-content');
            if (logContent) {
                logContent.textContent = data.logs || '暫無日誌';
            }
        } catch (error) {
            console.error('載入日誌失敗:', error);
        }
    }

    updateTime() {
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.textContent = new Date().toLocaleString('zh-TW');
        }
    }
}

// 科技感動畫效果 - 優化版
class TechEffects {
    static initParticles() {
        const particlesContainer = document.getElementById('particles');
        if (!particlesContainer) return;
        
        // 清除現有粒子
        particlesContainer.innerHTML = '';
        
        for (let i = 0; i < 30; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.cssText = `
                position: absolute;
                width: 2px;
                height: 2px;
                background: #00f5ff;
                border-radius: 50%;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation: float ${4 + Math.random() * 4}s ease-in-out infinite;
                opacity: ${0.4 + Math.random() * 0.6};
                animation-delay: ${Math.random() * 2}s;
            `;
            particlesContainer.appendChild(particle);
        }
    }
    
    static initNeuralNetwork() {
        const canvas = document.getElementById('neural-network');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        const nodes = [];
        for (let i = 0; i < 15; i++) {
            nodes.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3
            });
        }
        
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = '#00f5ff15';
            ctx.lineWidth = 1;
            
            // 更新節點位置
            nodes.forEach(node => {
                node.x += node.vx;
                node.y += node.vy;
                
                if (node.x <= 0 || node.x >= canvas.width) node.vx *= -1;
                if (node.y <= 0 || node.y >= canvas.height) node.vy *= -1;
            });
            
            // 繪製連線
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dist = Math.sqrt(
                        Math.pow(nodes[i].x - nodes[j].x, 2) + 
                        Math.pow(nodes[i].y - nodes[j].y, 2)
                    );
                    
                    if (dist < 200) {
                        const opacity = 1 - (dist / 200);
                        ctx.strokeStyle = `rgba(0, 245, 255, ${opacity * 0.3})`;
                        ctx.beginPath();
                        ctx.moveTo(nodes[i].x, nodes[i].y);
                        ctx.lineTo(nodes[j].x, nodes[j].y);
                        ctx.stroke();
                    }
                }
            }
            
            // 繪製節點
            ctx.fillStyle = '#00f5ff60';
            nodes.forEach(node => {
                ctx.beginPath();
                ctx.arc(node.x, node.y, 1.5, 0, Math.PI * 2);
                ctx.fill();
            });
            
            requestAnimationFrame(animate);
        }
        
        animate();
    }
    
    static initSmoothAnimations() {
        // 為卡片添加平滑動畫
        const cards = document.querySelectorAll('.tech-card, .metric-card');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, {
            threshold: 0.1
        });
        
        cards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(card);
        });
    }
    
    static initTypingEffect() {
        const typeElements = document.querySelectorAll('[data-typing]');
        typeElements.forEach(element => {
            const text = element.textContent;
            element.textContent = '';
            
            let index = 0;
            const typing = setInterval(() => {
                if (index < text.length) {
                    element.textContent += text.charAt(index);
                    index++;
                } else {
                    clearInterval(typing);
                    // 添加游標閃爍效果
                    element.innerHTML += '<span class="cursor">|</span>';
                    setTimeout(() => {
                        const cursor = element.querySelector('.cursor');
                        if (cursor) cursor.remove();
                    }, 2000);
                }
            }, 80);
        });
    }
    
    static addScanLines() {
        let scanLineActive = false;
        
        const createScanLine = () => {
            if (scanLineActive) return;
            
            scanLineActive = true;
            const scanLine = document.createElement('div');
            scanLine.className = 'scan-line-effect';
            scanLine.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 2px;
                background: linear-gradient(90deg, transparent, #00f5ff, transparent);
                z-index: 9999;
                animation: scanMove 3s linear;
                pointer-events: none;
            `;
            document.body.appendChild(scanLine);
            
            setTimeout(() => {
                if (scanLine.parentNode) {
                    scanLine.parentNode.removeChild(scanLine);
                }
                scanLineActive = false;
            }, 3000);
        };
        
        // 每隔一段時間觸發掃描線
        setInterval(createScanLine, 15000);
        
        // 初始掃描線
        setTimeout(createScanLine, 2000);
    }
    
    static initStatusIndicators() {
        // 為狀態指示器添加動畫
        const indicators = document.querySelectorAll('.status-indicator');
        indicators.forEach(indicator => {
            if (indicator.classList.contains('status-online')) {
                indicator.style.animation = 'pulse 2s ease-in-out infinite';
            }
        });
    }
    
    static initHoverEffects() {
        // 增強懸停效果
        const interactiveElements = document.querySelectorAll('.tech-button, .model-card, .nav-item');
        
        interactiveElements.forEach(element => {
            element.addEventListener('mouseenter', function() {
                this.style.filter = 'brightness(1.1)';
            });
            
            element.addEventListener('mouseleave', function() {
                this.style.filter = 'brightness(1)';
            });
        });
    }
            animation: scanMove 3s linear infinite;
        `;
        document.body.appendChild(scanLine);
    }
}

// 初始化儀表板和科技效果
document.addEventListener('DOMContentLoaded', function() {
    new AdminDashboard();
    
    // 初始化科技感效果
    setTimeout(() => {
        TechEffects.initParticles();
        TechEffects.initNeuralNetwork();
        TechEffects.initGlitchEffects();
        TechEffects.addScanLines();
    }, 1000);
    
    // 響應式調整
    window.addEventListener('resize', () => {
        const canvas = document.getElementById('neural-network');
        if (canvas) {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
    });
});
