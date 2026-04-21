import { fetchPacGroups, savePacGroups, postTestPac, postDiffPac } from './api.js';
import { copyTextToClipboard } from './ui.js';

let pacGroups = [];
let selectedPacGroupIdx = null;
let lastDiffData = null;
let lastPacContent = "";

export async function initPac() {
    await loadPacGroups();
}

async function loadPacGroups() {
    try {
        pacGroups = await fetchPacGroups();
        
        // Migration: If server list is empty, check localStorage
        if (pacGroups.length === 0) {
            const local = localStorage.getItem('pacGroups');
            if (local) {
                const localGroups = JSON.parse(local);
                if (localGroups.length > 0) {
                    pacGroups = localGroups;
                    await syncPacGroups();
                }
            }
        }
        updateGroupList();
    } catch (e) {
        console.error("Failed to load PAC groups", e);
    }
}

async function syncPacGroups() {
    try {
        await savePacGroups(pacGroups);
    } catch (e) {
        console.error("Failed to sync PAC groups", e);
    }
}

export function updateGroupList() {
    const list = document.getElementById('pacGroupList');
    const quickList = document.getElementById('pacQuickList');
    if (!list || !quickList) return;

    const renderItem = (g, i, isManagement) => {
        const isActive = selectedPacGroupIdx === i;
        return `
            <div class="badge pac-group-item text-dark d-flex align-items-center gap-2 shadow-sm ${isActive ? 'active' : ''}" onclick="selectPacGroup(${i})">
                <span>${g.name}</span>
                ${isManagement ? `<span class="text-danger fw-bold ms-1" onclick="event.stopPropagation(); deletePacGroup(${i})">&times;</span>` : ''}
            </div>
        `;
    };

    list.innerHTML = pacGroups.map((g, i) => renderItem(g, i, true)).join('');
    quickList.innerHTML = pacGroups.map((g, i) => renderItem(g, i, false)).join('');
    
    const quickSelect = document.getElementById('pacQuickSelect');
    if (quickSelect) quickSelect.style.display = pacGroups.length > 0 ? 'flex' : 'none';
}

export async function savePacGroup() {
    const name = document.getElementById('groupName').value;
    const prod = document.getElementById('prodUrl').value;
    const test = document.getElementById('testUrl').value;
    if(!name || !prod || !test) return alert("모든 필드를 입력해주세요.");
    pacGroups.push({ name, prod, test });
    await syncPacGroups();
    updateGroupList();
    document.getElementById('groupName').value = '';
}

export function selectPacGroup(i) {
    selectedPacGroupIdx = i;
    document.getElementById('prodUrl').value = pacGroups[i].prod;
    document.getElementById('testUrl').value = pacGroups[i].test;
    updateGroupList();
}

export async function deletePacGroup(i) {
    if (selectedPacGroupIdx === i) selectedPacGroupIdx = null;
    else if (selectedPacGroupIdx > i) selectedPacGroupIdx--;
    
    pacGroups.splice(i, 1);
    await syncPacGroups();
    updateGroupList();
}

function renderCommonResult(data) {
    const box = document.getElementById('commonResultBox');
    if (!box) return;
    box.style.display = 'block';
    box.innerHTML = `
        <div class="row g-2">
            <div class="col-sm-3 text-muted">Client IP</div>
            <div class="col-sm-9 fw-bold">${data.client_ip || 'Unknown'}</div>
            <div class="col-12 border-top my-1"></div>
            <div class="col-sm-3 text-muted">Target URL</div>
            <div class="col-sm-9 font-monospace">${data.target_url || data.sample_url}</div>
            <div class="col-12 border-top my-1"></div>
            <div class="col-sm-3 text-muted">Resolved IPs</div>
            <div class="col-sm-9 d-flex flex-wrap gap-1">
                ${data.resolved_ips && data.resolved_ips.length > 0 
                    ? data.resolved_ips.map(ip => `<span class="badge bg-light text-dark border font-monospace fw-normal">${ip}</span>`).join('')
                    : '<span class="text-danger small">Failed to resolve</span>'}
            </div>
        </div>`;
}

