#! Package base:compiler:pal
#! Emits the time, clock, sleep, and background timer C PAL (`spec_time_*`).

Class of OsDispatch is PalTime{
	namespace: ['base', 'compiler', 'pal'];

	replace Array of Array of String is using: [
		['base', 'sys', OsDispatch]
	];

	replace Function is init(){
	}

	replace Function of String is linux(){
		return '''long long spec_time_monotonic_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ((long long)ts.tv_sec * 1000000000LL) + (long long)ts.tv_nsec;
}

long long spec_time_epoch_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return ((long long)ts.tv_sec * 1000000000LL) + (long long)ts.tv_nsec;
}

void spec_time_sleep_ns(long long ns) {
    if (ns <= 0) return;
    struct timespec ts;
    ts.tv_sec = ns / 1000000000LL;
    ts.tv_nsec = ns % 1000000000LL;
    while (nanosleep(&ts, &ts) == -1 && errno == EINTR) {
    }
}

static bool _spec_pal_localtime_utc(long long epoch_sec, struct tm* local_tm, struct tm* utc_tm) {
    time_t t = (time_t)epoch_sec;
    if (!localtime_r(&t, local_tm)) return false;
    if (!gmtime_r(&t, utc_tm)) return false;
    return true;
}''';
	}

	replace Function of String is macos(){
		return self:linux();
	}

	replace Function of String is windows(){
		return '''long long spec_time_monotonic_ns(void) {
    LARGE_INTEGER freq, count;
    if (QueryPerformanceFrequency(&freq) && QueryPerformanceCounter(&count) && freq.QuadPart > 0) {
        long long whole = count.QuadPart / freq.QuadPart;
        long long rem = count.QuadPart % freq.QuadPart;
        return whole * 1000000000LL + (rem * 1000000000LL) / freq.QuadPart;
    }
    return 0;
}

long long spec_time_epoch_ns(void) {
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    ULARGE_INTEGER uli;
    uli.LowPart = ft.dwLowDateTime;
    uli.HighPart = ft.dwHighDateTime;
    if (uli.QuadPart < 116444736000000000ULL) return 0;
    return (long long)((uli.QuadPart - 116444736000000000ULL) * 100ULL);
}

void spec_time_sleep_ns(long long ns) {
    if (ns <= 0) return;
    long long target = spec_time_monotonic_ns() + ns;
    long long ms = ns / 1000000LL;
    if (ms > 1) {
        Sleep((DWORD)(ms - 1));
    }
    while (spec_time_monotonic_ns() < target) {
        Sleep(0);
    }
}

static bool _spec_pal_localtime_utc(long long epoch_sec, struct tm* local_tm, struct tm* utc_tm) {
    __time64_t t = (__time64_t)epoch_sec;
    if (_localtime64_s(local_tm, &t) != 0) return false;
    if (_gmtime64_s(utc_tm, &t) != 0) return false;
    return true;
}''';
	}

	Function of String is emitBody(){
		return ```{{self:getOsBlock(separatePosix: false)}}

long long spec_time_monotonic_us(void) {
    return spec_time_monotonic_ns() / 1000LL;
}

long long spec_time_monotonic_ms(void) {
    return spec_time_monotonic_ns() / 1000000LL;
}

long long spec_time_epoch_ms(void) {
    return spec_time_epoch_ns() / 1000000LL;
}

void spec_time_sleep_us(long long us) {
    if (us <= 0) return;
    spec_time_sleep_ns(us * 1000LL);
}

void spec_time_sleep_ms(long long ms) {
    if (ms <= 0) return;
    spec_time_sleep_ns(ms * 1000000LL);
}

static long long spec_days_from_civil_c(long long y, long long m, long long d) {
    y -= (m <= 2);
    long long era = (y >= 0 ? y : y - 399) / 400;
    long long yoe = y - era * 400;
    long long doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;
    long long doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + doe - 719468;
}

long long spec_time_local_offset_sec(long long epoch_sec) {
    struct tm local_tm, utc_tm;
    if (!_spec_pal_localtime_utc(epoch_sec, &local_tm, &utc_tm)) return 0;
    long long local_days = spec_days_from_civil_c((long long)local_tm.tm_year + 1900, (long long)local_tm.tm_mon + 1, (long long)local_tm.tm_mday);
    long long utc_days = spec_days_from_civil_c((long long)utc_tm.tm_year + 1900, (long long)utc_tm.tm_mon + 1, (long long)utc_tm.tm_mday);
    long long local_sec = local_days * 86400LL + (long long)local_tm.tm_hour * 3600LL + (long long)local_tm.tm_min * 60LL + (long long)local_tm.tm_sec;
    long long utc_sec = utc_days * 86400LL + (long long)utc_tm.tm_hour * 3600LL + (long long)utc_tm.tm_min * 60LL + (long long)utc_tm.tm_sec;
    return local_sec - utc_sec;
}

typedef struct SpecTimerTask {
    long long id;
    long long interval_ns;
    long long count;
    void* callback;
    bool cancelled;
    struct SpecTimerTask* next;
} SpecTimerTask;

static pthread_mutex_t _spec_timer_mutex = PTHREAD_MUTEX_INITIALIZER;
static SpecTimerTask* _spec_timer_head = NULL;
static long long _spec_next_timer_id = 0;

static void* spec_timer_worker(void* arg) {
    SpecTimerTask* task = (SpecTimerTask*)arg;
    long long target_ns = spec_time_monotonic_ns() + task->interval_ns;
    long long executed = 0;
    while (task->count <= 0 || executed < task->count) {
        for (;;) {
            pthread_mutex_lock(&_spec_timer_mutex);
            bool is_cancelled = task->cancelled;
            pthread_mutex_unlock(&_spec_timer_mutex);
            if (is_cancelled) goto done;
            long long now_ns = spec_time_monotonic_ns();
            long long rem_ns = target_ns - now_ns;
            if (rem_ns <= 0) break;
            long long chunk_ns = rem_ns > 20000000LL ? 20000000LL : rem_ns;
            spec_time_sleep_ns(chunk_ns);
        }
        pthread_mutex_lock(&_spec_timer_mutex);
        bool is_cancelled = task->cancelled;
        pthread_mutex_unlock(&_spec_timer_mutex);
        if (is_cancelled) break;
        if (task->callback) {
            void** cls = (void**)task->callback;
            if (cls[0]) ((void (*)(void*))cls[0])(cls[1]);
        }
        executed++;
        target_ns += task->interval_ns;
    }
done:
    pthread_mutex_lock(&_spec_timer_mutex);
    SpecTimerTask** cur = &_spec_timer_head;
    while (*cur) {
        if (*cur == task) {
            *cur = task->next;
            break;
        }
        cur = &(*cur)->next;
    }
    pthread_mutex_unlock(&_spec_timer_mutex);
    if (task->callback) Arc_release(NULL, (long long)(intptr_t)task->callback);
    free(task);
    spec_pool_thread_cleanup();
    spec_async_task_finished();
    return NULL;
}

long long spec_time_set_interval(long long ms, long long count, void* callback) {
    SpecTimerTask* task = (SpecTimerTask*)spec_xmalloc(sizeof(SpecTimerTask));
    task->interval_ns = (ms > 0 ? ms : 0) * 1000000LL;
    task->count = count;
    task->callback = callback ? (void*)(intptr_t)Arc_retain(NULL, (long long)(intptr_t)callback) : NULL;
    task->cancelled = false;
    pthread_mutex_lock(&_spec_timer_mutex);
    task->id = ++_spec_next_timer_id;
    task->next = _spec_timer_head;
    _spec_timer_head = task;
    pthread_mutex_unlock(&_spec_timer_mutex);
    spec_async_task_started();
    pthread_t tid;
    if (pthread_create(&tid, NULL, spec_timer_worker, task) != 0) {
        spec_timer_worker(task);
        return task->id;
    }
    pthread_detach(tid);
    return task->id;
}

long long spec_time_set_timeout(long long ms, void* callback) {
    return spec_time_set_interval(ms, 1, callback);
}

bool spec_time_cancel_timer(long long timer_id) {
    pthread_mutex_lock(&_spec_timer_mutex);
    SpecTimerTask* cur = _spec_timer_head;
    bool found = false;
    while (cur) {
        if (cur->id == timer_id) {
            cur->cancelled = true;
            found = true;
            break;
        }
        cur = cur->next;
    }
    pthread_mutex_unlock(&_spec_timer_mutex);
    return found;
}
```;
	}
}
