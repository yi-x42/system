/**
 * 全新的停止系統功能 - 簡潔可靠的實現
 */

// 等待DOM載入完成
document.addEventListener('DOMContentLoaded', function() {
    initializeShutdownButton();
});

function initializeShutdownButton() {
    console.log('🔧 初始化全新停止系統按鈕...');
    
    const shutdownBtn = document.getElementById('shutdown-system-btn');
    
    if (!shutdownBtn) {
        console.error('❌ 找不到停止系統按鈕');
        return;
    }
    
    console.log('✅ 找到停止系統按鈕');
    
    // 簡潔的停止處理函數
    async function handleShutdown() {
        console.log('🔴 停止系統被觸發');
        
        // 確認對話框
        const confirmed = confirm(
            '⚠️ 確認停止系統\n\n' +
            '這將關閉整個 YOLOv11 分析系統\n' +
            '所有正在執行的任務都會被終止\n\n' +
            '確定要繼續嗎？'
        );
        
        if (!confirmed) {
            console.log('⏹️ 用戶取消停止操作');
            return;
        }
        
        // 保存原始按鈕內容
        const originalHTML = shutdownBtn.innerHTML;
        
        // 顯示處理中狀態
        shutdownBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>停止中...</span>';
        shutdownBtn.disabled = true;
        
        try {
            console.log('🚀 發送停止請求...');
            
            // 獲取API基礎URL
            const apiBaseURL = getAPIBaseURL();
            const shutdownURL = `${apiBaseURL}/api/v1/frontend/system/shutdown`;
            
            console.log('📡 請求URL:', shutdownURL);
            
            const response = await fetch(shutdownURL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            console.log('📨 服務器回應:', response.status);
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ 停止成功:', result.message);
                
                // 顯示成功狀態
                shutdownBtn.innerHTML = '<i class="fas fa-check"></i><span>已停止</span>';
                
                // 延遲顯示提示
                setTimeout(() => {
                    alert('✅ 系統已安全停止\n\n重新啟動請執行: python start.py');
                }, 500);
                
            } else {
                throw new Error(`HTTP ${response.status} - ${response.statusText}`);
            }
            
        } catch (error) {
            console.error('❌ 停止失敗:', error);
            
            // 恢復按鈕狀態
            shutdownBtn.innerHTML = originalHTML;
            shutdownBtn.disabled = false;
            
            alert('❌ 停止系統失敗:\n' + error.message);
        }
    }
    
    // 綁定點擊事件
    shutdownBtn.addEventListener('click', handleShutdown);
    
    console.log('✅ 停止系統按鈕已成功綁定');
    
    // 創建全局測試函數
    window.shutdownSystem = handleShutdown;
    window.testShutdown = handleShutdown;
}

// 獲取API基礎URL的輔助函數
function getAPIBaseURL() {
    const currentHost = window.location.hostname;
    if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
        return 'http://localhost:8001';
    } else {
        return `http://${currentHost}:8001`;
    }
}

// 全局調試函數
window.debugShutdownButton = function() {
    const btn = document.getElementById('shutdown-system-btn');
    if (!btn) {
        console.error('❌ 找不到停止按鈕');
        return;
    }
    
    console.log('🔍 按鈕狀態診斷:');
    console.log('  元素:', btn);
    console.log('  disabled:', btn.disabled);
    console.log('  innerHTML:', btn.innerHTML);
    console.log('  顯示狀態:', getComputedStyle(btn).display);
    console.log('  可見性:', getComputedStyle(btn).visibility);
    
    const rect = btn.getBoundingClientRect();
    console.log('  位置:', rect);
    console.log('  可見:', rect.width > 0 && rect.height > 0);
};
