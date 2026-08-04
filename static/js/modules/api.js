export async function fetchPacGroups() {
    const response = await fetch('/api/pac-groups');
    return await response.json();
}

export async function savePacGroups(groups) {
    const response = await fetch('/api/pac-groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ groups })
    });
    return await response.json();
}

export async function fetchSystemProxy() {
    const response = await fetch('/api/system-proxy');
    return await response.json();
}

export async function fetchSystemDns() {
    const response = await fetch('/api/system-dns');
    return await response.json();
}

export async function fetchPublicIp() {
    const response = await fetch('https://api64.ipify.org?format=json');
    const data = await response.json();
    return data.ip;
}

export async function postDnsLookup(host) {
    const response = await fetch('/api/dns-lookup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host })
    });
    return await response.json();
}

export async function postTransform(type, data, action) {
    const response = await fetch(`/api/transform/${type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data, action })
    });
    return await response.json();
}

export async function postIpToSql(data) {
    const response = await fetch('/api/transform/iptosql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data })
    });
    return await response.json();
}

export async function postAnalyzeText(text, encoding) {
    const response = await fetch('/api/analyze-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, encoding })
    });
    return await response.json();
}

export async function fetchUnits() {
    const response = await fetch('/api/units');
    return await response.json();
}

export async function postConvert(category, value, fromUnit, toUnit) {
    const response = await fetch('/api/convert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, value, from_unit: fromUnit, to_unit: toUnit })
    });
    return await response.json();
}

export async function postBeautifyJson(data) {
    const response = await fetch('/api/beautify-json', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data })
    });
    return await response.json();
}

export async function postIpIntersect(listA, listB) {
    const response = await fetch('/api/ip-intersect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ list_a: listA, list_b: listB })
    });
    return await response.json();
}

export async function postPaloAltoGenerate(payload) {
    const response = await fetch('/api/paloalto/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    return await response.json();
}

export async function fetchPaloAltoDefaults() {
    const response = await fetch('/api/paloalto/defaults');
    return await response.json();
}

export async function postPaloAltoDefaults(defaults) {
    const response = await fetch('/api/paloalto/defaults', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(defaults)
    });
    return await response.json();
}

export async function postPaloAltoGenerateBulk(rows) {
    const response = await fetch('/api/paloalto/generate-bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows })
    });
    return await response.json();
}

export async function postPaloAltoGenerateBulkExcel(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch('/api/paloalto/generate-bulk-excel', {
        method: 'POST',
        body: formData
    });
    return await response.json();
}

export async function postTestPac(pacUrl, targetUrl) {
    const response = await fetch('/api/test-pac', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pac_url: pacUrl, target_url: targetUrl })
    });
    return await response.json();
}

export async function postDiffPac(prodUrl, testUrl, sampleUrl) {
    const response = await fetch('/api/diff-pac', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prod_url: prodUrl, test_url: testUrl, sample_url: sampleUrl })
    });
    return await response.json();
}
