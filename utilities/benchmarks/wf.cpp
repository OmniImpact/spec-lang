// =============================================================================
// Word/log-line frequency benchmark — C++17 (std::string + std::unordered_map).
// Usage: wf_cpp [count]
// Build: g++ -O2 -std=c++17 wf.cpp -o wf_cpp
// =============================================================================
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <unordered_map>

static inline uint64_t rng_next(uint64_t& st) {
    uint64_t s = st;
    s ^= s << 13;
    s ^= s >> 7;
    s ^= s << 17;
    st = s;
    return s;
}

int main(int argc, char** argv) {
    long long count = argc > 1 ? std::atoll(argv[1]) : 1000000LL;
    if (count < 1) count = 1;

    static const char* services[16] = {
        "auth", "api", "billing", "cache",
        "db", "edge", "feed", "gateway",
        "ingest", "jobs", "kv", "logs",
        "metrics", "notify", "proxy", "search"
    };
    static const char* levels[3] = { "INFO", "WARN", "ERR" };

    uint64_t st = 0x9E3779B97F4A7C15ULL;
    rng_next(st); rng_next(st); rng_next(st);

    std::unordered_map<std::string, long long> counts;
    auto t0 = std::chrono::steady_clock::now();

    for (long long i = 0; i < count; i++) {
        uint64_t r1 = rng_next(st) & 15ULL;
        uint64_t r2 = (rng_next(st) & 0x7FFFFFFFULL) % 3ULL;
        uint64_t r3 = (rng_next(st) & 0x7FFFFFFFULL) % 500ULL;

        std::string line = std::string(services[r1]) + ":" + levels[r2] + ":" + std::to_string(r3);
        size_t p1 = line.find(':');
        size_t p2 = line.find(':', p1 + 1);
        long long code = std::stoll(line.substr(p2 + 1));
        long long bucket = code & 63;
        std::string key = line.substr(0, p1) + ":" + line.substr(p1 + 1, p2 - p1 - 1) + ":" + std::to_string(bucket);
        counts[key]++;
    }

    long long total = 0, max_count = 0;
    for (const auto& kv : counts) {
        total += kv.second;
        if (kv.second > max_count) max_count = kv.second;
    }

    double ms = std::chrono::duration<double, std::milli>(
        std::chrono::steady_clock::now() - t0).count();
    if (ms < 1.0) ms = 1.0;
    std::printf("unique=%zu total=%lld max=%lld count=%lld ms=%.0f rate=%.4e\n",
        counts.size(), total, max_count, count, ms, (double)count / (ms / 1000.0));
    return 0;
}
