// Server Management
let pacGroups = JSON.parse(localStorage.getItem('pacGroups') || '[]');
let selectedPacGroupIdx = null;

function updateGroupList() {
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
    
    // Hide quick load if empty
    const quickSelect = document.getElementById('pacQuickSelect');
    if (quickSelect) quickSelect.style.display = pacGroups.length > 0 ? 'flex' : 'none';
}

function savePacGroup() {
    const name = document.getElementById('groupName').value;
    const prod = document.getElementById('prodUrl').value;
    const test = document.getElementById('testUrl').value;
    if(!name || !prod || !test) return alert("모든 필드를 입력해주세요.");
    pacGroups.push({ name, prod, test });
    localStorage.setItem('pacGroups', JSON.stringify(pacGroups));
    updateGroupList();
    document.getElementById('groupName').value = '';
}

function selectPacGroup(i) {
    selectedPacGroupIdx = i;
    document.getElementById('prodUrl').value = pacGroups[i].prod;
    document.getElementById('testUrl').value = pacGroups[i].test;
    updateGroupList();
}

function deletePacGroup(i) {
    if (selectedPacGroupIdx === i) selectedPacGroupIdx = null;
    else if (selectedPacGroupIdx > i) selectedPacGroupIdx--;
    
    pacGroups.splice(i, 1);
    localStorage.setItem('pacGroups', JSON.stringify(pacGroups));
    updateGroupList();
}

// Initialize lists
window.addEventListener('DOMContentLoaded', updateGroupList);

let lastDiffData = null;

async function comparePac() {
    const prodUrl = document.getElementById('prodUrl').value;
    const testUrl = document.getElementById('testUrl').value;
    const sampleUrl = document.getElementById('diffSampleUrl').value;
    if(!prodUrl || !testUrl) return alert("URL을 입력해주세요.");

    document.getElementById('diffLoading').classList.remove('d-none');
    document.getElementById('diffResults').style.display = 'none';

    try {
        const response = await fetch('/api/diff-pac', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prod_url: prodUrl, test_url: testUrl, sample_url: sampleUrl })
        });
        const data = await response.json();
        if(data.error) throw new Error(data.error);

        lastDiffData = data;
        document.getElementById('diffResults').style.display = 'block';
        
        // Show resolution results
        const existingRes = document.getElementById('diffResolutionAlert');
        if(existingRes) existingRes.remove();

        if (data.resolved_ips && data.resolved_ips.length > 0) {
            const resDiv = document.createElement('div');
            resDiv.id = 'diffResolutionAlert';
            resDiv.className = 'border rounded p-3 small mb-4 bg-white shadow-sm';
            resDiv.innerHTML = `
                <div class="row g-2">
                    <div class="col-sm-3 text-muted">Client IP</div>
                    <div class="col-sm-9 fw-bold">${data.client_ip || 'Unknown'}</div>
                    <div class="col-12 border-top my-1"></div>
                    <div class="col-sm-3 text-muted">Target URL</div>
                    <div class="col-sm-9 font-monospace">${data.sample_url}</div>
                    <div class="col-12 border-top my-1"></div>
                    <div class="col-sm-3 text-muted">Resolved IPs</div>
                    <div class="col-sm-9 d-flex flex-wrap gap-1">
                        ${data.resolved_ips.map(ip => `<span class="badge bg-light text-dark border font-monospace fw-normal">${ip}</span>`).join('')}
                    </div>
                </div>`;
            const resContainer = document.getElementById('diffResults');
            resContainer.insertBefore(resDiv, resContainer.firstChild);
        }

        updateStatus('prod', data.prod_status);
        updateStatus('test', data.test_status);
        
        // Render Summary
        const summary = {
            added: data.diff_result.filter(l => l.startsWith('+')).length,
            removed: data.diff_result.filter(l => l.startsWith('-')).length,
            total: data.diff_result.length
        };
        const summaryDiv = document.getElementById('diffSummary');
        summaryDiv.style.display = 'block';
        summaryDiv.innerHTML = `
            <div class="row text-center">
                <div class="col-4 border-end"><div class="text-muted small">Added</div><div class="h5 mb-0 text-success fw-bold">${summary.added}</div></div>
                <div class="col-4 border-end"><div class="text-muted small">Removed</div><div class="h5 mb-0 text-danger fw-bold">${summary.removed}</div></div>
                <div class="col-4"><div class="text-muted small">Diff Lines</div><div class="h5 mb-0 text-primary fw-bold">${data.changes_only.length}</div></div>
            </div>
        `;

        renderDiff();

    } catch (e) {
        alert("비교 실패: " + e.message);
    } finally {
        document.getElementById('diffLoading').classList.add('d-none');
    }
}

