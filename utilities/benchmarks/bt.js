// =============================================================================
// Binary-trees benchmark — Node.js (V8, worker_threads for >1 thread).
// Usage: node bt.js <threads> <max_depth>
// =============================================================================
'use strict';

const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

class Node {
    constructor(left, right) {
        this.left = left;
        this.right = right;
    }
}

function makeTree(depth) {
    if (depth <= 0) return new Node(null, null);
    return new Node(makeTree(depth - 1), makeTree(depth - 1));
}

function checkTree(n) {
    if (n.left === null) return 1;
    return 1 + checkTree(n.left) + checkTree(n.right);
}

if (!isMainThread) {
    const { depth, count } = workerData;
    // Small JIT warm-up inside worker
    for (let w = 0; w < 64; w++) checkTree(makeTree(8));
    let sum = 0;
    for (let i = 0; i < count; i++) {
        sum += checkTree(makeTree(depth));
    }
    parentPort.postMessage(sum);
} else {
    function runParallel(t, depth, iterations) {
        const base = Math.floor(iterations / t);
        const rem = iterations % t;
        return Promise.all(Array.from({ length: t }, (_, i) => new Promise((resolve, reject) => {
            const cnt = base + (i < rem ? 1 : 0);
            const w = new Worker(__filename, { workerData: { depth, count: cnt } });
            w.on('message', resolve);
            w.on('error', reject);
        }))).then((vals) => vals.reduce((a, b) => a + b, 0));
    }

    async function runOnce(t, maxDepthIn, report) {
        const minDepth = 4;
        const maxDepth = maxDepthIn < minDepth + 2 ? minDepth + 2 : maxDepthIn;
        const t0 = process.hrtime.bigint();
        let totalChecks = 0;

        let stretch = makeTree(maxDepth + 1);
        totalChecks += checkTree(stretch);
        stretch = null;

        const longLived = makeTree(maxDepth);

        for (let d = minDepth; d <= maxDepth; d += 2) {
            const iterations = 1 << (maxDepth - d + minDepth);
            if (t <= 1) {
                for (let i = 0; i < iterations; i++) {
                    totalChecks += checkTree(makeTree(d));
                }
            } else {
                totalChecks += await runParallel(t, d, iterations);
            }
        }

        totalChecks += checkTree(longLived);
        let ms = Number(process.hrtime.bigint() - t0) / 1e6;
        if (ms < 1) ms = 1;
        if (report) {
            const rate = totalChecks / (ms / 1000.0);
            console.log(`checksum=${totalChecks} threads=${t} depth=${maxDepth} ms=${Math.round(ms)} rate=${rate.toExponential(4)}`);
        }
    }

    (async () => {
        const t = Math.max(1, parseInt(process.argv[2] || '1', 10));
        const maxDepth = parseInt(process.argv[3] || '18', 10);
        for (let w = 0; w < 2; w++) await runOnce(1, 12, false);
        await runOnce(t, maxDepth, true);
    })();
}
