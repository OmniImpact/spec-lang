// =============================================================================
// Word/log-line frequency benchmark — Node.js (V8, Map + split, warmed 50k).
// Usage: node wf.js [count]
// =============================================================================
'use strict';

function runOnce(count, report) {
    const services = [
        'auth', 'api', 'billing', 'cache',
        'db', 'edge', 'feed', 'gateway',
        'ingest', 'jobs', 'kv', 'logs',
        'metrics', 'notify', 'proxy', 'search'
    ];
    const levels = ['INFO', 'WARN', 'ERR'];

    let st = 0x9E3779B9;
    function nx() {
        st ^= st << 13;
        st ^= st >>> 17;
        st ^= st << 5;
        return st >>> 0;
    }
    nx(); nx(); nx();

    const counts = new Map();
    const t0 = process.hrtime.bigint();

    for (let i = 0; i < count; i++) {
        const r1 = nx() & 15;
        const r2 = (nx() & 0x7FFFFFFF) % 3;
        const r3 = (nx() & 0x7FFFFFFF) % 500;

        const line = `${services[r1]}:${levels[r2]}:${r3}`;
        const parts = line.split(':');
        const code = parseInt(parts[2], 10);
        const bucket = code & 63;
        const key = `${parts[0]}:${parts[1]}:${bucket}`;
        counts.set(key, (counts.get(key) || 0) + 1);
    }

    let total = 0;
    let maxCount = 0;
    for (const v of counts.values()) {
        total += v;
        if (v > maxCount) maxCount = v;
    }

    let ms = Number(process.hrtime.bigint() - t0) / 1e6;
    if (ms < 1) ms = 1;
    if (report) {
        const rate = count / (ms / 1000.0);
        console.log(`unique=${counts.size} total=${total} max=${maxCount} count=${count} ms=${Math.round(ms)} rate=${rate.toExponential(4)}`);
    }
}

const count = Math.max(1, parseInt(process.argv[2] || '1000000', 10));
runOnce(50000, false);
runOnce(count, true);
