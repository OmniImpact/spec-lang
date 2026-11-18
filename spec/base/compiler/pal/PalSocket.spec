#! Package base:compiler:pal
#! Emits the TCP networking and socket C PAL (`spec_pal_tcp_*`, `spec_pal_socket_*`, `spec_socket_*`).

Class of OsDispatch is PalSocket{
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
		return '''static inline void _spec_set_last_os_sock_error(const char* fallback) {
    if (errno != 0) {
        _spec_set_sock_error(strerror(errno));
        return;
    }
    _spec_set_sock_error(fallback ? fallback : "Socket error");
}

long long spec_pal_tcp_connect(long long host_cstr, long long port, long long timeout_ms) {
    const char* h = (const char*)(intptr_t)host_cstr;
    if (!h || !*h || port <= 0 || port > 65535) {
        _spec_set_sock_error("Socket error: Invalid host or port");
        return -1;
    }
    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%lld", port);

    struct addrinfo hints, *res = NULL, *rp = NULL;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    int gai_rc = getaddrinfo(h, port_str, &hints, &res);
    if (gai_rc != 0 || !res) {
        _spec_set_sock_error(gai_strerror(gai_rc));
        return -1;
    }

    long long sock_fd = -1;
    int last_err = 0;
    for (rp = res; rp != NULL; rp = rp->ai_next) {
        int s = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (s < 0) { last_err = errno; continue; }
        if (timeout_ms > 0) {
            struct timeval tv;
            tv.tv_sec = timeout_ms / 1000;
            tv.tv_usec = (timeout_ms % 1000) * 1000;
            setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, (const void*)&tv, sizeof(tv));
            setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, (const void*)&tv, sizeof(tv));
        }
        if (connect(s, rp->ai_addr, rp->ai_addrlen) == 0) {
            sock_fd = (long long)s;
            break;
        }
        last_err = errno;
        close(s);
    }
    freeaddrinfo(res);
    if (sock_fd < 0) {
        _spec_set_sock_error(last_err != 0 ? strerror(last_err) : "Socket error: Connection failed");
    }
    return sock_fd;
}

long long spec_pal_tcp_listen(long long host_cstr, long long port, long long backlog) {
    if (port <= 0 || port > 65535) {
        _spec_set_sock_error("Socket error: Invalid port");
        return -1;
    }
    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%lld", port);
    const char* h = (const char*)(intptr_t)host_cstr;
    if (h && !*h) h = NULL;

    struct addrinfo hints, *res = NULL;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_PASSIVE;

    int gai_rc = getaddrinfo(h, port_str, &hints, &res);
    if (gai_rc != 0 || !res) {
        _spec_set_sock_error(gai_strerror(gai_rc));
        return -1;
    }

    int s = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (s < 0) { _spec_set_last_os_sock_error("Socket error: socket() failed"); freeaddrinfo(res); return -1; }
    int opt = 1;
    setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    if (bind(s, res->ai_addr, res->ai_addrlen) != 0 || listen(s, backlog > 0 ? (int)backlog : 128) != 0) {
        _spec_set_last_os_sock_error("Socket error: bind/listen failed");
        close(s);
        freeaddrinfo(res);
        return -1;
    }
    freeaddrinfo(res);
    return (long long)s;
}

long long spec_pal_socket_accept(long long fd) {
    if (fd < 0) {
        _spec_set_sock_error("Socket error: Socket is closed or invalid");
        return -1;
    }
    int s = accept((int)fd, NULL, NULL);
    if (s < 0) {
        _spec_set_last_os_sock_error("Socket error: accept() failed");
    }
    return (long long)s;
}

long long spec_pal_socket_send(long long fd, long long data_addr, long long len) {
    if (fd < 0) {
        _spec_set_sock_error("Socket error: Socket is closed or invalid");
        return -1;
    }
    if (!data_addr || len <= 0) return 0;
    const void* ptr = (const void*)(intptr_t)data_addr;
    ssize_t n = send((int)fd, ptr, (size_t)len, 0);
    if (n < 0) {
        _spec_set_last_os_sock_error("Socket error: send() failed");
        return -1;
    }
    return (long long)n;
}

long long spec_pal_socket_recv(long long fd, long long dst_addr, long long max_bytes) {
    if (fd < 0) {
        _spec_set_sock_error("Socket error: Socket is closed or invalid");
        return -1;
    }
    if (!dst_addr || max_bytes <= 0) return 0;
    void* ptr = (void*)(intptr_t)dst_addr;
    ssize_t n = recv((int)fd, ptr, (size_t)max_bytes, 0);
    if (n < 0) {
        _spec_set_last_os_sock_error("Socket error: recv() failed");
        return -1;
    }
    return (long long)n;
}

long long spec_socket_close(long long fd) {
    if (fd < 0) return 0;
    close((int)fd);
    return 0;
}

long long spec_socket_poll(long long fd, long long mode, long long timeout_ms) {
    if (fd < 0) return -1;
    struct pollfd pfd;
    pfd.fd = (int)fd;
    pfd.events = 0;
    if (mode & 1) pfd.events |= POLLIN;
    if (mode & 2) pfd.events |= POLLOUT;
    pfd.revents = 0;
    int ret = poll(&pfd, 1, (int)timeout_ms);
    if (ret > 0) return (pfd.revents & (POLLIN | POLLOUT)) ? 1 : 0;
    return (ret == 0) ? 0 : -1;
}

long long spec_socket_set_timeout(long long fd, long long timeout_ms) {
    if (fd < 0) return -1;
    struct timeval tv;
    tv.tv_sec = timeout_ms / 1000;
    tv.tv_usec = (timeout_ms % 1000) * 1000;
    setsockopt((int)fd, SOL_SOCKET, SO_RCVTIMEO, (const void*)&tv, sizeof(tv));
    setsockopt((int)fd, SOL_SOCKET, SO_SNDTIMEO, (const void*)&tv, sizeof(tv));
    return 0;
}''';
	}

	replace Function of String is macos(){
		return :linux();
	}

	replace Function of String is windows(){
		return '''static void _spec_ensure_winsock(void) {
    static bool init = false;
    if (!init) {
        WSADATA wsa;
        WSAStartup(MAKEWORD(2, 2), &wsa);
        init = true;
    }
}

static inline void _spec_set_last_os_sock_error(const char* fallback) {
    int err = WSAGetLastError();
    if (err != 0) {
        snprintf(_spec_last_sock_err, sizeof(_spec_last_sock_err), "Socket error: WSA error %d", err);
        return;
    }
    _spec_set_sock_error(fallback ? fallback : "Socket error");
}

long long spec_pal_tcp_connect(long long host_cstr, long long port, long long timeout_ms) {
    const char* h = (const char*)(intptr_t)host_cstr;
    if (!h || !*h || port <= 0 || port > 65535) {
        _spec_set_sock_error("Socket error: Invalid host or port");
        return -1;
    }
    _spec_ensure_winsock();
    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%lld", port);

    struct addrinfo hints, *res = NULL, *rp = NULL;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    int gai_rc = getaddrinfo(h, port_str, &hints, &res);
    if (gai_rc != 0 || !res) {
        snprintf(_spec_last_sock_err, sizeof(_spec_last_sock_err), "Socket error: getaddrinfo failed (%d)", gai_rc);
        return -1;
    }

    long long sock_fd = -1;
    int last_err = 0;
    for (rp = res; rp != NULL; rp = rp->ai_next) {
        SOCKET s = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (s == INVALID_SOCKET) { last_err = WSAGetLastError(); continue; }
        if (timeout_ms > 0) {
            DWORD tv = (DWORD)timeout_ms;
            setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof(tv));
            setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, (const char*)&tv, sizeof(tv));
        }
        if (connect(s, rp->ai_addr, (int)rp->ai_addrlen) == 0) {
            sock_fd = (long long)s;
            break;
        }
        last_err = WSAGetLastError();
        closesocket(s);
    }
    freeaddrinfo(res);
    if (sock_fd < 0) {
        snprintf(_spec_last_sock_err, sizeof(_spec_last_sock_err), "Socket error: WSA error %d", last_err);
    }
    return sock_fd;
}

long long spec_pal_tcp_listen(long long host_cstr, long long port, long long backlog) {
    if (port <= 0 || port > 65535) {
        _spec_set_sock_error("Socket error: Invalid port");
        return -1;
    }
    _spec_ensure_winsock();
    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%lld", port);
    const char* h = (const char*)(intptr_t)host_cstr;
    if (h && !*h) h = NULL;

    struct addrinfo hints, *res = NULL;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_PASSIVE;

    int gai_rc = getaddrinfo(h, port_str, &hints, &res);
    if (gai_rc != 0 || !res) {
        snprintf(_spec_last_sock_err, sizeof(_spec_last_sock_err), "Socket error: getaddrinfo failed (%d)", gai_rc);
        return -1;
    }

    SOCKET s = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (s == INVALID_SOCKET) { _spec_set_last_os_sock_error("Socket error: socket() failed"); freeaddrinfo(res); return -1; }
    BOOL opt = TRUE;
    setsockopt(s, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));
    if (bind(s, res->ai_addr, (int)res->ai_addrlen) != 0 || listen(s, backlog > 0 ? (int)backlog : 128) != 0) {
        _spec_set_last_os_sock_error("Socket error: bind/listen failed");
        closesocket(s);
        freeaddrinfo(res);
        return -1;
    }
    freeaddrinfo(res);
    return (long long)s;
}

long long spec_pal_socket_accept(long long fd) {
    if (fd < 0) {
        _spec_set_sock_error("Socket error: Socket is closed or invalid");
        return -1;
    }
    SOCKET s = accept((SOCKET)fd, NULL, NULL);
    if (s == INVALID_SOCKET) {
        _spec_set_last_os_sock_error("Socket error: accept() failed");
        return -1;
    }
    return (long long)s;
}

long long spec_pal_socket_send(long long fd, long long data_addr, long long len) {
    if (fd < 0) {
        _spec_set_sock_error("Socket error: Socket is closed or invalid");
        return -1;
    }
    if (!data_addr || len <= 0) return 0;
    const void* ptr = (const void*)(intptr_t)data_addr;
    int n = send((SOCKET)fd, (const char*)ptr, (int)len, 0);
    if (n == SOCKET_ERROR) {
        _spec_set_last_os_sock_error("Socket error: send() failed");
        return -1;
    }
    return (long long)n;
}

long long spec_pal_socket_recv(long long fd, long long dst_addr, long long max_bytes) {
    if (fd < 0) {
        _spec_set_sock_error("Socket error: Socket is closed or invalid");
        return -1;
    }
    if (!dst_addr || max_bytes <= 0) return 0;
    void* ptr = (void*)(intptr_t)dst_addr;
    int n = recv((SOCKET)fd, (char*)ptr, (int)max_bytes, 0);
    if (n < 0) {
        _spec_set_last_os_sock_error("Socket error: recv() failed");
        return -1;
    }
    return (long long)n;
}

long long spec_socket_close(long long fd) {
    if (fd < 0) return 0;
    closesocket((SOCKET)fd);
    return 0;
}

long long spec_socket_poll(long long fd, long long mode, long long timeout_ms) {
    if (fd < 0) return -1;
    WSAPOLLFD pfd;
    pfd.fd = (SOCKET)fd;
    pfd.events = 0;
    if (mode & 1) pfd.events |= POLLIN;
    if (mode & 2) pfd.events |= POLLOUT;
    pfd.revents = 0;
    int ret = WSAPoll(&pfd, 1, (INT)timeout_ms);
    if (ret > 0) return (pfd.revents & (POLLIN | POLLOUT)) ? 1 : 0;
    return (ret == 0) ? 0 : -1;
}

long long spec_socket_set_timeout(long long fd, long long timeout_ms) {
    if (fd < 0) return -1;
    DWORD tv = (timeout_ms > 0) ? (DWORD)timeout_ms : 0;
    setsockopt((SOCKET)fd, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof(tv));
    setsockopt((SOCKET)fd, SOL_SOCKET, SO_SNDTIMEO, (const char*)&tv, sizeof(tv));
    return 0;
}''';
	}

	Function of String is emitBody(){
		return ```static __thread char _spec_last_sock_err[128] = "";

static inline void _spec_set_sock_error(const char* msg) {
    const char* m = msg ? msg : "Socket error";
    snprintf(_spec_last_sock_err, sizeof(_spec_last_sock_err), "%s", m);
}

long long spec_pal_socket_last_error(void) {
    return (long long)(intptr_t)_spec_last_sock_err;
}

{{:getOsBlock(separatePosix: false)}}
```;
	}
}
