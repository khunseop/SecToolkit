import { fetchPaloAltoDefaults, postPaloAltoDefaults, postPaloAltoGenerateBulk, postPaloAltoGenerateBulkExcel, postPaloAltoGenerateServiceBulk } from './api.js';
import { copyTextToClipboard } from './ui.js';

const GRID_FIELDS = [
    'action', 'vsys', 'rule_name', 'disabled', 'rule_action',
    'from_zone', 'source', 'source_user', 'to_zone', 'destination',
    'service', 'application', 'description', 'log_end', 'log_setting',
    'move_position', 'anchor_rule'
];

// Fields that come from the shared "defaults" (saved via savePaDefaults / prefilled on new rows)
const DEFAULT_FIELDS = [
    'vsys', 'disabled', 'rule_action', 'from_zone', 'source', 'source_user',
    'to_zone', 'destination', 'service', 'application', 'description', 'log_end', 'log_setting'
];

let cachedDefaults = null;

function readGridRow(rowEl) {
    const row = {};
    for (const field of GRID_FIELDS) {
        const el = rowEl.querySelector(`.pa-grid-${field}`);
        if (!el) continue;
        row[field] = el.type === 'checkbox' ? el.checked : el.value.trim();
    }
    // delete 행은 별도 "필드 select + 값" UI를 쓰므로, 선택된 필드 하나에만 값을 채운다.
    if (row.action === 'delete') {
        const fieldName = rowEl.querySelector('.pa-delete-field').value;
        const value = rowEl.querySelector('.pa-delete-value').value.trim();
        for (const [name] of LIST_FIELD_DEFS) row[name] = '';
        if (fieldName && value) row[fieldName] = value;
    }
    return row;
}

const LIST_FIELD_DEFS = [
    ['from_zone'], ['source'], ['source_user'], ['to_zone'],
    ['destination'], ['service'], ['application']
];

function applyRowFields(rowEl, values) {
    if (!values) return;
    for (const field of DEFAULT_FIELDS) {
        const el = rowEl.querySelector(`.pa-grid-${field}`);
        if (!el || values[field] === undefined) continue;
        if (el.type === 'checkbox') {
            el.checked = !!values[field];
        } else {
            el.value = values[field] || '';
        }
    }
}

function updateRowVisibility(rowEl) {
    const action = rowEl.querySelector('.pa-grid-action').value;
    rowEl.querySelector('.pa-fields-set').style.display = action === 'set' ? '' : 'none';
    rowEl.querySelector('.pa-fields-delete').style.display = action === 'delete' ? '' : 'none';
    rowEl.querySelector('.pa-fields-move').style.display = action === 'move' ? '' : 'none';
}

function updateAnchorVisibility(rowEl) {
    const pos = rowEl.querySelector('.pa-grid-move_position').value;
    const anchorField = rowEl.querySelector('.pa-anchor-field');
    anchorField.style.display = (pos === 'before' || pos === 'after') ? '' : 'none';
}

function wireRow(rowEl) {
    rowEl.querySelector('.pa-grid-action').addEventListener('change', () => updateRowVisibility(rowEl));
    rowEl.querySelector('.pa-grid-move_position').addEventListener('change', () => updateAnchorVisibility(rowEl));
    rowEl.querySelector('.pa-delete-field').addEventListener('change', (e) => {
        const valueInput = rowEl.querySelector('.pa-delete-value');
        valueInput.disabled = !e.target.value;
        if (valueInput.disabled) valueInput.value = '';
    });
    rowEl.querySelector('.pa-row-dup').addEventListener('click', () => duplicateRow(rowEl));
    rowEl.querySelector('.pa-row-del').addEventListener('click', () => rowEl.remove());
    updateRowVisibility(rowEl);
    updateAnchorVisibility(rowEl);
}

function cloneRowValues(sourceRow, targetRow) {
    for (const field of GRID_FIELDS) {
        const src = sourceRow.querySelector(`.pa-grid-${field}`);
        const dst = targetRow.querySelector(`.pa-grid-${field}`);
        if (!src || !dst) continue;
        if (src.type === 'checkbox') dst.checked = src.checked;
        else dst.value = src.value;
    }
    const srcDeleteField = sourceRow.querySelector('.pa-delete-field');
    const dstDeleteField = targetRow.querySelector('.pa-delete-field');
    dstDeleteField.value = srcDeleteField.value;
    const srcDeleteValue = sourceRow.querySelector('.pa-delete-value');
    const dstDeleteValue = targetRow.querySelector('.pa-delete-value');
    dstDeleteValue.disabled = srcDeleteValue.disabled;
    dstDeleteValue.value = srcDeleteValue.value;
    updateRowVisibility(targetRow);
    updateAnchorVisibility(targetRow);
}

