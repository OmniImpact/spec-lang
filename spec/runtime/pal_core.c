/* Runtime Implementation */
void spec_panic(const char* msg) {
    fprintf(stderr, "[Spec Runtime Panic] %s\n", msg ? msg : "fatal error");
    exit(1);
}

void spec_panic_bounds(const char* coll, long long idx, size_t len) {
    fprintf(stderr, "[Spec Runtime Panic] %s index out of bounds: index %lld for length %zu\n", coll ? coll : "Collection", idx, len);
    exit(1);
}

void spec_panic_cast(const char* actual, const char* target) {
    fprintf(stderr, "[Spec Runtime Panic] Invalid downcast: instance of '%s' cannot be cast to '%s'\n", actual ? actual : "Unknown", target ? target : "Unknown");
    exit(1);
}

void spec_panic_byte_range(long long v) {
    fprintf(stderr, "[Spec Runtime Panic] Byte cast out of range: %lld (must be 0..255)\n", v);
    exit(1);
}

void spec_pal_format_float(double v, long long buf_addr) {
    char* buf = (char*)(intptr_t)buf_addr;
    if (buf) snprintf(buf, 64, "%.17g", v);
}

#ifdef _WIN32
extern unsigned char __stdcall SystemFunction036(void* buf, unsigned long len);
#endif

long long spec_pal_random_bytes(long long dst_addr, long long len) {
    if (dst_addr == 0 || len <= 0) return -1;
    unsigned char* dst = (unsigned char*)(intptr_t)dst_addr;
#ifdef _WIN32
    return SystemFunction036(dst, (unsigned long)len) ? 0 : -1;
#elif defined(__APPLE__) || defined(__FreeBSD__) || defined(__OpenBSD__) || defined(__NetBSD__)
    arc4random_buf(dst, (size_t)len);
    return 0;
#else
    FILE* f = fopen("/dev/urandom", "rb");
    if (!f) return -1;
    size_t got = fread(dst, 1, (size_t)len, f);
    fclose(f);
    return (got == (size_t)len) ? 0 : -1;
#endif
}

_Atomic int g_spec_active_threads = 0;

static inline void spec_thread_enter(void) {
    atomic_fetch_add_explicit(&g_spec_active_threads, 1, memory_order_release);
}

static inline void spec_thread_leave(void) {
    atomic_fetch_sub_explicit(&g_spec_active_threads, 1, memory_order_release);
}

static inline bool spec_is_multithreaded(void) {
    return atomic_load_explicit(&g_spec_active_threads, memory_order_acquire) > 0;
}

void spec_async_task_started(void) {
    spec_thread_enter();
    pthread_mutex_lock(&spec_task_mutex);
    spec_in_flight_tasks++;
    pthread_mutex_unlock(&spec_task_mutex);
}

void spec_async_task_finished(void) {
    pthread_mutex_lock(&spec_task_mutex);
    spec_in_flight_tasks--;
    if (spec_in_flight_tasks <= 0) {
        spec_in_flight_tasks = 0;
        pthread_cond_broadcast(&spec_task_cond);
    }
    pthread_mutex_unlock(&spec_task_mutex);
    spec_thread_leave();
}

void spec_drain_async_tasks(void) {
    pthread_mutex_lock(&spec_task_mutex);
    while (spec_in_flight_tasks > 0) {
        pthread_cond_wait(&spec_task_cond, &spec_task_mutex);
    }
    pthread_mutex_unlock(&spec_task_mutex);
}

