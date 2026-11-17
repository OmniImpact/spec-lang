#! Package base:compiler:pal
#! Emits the console I/O and terminal geometry C PAL (`spec_pal_print*`, `spec_pal_error_line`,
#! `spec_pal_read_*`, `spec_console_binary_mode`, `spec_term_*`).

Class of OsDispatch is PalConsole{
	namespace: ['base', 'compiler', 'pal'];

	replace Array of Array of String is using: [
		['base', 'sys', OsDispatch]
	];

	replace Function is init(){
	}

	replace Function of String is linux(){
		return '';
	}

	replace Function of String is macos(){
		return '';
	}

	replace Function of String is windows(){
		return '''    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);''';
	}

	Function of String is emitBody(){
		return ```long long spec_term_width(void) {
    long long w = 0;
    if (spec_pal_get_terminal_size(&w, NULL) && w > 0) return w;
    char* cols = getenv("COLUMNS");
    if (cols) return (long long)atoi(cols);
    return 78;
}

long long spec_term_height(void) {
    long long h = 0;
    if (spec_pal_get_terminal_size(NULL, &h) && h > 0) return h;
    char* lines = getenv("LINES");
    if (lines) return (long long)atoi(lines);
    return 24;
}

void spec_pal_error_line(long long data_addr, long long len) {
    if (data_addr && len > 0) fwrite((const void*)(intptr_t)data_addr, 1, (size_t)len, stderr);
    fputc('\\n', stderr);
}

void spec_pal_print_line(long long data_addr, long long len) {
    if (data_addr && len > 0) fwrite((const void*)(intptr_t)data_addr, 1, (size_t)len, stdout);
    fputc('\\n', stdout);
}

void spec_pal_print(long long data_addr, long long len) {
    if (data_addr && len > 0) fwrite((const void*)(intptr_t)data_addr, 1, (size_t)len, stdout);
    fflush(stdout);
}

long long spec_pal_read_line(long long out_len_addr) {
    long long* out_len = (long long*)(intptr_t)out_len_addr;
    if (out_len) *out_len = 0;
    size_t cap = 256;
    size_t len = 0;
    char* buf = (char*)spec_xmalloc(cap);
    int ch;
    bool got_any = false;
    while ((ch = fgetc(stdin)) != EOF) {
        got_any = true;
        if (ch == '\\n') break;
        if (len + 1 >= cap) {
            cap *= 2;
            buf = (char*)spec_xrealloc(buf, cap);
        }
        buf[len++] = (char)ch;
    }
    if (!got_any && len == 0) {
        free(buf);
        return 0;
    }
    while (len > 0 && (buf[len - 1] == '\\n' || buf[len - 1] == '\\r')) len--;
    buf[len] = '\\0';
    if (out_len) *out_len = (long long)len;
    return (long long)(intptr_t)buf;
}

void spec_pal_console_free(long long ptr) {
    if (ptr) free((void*)(intptr_t)ptr);
}

long long spec_pal_read_bytes(long long dst_addr, long long count) {
    if (!dst_addr || count <= 0) return 0;
    char* buf = (char*)(intptr_t)dst_addr;
    size_t want = (size_t)count;
    size_t got = 0;
    while (got < want) {
        size_t n = fread(buf + got, 1, want - got, stdin);
        if (n == 0) break;
        got += n;
    }
    return (long long)got;
}

void spec_console_binary_mode(void) {
{{self:getOsBlock(separatePosix: false)}}
}
```;
	}
}