function renderDiff() {
    if(!lastDiffData) return;
    const showOnlyChanges = document.getElementById('diffOnlyToggle').checked;
    const diffLines = showOnlyChanges ? lastDiffData.changes_only : lastDiffData.diff_result;
    
    const viewer = document.getElementById('diffViewer');
    viewer.innerHTML = diffLines.map(line => {
        let cls = '';
        if(line.startsWith('+')) cls = 'add';
        else if(line.startsWith('-')) cls = 'remove';
        else if(line.startsWith('?')) return ''; // Skip diff pointers
        
        return `<div class="diff-line ${cls}"><span class="diff-prefix">${line[0]}</span>${line.substring(2)}</div>`;
    }).join('');
}

function copyFullReport() {
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

// Global functions reused
function switchCategory(catId) {
    document.querySelectorAll('.main-nav .nav-link').forEach(el => el.classList.remove('active'));
    document.getElementById('cat-' + catId).classList.add('active');
    document.querySelectorAll('.sub-nav').forEach(el => el.classList.add('d-none'));
    const activeSubNav = document.getElementById('sub-' + catId);
    activeSubNav.classList.remove('d-none');
    const firstLink = activeSubNav.querySelector('.nav-link');
    if (firstLink) firstLink.click();
}

function showTool(toolId) {
    document.querySelectorAll('.sub-nav .nav-link').forEach(el => el.classList.remove('active'));
    const link = document.getElementById('tool-' + toolId);
    if(link) link.classList.add('active');
    document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
    const view = document.getElementById('view-' + toolId);
    if(view) view.classList.add('active');
}

async function transform(type, action) {
    const input = document.getElementById(`${type}Input`).value;
    if(!input) return;
    const response = await fetch(`/api/transform/${type}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ data: input, action: action }) });
    const result = await response.json();
    document.getElementById(`${type}Output`).value = result.result || result.error;
}

// Text Counter Listener
document.addEventListener('DOMContentLoaded', () => {
    const counterInput = document.getElementById('counterInput');
    if (counterInput) {
        counterInput.addEventListener('input', async function() {
            const response = await fetch('/api/analyze-text', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify({ 
                    text: this.value, 
                    encoding: document.getElementById('encodingSelect').value 
                }) 
            });
            const data = await response.json();
            document.getElementById('byteResult').innerText = data.bytes;
            document.getElementById('charCountResult').innerText = data.chars;
            if (data.details) {
                document.getElementById('detailResult').innerHTML = Object.entries(data.details).map(([k, v]) => `<span class="badge bg-white text-dark border fw-normal">${k}: ${v}</span>`).join('');
            }
        });
    }
});

function copyAnalysisReport() {
    const report = `[Text Analysis]\n- Bytes: ${document.getElementById('byteResult').innerText}\n- Chars: ${document.getElementById('charCountResult').innerText}\n- Details: ${Array.from(document.querySelectorAll('#detailResult span')).map(s=>s.innerText).join(', ')}`;
    copyTextToClipboard(report);
}

let unitMap = {};
window.addEventListener('load', async () => {
    try {
        const resp = await fetch('/api/units');
        unitMap = await resp.json();
        loadUnits();
    } catch (e) {
        console.error("Failed to load units", e);
    }
});

function loadUnits() {
    const unitCategory = document.getElementById('unitCategory');
    if (!unitCategory) return;
    const cat = unitCategory.value;
    const units = unitMap[cat] || [];
    const leftSelect = document.getElementById('leftUnit');
    const rightSelect = document.getElementById('rightUnit');
    if (!leftSelect || !rightSelect) return;
    
    leftSelect.innerHTML = rightSelect.innerHTML = '';
    units.forEach((u, i) => {
        leftSelect.innerHTML += `<option value="${u}" ${i===0?'selected':''}>${u}</option>`;
        rightSelect.innerHTML += `<option value="${u}" ${i===1?'selected':''}>${u}</option>`;
    });
    if(units.length > 0) doConvert('left');
}

async function doConvert(direction) {
    const cat = document.getElementById('unitCategory').value;
    const val = document.getElementById(direction === 'left' ? 'leftVal' : 'rightVal').value;
    const fromUnit = document.getElementById(direction === 'left' ? 'leftUnit' : 'rightUnit').value;
    const toUnit = document.getElementById(direction === 'left' ? 'rightUnit' : 'leftUnit').value;
    if (val === '') return;
    const response = await fetch('/api/convert', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: cat, value: parseFloat(val), from_unit: fromUnit, to_unit: toUnit }) });
    const data = await response.json();
    document.getElementById(direction === 'left' ? 'rightVal' : 'leftVal').value = data.result;
    document.getElementById('unitFormula').innerText = data.formula || "";
}

async function beautifyJson() {
    const input = document.getElementById('jsonInput').value;
    const response = await fetch('/api/beautify-json', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ data: input }) });
    const result = await response.json();
    document.getElementById('jsonOutput').value = result.formatted || result.error;
}

async function uploadHar() {
    const file = document.getElementById('harFile').files[0];
    if(!file) return;
    const formData = new FormData(); formData.append('file', file);
    const response = await fetch('/api/extract-har', { method: 'POST', body: formData });
    const data = await response.json();
    const resultsBody = document.getElementById('harResults');
    resultsBody.innerHTML = '';
    if(data.results) {
        document.getElementById('harTableContainer').style.display = 'block';
        data.results.forEach(item => {
            resultsBody.innerHTML += `<tr><td><span class="badge bg-light text-dark border">${item.method}</span></td><td class="text-truncate" style="max-width:200px;">${item.url}</td><td class="text-truncate" style="max-width:150px;">${item.headers.Authorization}</td></tr>`;
        });
    }
}

let lastSearchPos = 0;
function searchInPac(event) {
    if (event && event.key !== 'Enter') return;
    
    const textarea = document.getElementById('pacPreview');
    const query = document.getElementById('pacSearchInput').value.toLowerCase();
    if (!query) return;

    const text = textarea.value.toLowerCase();
    let pos = text.indexOf(query, lastSearchPos + 1);
    
    if (pos === -1) {
        pos = text.indexOf(query); // Wrap around
    }

    if (pos !== -1) {
        textarea.focus();
        textarea.setSelectionRange(pos, pos + query.length);
        
        // Scroll to position (heuristic)
        const lineNum = text.substr(0, pos).split('\n').length;
        textarea.scrollTop = (lineNum - 3) * 18; 
        
        lastSearchPos = pos;
    } else {
        alert("검색 결과가 없습니다.");
        lastSearchPos = 0;
    }
}

async function testPac() {
    const pacUrl = document.getElementById('pacUrl').value;
    const targetUrl = document.getElementById('targetUrl').value;
    if(!pacUrl || !targetUrl) return;
    const response = await fetch('/api/test-pac', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pac_url: pacUrl, target_url: targetUrl }) });
    const data = await response.json();
    document.getElementById('pacResultBox').style.display = 'block';
    if(data.error) {
        document.getElementById('pacResultText').innerText = "Error";
        document.getElementById('pacResolvedIp').innerHTML = "-";
        document.getElementById('pacMyIp').innerText = "-";
        document.getElementById('pacPreview').value = data.error;
    } else {
        const ipContainer = document.getElementById('pacResolvedIp');
        if (data.resolved_ips && data.resolved_ips.length > 0) {
            ipContainer.innerHTML = data.resolved_ips.map(ip => 
                `<span class="badge bg-white text-dark border font-monospace" style="font-weight:500">${ip}</span>`
            ).join('');
        } else {
            ipContainer.innerHTML = '<span class="text-danger small">Failed to resolve</span>';
        }
        
        document.getElementById('pacMyIp').innerText = data.client_ip || "Unknown";
        document.getElementById('pacResultText').innerText = data.result;
        document.getElementById('pacPreview').value = data.pac_preview;
        lastSearchPos = 0;
    }
}

function copyToClipboard(id) { copyTextToClipboard(document.getElementById(id).value); }
function copyTextToClipboard(text) {
    if (!text) return;
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => alert("복사되었습니다."));
    } else {
        const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select(); document.execCommand("copy"); document.body.removeChild(ta); alert("복사되었습니다.");
    }
}
