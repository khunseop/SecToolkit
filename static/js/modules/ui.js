export function switchCategory(catId) {
    document.querySelectorAll('.main-nav .nav-link').forEach(link => link.classList.remove('active'));
    document.getElementById(`cat-${catId}`).classList.add('active');
    
    document.querySelectorAll('.sub-nav').forEach(nav => nav.classList.add('d-none'));
    document.getElementById(`sub-${catId}`).classList.remove('d-none');
    
    // Auto-show first tool
    const firstTool = document.getElementById(`sub-${catId}`).querySelector('.nav-link');
    if (firstTool) firstTool.click();
}

export function showTool(toolId) {
    document.querySelectorAll('.sub-nav .nav-link').forEach(link => link.classList.remove('active'));
    const toolEl = document.getElementById(`tool-${toolId}`);
    if (toolEl) toolEl.classList.add('active');
    
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
    const viewEl = document.getElementById(`view-${toolId}`);
    if (viewEl) viewEl.classList.add('active');

    // Auto-refresh System Info if selected
    if (toolId === 'sysinfo' && window.refreshSystemInfo) {
        window.refreshSystemInfo();
    }
}

export function copyToClipboard(id) {
    const el = document.getElementById(id);
    if (el) copyTextToClipboard(el.value || el.innerText);
}

export function copyTextToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert("복사되었습니다.");
    }).catch(err => {
        console.error('Copy failed', err);
    });
}
