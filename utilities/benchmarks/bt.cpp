// =============================================================================
// Binary-trees benchmark — C++17 (std::unique_ptr + std::thread).
// Usage: bt_cpp <threads> <max_depth>
// Build: g++ -O2 -std=c++17 bt.cpp -o bt_cpp -pthread
// =============================================================================
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <thread>
#include <vector>

struct Node {
    std::unique_ptr<Node> left;
    std::unique_ptr<Node> right;
    Node() = default;
    Node(std::unique_ptr<Node> l, std::unique_ptr<Node> r)
        : left(std::move(l)), right(std::move(r)) {}
};

static std::unique_ptr<Node> make_tree(int depth) {
    if (depth <= 0) return std::make_unique<Node>();
    return std::make_unique<Node>(make_tree(depth - 1), make_tree(depth - 1));
}

static long long check_tree(const Node* n) {
    if (!n->left) return 1;
    return 1 + check_tree(n->left.get()) + check_tree(n->right.get());
}

int main(int argc, char** argv) {
    int T = argc > 1 ? std::atoi(argv[1]) : 1;
    int max_depth = argc > 2 ? std::atoi(argv[2]) : 18;
    if (T < 1) T = 1;
    const int min_depth = 4;
    if (max_depth < min_depth + 2) max_depth = min_depth + 2;

    auto t0 = std::chrono::steady_clock::now();
    long long total_checks = 0;

    {
        auto stretch = make_tree(max_depth + 1);
        total_checks += check_tree(stretch.get());
    }

    auto long_lived = make_tree(max_depth);

    for (int d = min_depth; d <= max_depth; d += 2) {
        long long iterations = 1LL << (max_depth - d + min_depth);
        if (T <= 1) {
            for (long long i = 0; i < iterations; i++) {
                auto t = make_tree(d);
                total_checks += check_tree(t.get());
            }
        } else {
            std::vector<std::thread> th;
            std::vector<long long> sums(T, 0);
            long long base = iterations / T, rem = iterations % T;
            th.reserve(T);
            for (int i = 0; i < T; i++) {
                long long cnt = base + (i < rem ? 1 : 0);
                th.emplace_back([&, i, cnt, d]() {
                    long long s = 0;
                    for (long long k = 0; k < cnt; k++) {
                        auto t = make_tree(d);
                        s += check_tree(t.get());
                    }
                    sums[i] = s;
                });
            }
            for (int i = 0; i < T; i++) {
                th[i].join();
                total_checks += sums[i];
            }
        }
    }

    total_checks += check_tree(long_lived.get());

    double ms = std::chrono::duration<double, std::milli>(
        std::chrono::steady_clock::now() - t0).count();
    if (ms < 1.0) ms = 1.0;
    std::printf("checksum=%lld threads=%d depth=%d ms=%.0f rate=%.4e\n",
        total_checks, T, max_depth, ms, (double)total_checks / (ms / 1000.0));
    return 0;
}
