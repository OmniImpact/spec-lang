/* =============================================================================
 * 32-bit-RNG variant of the anchor benchmark.
 *
 * Python, Ruby, and JavaScript have no practical native 64-bit integer loop
 * (BigInt/boxing distorts more than it reveals), so those languages run an
 * equivalent xorshift32. This binary quantifies the RNG-width effect on the
 * anchor so the cross-language table cites a measured correction instead of a
 * guess. Same structure as mc_pi.c otherwise.
 *
 * Usage: mc_pi32 <threads> <points>
 * Build: gcc -O2 mc_pi32.c -o mc_pi32 -pthread -lm
 * ========================================================================== */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>

static inline uint32_t rng_next(uint32_t* st) {
    uint32_t s = *st;
    s ^= s << 13;
    s ^= s >> 17;
    s ^= s << 5;
    *st = s;
    return s;
}

typedef struct { int idx; long long count; long long hits; } Task;

static void* worker(void* ap) {
    Task* t = (Task*)ap;
    uint32_t st = 0x9E3779B9u ^ ((uint32_t)t->idx * 0x85EBCA6Bu + 0x94D049BBu);
    if (st == 0) st = 1;
    rng_next(&st); rng_next(&st); rng_next(&st);
    long long h = 0;
    const double scale = 1.0 / 4294967296.0;
    for (long long i = 0; i < t->count; i++) {
        double x = (double)rng_next(&st) * scale;
        double y = (double)rng_next(&st) * scale;
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
