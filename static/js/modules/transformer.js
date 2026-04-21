import { postTransform, postAnalyzeText } from './api.js';
import { copyTextToClipboard } from './ui.js';

export async function transform(type, action) {
    const input = document.getElementById(`${type}Input`).value;
    if(!input) return;
    const result = await postTransform(type, input, action);
    document.getElementById(`${type}Output`).value = result.result || result.error;
}

export function copyAnalysisReport() {
    const byteEl = document.getElementById('byteResult');
    const charEl = document.getElementById('charCountResult');
    const detailEl = document.getElementById('detailResult');
    
    if (!byteEl || !charEl || !detailEl) return;
    
    const report = `[Text Analysis]\n- Bytes: ${byteEl.innerText}\n- Chars: ${charEl.innerText}\n- Details: ${Array.from(detailEl.querySelectorAll('span')).map(s=>s.innerText).join(', ')}`;
    copyTextToClipboard(report);
}

export function initTextCounter() {
    const counterInput = document.getElementById('counterInput');
    if (counterInput) {
        counterInput.addEventListener('input', async function() {
            const data = await postAnalyzeText(this.value, document.getElementById('encodingSelect').value);
            document.getElementById('byteResult').innerText = data.bytes;
            document.getElementById('charCountResult').innerText = data.chars;
            if (data.details) {
                document.getElementById('detailResult').innerHTML = Object.entries(data.details).map(([k, v]) => `<span class="badge bg-white text-dark border fw-normal">${k}: ${v}</span>`).join('');
            }
        });
    }
}
