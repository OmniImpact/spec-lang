#! Package base:compiler:pal
#! Emits the directory and path metadata C PAL (`spec_pal_dir_*`, `spec_exe_dir`, `spec_file_size`).

Class is PalDir{
	namespace: ['base', 'compiler', 'pal'];

	replace Function is init(){
	}

	Function of String is emitBody(){
		return '''long long spec_pal_dir_open(SpecBuf* path) {
    if (!path || path->length == 0) return 0;
    DIR* d = opendir(spec_buf_to_cstring(path));
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

String spec_pal_last_error(void) {
    const char* m = strerror(errno);
    if (!m) m = "Unknown error";
    return spec_string_from_bytes(m, strlen(m));
}

SpecBuf* spec_exe_dir(void) {
    char buf[4096];
    if (!spec_pal_get_exe_path(buf, sizeof(buf))) return spec_string_from_bytes(".", 1);
    char* slash = strrchr(buf, '/');
#if defined(_WIN32)
    char* bslash = strrchr(buf, '\\');
    if (bslash > slash) slash = bslash;
#endif
    if (!slash) return spec_string_from_bytes(".", 1);
    return spec_string_from_bytes(buf, (size_t)(slash - buf));
}

long long spec_file_size(SpecBuf* path) {
    struct stat st;
    if (stat(spec_buf_to_cstring(path), &st) != 0) return -1;
    return (long long)st.st_size;
}
''';
	}
}
