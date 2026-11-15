/* =============================================================================
 * Binary-trees benchmark (Benchmarks Game style) — C anchor.
 *
 * Usage: bt <threads> <max_depth>
 * Output: checksum=<N> threads=<T> depth=<D> ms=<ms> rate=<nodes/sec>
 * Build: gcc -O2 bt.c -o bt -pthread
 * ========================================================================== */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>

typedef struct Node {
    struct Node* left;
    struct Node* right;
} Node;

static Node* make_tree(int depth) {
    Node* n = (Node*)malloc(sizeof(Node));
    if (depth <= 0) {
        n->left = NULL;
        n->right = NULL;
    } else {
        n->left = make_tree(depth - 1);
        n->right = make_tree(depth - 1);
    }
    return n;
}

static long long check_tree(const Node* n) {
    if (n->left == NULL) return 1;
    return 1 + check_tree(n->left) + check_tree(n->right);
}

static void free_tree(Node* n) {
    if (n->left != NULL) {
        free_tree(n->left);
        free_tree(n->right);
    }
    free(n);
}

typedef struct {
    int depth;
    long long count;
    long long sum;
} Task;

static void* worker(void* ap) {
    Task* t = (Task*)ap;
    long long s = 0;
    for (long long i = 0; i < t->count; i++) {
        Node* tree = make_tree(t->depth);
        s += check_tree(tree);
        free_tree(tree);
    }
    t->sum = s;
    return NULL;
}

static double now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

int main(int argc, char** argv) {
    int T = argc > 1 ? atoi(argv[1]) : 1;
    int max_depth = argc > 2 ? atoi(argv[2]) : 18;
    if (T < 1) T = 1;
    const int min_depth = 4;
    if (max_depth < min_depth + 2) max_depth = min_depth + 2;

    double t0 = now_ms();
    long long total_checks = 0;

    Node* stretch = make_tree(max_depth + 1);
    total_checks += check_tree(stretch);
    free_tree(stretch);

    Node* long_lived = make_tree(max_depth);

    pthread_t* th = T > 1 ? (pthread_t*)malloc(sizeof(pthread_t) * (size_t)T) : NULL;
    Task* tasks = T > 1 ? (Task*)malloc(sizeof(Task) * (size_t)T) : NULL;

    for (int d = min_depth; d <= max_depth; d += 2) {
        long long iterations = 1LL << (max_depth - d + min_depth);
        if (T <= 1) {
            for (long long i = 0; i < iterations; i++) {
                Node* tree = make_tree(d);
                total_checks += check_tree(tree);
                free_tree(tree);
            }
        } else {
            long long base = iterations / T, rem = iterations % T;
            for (int i = 0; i < T; i++) {
                tasks[i].depth = d;
                tasks[i].count = base + (i < rem ? 1 : 0);
                tasks[i].sum = 0;
                pthread_create(&th[i], NULL, worker, &tasks[i]);
            }
            for (int i = 0; i < T; i++) {
                pthread_join(th[i], NULL);
                total_checks += tasks[i].sum;
            }
        }
    }

    total_checks += check_tree(long_lived);
    free_tree(long_lived);
    free(th);
    free(tasks);

    double ms = now_ms() - t0;
    if (ms < 1.0) ms = 1.0;
    printf("checksum=%lld threads=%d depth=%d ms=%.0f rate=%.4e\n",
        total_checks, T, max_depth, ms, (double)total_checks / (ms / 1000.0));
    return 0;
}
