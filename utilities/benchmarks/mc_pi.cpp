// =============================================================================
// Monte Carlo pi benchmark — C++17, same algorithm as mc_pi.c (xorshift64,
// identical constants, identical per-point work, thread fan-out + join).
//
// Usage: mc_pi_cpp <threads> <points>
// Build: g++ -O2 -std=c++17 mc_pi.cpp -o mc_pi_cpp -pthread
// =============================================================================
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <thread>
#include <vector>
#include <chrono>

static inline uint64_t rng_next(uint64_t& st) {
    st ^= st << 13;
    st ^= st >> 7;
    st ^= st << 17;
    return st;
}

int main(int argc, char** argv) {
    int T = argc > 1 ? atoi(argv[1]) : 8;
    long long N = argc > 2 ? atoll(argv[2]) : 200000000LL;
    if (T < 1) T = 1;
    std::vector<long long> hits((size_t)T, 0);
    auto t0 = std::chrono::steady_clock::now();
    {
        std::vector<std::thread> th;
        th.reserve((size_t)T);
        for (int i = 0; i < T; i++) {
            th.emplace_back([&, i] {
                uint64_t st = 0x9E3779B97F4A7C15ULL
                    ^ ((uint64_t)i * 0xBF58476D1CE4E5B9ULL + 0x94D049BB133111EBULL);
                if (st == 0) st = 1;
                rng_next(st); rng_next(st); rng_next(st);
                long long h = 0;
                const double scale = 1.0 / 9007199254740992.0;
                long long per = N / T + (i < N % T ? 1 : 0);
                for (long long k = 0; k < per; k++) {
                    double x = (double)(rng_next(st) >> 11) * scale;
                    double y = (double)(rng_next(st) >> 11) * scale;
                    if (x * x + y * y <= 1.0) h++;
                }
                hits[(size_t)i] = h;
            });
        }
        for (auto& t : th) t.join();
    }
    auto t1 = std::chrono::steady_clock::now();
    long long H = 0;
    for (long long v : hits) H += v;
    double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    printf("pi=%.5f threads=%d points=%lld ms=%.0f rate=%.4e\n",
        4.0 * (double)H / (double)N, T, N, ms, (double)N / (ms / 1000.0));
    return 0;
}
