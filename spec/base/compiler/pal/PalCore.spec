#! Package base:compiler:pal
#! Emits the core C PAL: OS headers, platform introspection shims, panic handlers,
#! float formatting helper, and async task synchronization.

Class of OsDispatch is PalCore{
	namespace: ['base', 'compiler', 'pal'];

	replace Array of Array of String is using: [
		['base', 'sys', OsDispatch]
	];

	replace Function is init(){
	}

	replace Function of String is linux(){
		return '''#define _GNU_SOURCE
#include <sched.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <ctype.h>
#include <time.h>
#include <errno.h>
#include <math.h>
#include <unistd.h>
#include <stdarg.h>
#include <dirent.h>
#include <sys/stat.h>
#include <pthread.h>
#include <sys/wait.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <poll.h>
#include <fcntl.h>
#include <stdatomic.h>

static bool spec_pal_get_exe_path(char* buf, size_t size) {
    ssize_t n = readlink("/proc/self/exe", buf, size - 1);
    if (n > 0) {
        buf[n] = '\0';
        return true;
    }
    return false;
}

static long long spec_pal_get_cpu_count(void) {
    cpu_set_t set;
    if (sched_getaffinity(0, sizeof(set), &set) == 0) {
        long long n = 0;
        for (int i = 0; i < CPU_SETSIZE; i++) {
            if (CPU_ISSET(i, &set)) n++;
        }
        if (n > 0) return n;
    }
    long long n = sysconf(_SC_NPROCESSORS_ONLN);
    return n > 0 ? n : 1;
}

static bool spec_pal_get_terminal_size(long long* width, long long* height) {
    if (!isatty(1)) return false;
    struct winsize ws;
    if (ioctl(1, TIOCGWINSZ, &ws) == 0) {
        if (width && ws.ws_col > 0) *width = (long long)ws.ws_col;
        if (height && ws.ws_row > 0) *height = (long long)ws.ws_row;
        return true;
    }
    return false;
}

static long long spec_pal_get_page_size(void) {
    long long ps = sysconf(_SC_PAGESIZE);
    return ps > 0 ? ps : 4096;
}

static long long spec_pal_get_wall_time_us(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ((long long)ts.tv_sec * 1000000) + (ts.tv_nsec / 1000);
}

static long long spec_pal_get_cpu_time_us(void) {
    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) == 0) {
        return ((long long)ru.ru_utime.tv_sec + ru.ru_stime.tv_sec) * 1000000 + (ru.ru_utime.tv_usec + ru.ru_stime.tv_usec);
    }
    return 0;
}

static void spec_pal_sleep_ms(long long ms) {
    if (ms <= 0) return;
    struct timespec ts;
    ts.tv_sec = ms / 1000;
    ts.tv_nsec = (ms % 1000) * 1000000L;
    nanosleep(&ts, NULL);
}

static long long spec_pal_get_current_rss_kb(long long page_size) {
    FILE* f = fopen("/proc/self/statm", "r");
    if (f) {
        long long dummy = 0, rss_pages = 0;
        int matched = fscanf(f, "%lld %lld", &dummy, &rss_pages);
        fclose(f);
        if (matched == 2) {
            return (rss_pages * page_size) / 1024;
        }
    }
    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) == 0) {
        return (long long)ru.ru_maxrss;
    }
    return 0;
}

static long long spec_pal_get_peak_rss_kb(void) {
    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) == 0) {
        return (long long)ru.ru_maxrss;
    }
    return 0;
}

long long spec_pal_slab_alloc(void) {
    uintptr_t raw = (uintptr_t)mmap(NULL, 131072, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (raw == (uintptr_t)MAP_FAILED) return 0;
    uintptr_t aligned = (raw + 65535ULL) & ~65535ULL;
    if (aligned > raw) munmap((void*)raw, aligned - raw);
    uintptr_t end = raw + 131072;
    if (end > aligned + 65536) munmap((void*)(aligned + 65536), end - (aligned + 65536));
    return (long long)aligned;
}

void spec_pal_slab_free(long long addr) {
    if (addr) munmap((void*)(intptr_t)addr, 65536);
}

long long spec_pal_vm_alloc(long long bytes) {
    size_t sz = (size_t)((bytes <= 0 ? 4096 : bytes + 4095) & ~4095LL);
    void* p = mmap(NULL, sz, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    return (p == MAP_FAILED) ? 0 : (long long)(intptr_t)p;
}

void spec_pal_vm_free(long long addr, long long bytes) {
    if (!addr) return;
    size_t sz = (size_t)((bytes <= 0 ? 4096 : bytes + 4095) & ~4095LL);
    munmap((void*)(intptr_t)addr, sz);
}

long long spec_pal_vm_realloc(long long addr, long long old_bytes, long long new_bytes) {
    if (!addr) return spec_pal_vm_alloc(new_bytes);
    size_t old_sz = (size_t)((old_bytes <= 0 ? 4096 : old_bytes + 4095) & ~4095LL);
    size_t new_sz = (size_t)((new_bytes <= 0 ? 4096 : new_bytes + 4095) & ~4095LL);
    if (old_sz == new_sz) return addr;
    void* p = mremap((void*)(intptr_t)addr, old_sz, new_sz, MREMAP_MAYMOVE);
    return (p == MAP_FAILED) ? 0 : (long long)(intptr_t)p;
}''';
	}

	replace Function of String is macos(){
		return '''#define _DARWIN_C_SOURCE
#include <sys/types.h>
#include <mach-o/dyld.h>
#include <mach/mach.h>
#include <mach/mach_init.h>
#include <mach/task.h>
#include <sys/sysctl.h>
#include <dlfcn.h>
#include <AudioToolbox/AudioToolbox.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <ctype.h>
#include <time.h>
#include <errno.h>
#include <math.h>
#include <unistd.h>
#include <stdarg.h>
#include <dirent.h>
#include <sys/stat.h>
#include <pthread.h>
#include <sys/wait.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <poll.h>
#include <fcntl.h>
#include <stdatomic.h>

static bool spec_pal_get_exe_path(char* buf, size_t size) {
    uint32_t bufsize = (uint32_t)size;
    return _NSGetExecutablePath(buf, &bufsize) == 0;
}

static long long spec_pal_get_cpu_count(void) {
    int count = 0;
    size_t size = sizeof(count);
    if (sysctlbyname("hw.ncpu", &count, &size, NULL, 0) == 0 && count > 0) {
        return (long long)count;
    }
    long long n = sysconf(_SC_NPROCESSORS_ONLN);
    return n > 0 ? n : 1;
}

static bool spec_pal_get_terminal_size(long long* width, long long* height) {
    if (!isatty(1)) return false;
    struct winsize ws;
    if (ioctl(1, TIOCGWINSZ, &ws) == 0) {
        if (width && ws.ws_col > 0) *width = (long long)ws.ws_col;
        if (height && ws.ws_row > 0) *height = (long long)ws.ws_row;
        return true;
    }
    return false;
}

static long long spec_pal_get_page_size(void) {
    long long ps = sysconf(_SC_PAGESIZE);
    return ps > 0 ? ps : 4096;
}

static long long spec_pal_get_wall_time_us(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ((long long)ts.tv_sec * 1000000) + (ts.tv_nsec / 1000);
}

static long long spec_pal_get_cpu_time_us(void) {
    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) == 0) {
        return ((long long)ru.ru_utime.tv_sec + ru.ru_stime.tv_sec) * 1000000 + (ru.ru_utime.tv_usec + ru.ru_stime.tv_usec);
    }
    return 0;
}

static void spec_pal_sleep_ms(long long ms) {
    if (ms <= 0) return;
    struct timespec ts;
    ts.tv_sec = ms / 1000;
    ts.tv_nsec = (ms % 1000) * 1000000L;
    nanosleep(&ts, NULL);
}

static long long spec_pal_get_current_rss_kb(long long page_size) {
    (void)page_size;
    struct mach_task_basic_info info;
    mach_msg_type_number_t count = MACH_TASK_BASIC_INFO_COUNT;
    if (task_info(mach_task_self(), MACH_TASK_BASIC_INFO, (task_info_t)&info, &count) == KERN_SUCCESS) {
        return (long long)(info.resident_size / 1024);
    }
    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) == 0) {
        return (long long)(ru.ru_maxrss / 1024);
    }
    return 0;
}

static long long spec_pal_get_peak_rss_kb(void) {
    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) == 0) {
        return (long long)(ru.ru_maxrss / 1024);
    }
    return 0;
}

long long spec_pal_slab_alloc(void) {
    uintptr_t raw = (uintptr_t)mmap(NULL, 131072, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (raw == (uintptr_t)MAP_FAILED) return 0;
    uintptr_t aligned = (raw + 65535ULL) & ~65535ULL;
    if (aligned > raw) munmap((void*)raw, aligned - raw);
    uintptr_t end = raw + 131072;
    if (end > aligned + 65536) munmap((void*)(aligned + 65536), end - (aligned + 65536));
    return (long long)aligned;
}

void spec_pal_slab_free(long long addr) {
    if (addr) munmap((void*)(intptr_t)addr, 65536);
}

long long spec_pal_vm_alloc(long long bytes) {
    size_t sz = (size_t)((bytes <= 0 ? 4096 : bytes + 4095) & ~4095LL);
    void* p = mmap(NULL, sz, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    return (p == MAP_FAILED) ? 0 : (long long)(intptr_t)p;
}

void spec_pal_vm_free(long long addr, long long bytes) {
    if (!addr) return;
    size_t sz = (size_t)((bytes <= 0 ? 4096 : bytes + 4095) & ~4095LL);
    munmap((void*)(intptr_t)addr, sz);
}

long long spec_pal_vm_realloc(long long addr, long long old_bytes, long long new_bytes) {
    if (!addr) return spec_pal_vm_alloc(new_bytes);
    size_t old_sz = (size_t)((old_bytes <= 0 ? 4096 : old_bytes + 4095) & ~4095LL);
    size_t new_sz = (size_t)((new_bytes <= 0 ? 4096 : new_bytes + 4095) & ~4095LL);
    if (old_sz == new_sz) return addr;
    long long np = spec_pal_vm_alloc(new_bytes);
    if (!np) return 0;
    size_t cp = (size_t)(old_bytes < new_bytes ? old_bytes : new_bytes);
    if (cp > 0) memcpy((void*)(intptr_t)np, (void*)(intptr_t)addr, cp);
    spec_pal_vm_free(addr, old_bytes);
    return np;
}''';
	}

	replace Function of String is windows(){
		return '''#define _WIN32_WINNT 0x0600
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <mmeapi.h>
#include <psapi.h>
#include <io.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <ctype.h>
#include <time.h>
#include <errno.h>
#include <math.h>
#include <unistd.h>
#include <stdarg.h>
#include <dirent.h>
#include <sys/stat.h>
#include <pthread.h>
#include <stdatomic.h>

static bool spec_pal_get_exe_path(char* buf, size_t size) {
    DWORD n = GetModuleFileNameA(NULL, buf, (DWORD)size);
    if (n > 0 && n < size) {
        for (DWORD i = 0; i < n; i++) {
            if (buf[i] == '\\') buf[i] = '/';
        }
        return true;
    }
    return false;
}

static long long spec_pal_get_cpu_count(void) {
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    return si.dwNumberOfProcessors > 0 ? (long long)si.dwNumberOfProcessors : 1;
}

static bool spec_pal_get_terminal_size(long long* width, long long* height) {
    CONSOLE_SCREEN_BUFFER_INFO csbi;
    if (GetConsoleScreenBufferInfo(GetStdHandle(STD_OUTPUT_HANDLE), &csbi)) {
        if (width) {
            int w = csbi.srWindow.Right - csbi.srWindow.Left + 1;
            if (w > 0) *width = (long long)w;
        }
        if (height) {
            int h = csbi.srWindow.Bottom - csbi.srWindow.Top + 1;
            if (h > 0) *height = (long long)h;
        }
        return true;
    }
    return false;
}

static long long spec_pal_get_page_size(void) {
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    return si.dwPageSize > 0 ? (long long)si.dwPageSize : 4096;
}

static long long spec_pal_get_wall_time_us(void) {
    LARGE_INTEGER freq, count;
    if (QueryPerformanceFrequency(&freq) && QueryPerformanceCounter(&count) && freq.QuadPart > 0) {
        return (long long)((count.QuadPart * 1000000) / freq.QuadPart);
    }
    return 0;
}

static long long spec_pal_get_cpu_time_us(void) {
    FILETIME creationTime, exitTime, kernelTime, userTime;
    if (GetProcessTimes(GetCurrentProcess(), &creationTime, &exitTime, &kernelTime, &userTime)) {
        ULARGE_INTEGER kt, ut;
        kt.LowPart = kernelTime.dwLowDateTime;
        kt.HighPart = kernelTime.dwHighDateTime;
        ut.LowPart = userTime.dwLowDateTime;
        ut.HighPart = userTime.dwHighDateTime;
        return (long long)((kt.QuadPart + ut.QuadPart) / 10);
    }
    return 0;
}

static void spec_pal_sleep_ms(long long ms) {
    if (ms <= 0) return;
    Sleep((DWORD)ms);
}

typedef BOOL (WINAPI *spec_pfn_GetProcessMemoryInfo)(HANDLE, PROCESS_MEMORY_COUNTERS*, DWORD);
static bool spec_win_get_memory_info(PROCESS_MEMORY_COUNTERS* pmc) {
    static spec_pfn_GetProcessMemoryInfo fn = NULL;
    static bool resolved = false;
    if (!resolved) {
        HMODULE h = GetModuleHandleA("kernel32.dll");
        if (h) fn = (spec_pfn_GetProcessMemoryInfo)(void*)GetProcAddress(h, "K32GetProcessMemoryInfo");
        if (!fn) {
            h = LoadLibraryA("psapi.dll");
            if (h) fn = (spec_pfn_GetProcessMemoryInfo)(void*)GetProcAddress(h, "GetProcessMemoryInfo");
        }
        resolved = true;
    }
    if (fn) {
        return fn(GetCurrentProcess(), pmc, (DWORD)sizeof(*pmc)) != 0;
    }
    return false;
}

static long long spec_pal_get_current_rss_kb(long long page_size) {
    (void)page_size;
    PROCESS_MEMORY_COUNTERS pmc;
    if (spec_win_get_memory_info(&pmc)) {
        return (long long)(pmc.WorkingSetSize / 1024);
    }
    return 0;
}

static long long spec_pal_get_peak_rss_kb(void) {
    PROCESS_MEMORY_COUNTERS pmc;
    if (spec_win_get_memory_info(&pmc)) {
        return (long long)(pmc.PeakWorkingSetSize / 1024);
    }
    return 0;
}

long long spec_pal_slab_alloc(void) {
    void* p = VirtualAlloc(NULL, 65536, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    return (long long)(intptr_t)p;
}

void spec_pal_slab_free(long long addr) {
    if (addr) VirtualFree((void*)(intptr_t)addr, 0, MEM_RELEASE);
}

long long spec_pal_vm_alloc(long long bytes) {
    SIZE_T sz = (SIZE_T)(bytes <= 0 ? 4096 : bytes);
    void* p = VirtualAlloc(NULL, sz, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    return (long long)(intptr_t)p;
}

void spec_pal_vm_free(long long addr, long long bytes) {
    (void)bytes;
    if (addr) VirtualFree((void*)(intptr_t)addr, 0, MEM_RELEASE);
}

long long spec_pal_vm_realloc(long long addr, long long old_bytes, long long new_bytes) {
    if (!addr) return spec_pal_vm_alloc(new_bytes);
    long long np = spec_pal_vm_alloc(new_bytes);
    if (!np) return 0;
    size_t cp = (size_t)(old_bytes < new_bytes ? old_bytes : new_bytes);
    if (cp > 0) memcpy((void*)(intptr_t)np, (void*)(intptr_t)addr, cp);
    spec_pal_vm_free(addr, old_bytes);
    return np;
}''';
	}

	Function of String is emitHeader(){
		return ```/* Generated by Pure-Spec Compiler */
{{self:getOsBlock(separatePosix: true)}}

void spec_panic(const char* msg);
void spec_panic_bounds(const char* coll, long long idx, size_t len);
void spec_async_task_started(void);
void spec_async_task_finished(void);
extern void spec_fast_random_seed(long long idx);
extern void spec_pool_thread_cleanup(void);
extern long long Arc_retain(void* self, long long objAddr);
extern void Arc_release(void* self, long long objAddr);

static inline void* spec_xmalloc(size_t n) {
    void* p = malloc(n ? n : 1);
    if (!p) { fprintf(stderr, "[Spec Panic] Out of memory\\n"); exit(1); }
    return p;
}

static inline void* spec_xrealloc(void* old, size_t n) {
    void* p = realloc(old, n ? n : 1);
    if (!p) { fprintf(stderr, "[Spec Panic] Out of memory\\n"); exit(1); }
    return p;
}

/* Spec Async Task Manager */
static int spec_in_flight_tasks = 0;
static pthread_mutex_t spec_task_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t spec_task_cond = PTHREAD_COND_INITIALIZER;
```;
	}

	Function of String is emitBody(){
		return '''/* Runtime Implementation */
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
''';
	}
}
