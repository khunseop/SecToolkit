import { fetchPublicIp, fetchSystemProxy, postDnsLookup } from './api.js';

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

export async function refreshSystemInfo() {
    const ipDisplay = document.getElementById('sysPublicIp');
    const proxyRawDisplay = document.getElementById('sysProxyRaw');
    const proxyFormattedDisplay = document.getElementById('sysProxyFormatted');
    const osDisplay = document.getElementById('sysOsInfo');
    
    if (ipDisplay) ipDisplay.innerText = 'Loading...';
    if (proxyRawDisplay) proxyRawDisplay.innerText = 'Fetching settings...';
    if (proxyFormattedDisplay) proxyFormattedDisplay.innerHTML = '<div class="col-12 text-muted small">Fetching settings...</div>';
    
    // 1. Fetch Public IP
    try {
        const ip = await fetchPublicIp();
        if (ipDisplay) ipDisplay.innerText = ip;
    } catch (e) {
        if (ipDisplay) ipDisplay.innerText = 'Error';
    }

    // 2. Fetch System Proxy
    try {
        const data = await fetchSystemProxy();
        
        if (osDisplay) osDisplay.innerText = data.system || "-";
        if (proxyRawDisplay) proxyRawDisplay.innerText = data.raw || "No info";
        
        if (proxyFormattedDisplay) {
            if (data.settings && Object.keys(data.settings).length > 0) {
                proxyFormattedDisplay.innerHTML = Object.entries(data.settings).map(([label, val]) => {
                    let cardClass = "bg-white";
                    let valDisplay = val;
                    
                    // Status coloring
                    if (val === "ON") {
                        cardClass = "bg-success-subtle border-success";
                        valDisplay = `<span class="badge bg-success">ON</span>`;
                    } else if (val === "OFF") {
                        valDisplay = `<span class="badge bg-light text-muted border">OFF</span>`;
                    } else if (label.includes('Address') || label.includes('PAC')) {
                        cardClass = "bg-primary-subtle border-primary-subtle";
                        valDisplay = `<code class="text-primary fw-bold">${val}</code>`;
                    } else if (label.includes('Bypass')) {
                        // Split exceptions by semicolon for better display
                        const exceptions = val.split(';').filter(x => x.trim());
                        valDisplay = exceptions.map(ex => `<span class="badge bg-white text-dark border fw-normal me-1 mb-1">${ex}</span>`).join('');
                    }
                    
                    return `
                        <div class="col-md-6 col-lg-4">
                            <div class="p-3 border rounded h-100 ${cardClass} shadow-sm">
                                <small class="text-muted d-block mb-2 fw-bold text-uppercase" style="font-size: 0.65rem; letter-spacing: 0.5px;">${label}</small>
                                <div class="fw-bold text-break" style="font-size: 0.9rem;">${valDisplay}</div>
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                proxyFormattedDisplay.innerHTML = `<div class="col-12"><div class="alert alert-info py-2 small mb-0">Detailed view not available for ${data.system}. Please check Raw Output below.</div></div>`;
            }
        }
    } catch (e) {
        if (proxyRawDisplay) proxyRawDisplay.innerText = 'Failed to fetch proxy settings';
    }
}
