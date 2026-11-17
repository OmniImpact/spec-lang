#! Package base:compiler:pal
#! Emits the file I/O and async task worker C PAL (`spec_pal_file_*`, `spec_pal_spawn_async`).

Class of OsDispatch is PalFile{
	namespace: ['base', 'compiler', 'pal'];

	replace Array of Array of String is using: [
		['base', 'sys', OsDispatch]
	];

	replace Function is init(){
	}

	Function of String is emitHeader(){
		return '';
	}

	replace Function of String is linux(){
		return '''static void _spec_pal_ensure_tmp_dir(const char* pc) {
    (void)pc;
}

static int _spec_pal_mkstemp_win_fallback(const char* tpl, char** buf_io, char* suffix, size_t suffix_cap) {
    (void)tpl; (void)buf_io; (void)suffix; (void)suffix_cap;
    return -1;
}''';
	}

	replace Function of String is macos(){
		return self:linux();
	}

	replace Function of String is windows(){
		return '''static void _spec_pal_ensure_tmp_dir(const char* pc) {
    if (!pc || strncmp(pc, "/tmp/", 5) == 0 || strncmp(pc, "\\tmp\\", 5) == 0 || strcmp(pc, "/tmp") == 0) {
        CreateDirectoryA("/tmp", NULL);
    }
}

static int _spec_pal_mkstemp_win_fallback(const char* tpl, char** buf_io, char* suffix, size_t suffix_cap) {
    if (strncmp(tpl, "/tmp/", 5) != 0 && strcmp(tpl, "/tmp") != 0) return -1;
    char temp_dir[MAX_PATH];
    DWORD td_len = GetTempPathA(MAX_PATH, temp_dir);
    if (td_len == 0 || td_len >= MAX_PATH) return -1;
    const char* base = strrchr(tpl, '/');
    const char* b2 = strrchr(tpl, '\\');
    if (b2 && (!base || b2 > base)) base = b2;
    if (base) base++; else base = tpl;
    free(*buf_io);
    char* buf = (char*)spec_xmalloc(strlen(temp_dir) + strlen(base) + 32);
    sprintf(buf, "%s%s", temp_dir, base);
    suffix[0] = '\0';
    char* xpos = strstr(buf, "XXXXXX");
    if (!xpos) {
        strcat(buf, "_XXXXXX");
    } else {
        if (strlen(xpos + 6) < suffix_cap) {
            strcpy(suffix, xpos + 6);
        }
        xpos[6] = '\0';
    }
    *buf_io = buf;
    return mkstemp(buf);
}''';
	}

	Function of String is emitBody(){
		return ```{{self:getOsBlock(separatePosix: false)}}

static void* spec_pal_async_worker(void* arg) {
    void** cls = (void**)arg;
    if (cls && cls[0]) {
        ((void (*)(void*))cls[0])(cls[1]);
    }
    if (arg) Arc_release(NULL, (long long)(intptr_t)arg);
    spec_pool_thread_cleanup();
    spec_async_task_finished();
    return NULL;
}

void spec_pal_spawn_async(void* task_closure) {
    if (!task_closure) return;
    spec_async_task_started();
    pthread_t tid;
    if (pthread_create(&tid, NULL, spec_pal_async_worker, task_closure) != 0) {
        spec_pal_async_worker(task_closure);
        return;
    }
    pthread_detach(tid);
}

long long spec_pal_file_read(long long path_cstr, long long out_len_addr) {
    long long* out_len = (long long*)(intptr_t)out_len_addr;
    if (out_len) *out_len = 0;
    const char* pc = (const char*)(intptr_t)path_cstr;
    if (!pc || !*pc) return -1;
    FILE* f = fopen(pc, "rb");
    if (!f) return -1;
    if (fseek(f, 0, SEEK_END) != 0) {
        fclose(f);
        return -1;
    }
    long size = ftell(f);
    if (size < 0) {
        fclose(f);
        return -1;
    }
    fseek(f, 0, SEEK_SET);
    char* buf = (char*)malloc((size_t)size + 1);
    if (!buf) {
        fclose(f);
        return -2;
    }
    size_t read_bytes = fread(buf, 1, (size_t)size, f);
    fclose(f);
    buf[read_bytes] = '\\0';
    if (out_len) *out_len = (long long)read_bytes;
    return (long long)(intptr_t)buf;
}

long long spec_pal_file_write(long long path_cstr, long long data_addr, long long len_ll, long long append) {
    const char* pc = (const char*)(intptr_t)path_cstr;
    if (!pc || !*pc) return -1;
    _spec_pal_ensure_tmp_dir(pc);
    size_t len = (len_ll > 0 && data_addr) ? (size_t)len_ll : 0;
    if (append && len == 0) return 0;
    const char* cc = len ? (const char*)(intptr_t)data_addr : "";
    FILE* f = fopen(pc, append ? "ab" : "wb");
    if (!f) return -1;
    size_t written = fwrite(cc, 1, len, f);
    if (fclose(f) != 0) return -1;
    if (written != len) return -1;
    return (long long)written;
}

bool spec_pal_file_exists(long long path_cstr) {
    const char* pc = (const char*)(intptr_t)path_cstr;
    if (!pc || !*pc) return false;
    FILE* f = fopen(pc, "r");
    if (f) {
        fclose(f);
        return true;
    }
    return false;
}

bool spec_pal_file_remove(long long path_cstr) {
    const char* pc = (const char*)(intptr_t)path_cstr;
    if (!pc || !*pc) return false;
    return remove(pc) == 0;
}

long long spec_pal_file_temp(long long tpl_cstr) {
    _spec_pal_ensure_tmp_dir(NULL);
    const char* tpl = (const char*)(intptr_t)tpl_cstr;
    if (!tpl || !*tpl) tpl = "/tmp/spec_XXXXXX";
    size_t len = strlen(tpl);
    char* buf = (char*)spec_xmalloc(len + 32);
    strcpy(buf, tpl);
    char suffix[64];
    suffix[0] = '\\0';
    char* xpos = strstr(buf, "XXXXXX");
    if (!xpos) {
        strcat(buf, "_XXXXXX");
    } else {
        if (strlen(xpos + 6) < sizeof(suffix)) {
            strcpy(suffix, xpos + 6);
        }
        xpos[6] = '\\0';
    }
    int fd = mkstemp(buf);
    if (fd == -1) {
        fd = _spec_pal_mkstemp_win_fallback(tpl, &buf, suffix, sizeof(suffix));
    }
    if (fd == -1) {
        free(buf);
        return 0;
    }
    close(fd);
    if (suffix[0] != '\\0') {
        size_t final_len = strlen(buf) + strlen(suffix) + 1;
        char* final_path = (char*)spec_xmalloc(final_len);
        sprintf(final_path, "%s%s", buf, suffix);
        if (rename(buf, final_path) != 0) {
            free(final_path);
            free(buf);
            return 0;
        }
        free(buf);
        return (long long)(intptr_t)final_path;
    }
    return (long long)(intptr_t)buf;
}
```;
	}
}