export async function testProdPac() {
    const prodUrlEl = document.getElementById('prodUrl');
    const diffSampleUrlEl = document.getElementById('diffSampleUrl');
    const loadingEl = document.getElementById('diffLoading');
    
    if (!prodUrlEl || !diffSampleUrlEl || !loadingEl) return;

    const pacUrl = prodUrlEl.value;
    const targetUrl = diffSampleUrlEl.value;
    if(!pacUrl) return alert("Prod PAC URL을 입력하거나 매니저에서 선택해주세요.");

    loadingEl.classList.remove('d-none');
    
    document.getElementById('commonResultBox').style.display = 'none';
    document.getElementById('statusCardsRow').style.display = 'none';
    document.getElementById('testStatusCol').style.display = 'none';
    document.getElementById('diffModeContent').style.display = 'none';
    document.getElementById('testModeContent').style.display = 'none';

    try {
        const data = await postTestPac(pacUrl, targetUrl);
        if(data.error) throw new Error(data.error);
        
        renderCommonResult(data);
        
        document.getElementById('statusCardsRow').style.display = 'flex';
        document.getElementById('prodStatusCol').className = 'col-12 mb-2';
        updateStatus('prod', { valid: true, proxy: data.result });
        
        document.getElementById('testModeContent').style.display = 'block';
        lastPacContent = data.pac_preview;
        document.getElementById('pacSearchInput').value = '';
        renderPacContent(lastPacContent);
    } catch (e) {
        alert("테스트 실패: " + e.message);
    } finally {
        loadingEl.classList.add('d-none');
    }
}

export async function comparePac() {
    const prodUrlEl = document.getElementById('prodUrl');
    const testUrlEl = document.getElementById('testUrl');
    const sampleUrlEl = document.getElementById('diffSampleUrl');
    const loadingEl = document.getElementById('diffLoading');
    
    if (!prodUrlEl || !testUrlEl || !sampleUrlEl || !loadingEl) return;

    const prodUrl = prodUrlEl.value;
    const testUrl = testUrlEl.value;
    const sampleUrl = sampleUrlEl.value;
    if(!prodUrl || !testUrl) return alert("Prod 및 Test PAC URL을 모두 입력해주세요.");

    loadingEl.classList.remove('d-none');
    
    document.getElementById('commonResultBox').style.display = 'none';
    document.getElementById('statusCardsRow').style.display = 'none';
    document.getElementById('testStatusCol').style.display = 'none';
    document.getElementById('diffModeContent').style.display = 'none';
    document.getElementById('testModeContent').style.display = 'none';

    try {
        const data = await postDiffPac(prodUrl, testUrl, sampleUrl);
        if(data.error) throw new Error(data.error);

        lastDiffData = data;
        renderCommonResult(data);
        
        document.getElementById('statusCardsRow').style.display = 'flex';
        document.getElementById('prodStatusCol').className = 'col-md-6';
        document.getElementById('testStatusCol').style.display = 'block';
        
        updateStatus('prod', data.prod_status);
        updateStatus('test', data.test_status);
        
        const summary = {
            added: data.diff_result.filter(l => l.startsWith('+')).length,
            removed: data.diff_result.filter(l => l.startsWith('-')).length,
            total: data.diff_result.length
        };
        const summaryDiv = document.getElementById('diffSummary');
        if (summaryDiv) {
            summaryDiv.style.display = 'block';
            summaryDiv.innerHTML = `
                <div class="row text-center">
                    <div class="col-4 border-end"><div class="text-muted small">Added</div><div class="h5 mb-0 text-success fw-bold">${summary.added}</div></div>
                    <div class="col-4 border-end"><div class="text-muted small">Removed</div><div class="h5 mb-0 text-danger fw-bold">${summary.removed}</div></div>
                    <div class="col-4"><div class="text-muted small">Diff Lines</div><div class="h5 mb-0 text-primary fw-bold">${data.changes_only.length}</div></div>
                </div>
            `;
        }

        document.getElementById('diffModeContent').style.display = 'block';
        renderDiff();
    } catch (e) {
        alert("비교 실패: " + e.message);
    } finally {
        loadingEl.classList.add('d-none');
    }
}

