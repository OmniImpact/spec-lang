/* =============================================================================
 * Monte Carlo pi anchor benchmark — the C baseline every other language is
 * measured against in README-PERFORMANCE.md.
 *
 * Identical algorithm to the Spec runtime's fastRandom: xorshift64 with the
 * same constants and the same per-thread deterministic seeding, two draws per
 * point, hit when x*x + y*y <= 1.0. Thread fan-out + join, hits summed.
 *
 * Usage: mc_pi <threads> <points>
 * Output: pi=<v> threads=<T> points=<N> ms=<ms> rate=<pts/sec>
 *
 * Build: gcc -O2 mc_pi.c -o mc_pi -pthread -lm
 * ========================================================================== */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>

static inline uint64_t rng_next(uint64_t* st) {
    uint64_t s = *st;
    s ^= s << 13;
    s ^= s >> 7;
    s ^= s << 17;
    *st = s;
    return s;
}

typedef struct { int idx; long long count; long long hits; } Task;

static void* worker(void* ap) {
    Task* t = (Task*)ap;
    uint64_t st = 0x9E3779B97F4A7C15ULL
        ^ ((uint64_t)t->idx * 0xBF58476D1CE4E5B9ULL + 0x94D049BB133111EBULL);
    if (st == 0) st = 1;
    rng_next(&st); rng_next(&st); rng_next(&st);
    long long h = 0;
    const double scale = 1.0 / 9007199254740992.0;
    for (long long i = 0; i < t->count; i++) {
        double x = (double)(rng_next(&st) >> 11) * scale;
        double y = (double)(rng_next(&st) >> 11) * scale;
        if (x * x + y * y <= 1.0) h++;
    }
    t->hits = h;
    return NULL;
}

static double now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

int main(int argc, char** argv) {
    int T = argc > 1 ? atoi(argv[1]) : 8;
    long long N = argc > 2 ? atoll(argv[2]) : 200000000LL;
    if (T < 1) T = 1;
    pthread_t* th = (pthread_t*)malloc(sizeof(pthread_t) * (size_t)T);
    Task* tasks = (Task*)malloc(sizeof(Task) * (size_t)T);
    long long base = N / T, rem = N % T;
    double t0 = now_ms();
    for (int i = 0; i < T; i++) {
        tasks[i].idx = i;
        tasks[i].count = base + (i < rem ? 1 : 0);
        pthread_create(&th[i], NULL, worker, &tasks[i]);
    }
    long long hits = 0;
    for (int i = 0; i < T; i++) { pthread_join(th[i], NULL); hits += tasks[i].hits; }
    double ms = now_ms() - t0;
    printf("pi=%.5f threads=%d points=%lld ms=%.0f rate=%.4e\n",
        4.0 * (double)hits / (double)N, T, N, ms, (double)N / (ms / 1000.0));
    free(th); free(tasks);
    return 0;
}
