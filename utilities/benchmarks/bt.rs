// =============================================================================
// Binary-trees benchmark — Rust (Box<Node> + std::thread::scope).
// Usage: bt_rs <threads> <max_depth>
// Build: rustc -O bt.rs -o bt_rs
// =============================================================================
use std::env;
use std::thread;
use std::time::Instant;

struct Node {
    left: Option<Box<Node>>,
    right: Option<Box<Node>>,
}

fn make_tree(depth: i32) -> Box<Node> {
    if depth <= 0 {
        Box::new(Node { left: None, right: None })
    } else {
        Box::new(Node {
            left: Some(make_tree(depth - 1)),
            right: Some(make_tree(depth - 1)),
        })
    }
}

fn check_tree(n: &Node) -> i64 {
    match (&n.left, &n.right) {
        (Some(l), Some(r)) => 1 + check_tree(l) + check_tree(r),
        _ => 1,
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut t: usize = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(1);
    let mut max_depth: i32 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(18);
    if t < 1 { t = 1; }
    let min_depth: i32 = 4;
    if max_depth < min_depth + 2 { max_depth = min_depth + 2; }

    let t0 = Instant::now();
    let mut total_checks: i64 = 0;

    {
        let stretch = make_tree(max_depth + 1);
        total_checks += check_tree(&stretch);
    }

    let long_lived = make_tree(max_depth);

    let mut d = min_depth;
    while d <= max_depth {
        let iterations: i64 = 1_i64 << (max_depth - d + min_depth);
        if t <= 1 {
            for _ in 0..iterations {
                let tree = make_tree(d);
                total_checks += check_tree(&tree);
            }
        } else {
            let base = iterations / (t as i64);
            let rem = iterations % (t as i64);
            let sum: i64 = thread::scope(|s| {
                let mut handles = Vec::with_capacity(t);
                for i in 0..t {
                    let cnt = base + if (i as i64) < rem { 1 } else { 0 };
                    handles.push(s.spawn(move || {
                        let mut ls: i64 = 0;
                        for _ in 0..cnt {
                            let tree = make_tree(d);
                            ls += check_tree(&tree);
                        }
                        ls
                    }));
                }
                handles.into_iter().map(|h| h.join().unwrap()).sum()
            });
            total_checks += sum;
        }
        d += 2;
    }

    total_checks += check_tree(&long_lived);

    let mut ms = t0.elapsed().as_secs_f64() * 1000.0;
    if ms < 1.0 { ms = 1.0; }
    println!(
        "checksum={} threads={} depth={} ms={:.0} rate={:.4e}",
        total_checks, t, max_depth, ms, (total_checks as f64) / (ms / 1000.0)
    );
}
