import { fetchPaloAltoDefaults, postPaloAltoDefaults, postPaloAltoGenerateBulk, postPaloAltoGenerateBulkExcel } from './api.js';

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
    return row;
}

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

function renderBulkResults(results) {
    const lines = results.map(r => {
        if (r.error) return `# ERROR (row ${r.row_index + 1}): ${r.error}`;
        return r.command;
    });
    document.getElementById('paBulkResult').value = lines.join('\n');
}

export function addGridRow() {
    const template = document.getElementById('paGridRowTemplate');
    const row = template.content.firstElementChild.cloneNode(true);
    document.getElementById('paGridBody').appendChild(row);
    applyRowFields(row, cachedDefaults);
}

export async function generateBulkFromGrid() {
    const rowEls = document.querySelectorAll('#paGridBody tr');
    const rows = Array.from(rowEls).map(readGridRow).filter(r => r.rule_name);
    if (rows.length === 0) {
        alert('최소 1개 이상의 rule_name을 입력하세요.');
        return;
    }
    const result = await postPaloAltoGenerateBulk(rows);
    if (result.error) {
        document.getElementById('paBulkResult').value = `Error: ${result.error}`;
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
    document.getElementById('paBulkResult').value = '업로드 및 처리 중...';
    const result = await postPaloAltoGenerateBulkExcel(file);
    if (result.error) {
        document.getElementById('paBulkResult').value = `Error: ${result.error}`;
        return;
    }
    renderBulkResults(result.results);
}

export async function savePaDefaults() {
    const firstRow = document.querySelector('#paGridBody tr');
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

export async function initPaloAlto() {
    cachedDefaults = await fetchPaloAltoDefaults();
    addGridRow();
}
