#! Package base:compiler:pal
#! Emits the process, concurrency, and resource monitoring C PAL (`spec_pal_process_*`,
#! `spec_process_*`, `spec_parallel_*`, `spec_monitor_*`).

Class of OsDispatch is PalProcess{
	namespace: ['base', 'compiler', 'pal'];

	replace Array of Array of String is using: [
		['base', 'sys', OsDispatch]
	];

	replace Function is init(){
	}

	Function of String is emitHeader(){
		return '''/* Process Resource Monitoring (instantaneous RSS and CPU sampling) */
static _Atomic int _spec_mon_state = 0;
static _Atomic long long _spec_mon_sample_count = 0;
static _Atomic long long _spec_mon_mem_sum_kb = 0;
static _Atomic long long _spec_mon_peak_mem_kb = 0;
static _Atomic long long _spec_mon_peak_cpu_pct = 0;
static long long _spec_mon_start_wall_us = 0;
static long long _spec_mon_start_cpu_us = 0;
static long long _spec_mon_total_wall_us = 0;
static long long _spec_mon_total_cpu_us = 0;
''';
	}

	local Function of String is posixExecuteAndMeasure(String is rssScale, String is osLiteral){
		return '''long long spec_pal_process_execute_cstr(long long cmd_cstr, long long argv_addr, long long nargs_ll) {
    const char* cc = (const char*)(intptr_t)cmd_cstr;
    if (!cc || !*cc) return -1;
    const char** raw_args = (const char**)(intptr_t)argv_addr;
    size_t nargs = (nargs_ll > 0 && raw_args) ? (size_t)nargs_ll : 0;
    size_t total_len = strlen(cc) + 1;
    for (size_t i = 0; i < nargs; i++) {
        const char* a = raw_args[i] ? raw_args[i] : "";
        size_t quotes = 0;
        for (size_t k = 0; a[k]; k++) if (a[k] == 39) quotes++;
        total_len += strlen(a) + 3 * quotes + 3;
    }
    char* cmd_line = (char*)spec_xmalloc(total_len + 1);
    char* w = cmd_line;
    size_t cmd_len = strlen(cc);
    memcpy(w, cc, cmd_len);
    w += cmd_len;
    for (size_t i = 0; i < nargs; i++) {
        const char* a = raw_args[i] ? raw_args[i] : "";
        *w++ = ' ';
        *w++ = 39;
        for (size_t k = 0; a[k]; k++) {
            if (a[k] == 39) { *w++ = 39; *w++ = 92; *w++ = 39; *w++ = 39; }
            else *w++ = a[k];
        }
        *w++ = 39;
    }
    *w = 0;
    int status = system(cmd_line);
    free(cmd_line);
    if (status == -1) return -1;
    if (WIFSIGNALED(status)) return 128 + (long long)WTERMSIG(status);
    return (long long)WEXITSTATUS(status);
}

void spec_pal_process_measure_cstr(long long cmd_cstr, long long argv_addr, long long nargs_ll, long long out_addr) {
    long long* out = (long long*)(intptr_t)out_addr;
    long long exit_code = -1;
    long long wall_us = 0;
    long long cpu_us = 0;
    long long rss_kb = 0;
    const char* cc = (const char*)(intptr_t)cmd_cstr;
    if (!cc || !*cc) {
        if (out) { out[0] = exit_code; out[1] = wall_us; out[2] = cpu_us; out[3] = rss_kb; }
        return;
    }
    const char** raw_args = (const char**)(intptr_t)argv_addr;
    size_t nargs = (nargs_ll > 0 && raw_args) ? (size_t)nargs_ll : 0;
    fflush(stdout);
    fflush(stderr);
    char** argv_exec = (char**)spec_xmalloc((nargs + 2) * sizeof(char*));
    argv_exec[0] = (char*)cc;
    for (size_t i = 0; i < nargs; i++) {
        argv_exec[i + 1] = (char*)(raw_args[i] ? raw_args[i] : "");
    }
    argv_exec[nargs + 1] = NULL;
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    pid_t pid = fork();
    if (pid == 0) {
        execvp(cc, argv_exec);
        _exit(127);
    } else if (pid > 0) {
        int status = 0;
        struct rusage ru;
        memset(&ru, 0, sizeof(ru));
        pid_t wres;
        do {
            wres = wait4(pid, &status, 0, &ru);
        } while (wres == -1 && errno == EINTR);
        clock_gettime(CLOCK_MONOTONIC, &t1);
        fflush(stdout);
        fflush(stderr);
        wall_us = (long long)(t1.tv_sec - t0.tv_sec) * 1000000LL + (long long)(t1.tv_nsec - t0.tv_nsec) / 1000LL;
        if (wall_us < 0) wall_us = 0;
        if (wres > 0) {
            cpu_us = (long long)(ru.ru_utime.tv_sec + ru.ru_stime.tv_sec) * 1000000LL + (long long)(ru.ru_utime.tv_usec + ru.ru_stime.tv_usec);
            rss_kb = (long long)ru.ru_maxrss''' . rssScale . ''';
            if (WIFEXITED(status)) exit_code = (long long)WEXITSTATUS(status);
            else if (WIFSIGNALED(status)) exit_code = 128 + (long long)WTERMSIG(status);
        }
    }
    free(argv_exec);
    if (out) { out[0] = exit_code; out[1] = wall_us; out[2] = cpu_us; out[3] = rss_kb; }
}

long long spec_process_get_pid(void) {
    return (long long)getpid();
}

long long spec_pal_os_name(void) {
    return (long long)(intptr_t)"''' . osLiteral . '''";
}''';
	}

	replace Function of String is linux(){
		return :posixExecuteAndMeasure(rssScale: '', osLiteral: 'linux');
	}

	replace Function of String is macos(){
		return :posixExecuteAndMeasure(rssScale: ' / 1024', osLiteral: 'macos');
	}

	replace Function of String is windows(){
		return '''long long spec_pal_process_execute_cstr(long long cmd_cstr, long long argv_addr, long long nargs_ll) {
    const char* cc = (const char*)(intptr_t)cmd_cstr;
    if (!cc || !*cc) return -1;
    const char** raw_args = (const char**)(intptr_t)argv_addr;
    size_t nargs = (nargs_ll > 0 && raw_args) ? (size_t)nargs_ll : 0;
    size_t total_len = strlen(cc) + 1;
    for (size_t i = 0; i < nargs; i++) {
        const char* a = raw_args[i] ? raw_args[i] : "";
        total_len += strlen(a) * 2 + 4;
    }
    char* cmd_line = (char*)spec_xmalloc(total_len + 1);
    char* w = cmd_line;
    size_t cmd_len = strlen(cc);
    memcpy(w, cc, cmd_len);
    w += cmd_len;
    for (size_t i = 0; i < nargs; i++) {
        const char* a = raw_args[i] ? raw_args[i] : "";
        *w++ = ' ';
        bool needs_quote = (*a == 0);
        for (size_t k = 0; a[k]; k++) {
            if (a[k] == ' ' || a[k] == '\t' || a[k] == '\n' || a[k] == '\v' || a[k] == '\"') {
                needs_quote = true;
                break;
            }
        }
        if (!needs_quote) {
            size_t alen = strlen(a);
            memcpy(w, a, alen);
            w += alen;
        } else {
            *w++ = '\"';
            size_t slashes = 0;
            for (size_t k = 0; a[k]; k++) {
                if (a[k] == '\\') {
                    slashes++;
                } else if (a[k] == '\"') {
                    for (size_t s = 0; s < slashes * 2 + 1; s++) *w++ = '\\';
                    *w++ = '\"';
                    slashes = 0;
                } else {
                    for (size_t s = 0; s < slashes; s++) *w++ = '\\';
                    *w++ = a[k];
                    slashes = 0;
                }
            }
            for (size_t s = 0; s < slashes * 2; s++) *w++ = '\\';
            *w++ = '\"';
        }
    }
    *w = 0;
    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    memset(&si, 0, sizeof(si));
    si.cb = sizeof(si);
    memset(&pi, 0, sizeof(pi));
    DWORD exit_code = 1;
    wchar_t* wcmd = spec_win_utf8_to_wide(cmd_line);
    if (wcmd && CreateProcessW(NULL, wcmd, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {
        free(wcmd);
        WaitForSingleObject(pi.hProcess, INFINITE);
        GetExitCodeProcess(pi.hProcess, &exit_code);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        free(cmd_line);
        return (long long)exit_code;
    }
    free(wcmd);
    int status = system(cmd_line);
    free(cmd_line);
    return (long long)status;
}

void spec_pal_process_measure_cstr(long long cmd_cstr, long long argv_addr, long long nargs_ll, long long out_addr) {
    long long* out = (long long*)(intptr_t)out_addr;
    long long exit_code = -1;
    long long wall_us = 0;
    long long cpu_us = 0;
    long long rss_kb = 0;
    const char* cc = (const char*)(intptr_t)cmd_cstr;
    if (!cc || !*cc) {
        if (out) { out[0] = exit_code; out[1] = wall_us; out[2] = cpu_us; out[3] = rss_kb; }
        return;
    }
    const char** raw_args = (const char**)(intptr_t)argv_addr;
    size_t nargs = (nargs_ll > 0 && raw_args) ? (size_t)nargs_ll : 0;
    fflush(stdout);
    fflush(stderr);
    size_t total_len = strlen(cc) + 1;
    for (size_t i = 0; i < nargs; i++) {
        const char* a = raw_args[i] ? raw_args[i] : "";
        total_len += strlen(a) * 2 + 4;
    }
    char* cmd_line = (char*)spec_xmalloc(total_len + 1);
    char* w = cmd_line;
    size_t cmd_len = strlen(cc);
    memcpy(w, cc, cmd_len);
    w += cmd_len;
    for (size_t i = 0; i < nargs; i++) {
        const char* a = raw_args[i] ? raw_args[i] : "";
        *w++ = ' ';
        bool needs_quote = (*a == 0);
        for (size_t k = 0; a[k]; k++) {
            if (a[k] == ' ' || a[k] == '\t' || a[k] == '\n' || a[k] == '\v' || a[k] == '\"') {
                needs_quote = true;
                break;
            }
        }
        if (!needs_quote) {
            size_t alen = strlen(a);
            memcpy(w, a, alen);
            w += alen;
        } else {
            *w++ = '\"';
            size_t slashes = 0;
            for (size_t k = 0; a[k]; k++) {
                if (a[k] == '\\') {
                    slashes++;
                } else if (a[k] == '\"') {
                    for (size_t s = 0; s < slashes * 2 + 1; s++) *w++ = '\\';
                    *w++ = '\"';
                    slashes = 0;
                } else {
                    for (size_t s = 0; s < slashes; s++) *w++ = '\\';
                    *w++ = a[k];
                    slashes = 0;
                }
            }
            for (size_t s = 0; s < slashes * 2; s++) *w++ = '\\';
            *w++ = '\"';
        }
    }
    *w = 0;
    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    memset(&si, 0, sizeof(si));
    si.cb = sizeof(si);
    memset(&pi, 0, sizeof(pi));
    LARGE_INTEGER freq, q0, q1;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&q0);
    wchar_t* wcmd = spec_win_utf8_to_wide(cmd_line);
    if (wcmd && CreateProcessW(NULL, wcmd, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {
        WaitForSingleObject(pi.hProcess, INFINITE);
        QueryPerformanceCounter(&q1);
        DWORD dw_exit = 1;
        if (GetExitCodeProcess(pi.hProcess, &dw_exit)) exit_code = (long long)dw_exit;
        FILETIME ft_create, ft_exit, ft_kernel, ft_user;
        if (GetProcessTimes(pi.hProcess, &ft_create, &ft_exit, &ft_kernel, &ft_user)) {
            ULARGE_INTEGER uk, uu;
            uk.LowPart = ft_kernel.dwLowDateTime;
            uk.HighPart = ft_kernel.dwHighDateTime;
            uu.LowPart = ft_user.dwLowDateTime;
            uu.HighPart = ft_user.dwHighDateTime;
            cpu_us = (long long)((uk.QuadPart + uu.QuadPart) / 10ULL);
        }
        PROCESS_MEMORY_COUNTERS pmc;
        memset(&pmc, 0, sizeof(pmc));
        pmc.cb = sizeof(pmc);
        if (GetProcessMemoryInfo(pi.hProcess, &pmc, sizeof(pmc))) {
            rss_kb = (long long)(pmc.PeakWorkingSetSize / 1024ULL);
        }
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        if (freq.QuadPart > 0) {
            wall_us = (long long)(((q1.QuadPart - q0.QuadPart) * 1000000LL) / freq.QuadPart);
        }
    }
    free(wcmd);
    free(cmd_line);
    if (out) { out[0] = exit_code; out[1] = wall_us; out[2] = cpu_us; out[3] = rss_kb; }
}

long long spec_process_get_pid(void) {
    return (long long)GetCurrentProcessId();
}

long long spec_pal_os_name(void) {
    return (long long)(intptr_t)"windows";
}''';
	}

	Function of String is emitBody(){
		return ```{{:getOsBlock(separatePosix: true)}}

void spec_process_sleep(long long ms) {
    spec_pal_sleep_ms(ms);
}

long long spec_pal_getenv(long long key_cstr) {
    const char* k = (const char*)(intptr_t)key_cstr;
    if (!k || !*k) return 0;
    const char* val = getenv(k);
    return (long long)(intptr_t)val;
}

long long spec_clock_ms(void) {
    return spec_pal_get_wall_time_us() / 1000;
}

long long spec_mem_peak_kb(void) {
    return spec_pal_get_peak_rss_kb();
}

long long spec_thread_count(void) {
    return spec_pal_get_cpu_count();
}

long long spec_monitor_avg_cpu_pct(void) {
    if (_spec_mon_total_wall_us <= 0) return 0;
    return (_spec_mon_total_cpu_us * 100) / _spec_mon_total_wall_us;
}

long long spec_monitor_peak_cpu_pct(void) {
    return _spec_mon_peak_cpu_pct;
}

long long spec_monitor_avg_mem_kb(void) {
    long long count = _spec_mon_sample_count;
    if (count <= 0) return _spec_mon_peak_mem_kb;
    return _spec_mon_mem_sum_kb / count;
}

long long spec_monitor_peak_mem_kb(void) {
    return _spec_mon_peak_mem_kb;
}

void spec_monitor_start(void) {
    int expected = 0;
    if (!atomic_compare_exchange_strong(&_spec_mon_state, &expected, 1)) {
        _spec_mon_state = 0;
        return;
    }
    _spec_mon_sample_count = 0;
    _spec_mon_mem_sum_kb = 0;
    _spec_mon_peak_mem_kb = 0;
    _spec_mon_peak_cpu_pct = 0;

    _spec_mon_start_wall_us = spec_pal_get_wall_time_us();
    _spec_mon_start_cpu_us = spec_pal_get_cpu_time_us();

    long long page_size = spec_pal_get_page_size();
    long long last_wall_us = _spec_mon_start_wall_us;
    long long last_cpu_us = _spec_mon_start_cpu_us;

    while (atomic_load(&_spec_mon_state) == 1) {
        for (int s = 0; s < 4 && atomic_load(&_spec_mon_state) == 1; s++) {
            spec_pal_sleep_ms(5);
        }
        if (atomic_load(&_spec_mon_state) != 1) break;

        long long cur_rss_kb = spec_pal_get_current_rss_kb(page_size);
        if (cur_rss_kb > 0) {
            _spec_mon_mem_sum_kb += cur_rss_kb;
            _spec_mon_sample_count++;
            if (cur_rss_kb > _spec_mon_peak_mem_kb) {
                _spec_mon_peak_mem_kb = cur_rss_kb;
            }
        }

        long long now_wall_us = spec_pal_get_wall_time_us();
        long long now_cpu_us = spec_pal_get_cpu_time_us();

        long long d_wall = now_wall_us - last_wall_us;
        long long d_cpu = now_cpu_us - last_cpu_us;
        if (d_wall >= 15000) {
            long long cpu_pct = (d_cpu * 100) / d_wall;
            if (cpu_pct > _spec_mon_peak_cpu_pct) {
                _spec_mon_peak_cpu_pct = cpu_pct;
            }
            last_wall_us = now_wall_us;
            last_cpu_us = now_cpu_us;
        }
    }
    _spec_mon_state = 0;
}

void spec_monitor_stop(void) {
    atomic_store(&_spec_mon_state, 2);

    long long end_wall_us = spec_pal_get_wall_time_us();
    long long end_cpu_us = spec_pal_get_cpu_time_us();

    _spec_mon_total_wall_us = end_wall_us - _spec_mon_start_wall_us;
    _spec_mon_total_cpu_us = end_cpu_us - _spec_mon_start_cpu_us;

    long long peak_ru = spec_pal_get_peak_rss_kb();
    if (peak_ru > _spec_mon_peak_mem_kb) {
        _spec_mon_peak_mem_kb = peak_ru;
    }
    long long avg_cpu = spec_monitor_avg_cpu_pct();
    if (avg_cpu > _spec_mon_peak_cpu_pct) {
        _spec_mon_peak_cpu_pct = avg_cpu;
    }
}

void spec_process_exit(long long status) {
    exit((int)status);
}

/* OS Thread, Mutex, and Condition Variable Primitives (base:sysinternal:Thread) */
static _Atomic long long _spec_thread_seq = 0;

#ifdef _WIN32
typedef struct {
    HANDLE hThread;
} SpecWinThread;

static DWORD WINAPI _spec_win_thread_trampoline(LPVOID arg) {
    void** cls = (void**)arg;
    spec_fast_random_seed(atomic_fetch_add_explicit(&_spec_thread_seq, 1, memory_order_relaxed) + 1);
    if (cls && cls[0]) {
        ((void (*)(void*))cls[0])(cls[1]);
    }
    if (arg) Arc_release(NULL, (long long)(intptr_t)arg);
    spec_pool_thread_cleanup();
    spec_thread_leave();
    return 0;
}

long long spec_thread_spawn(void* task_closure) {
    if (!task_closure) return 0;
    Arc_retain(NULL, (long long)(intptr_t)task_closure);
    spec_thread_enter();
    HANDLE h = CreateThread(NULL, 0, _spec_win_thread_trampoline, task_closure, 0, NULL);
    if (!h) {
        _spec_win_thread_trampoline(task_closure);
        return 0;
    }
    SpecWinThread* th = (SpecWinThread*)spec_xmalloc(sizeof(SpecWinThread));
    th->hThread = h;
    return (long long)(intptr_t)th;
}

void spec_thread_join(long long handle) {
    if (!handle) return;
    SpecWinThread* th = (SpecWinThread*)(intptr_t)handle;
    if (th->hThread) {
        WaitForSingleObject(th->hThread, INFINITE);
        CloseHandle(th->hThread);
    }
    free(th);
}

long long spec_thread_current_id(void) {
    return (long long)GetCurrentThreadId();
}

long long spec_mutex_create(void) {
    SRWLOCK* lk = (SRWLOCK*)spec_xmalloc(sizeof(SRWLOCK));
    InitializeSRWLock(lk);
    return (long long)(intptr_t)lk;
}

void spec_mutex_destroy(long long handle) {
    if (handle) free((void*)(intptr_t)handle);
}

void spec_mutex_lock(long long handle) {
    if (handle) AcquireSRWLockExclusive((SRWLOCK*)(intptr_t)handle);
}

void spec_mutex_unlock(long long handle) {
    if (handle) ReleaseSRWLockExclusive((SRWLOCK*)(intptr_t)handle);
}

long long spec_cond_create(void) {
    CONDITION_VARIABLE* cv = (CONDITION_VARIABLE*)spec_xmalloc(sizeof(CONDITION_VARIABLE));
    InitializeConditionVariable(cv);
    return (long long)(intptr_t)cv;
}

void spec_cond_destroy(long long handle) {
    if (handle) free((void*)(intptr_t)handle);
}

void spec_cond_wait(long long cond, long long mutex) {
    if (cond && mutex) {
        SleepConditionVariableSRW((CONDITION_VARIABLE*)(intptr_t)cond, (SRWLOCK*)(intptr_t)mutex, INFINITE, 0);
    }
}

void spec_cond_signal(long long cond) {
    if (cond) WakeConditionVariable((CONDITION_VARIABLE*)(intptr_t)cond);
}

void spec_cond_broadcast(long long cond) {
    if (cond) WakeAllConditionVariable((CONDITION_VARIABLE*)(intptr_t)cond);
}
#else
typedef struct {
    pthread_t tid;
} SpecPosixThread;

static void* _spec_posix_thread_trampoline(void* arg) {
    void** cls = (void**)arg;
    spec_fast_random_seed(atomic_fetch_add_explicit(&_spec_thread_seq, 1, memory_order_relaxed) + 1);
    if (cls && cls[0]) {
        ((void (*)(void*))cls[0])(cls[1]);
    }
    if (arg) Arc_release(NULL, (long long)(intptr_t)arg);
    spec_pool_thread_cleanup();
    spec_thread_leave();
    return NULL;
}

long long spec_thread_spawn(void* task_closure) {
    if (!task_closure) return 0;
    Arc_retain(NULL, (long long)(intptr_t)task_closure);
    spec_thread_enter();
    SpecPosixThread* th = (SpecPosixThread*)spec_xmalloc(sizeof(SpecPosixThread));
    if (pthread_create(&th->tid, NULL, _spec_posix_thread_trampoline, task_closure) != 0) {
        free(th);
        _spec_posix_thread_trampoline(task_closure);
        return 0;
    }
    return (long long)(intptr_t)th;
}

void spec_thread_join(long long handle) {
    if (!handle) return;
    SpecPosixThread* th = (SpecPosixThread*)(intptr_t)handle;
    pthread_join(th->tid, NULL);
    free(th);
}

long long spec_thread_current_id(void) {
    return (long long)(uintptr_t)pthread_self();
}

long long spec_mutex_create(void) {
    pthread_mutex_t* m = (pthread_mutex_t*)spec_xmalloc(sizeof(pthread_mutex_t));
    pthread_mutex_init(m, NULL);
    return (long long)(intptr_t)m;
}

void spec_mutex_destroy(long long handle) {
    if (!handle) return;
    pthread_mutex_t* m = (pthread_mutex_t*)(intptr_t)handle;
    pthread_mutex_destroy(m);
    free(m);
}

void spec_mutex_lock(long long handle) {
    if (handle) pthread_mutex_lock((pthread_mutex_t*)(intptr_t)handle);
}

void spec_mutex_unlock(long long handle) {
    if (handle) pthread_mutex_unlock((pthread_mutex_t*)(intptr_t)handle);
}

long long spec_cond_create(void) {
    pthread_cond_t* c = (pthread_cond_t*)spec_xmalloc(sizeof(pthread_cond_t));
    pthread_cond_init(c, NULL);
    return (long long)(intptr_t)c;
}

void spec_cond_destroy(long long handle) {
    if (!handle) return;
    pthread_cond_t* c = (pthread_cond_t*)(intptr_t)handle;
    pthread_cond_destroy(c);
    free(c);
}

void spec_cond_wait(long long cond, long long mutex) {
    if (cond && mutex) {
        pthread_cond_wait((pthread_cond_t*)(intptr_t)cond, (pthread_mutex_t*)(intptr_t)mutex);
    }
}

void spec_cond_signal(long long cond) {
    if (cond) pthread_cond_signal((pthread_cond_t*)(intptr_t)cond);
}

void spec_cond_broadcast(long long cond) {
    if (cond) pthread_cond_broadcast((pthread_cond_t*)(intptr_t)cond);
}
#endif
```;
	}
}
