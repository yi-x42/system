// 修復版本的導航管理器 - 專門處理資料來源管理導航問題

// 等待 DOM 載入完成後執行修復
document.addEventListener('DOMContentLoaded', function() {
    // 找到資料來源管理連結
    const dataSourceLinks = document.querySelectorAll('a[href*="data_source"]');
    
    dataSourceLinks.forEach(link => {
        // 移除任何可能的事件監聽器
        const newLink = link.cloneNode(true);
        link.parentNode.replaceChild(newLink, link);
        
        // 確保連結可以正常工作
        newLink.addEventListener('click', function(e) {
            console.log('✅ 資料來源管理連結被點擊:', this.href);
            // 不阻止預設行為，讓瀏覽器正常處理
        });
    });
    
    console.log('✅ 資料來源管理導航修復完成');
});