function duplicateRow(rowEl) {
    const template = document.getElementById('paGridRowTemplate');
    const newRow = template.content.firstElementChild.cloneNode(true);
    wireRow(newRow);
    cloneRowValues(rowEl, newRow);
    rowEl.after(newRow);
}

function renderBulkResults(results, containerId = 'paBulkResultList') {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    if (results.length === 0) return;
    for (const r of results) {
        const isError = !!r.error;
        const item = document.createElement('div');
        item.className = `pa-result-row px-2 py-1 rounded mb-1 ${isError ? 'pa-result-error' : 'pa-result-ok'}`;

        const line = document.createElement('div');
        line.className = 'd-flex align-items-center gap-2';

        const badge = document.createElement('span');
        badge.className = `badge ${isError ? 'bg-danger' : 'bg-success'}`;
        badge.textContent = isError ? '에러' : '성공';

        const rowNum = document.createElement('span');
        rowNum.className = 'small text-muted';
        rowNum.style.width = '2.5rem';
        rowNum.style.flexShrink = '0';
        rowNum.textContent = `#${r.row_index + 1}`;

        const text = document.createElement('code');
        text.className = 'flex-grow-1 text-break font-monospace';
        text.textContent = isError ? r.error : r.command;

        const copyBtn = document.createElement('button');
        copyBtn.type = 'button';
        copyBtn.className = 'btn btn-sm btn-outline-secondary';
        copyBtn.textContent = '복사';
        copyBtn.disabled = isError;
        copyBtn.addEventListener('click', () => copyTextToClipboard(r.command));

        line.append(badge, rowNum, text, copyBtn);
        item.appendChild(line);

        // 필드별 객체 개수를 보여줘서, 여러 행이 콤마로 잘 병합됐는지 눈으로 검증할 수 있게 한다
        const countEntries = r.counts ? Object.entries(r.counts) : [];
        if (!isError && countEntries.length > 0) {
            const countsLine = document.createElement('div');
            countsLine.className = 'small text-muted';
            countsLine.style.marginLeft = '2.5rem';
            countsLine.textContent = countEntries.map(([field, count]) => `${field} ${count}개`).join(' · ');
            item.appendChild(countsLine);
        }

        container.appendChild(item);
    }
}

export function addGridRow() {
    const template = document.getElementById('paGridRowTemplate');
    const row = template.content.firstElementChild.cloneNode(true);
    wireRow(row);
    document.getElementById('paGridBody').appendChild(row);
    applyRowFields(row, cachedDefaults);
}

function clearRowInvalid() {
    document.querySelectorAll('#paGridBody .pa-row-invalid').forEach(el => el.classList.remove('pa-row-invalid'));
}

