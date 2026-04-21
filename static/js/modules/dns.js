import { postDnsLookup, fetchSystemDns } from './api.js';

export async function doDnsLookup() {
    const hostInput = document.getElementById('dnsHostInput');
    const host = hostInput.value.trim();
    if (!host) return;

    const resDiv = document.getElementById('dnsResult');
    const resHost = document.getElementById('dnsResultHost');
    const resIps = document.getElementById('dnsResultIps');
    const resReverse = document.getElementById('dnsResultReverse');

    resDiv.classList.remove('d-none');
    resHost.innerText = 'Searching...';
    resIps.innerText = '';
    resReverse.innerText = '';

    try {
        const data = await postDnsLookup(host);
        if (data.error) {
            resHost.innerHTML = `<span class="text-danger">Error: ${data.error}</span>`;
        } else {
            resHost.innerText = data.host;
            resIps.innerText = data.ips && data.ips.length > 0 ? data.ips.join(', ') : 'None';
            resReverse.innerText = data.reverse_name || '-';
        }
    } catch (err) {
        resHost.innerText = 'Lookup failed.';
    }
}

export async function refreshDnsInfo() {
    const rawDisplay = document.getElementById('sysDnsRaw');
    const formattedDisplay = document.getElementById('sysDnsFormatted');
    
    if (rawDisplay) rawDisplay.innerText = 'Fetching...';
    if (formattedDisplay) formattedDisplay.innerHTML = '<div class="col-12 text-muted small">Fetching...</div>';

    try {
        const data = await fetchSystemDns();
        if (rawDisplay) rawDisplay.innerText = data.raw || "No info";
        
        if (formattedDisplay) {
            if (data.settings && Object.keys(data.settings).length > 0) {
                formattedDisplay.innerHTML = Object.entries(data.settings).map(([alias, servers]) => `
                    <div class="col-md-6">
                        <div class="p-3 border rounded h-100 bg-white shadow-sm">
                            <small class="text-muted d-block mb-2 fw-bold text-uppercase" style="font-size: 0.65rem;">${alias}</small>
                            <div class="fw-bold font-monospace text-primary" style="font-size: 0.95rem;">${servers}</div>
                        </div>
                    </div>
                `).join('');
            } else {
                formattedDisplay.innerHTML = `<div class="col-12"><div class="alert alert-info py-2 small mb-0">No active DNS server settings found. Please check Raw Output.</div></div>`;
            }
        }
    } catch (e) {
        if (rawDisplay) rawDisplay.innerText = 'Failed to fetch DNS settings';
    }
}

export function initDns() {
    refreshDnsInfo();
}
