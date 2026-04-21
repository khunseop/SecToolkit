import { fetchUnits, postConvert, postBeautifyJson } from './api.js';

let unitMap = {};

export async function initAnalyzer() {
    try {
        unitMap = await fetchUnits();
        loadUnits();
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
