// =============================================================================
// Word/log-line frequency benchmark — Rust (String + std::collections::HashMap).
// Usage: wf_rs [count]
// Build: rustc -O wf.rs -o wf_rs
// =============================================================================
use std::collections::HashMap;
use std::env;
use std::time::Instant;

#[inline]
fn rng_next(st: &mut u64) -> u64 {
    let mut s = *st;
    s ^= s << 13;
    s ^= s >> 7;
    s ^= s << 17;
    *st = s;
    s
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut count: i64 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(1_000_000);
    if count < 1 { count = 1; }

    let services = [
        "auth", "api", "billing", "cache",
        "db", "edge", "feed", "gateway",
        "ingest", "jobs", "kv", "logs",
        "metrics", "notify", "proxy", "search",
    ];
    let levels = ["INFO", "WARN", "ERR"];

    let mut st: u64 = 0x9E37_79B9_7F4A_7C15;
    rng_next(&mut st); rng_next(&mut st); rng_next(&mut st);

    let mut counts: HashMap<String, i64> = HashMap::new();
    let t0 = Instant::now();

    for _ in 0..count {
        let r1 = (rng_next(&mut st) & 15) as usize;
        let r2 = ((rng_next(&mut st) & 0x7FFF_FFFF) % 3) as usize;
        let r3 = (rng_next(&mut st) & 0x7FFF_FFFF) % 500;

        let line = format!("{}:{}:{}", services[r1], levels[r2], r3);
        let mut parts = line.split(':');
        let p0 = parts.next().unwrap();
        let p1 = parts.next().unwrap();
        let code: i64 = parts.next().unwrap().parse().unwrap();
        let bucket = code & 63;
        let key = format!("{}:{}:{}", p0, p1, bucket);
        *counts.entry(key).or_insert(0) += 1;
    }

    let mut total: i64 = 0;
    let mut max_count: i64 = 0;
    for &v in counts.values() {
        total += v;
        if v > max_count { max_count = v; }
    }

    let mut ms = t0.elapsed().as_secs_f64() * 1000.0;
    if ms < 1.0 { ms = 1.0; }
    println!(
        "unique={} total={} max={} count={} ms={:.0} rate={:.4e}",
        counts.len(), total, max_count, count, ms, (count as f64) / (ms / 1000.0)
    );
}
