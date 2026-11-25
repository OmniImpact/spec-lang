long long spec_term_width(void) {
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

long long spec_term_is_tty(void) {
#ifdef _WIN32
    DWORD mode = 0;
    if (GetConsoleMode(GetStdHandle(STD_OUTPUT_HANDLE), &mode)) return 1;
    return _isatty(_fileno(stdout)) ? 1 : 0;
#else
    return isatty(1) ? 1 : 0;
#endif
}

long long spec_term_enable_vt(void) {
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    if (hOut == INVALID_HANDLE_VALUE) return 0;
    DWORD mode = 0;
    if (!GetConsoleMode(hOut, &mode)) return 0;
    if (SetConsoleMode(hOut, mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING)) return 1;
    return 0;
#else
    return isatty(1) ? 1 : 0;
#endif
}

static inline void _spec_win_init_utf8_console(void) {
#ifdef _WIN32
    static _Atomic int _inited = 0;
    if (atomic_load_explicit(&_inited, memory_order_relaxed) == 0) {
        SetConsoleOutputCP(CP_UTF8);
        SetConsoleCP(CP_UTF8);
        atomic_store_explicit(&_inited, 1, memory_order_relaxed);
    }
#endif
}

void spec_pal_error_line(long long data_addr, long long len) {
    _spec_win_init_utf8_console();
    if (data_addr && len > 0) fwrite((const void*)(intptr_t)data_addr, 1, (size_t)len, stderr);
    fputc('\n', stderr);
}

void spec_pal_print_line(long long data_addr, long long len) {
    _spec_win_init_utf8_console();
    if (data_addr && len > 0) fwrite((const void*)(intptr_t)data_addr, 1, (size_t)len, stdout);
    fputc('\n', stdout);
}

void spec_pal_print(long long data_addr, long long len) {
    _spec_win_init_utf8_console();
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
        if (ch == '\n') break;
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
    while (len > 0 && (buf[len - 1] == '\n' || buf[len - 1] == '\r')) len--;
    buf[len] = '\0';
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
#if defined(_WIN32)
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
#endif
}

#if !defined(_WIN32)
static struct termios _spec_orig_termios;
static bool _spec_raw_active = false;
static bool _spec_raw_atexit_reg = false;

static void _spec_restore_termios(void) {
    if (_spec_raw_active) {
        tcsetattr(STDIN_FILENO, TCSAFLUSH, &_spec_orig_termios);
        const char* seq = "\x1b[<u\x1b[?25h\x1b[?1049l";
        ssize_t _unused = write(STDOUT_FILENO, seq, strlen(seq));
        (void)_unused;
        _spec_raw_active = false;
    }
}
#endif

void spec_pal_raw_mode(long long enable) {
#if !defined(_WIN32)
    if (!isatty(STDIN_FILENO)) return;
    if (enable) {
        if (!_spec_raw_active) {
            if (tcgetattr(STDIN_FILENO, &_spec_orig_termios) == 0) {
                if (!_spec_raw_atexit_reg) {
                    atexit(_spec_restore_termios);
                    _spec_raw_atexit_reg = true;
                }
                struct termios raw = _spec_orig_termios;
                raw.c_iflag &= ~(unsigned long)(BRKINT | ICRNL | INPCK | ISTRIP | IXON);
                raw.c_oflag &= ~(unsigned long)(OPOST);
                raw.c_cflag |= (unsigned long)(CS8);
                raw.c_lflag &= ~(unsigned long)(ECHO | ICANON | IEXTEN | ISIG);
                raw.c_cc[VMIN] = 0;
                raw.c_cc[VTIME] = 0;
                if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) == 0) {
                    _spec_raw_active = true;
                }
            }
        }
    } else {
        if (_spec_raw_active) {
            tcsetattr(STDIN_FILENO, TCSAFLUSH, &_spec_orig_termios);
            _spec_raw_active = false;
        }
    }
#else
    (void)enable;
#endif
}

long long spec_pal_poll_byte(long long timeout_ms) {
#if !defined(_WIN32)
    struct pollfd pfd;
    pfd.fd = STDIN_FILENO;
    pfd.events = POLLIN;
    pfd.revents = 0;
    int t = timeout_ms < 0 ? -1 : (int)timeout_ms;
    int rc = poll(&pfd, 1, t);
    if (rc > 0 && (pfd.revents & POLLIN)) {
        unsigned char ch = 0;
        ssize_t n = read(STDIN_FILENO, &ch, 1);
        if (n == 1) return (long long)ch;
    }
    return -1;
#else
    (void)timeout_ms;
    return -1;
#endif
}
