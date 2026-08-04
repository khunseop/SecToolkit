import { postPaloAltoGenerate, fetchPaloAltoDefaults, postPaloAltoDefaults, postPaloAltoGenerateBulk, postPaloAltoGenerateBulkExcel } from './api.js';

const GRID_FIELDS = [
    'action', 'vsys', 'rule_name', 'disabled', 'rule_action',
    'from_zone', 'source', 'source_user', 'to_zone', 'destination',
    'service', 'application', 'description', 'log_end', 'log_setting',
    'move_position', 'anchor_rule'
];

function getOptionFields() {
    return {
        vsys: document.getElementById('paVsys').value.trim(),
        disabled: document.getElementById('paDisabled').checked,
        rule_action: document.getElementById('paRuleAction').value,
        from_zone: document.getElementById('paFromZone').value,
        source: document.getElementById('paSource').value,
        source_user: document.getElementById('paSourceUser').value,
        to_zone: document.getElementById('paToZone').value,
        destination: document.getElementById('paDestination').value,
        service: document.getElementById('paService').value,
        application: document.getElementById('paApplication').value,
        description: document.getElementById('paDescription').value,
        log_end: document.getElementById('paLogEnd').value,
        log_setting: document.getElementById('paLogSetting').value
    };
}

function applyOptionFields(defaults) {
    if (!defaults) return;
    document.getElementById('paVsys').value = defaults.vsys || '';
    document.getElementById('paDisabled').checked = !!defaults.disabled;
    document.getElementById('paRuleAction').value = defaults.rule_action || 'allow';
    document.getElementById('paFromZone').value = defaults.from_zone || '';
    document.getElementById('paSource').value = defaults.source || '';
    document.getElementById('paSourceUser').value = defaults.source_user || '';
    document.getElementById('paToZone').value = defaults.to_zone || '';
    document.getElementById('paDestination').value = defaults.destination || '';
    document.getElementById('paService').value = defaults.service || '';
    document.getElementById('paApplication').value = defaults.application || '';
    document.getElementById('paDescription').value = defaults.description || '';
    document.getElementById('paLogEnd').value = defaults.log_end || '';
    document.getElementById('paLogSetting').value = defaults.log_setting || '';
}

export function updatePaFormVisibility() {
    const action = document.getElementById('paAction').value;
    document.getElementById('paCreateFields').classList.toggle('d-none', action !== 'create' && action !== 'modify');
    document.getElementById('paSaveDefaultsBtn').classList.toggle('d-none', action !== 'create' && action !== 'modify');
    document.getElementById('paMoveFields').classList.toggle('d-none', action !== 'move');

    if (action === 'move') {
        const position = document.getElementById('paMovePosition').value;
        document.getElementById('paAnchorField').classList.toggle('d-none', position !== 'before' && position !== 'after');
    }
}

export async function generatePaCommand() {
    const payload = {
        action: document.getElementById('paAction').value,
        rule_name: document.getElementById('paRuleName').value.trim(),
        move_position: document.getElementById('paMovePosition').value,
        anchor_rule: document.getElementById('paAnchorRule').value.trim(),
        ...getOptionFields()
    };

    const result = await postPaloAltoGenerate(payload);
    const resultEl = document.getElementById('paResult');
    if (result.error) {
        resultEl.value = `Error: ${result.error}`;
        return;
    }
    resultEl.value = result.command || '';
}

export async function savePaDefaults() {
    const defaults = getOptionFields();
    const result = await postPaloAltoDefaults(defaults);
    if (result.success) {
        alert('기본값이 저장되었습니다.');
    } else {
        alert('기본값 저장에 실패했습니다.');
    }
}

export async function initPaloAlto() {
    const defaults = await fetchPaloAltoDefaults();
    applyOptionFields(defaults);
    updatePaFormVisibility();
    addGridRow();
}

export function addGridRow() {
    const template = document.getElementById('paGridRowTemplate');
    const row = template.content.firstElementChild.cloneNode(true);
    document.getElementById('paGridBody').appendChild(row);
}

function readGridRow(rowEl) {
    const row = {};
    for (const field of GRID_FIELDS) {
        const el = rowEl.querySelector(`.pa-grid-${field}`);
        if (!el) continue;
        row[field] = el.type === 'checkbox' ? el.checked : el.value.trim();
    }
    return row;
}

function renderBulkResults(results) {
    const lines = results.map(r => {
        if (r.error) return `# ERROR (row ${r.row_index + 1}): ${r.error}`;
        return r.command;
    });
    document.getElementById('paBulkResult').value = lines.join('\n');
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