export function renderDiff() {
    if(!lastDiffData) return;
    const diffOnlyToggle = document.getElementById('diffOnlyToggle');
    const showOnlyChanges = diffOnlyToggle ? diffOnlyToggle.checked : false;
    const diffLines = showOnlyChanges ? lastDiffData.changes_only : lastDiffData.diff_result;
    
    const viewer = document.getElementById('diffViewer');
    if (!viewer) return;
    viewer.innerHTML = diffLines.map(line => {
        let cls = '';
        if(line.startsWith('+')) cls = 'add';
        else if(line.startsWith('-')) cls = 'remove';
        else if(line.startsWith('?')) return '';
        
        return `<div class="diff-line ${cls}"><span class="diff-prefix">${line[0]}</span>${line.substring(2)}</div>`;
    }).join('');
}

export function copyFullReport() {
    if(!lastDiffData) return;
    const data = lastDiffData;
    const added = data.diff_result.filter(l => l.startsWith('+')).length;
    const removed = data.diff_result.filter(l => l.startsWith('-')).length;
    
    let report = `[PAC Comparison Report]\n`;
    report += `Your IP: ${data.client_ip || 'Unknown'}\n`;
    report += `Sample URL: ${data.sample_url}\n`;
    report += `Resolved IPs: ${data.resolved_ips.join(', ')}\n\n`;
    
    report += `[Validation Results]\n`;
    report += `- Production: ${data.prod_status.valid ? 'OK' : 'Error'} (${data.prod_status.proxy})\n`;
    report += `- Test (Proposed): ${data.test_status.valid ? 'OK' : 'Error'} (${data.test_status.proxy})\n`;
    report += `- Matching Result: ${data.prod_status.proxy === data.test_status.proxy ? 'SAME' : 'CHANGED'}\n\n`;
    
    report += `[Content Diff Summary]\n`;
    report += `- Lines Added: ${added}\n`;
    report += `- Lines Removed: ${removed}\n`;
    report += `- Total Changes: ${data.changes_only.length} lines\n\n`;
    
    report += `[Changes List]\n`;
    if (data.changes_only.length > 0) {
        report += data.changes_only.join('\n');
    } else {
        report += "No changes detected.";
    }
    
    copyTextToClipboard(report);
}

function updateStatus(type, status) {
    const card = document.getElementById(type + 'StatusCard');
    const validText = document.getElementById(type + 'ValidText');
    const proxyText = document.getElementById(type + 'ProxyResult');
    
    if (!card || !validText || !proxyText) return;

    if(status.valid) {
        card.className = 'p-3 rounded border h-100 border-success-subtle bg-success-subtle bg-opacity-10';
        validText.className = 'fw-bold text-success';
        validText.innerText = "Syntax OK";
        proxyText.innerHTML = `Result: ${status.proxy}`;
    } else {
        card.className = 'p-3 rounded border h-100 border-danger-subtle bg-danger-subtle bg-opacity-10';
        validText.className = 'fw-bold text-danger';
        validText.innerText = "Syntax Error";
        proxyText.innerText = status.error;
    }
}

export function searchInPac() {
    const searchInput = document.getElementById('pacSearchInput');
    if (!searchInput) return;
    const query = searchInput.value.toLowerCase();
    renderPacContent(lastPacContent, query);
}

function renderPacContent(content, filter = '') {
    if(!content) return;
    const lines = content.split('\n');
    const viewer = document.getElementById('pacViewer');
    if (!viewer) return;
    
    let html = '';
    lines.forEach((line, i) => {
        const lineNum = i + 1;
        const isMatch = filter && line.toLowerCase().includes(filter);
        if (filter && !isMatch) return;

        html += `
            <div class="pac-line ${isMatch ? 'match' : ''}">
                <span class="line-num">${lineNum}</span>
                <span class="line-content">${line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</span>
            </div>
        `;
    });
    viewer.innerHTML = html;
}
