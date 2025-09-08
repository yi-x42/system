
// 修復載入超時問題
class DataSourceManagerFixed extends DataSourceManager {
    constructor() {
        super();
        this.loadTimeout = 15000; // 15秒超時
        this.retryCount = 3;
    }

    async loadDataSources() {
        for (let attempt = 1; attempt <= this.retryCount; attempt++) {
            try {
                console.log(`🔄 嘗試載入資料來源 (第 ${attempt} 次)...`);
                
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.loadTimeout);
                
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
                    this.hideLoadingIndicators();
                    return;
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            } catch (error) {
                console.error(`❌ 第 ${attempt} 次載入失敗:`, error);
                
                if (attempt === this.retryCount) {
                    // 最後一次嘗試失敗，顯示錯誤
                    this.showLoadingError(error);
                    this.hideLoadingIndicators();
                } else {
                    // 等待後重試
                    await new Promise(resolve => setTimeout(resolve, 2000 * attempt));
                }
            }
        }
    }

    hideLoadingIndicators() {
        // 隱藏所有載入指示器
        const loadingElements = document.querySelectorAll('.loading-placeholder, .text-muted:contains("正在載入")');
        loadingElements.forEach(el => {
            if (el.textContent.includes('正在載入')) {
                el.style.display = 'none';
            }
        });
        
        // 顯示空狀態訊息
        this.showEmptyState();
    }

    showLoadingError(error) {
        const errorHtml = `
            <div class="alert alert-danger" role="alert">
                <h6><i class="fas fa-exclamation-triangle"></i> 載入失敗</h6>
                <p>無法載入資料來源清單: ${error.message}</p>
                <div class="mt-2">
                    <button class="btn btn-outline-danger btn-sm" onclick="location.reload()">
                        <i class="fas fa-redo"></i> 重新載入頁面
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" onclick="dataSourceManager.loadDataSources()">
                        <i class="fas fa-sync"></i> 重試載入
                    </button>
                </div>
            </div>
        `;
        
        document.getElementById('cameraList').innerHTML = errorHtml;
        document.getElementById('videoList').innerHTML = errorHtml;
    }

    showEmptyState() {
        const emptyStateHtml = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-inbox fa-2x mb-2"></i>
                <p>目前沒有資料來源</p>
                <button class="btn btn-outline-primary btn-sm" onclick="dataSourceManager.showAddCameraModal()">
                    <i class="fas fa-plus"></i> 新增攝影機
                </button>
            </div>
        `;
        
        if (this.dataSources.length === 0) {
            document.getElementById('cameraList').innerHTML = emptyStateHtml;
            document.getElementById('videoList').innerHTML = emptyStateHtml.replace('新增攝影機', '上傳影片');
        }
    }
}

// 替換原有的資料來源管理器
if (typeof dataSourceManager !== 'undefined') {
    dataSourceManager = new DataSourceManagerFixed();
}
