long long spec_pal_dir_open_cstr(long long path_cstr) {
    const char* p = (const char*)(intptr_t)path_cstr;
    if (!p || !*p) return 0;
    DIR* d = opendir(p);
    return (long long)(intptr_t)d;
}

long long spec_pal_dir_next(long long handle) {
    if (!handle) return 0;
    DIR* d = (DIR*)(intptr_t)handle;
    struct dirent* ent;
    while ((ent = readdir(d)) != NULL) {
        if (strcmp(ent->d_name, ".") == 0 || strcmp(ent->d_name, "..") == 0) continue;
        return (long long)(intptr_t)ent->d_name;
    }
    return 0;
}

void spec_pal_dir_close(long long handle) {
    if (!handle) return;
    closedir((DIR*)(intptr_t)handle);
}

long long spec_pal_last_error_cstr(void) {
    const char* m = strerror(errno);
    return (long long)(intptr_t)(m ? m : "Unknown error");
}

long long spec_pal_exe_dir(long long buf_addr, long long buf_size) {
    char* buf = (char*)(intptr_t)buf_addr;
    if (!buf || buf_size <= 1) return 0;
    if (!spec_pal_get_exe_path(buf, (size_t)buf_size)) {
        buf[0] = '.';
        buf[1] = '\0';
        return 1;
    }
    char* slash = strrchr(buf, '/');
#if defined(_WIN32)
    char* bslash = strrchr(buf, '\\');
    if (bslash > slash) slash = bslash;
#endif
    if (!slash) {
        buf[0] = '.';
        buf[1] = '\0';
        return 1;
    }
    return (long long)(slash - buf);
}

long long spec_pal_exe_path(long long buf_addr, long long buf_size) {
    char* buf = (char*)(intptr_t)buf_addr;
    if (!buf || buf_size <= 1) return 0;
    if (!spec_pal_get_exe_path(buf, (size_t)buf_size)) return 0;
    return (long long)strlen(buf);
}

long long spec_pal_file_size_cstr(long long path_cstr) {
    const char* p = (const char*)(intptr_t)path_cstr;
    if (!p || !*p) return -1;
#ifdef _WIN32
    wchar_t* wp = spec_win_utf8_to_wide(p);
    if (!wp) return -1;
    struct _stat64 st;
    int r = _wstat64(wp, &st);
    free(wp);
    if (r != 0) return -1;
    return (long long)st.st_size;
#else
    struct stat st;
    if (stat(p, &st) != 0) return -1;
    return (long long)st.st_size;
#endif
}

bool spec_pal_dir_mkdir(long long path_cstr) {
    const char* p = (const char*)(intptr_t)path_cstr;
    if (!p || !*p) return false;
#ifdef _WIN32
    wchar_t* wp = spec_win_utf8_to_wide(p);
    if (!wp) return false;
    int r = _wmkdir(wp);
    free(wp);
    return r == 0;
#else
    return mkdir(p, 0755) == 0;
#endif
}

bool spec_pal_dir_rmdir(long long path_cstr) {
    const char* p = (const char*)(intptr_t)path_cstr;
    if (!p || !*p) return false;
#ifdef _WIN32
    wchar_t* wp = spec_win_utf8_to_wide(p);
    if (!wp) return false;
    int r = _wrmdir(wp);
    free(wp);
    return r == 0;
#else
    return rmdir(p) == 0;
#endif
}
