import { fetchUnits, postConvert, postBeautifyJson, postIpIntersect, postIpSummarize } from './api.js';

let unitMap = {};

export async function initAnalyzer() {
    try {
        unitMap = await fetchUnits();
        loadUnits();
        initIpTools();
    } catch (e) {
        console.error("Failed to load units", e);
    }
}

export function loadUnits() {
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

export async function doConvert(direction) {
    const catEl = document.getElementById('unitCategory');
    const leftValEl = document.getElementById('leftVal');
    const rightValEl = document.getElementById('rightVal');
    const leftUnitEl = document.getElementById('leftUnit');
    const rightUnitEl = document.getElementById('rightUnit');
    const formulaEl = document.getElementById('unitFormula');
    
    if (!catEl || !leftValEl || !rightValEl || !leftUnitEl || !rightUnitEl) return;

    const cat = catEl.value;
    const val = (direction === 'left' ? leftValEl : rightValEl).value;
    const fromUnit = (direction === 'left' ? leftUnitEl : rightUnitEl).value;
    const toUnit = (direction === 'left' ? rightUnitEl : leftUnitEl).value;
    
    if (val === '') return;
    
    const data = await postConvert(cat, parseFloat(val), fromUnit, toUnit);
    (direction === 'left' ? rightValEl : leftValEl).value = data.result;
    if (formulaEl) formulaEl.innerText = data.formula || "";
}

export async function beautifyJson() {
    const inputEl = document.getElementById('jsonInput');
    const outputEl = document.getElementById('jsonOutput');
    if (!inputEl || !outputEl) return;

    const input = inputEl.value;
    const result = await postBeautifyJson(input);
    outputEl.value = result.formatted || result.error;
}

export async function uploadHar() {
    const harFileEl = document.getElementById('harFile');
    if(!harFileEl || !harFileEl.files[0]) return;
    
    const file = harFileEl.files[0];
    const formData = new FormData(); 
    formData.append('file', file);
    
    const response = await fetch('/api/extract-har', { method: 'POST', body: formData });
    const data = await response.json();
    
    const resultsBody = document.getElementById('harResults');
    const tableContainer = document.getElementById('harTableContainer');
    
    if (!resultsBody || !tableContainer) return;
    
    resultsBody.innerHTML = '';
    if(data.results) {
        tableContainer.style.display = 'block';
        data.results.forEach(item => {
            resultsBody.innerHTML += `<tr><td><span class="badge bg-light text-dark border">${item.method}</span></td><td class="text-truncate" style="max-width:200px;">${item.url}</td><td class="text-truncate" style="max-width:150px;">${item.headers.Authorization}</td></tr>`;
        });
    }
}

export async function findIpIntersections() {
    const listA = document.getElementById('intersectInputA').value;
    const listB = document.getElementById('intersectInputB').value;
    
    if(!listA || !listB) {
        alert("Set A와 Set B를 모두 입력해 주세요.");
        return;
    }
    
    const resultsDiv = document.getElementById('intersectResults');
    resultsDiv.innerHTML = '<div class="text-center py-5"><div class="spinner-border spinner-border-sm text-primary"></div><br><small class="text-muted">비교 중...</small></div>';
    
    try {
        const data = await postIpIntersect(listA, listB);
        const matches = data.matches || [];
        
        document.getElementById('intersectCount').innerText = `${matches.length} matches`;
        
        if (matches.length === 0) {
            resultsDiv.innerHTML = '<div class="text-center text-muted py-5 mt-5"><small>겹치는 대역이 없습니다.</small></div>';
            document.getElementById('intersectResultsText').value = "";
            document.getElementById('btnCopyIntersect').disabled = true;
            return;
        }
        
        let html = '';
        let textResults = '';
        
        matches.forEach(m => {
            html += `
                <div class="card mb-2 border-0 shadow-sm">
                    <div class="card-body p-2 small">
                        <div class="fw-bold text-primary mb-1">${m.overlap}</div>
                        <div class="text-muted" style="font-size: 0.75rem;">
                            <span class="badge bg-light text-dark border-0">A</span> ${m.source_a}<br>
                            <span class="badge bg-light text-dark border-0">B</span> ${m.source_b}
                        </div>
                    </div>
                </div>
            `;
            textResults += `[Match] Overlap: ${m.overlap} (A: ${m.source_a}, B: ${m.source_b})\n`;
        });
        
        resultsDiv.innerHTML = html;
        document.getElementById('intersectResultsText').value = textResults;
        document.getElementById('btnCopyIntersect').disabled = false;
        
    } catch (error) {
        resultsDiv.innerHTML = `<div class="alert alert-danger small p-2">Error: ${error.message}</div>`;
    }
}

export async function summarizeIps() {
    const inputEl = document.getElementById('summarizeInput');
    const classC = document.getElementById('summarizeClassC').checked;
    const ipList = inputEl.value;

    if (!ipList.trim()) {
        alert("IP 목록을 입력해 주세요.");
        return;
    }

    const resultsDiv = document.getElementById('summarizeResults');
    const errorsDiv = document.getElementById('summarizeErrors');
    resultsDiv.innerHTML = '<div class="text-center py-5"><div class="spinner-border spinner-border-sm text-primary"></div><br><small class="text-muted">축약 중...</small></div>';
    errorsDiv.classList.add('d-none');

    try {
        const data = await postIpSummarize(ipList, classC);
        const results = data.results || [];
        const errors = data.errors || [];

        document.getElementById('summarizeResultCount').innerText = `${results.length} blocks`;

        if (results.length === 0) {
            resultsDiv.innerHTML = '<div class="text-center text-muted py-5 mt-5"><small>축약할 수 있는 유효한 IP가 없습니다.</small></div>';
            document.getElementById('summarizeResultsText').value = "";
            document.getElementById('btnCopySummarize').disabled = true;
        } else {
            let html = '';
            let textResults = '';

            results.forEach(r => {
                html += `
                    <div class="card mb-2 border-0 shadow-sm">
                        <div class="card-body p-2 small">
                            <div class="fw-bold text-primary mb-1">${r.cidr}</div>
                            <div class="text-muted" style="font-size: 0.75rem;">${r.netmask}</div>
                        </div>
                    </div>
                `;
                textResults += `${r.cidr} (${r.netmask})\n`;
            });

            resultsDiv.innerHTML = html;
            document.getElementById('summarizeResultsText').value = textResults;
            document.getElementById('btnCopySummarize').disabled = false;
        }

        if (errors.length > 0) {
            document.getElementById('summarizeErrorList').innerText = errors.join('\n');
            errorsDiv.classList.remove('d-none');
        }

    } catch (error) {
        resultsDiv.innerHTML = `<div class="alert alert-danger small p-2">Error: ${error.message}</div>`;
    }
}

export function initIpTools() {
    const inputs = ['intersectInputA', 'intersectInputB'];
    inputs.forEach(id => {
        const el = document.getElementById(id);
        const badge = document.getElementById(id === 'intersectInputA' ? 'countA' : 'countB');
        if (el && badge) {
            el.addEventListener('input', () => {
                const lines = el.value.split('\n').filter(l => l.trim()).length;
                badge.innerText = `${lines} lines`;
            });
        }
    });

    const summarizeInput = document.getElementById('summarizeInput');
    const summarizeBadge = document.getElementById('summarizeCount');
    if (summarizeInput && summarizeBadge) {
        summarizeInput.addEventListener('input', () => {
            const lines = summarizeInput.value.split('\n').filter(l => l.trim()).length;
            summarizeBadge.innerText = `${lines} lines`;
        });
    }
}
