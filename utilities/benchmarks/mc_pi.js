// =============================================================================
// Monte Carlo pi benchmark — JavaScript / Node.js. Same per-point work shape
// as mc_pi.c but with an xorshift32: JS has no fast native 64-bit integers
// (BigInt boxing distorts far more than the width does), and the 32-bit
// variant's cost is quantified separately against mc_pi32.c.
//
// threads=1 runs in the main thread; threads>1 fans out over worker_threads
// (the standard Node mechanism for CPU parallelism). Workers JIT-warm on a
// discarded slice before measuring; spawn overhead stays inside the measured
// wall time, honestly.
//
// Usage: node mc_pi.js <threads> <points>
// =============================================================================
'use strict';

const D = 1.0 / 4294967296.0;

function slice(idx, per) {
    let st = (0x9E3779B9 ^ ((idx * 0x85EBCA6B + 0x94D049BB) | 0)) >>> 0;
    if (st === 0) st = 1;
    let h = 0;
    for (let k = 0; k < per; k++) {
        st = (st ^ (st << 13)) >>> 0;
        st = (st ^ (st >>> 17)) >>> 0;
        st = (st ^ (st << 5)) >>> 0;
        const x = st * D;
        st = (st ^ (st << 13)) >>> 0;
        st = (st ^ (st >>> 17)) >>> 0;
        st = (st ^ (st << 5)) >>> 0;
        const y = st * D;
        if (x * x + y * y <= 1.0) h++;
    }
    return h;
}

const { isMainThread, workerData, parentPort } = require('worker_threads');

if (!isMainThread) {
    // Worker: JIT-warm on a discarded slice, then measure our share.
    slice(workerData.idx, Math.min(2_000_000, workerData.per));
    parentPort.postMessage(slice(workerData.idx, workerData.per));
} else {
    const args = process.argv.slice(2);
    const T = Math.max(1, args.length > 0 ? parseInt(args[0], 10) : 8);
    const N = args.length > 1 ? parseInt(args[1], 10) : 200000000;
    if (T === 1) {
        slice(0, Math.min(20_000_000, N)); // main-thread JIT warm-up
        const t0 = process.hrtime.bigint();
        const h = slice(0, N);
        const ms = Number(process.hrtime.bigint() - t0) / 1e6;
        console.log(`pi=${(4.0 * h / N).toFixed(5)} threads=1 points=${N} ms=${ms.toFixed(0)} rate=${(N / (ms / 1000.0)).toExponential(4)}`);
    } else {
        const { Worker } = require('worker_threads');
        const t0 = process.hrtime.bigint();
        let done = 0;
        let hits = 0;
        for (let i = 0; i < T; i++) {
            const per = Math.floor(N / T) + (i < N % T ? 1 : 0);
            new Worker(__filename, { workerData: { idx: i, per } })
                .on('message', (h) => {
                    hits += h;
                    if (++done === T) {
                        const ms = Number(process.hrtime.bigint() - t0) / 1e6;
                        console.log(`pi=${(4.0 * hits / N).toFixed(5)} threads=${T} points=${N} ms=${ms.toFixed(0)} rate=${(N / (ms / 1000.0)).toExponential(4)}`);
                        process.exit(0);
                    }
                });
        }
    }
}
