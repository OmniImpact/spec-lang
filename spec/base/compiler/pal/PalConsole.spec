#! Package base:compiler:pal
#! Emits the console I/O and terminal geometry C PAL (`spec_print*`, `spec_error_line`,
#! `spec_read_*`, `spec_console_binary_mode`, `spec_term_*`).

Class is PalConsole{
	namespace: ['base', 'compiler', 'pal'];

	replace Function is init(){
	}

	Function of String is emitBody(){
		return '''long long spec_term_width(void) {
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

void spec_error_line(String s) {
    const char* cs = s ? spec_buf_to_cstring((SpecBuf*)s) : "";
    fprintf(stderr, "%s\n", cs);
}

void spec_print_line(String s) {
    printf("%s\n", s ? spec_buf_to_cstring((SpecBuf*)s) : "");
}

void spec_print(String s) {
    printf("%s", s ? spec_buf_to_cstring((SpecBuf*)s) : "");
    fflush(stdout);
}

void spec_read_line(SpecClosure* on_line) {
#if defined(_WIN32)
    char buf[4096];
    if (fgets(buf, sizeof(buf), stdin)) {
        size_t len = strlen(buf);
        while (len > 0 && (buf[len - 1] == '\n' || buf[len - 1] == '\r')) {
            buf[len - 1] = '\0';
            len--;
        }
        String text = spec_string_from_chars(buf);
        spec_call_closure_str(on_line, text);
        spec_release(text);
    }
#else
    char* _line = NULL;
    size_t _cap = 0;
    ssize_t _n = getline(&_line, &_cap, stdin);
    if (_n >= 0) {
        if (_n > 0 && _line[_n - 1] == '\n') _line[_n - 1] = '\0';
        String text = spec_string_from_chars(_line);
        spec_call_closure_str(on_line, text);
        spec_release(text);
    }
    free(_line);
#endif
}

String spec_read_bytes(long long count) {
    if (count <= 0) return spec_string_from_bytes("", 0);
    size_t want = (size_t)count;
    char* buf = (char*)spec_xmalloc(want);
    size_t got = 0;
    while (got < want) {
        size_t n = fread(buf + got, 1, want - got, stdin);
        if (n == 0) break;
        got += n;
    }
    String res = spec_string_from_bytes(buf, got);
    free(buf);
    return res;
}

void spec_console_binary_mode(void) {
#if defined(_WIN32)
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
#endif
}
''';
	}
}
