/* =============================================================================
 * Word/log-line frequency benchmark — C anchor (open-addressing hash table).
 *
 * Usage: wf [count]
 * Output: unique=<U> total=<N> max=<M> count=<N> ms=<ms> rate=<lines/sec>
 * Build: gcc -O2 wf.c -o wf
 * ========================================================================== */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

static inline uint64_t rng_next(uint64_t* st) {
    uint64_t s = *st;
    s ^= s << 13;
    s ^= s >> 7;
    s ^= s << 17;
    *st = s;
    return s;
}

typedef struct {
    char* key;
    long long val;
} Entry;

typedef struct {
    Entry* entries;
    size_t cap;
    size_t len;
} HashMap;

static uint64_t fnv1a(const char* s) {
    uint64_t h = 14695981039346656037ULL;
    while (*s) {
        h ^= (unsigned char)*s++;
        h *= 1099511628211ULL;
    }
    return h;
}

static void map_init(HashMap* m, size_t cap) {
    m->cap = cap;
    m->len = 0;
    m->entries = (Entry*)calloc(cap, sizeof(Entry));
}

static void map_grow(HashMap* m) {
    size_t old_cap = m->cap;
    Entry* old = m->entries;
    m->cap = old_cap * 2;
    m->entries = (Entry*)calloc(m->cap, sizeof(Entry));
    size_t mask = m->cap - 1;
    for (size_t i = 0; i < old_cap; i++) {
        if (old[i].key) {
            size_t idx = (size_t)fnv1a(old[i].key) & mask;
            while (m->entries[idx].key) idx = (idx + 1) & mask;
            m->entries[idx] = old[i];
        }
    }
    free(old);
}

static void map_inc(HashMap* m, const char* key) {
    if ((m->len + 1) * 10 >= m->cap * 7) map_grow(m);
    size_t mask = m->cap - 1;
    size_t idx = (size_t)fnv1a(key) & mask;
    while (m->entries[idx].key) {
        if (strcmp(m->entries[idx].key, key) == 0) {
            m->entries[idx].val++;
            return;
        }
        idx = (idx + 1) & mask;
    }
    m->entries[idx].key = strdup(key);
    m->entries[idx].val = 1;
    m->len++;
}

static void map_free(HashMap* m) {
    for (size_t i = 0; i < m->cap; i++) free(m->entries[i].key);
    free(m->entries);
}

static double now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

int main(int argc, char** argv) {
    long long count = argc > 1 ? atoll(argv[1]) : 1000000LL;
    if (count < 1) count = 1;

    static const char* services[16] = {
        "auth", "api", "billing", "cache",
        "db", "edge", "feed", "gateway",
        "ingest", "jobs", "kv", "logs",
        "metrics", "notify", "proxy", "search"
    };
    static const char* levels[3] = { "INFO", "WARN", "ERR" };

    uint64_t st = 0x9E3779B97F4A7C15ULL;
    rng_next(&st); rng_next(&st); rng_next(&st);

    HashMap counts;
    map_init(&counts, 1024);

    double t0 = now_ms();
    char line[64];
    char key[128];
    for (long long i = 0; i < count; i++) {
        uint64_t r1 = rng_next(&st) & 15ULL;
        uint64_t r2 = (rng_next(&st) & 0x7FFFFFFFULL) % 3ULL;
        uint64_t r3 = (rng_next(&st) & 0x7FFFFFFFULL) % 500ULL;

        snprintf(line, sizeof(line), "%s:%s:%llu", services[r1], levels[r2], (unsigned long long)r3);
        char* p1 = strchr(line, ':');
        char* p2 = strchr(p1 + 1, ':');
        *p1 = '\0';
        *p2 = '\0';
        long long code = strtoll(p2 + 1, NULL, 10);
        long long bucket = code & 63;
        snprintf(key, sizeof(key), "%s:%s:%lld", line, p1 + 1, bucket);
        map_inc(&counts, key);
    }

    long long total = 0, max_count = 0;
    for (size_t i = 0; i < counts.cap; i++) {
        if (counts.entries[i].key) {
            long long v = counts.entries[i].val;
            total += v;
            if (v > max_count) max_count = v;
        }
    }

    double ms = now_ms() - t0;
    if (ms < 1.0) ms = 1.0;
    printf("unique=%zu total=%lld max=%lld count=%lld ms=%.0f rate=%.4e\n",
        counts.len, total, max_count, count, ms, (double)count / (ms / 1000.0));
    map_free(&counts);
    return 0;
}