export async function generateBulkFromGrid() {
    clearRowInvalid();
    const rowEls = Array.from(document.querySelectorAll('#paGridBody .pa-row'));
    const invalidRows = rowEls.filter(el => !el.querySelector('.pa-grid-rule_name').value.trim());
    if (invalidRows.length > 0) {
        invalidRows.forEach(el => el.classList.add('pa-row-invalid'));
        invalidRows[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
        alert('rule_name이 비어 있는 행이 있습니다 (빨간 테두리로 표시됨).');
        return;
    }
    const rows = rowEls.map(readGridRow);
    if (rows.length === 0) {
        alert('최소 1개 이상의 행을 입력하세요.');
        return;
    }
    const result = await postPaloAltoGenerateBulk(rows);
    if (result.error) {
        renderBulkResults([{ row_index: 0, error: result.error }]);
        return;
    }
    renderBulkResults(result.results);
}

export async function uploadExcelAndGenerate() {
    const fileInput = document.getElementById('paExcelFile');
    const file = fileInput.files[0];
    if (!file) {
        alert('업로드할 엑셀 파일을 선택하세요.');
        return;
    }
    renderBulkResults([{ row_index: 0, error: '업로드 및 처리 중...' }]);
    const result = await postPaloAltoGenerateBulkExcel(file);
    if (result.error) {
        renderBulkResults([{ row_index: 0, error: result.error }]);
        return;
    }
    renderBulkResults(result.results);
}

export async function savePaDefaults() {
    const firstRow = document.querySelector('#paGridBody .pa-row');
    if (!firstRow) return;
    const values = readGridRow(firstRow);
    const defaults = {};
    for (const field of DEFAULT_FIELDS) {
        defaults[field] = values[field];
    }
    const result = await postPaloAltoDefaults(defaults);
    if (result.success) {
        cachedDefaults = defaults;
        alert('1행의 값이 기본값으로 저장되었습니다. 새로 추가되는 행에 자동으로 채워집니다.');
    } else {
        alert('기본값 저장에 실패했습니다.');
    }
}

export function applyDefaultsToAllRows() {
    if (!cachedDefaults) {
        alert('저장된 기본값이 없습니다. 먼저 "1행 값을 기본값으로 저장"을 눌러주세요.');
        return;
    }
    document.querySelectorAll('#paGridBody .pa-row').forEach(row => applyRowFields(row, cachedDefaults));
}

export function copyAllPaResults() {
    const commands = Array.from(document.querySelectorAll('#paBulkResultList .pa-result-ok code'))
        .map(el => el.textContent);
    if (commands.length === 0) {
        alert('복사할 성공 결과가 없습니다.');
        return;
    }
    copyTextToClipboard(commands.join('\n'));
}

// --- Service Object 생성 ---

const SERVICE_FIELDS = ['vsys', 'name', 'protocol', 'port'];

function readServiceRow(rowEl) {
    const row = {};
    for (const field of SERVICE_FIELDS) {
        const el = rowEl.querySelector(`.pa-svc-${field}`);
        if (!el) continue;
        row[field] = el.value.trim();
    }
    return row;
}

function wireServiceRow(rowEl) {
    rowEl.querySelector('.pa-row-dup').addEventListener('click', () => duplicateServiceRow(rowEl));
    rowEl.querySelector('.pa-row-del').addEventListener('click', () => rowEl.remove());
}

function duplicateServiceRow(rowEl) {
    const newRow = addServiceRow();
    for (const field of SERVICE_FIELDS) {
        const src = rowEl.querySelector(`.pa-svc-${field}`);
        const dst = newRow.querySelector(`.pa-svc-${field}`);
        if (src && dst) dst.value = src.value;
    }
    rowEl.after(newRow);
}

export function addServiceRow() {
    const template = document.getElementById('paServiceRowTemplate');
    const row = template.content.firstElementChild.cloneNode(true);
    wireServiceRow(row);
    document.getElementById('paServiceGridBody').appendChild(row);
    return row;
}

// 엑셀에서 여러 행을 복사해 붙여넣으면(탭으로 구분) 한 줄씩 행으로 추가한다.
// 3칸이면 name/protocol/port, 4칸이면 vsys/name/protocol/port로 인식한다.
export function fillServiceRowsFromPaste() {
    const textarea = document.getElementById('paServicePasteArea');
    const lines = textarea.value.split(/\r?\n/).map(line => line.trim()).filter(line => line);
    if (lines.length === 0) {
        alert('붙여넣은 내용이 없습니다.');
        return;
    }
    for (const line of lines) {
        const cells = (line.includes('\t') ? line.split('\t') : line.split(',')).map(c => c.trim());
        const [vsys, name, protocol, port] = cells.length >= 4
            ? cells
            : ['', cells[0] || '', cells[1] || '', cells[2] || ''];

        const row = addServiceRow();
        row.querySelector('.pa-svc-vsys').value = vsys;
        row.querySelector('.pa-svc-name').value = name;
        row.querySelector('.pa-svc-protocol').value = ['tcp', 'udp'].includes((protocol || '').toLowerCase()) ? protocol.toLowerCase() : 'tcp';
        row.querySelector('.pa-svc-port').value = port;
    }
    textarea.value = '';
}

export async function generateServiceBulk() {
    document.querySelectorAll('#paServiceGridBody .pa-row-invalid').forEach(el => el.classList.remove('pa-row-invalid'));
    const rowEls = Array.from(document.querySelectorAll('#paServiceGridBody .pa-row'));
    const invalidRows = rowEls.filter(el => !el.querySelector('.pa-svc-name').value.trim() || !el.querySelector('.pa-svc-port').value.trim());
    if (invalidRows.length > 0) {
        invalidRows.forEach(el => el.classList.add('pa-row-invalid'));
        invalidRows[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
        alert('name 또는 port가 비어 있는 행이 있습니다 (빨간 테두리로 표시됨).');
        return;
    }
    const rows = rowEls.map(readServiceRow);
    if (rows.length === 0) {
        alert('최소 1개 이상의 행을 입력하세요.');
        return;
    }
    const result = await postPaloAltoGenerateServiceBulk(rows);
    if (result.error) {
        renderBulkResults([{ row_index: 0, error: result.error }], 'paServiceResultList');
        return;
    }
    renderBulkResults(result.results, 'paServiceResultList');
}

export function copyAllServiceResults() {
    const commands = Array.from(document.querySelectorAll('#paServiceResultList .pa-result-ok code'))
        .map(el => el.textContent);
    if (commands.length === 0) {
        alert('복사할 성공 결과가 없습니다.');
        return;
    }
    copyTextToClipboard(commands.join('\n'));
}

export async function initPaloAlto() {
    cachedDefaults = await fetchPaloAltoDefaults();
    addGridRow();
    addServiceRow();
}
