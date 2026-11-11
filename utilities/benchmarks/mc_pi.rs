// =============================================================================
// Monte Carlo pi benchmark — Rust (std only, no crates), same algorithm as
// mc_pi.c (xorshift64, identical constants, identical per-point work).
// Scoped threads keep the fan-out + join shape; the RNG is a plain mut u64 so
// LLVM can keep the whole loop in registers.
//
// Usage: mc_pi_rs <threads> <points>
// Build: rustc -O mc_pi.rs -o mc_pi_rs
// =============================================================================
use std::thread;
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let t: usize = args.get(1).map(|s| s.parse().unwrap_or(8)).unwrap_or(8);
    let n: u64 = args.get(2).map(|s| s.parse().unwrap_or(200_000_000)).unwrap_or(200_000_000);
    let t = t.max(1);

    let t0 = Instant::now();
    let hits: Vec<u64> = thread::scope(|s| {
        let mut joins = Vec::with_capacity(t);
        for i in 0..t {
            let per = n / t as u64 + if (i as u64) < n % t as u64 { 1 } else { 0 };
            joins.push(s.spawn(move || {
                let mut st: u64 = 0x9E3779B9_7F4A7C15
                    ^ ((i as u64).wrapping_mul(0xBF58476D_1CE4E5B9)
                        .wrapping_add(0x94D049BB_133111EB));
                if st == 0 {
                    st = 1;
                }
                let mut h: u64 = 0;
                let scale = 1.0f64 / 9007199254740992.0;
                let mut x;
                let mut y;
                for _ in 0..per {
                    st ^= st << 13;
                    st ^= st >> 7;
                    st ^= st << 17;
                    x = ((st >> 11) as f64) * scale;
                    st ^= st << 13;
                    st ^= st >> 7;
                    st ^= st << 17;
                    y = ((st >> 11) as f64) * scale;
                    if x * x + y * y <= 1.0 {
                        h += 1;
                    }
                }
                h
            }));
        }
        joins.into_iter().map(|j| j.join().unwrap()).collect()
    });
    let ms = t0.elapsed().as_secs_f64() * 1000.0;

    let total: u64 = hits.iter().sum();
    println!(
        "pi={:.5} threads={} points={} ms={:.0} rate={:.4e}",
        4.0 * total as f64 / n as f64,
        t,
        n,
        ms,
        n as f64 / (ms / 1000.0)
    );
}
