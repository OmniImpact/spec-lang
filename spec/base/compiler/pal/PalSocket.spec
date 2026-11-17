#! Package base:compiler:pal
#! Emits the TCP networking and socket C PAL (`spec_tcp_*`, `spec_socket_*`, `spec_pal_socket_*`).

Class is PalSocket{
	namespace: ['base', 'compiler', 'pal'];

	replace Function is init(){
	}

	Function of String is emitHeader(){
		return '''/* Networking & Sockets Floor */
#if defined(_WIN32)
static void _spec_ensure_winsock(void) {
    static bool init = false;
    if (!init) {
        WSADATA wsa;
        WSAStartup(MAKEWORD(2, 2), &wsa);
        init = true;
    }
}
#endif
''';
	}

	Function of String is emitBody(){
		return '''static inline void _spec_emit_last_sock_error(SpecClosure* on_error, const char* fallback) {
    if (!on_error || !on_error->fn) return;
#if defined(_WIN32)
    int err = WSAGetLastError();
    if (err != 0) {
        char ebuf[64];
        snprintf(ebuf, sizeof(ebuf), "Socket error: WSA error %d", err);
        _spec_emit_str_error(on_error, ebuf);
        return;
    }
#else
    if (errno != 0) {
        _spec_emit_str_error(on_error, strerror(errno));
        return;
    }
#endif
    _spec_emit_str_error(on_error, fallback ? fallback : "Socket error");
}

long long spec_tcp_connect_cb(String host, long long port, long long timeout_ms, SpecClosure* on_error) {
    if (!host || port <= 0 || port > 65535) {
        _spec_emit_str_error(on_error, "Socket error: Invalid host or port");
        return -1;
    }
#if defined(_WIN32)
    _spec_ensure_winsock();
#endif
    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%lld", port);
    const char* h = spec_buf_to_cstring((SpecBuf*)host);

    struct addrinfo hints, *res = NULL, *rp = NULL;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    int gai_rc = getaddrinfo(h, port_str, &hints, &res);
    if (gai_rc != 0 || !res) {
#if defined(_WIN32)
        char ebuf[96];
        snprintf(ebuf, sizeof(ebuf), "Socket error: getaddrinfo failed (%d)", gai_rc);
        _spec_emit_str_error(on_error, ebuf);
#else
        _spec_emit_str_error(on_error, gai_strerror(gai_rc));
#endif
        return -1;
    }

    long long sock_fd = -1;
    int last_err = 0;
    for (rp = res; rp != NULL; rp = rp->ai_next) {
#if defined(_WIN32)
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
#else
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
#endif
    }
    freeaddrinfo(res);
    if (sock_fd < 0) {
#if defined(_WIN32)
        char ebuf[64];
        snprintf(ebuf, sizeof(ebuf), "Socket error: WSA error %d", last_err);
        _spec_emit_str_error(on_error, ebuf);
#else
        _spec_emit_str_error(on_error, last_err != 0 ? strerror(last_err) : "Socket error: Connection failed");
#endif
    }
    return sock_fd;
}

long long spec_tcp_connect(String host, long long port, long long timeout_ms) {
    return spec_tcp_connect_cb(host, port, timeout_ms, NULL);
}

long long spec_tcp_listen_cb(String host, long long port, long long backlog, SpecClosure* on_error) {
    if (port <= 0 || port > 65535) {
        _spec_emit_str_error(on_error, "Socket error: Invalid port");
        return -1;
    }
#if defined(_WIN32)
    _spec_ensure_winsock();
#endif
    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%lld", port);
    const char* h = (host && host->length > 0) ? spec_buf_to_cstring((SpecBuf*)host) : NULL;

    struct addrinfo hints, *res = NULL;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_PASSIVE;

    int gai_rc = getaddrinfo(h, port_str, &hints, &res);
    if (gai_rc != 0 || !res) {
#if defined(_WIN32)
        char ebuf[96];
        snprintf(ebuf, sizeof(ebuf), "Socket error: getaddrinfo failed (%d)", gai_rc);
        _spec_emit_str_error(on_error, ebuf);
#else
        _spec_emit_str_error(on_error, gai_strerror(gai_rc));
#endif
        return -1;
    }

#if defined(_WIN32)
    SOCKET s = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (s == INVALID_SOCKET) { _spec_emit_last_sock_error(on_error, "Socket error: socket() failed"); freeaddrinfo(res); return -1; }
    BOOL opt = TRUE;
    setsockopt(s, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));
    if (bind(s, res->ai_addr, (int)res->ai_addrlen) != 0 || listen(s, backlog > 0 ? (int)backlog : 128) != 0) {
        _spec_emit_last_sock_error(on_error, "Socket error: bind/listen failed");
        closesocket(s);
        freeaddrinfo(res);
        return -1;
    }
    freeaddrinfo(res);
    return (long long)s;
#else
    int s = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (s < 0) { _spec_emit_last_sock_error(on_error, "Socket error: socket() failed"); freeaddrinfo(res); return -1; }
    int opt = 1;
    setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    if (bind(s, res->ai_addr, res->ai_addrlen) != 0 || listen(s, backlog > 0 ? (int)backlog : 128) != 0) {
        _spec_emit_last_sock_error(on_error, "Socket error: bind/listen failed");
        close(s);
        freeaddrinfo(res);
        return -1;
    }
    freeaddrinfo(res);
    return (long long)s;
#endif
}

long long spec_tcp_listen(String host, long long port, long long backlog) {
    return spec_tcp_listen_cb(host, port, backlog, NULL);
}

long long spec_socket_accept_cb(long long fd, SpecClosure* on_error) {
    if (fd < 0) {
        _spec_emit_str_error(on_error, "Socket error: Socket is closed or invalid");
        return -1;
    }
#if defined(_WIN32)
    SOCKET s = accept((SOCKET)fd, NULL, NULL);
    if (s == INVALID_SOCKET) {
        _spec_emit_last_sock_error(on_error, "Socket error: accept() failed");
        return -1;
    }
    return (long long)s;
#else
    int s = accept((int)fd, NULL, NULL);
    if (s < 0) {
        _spec_emit_last_sock_error(on_error, "Socket error: accept() failed");
    }
    return (long long)s;
#endif
}

long long spec_socket_accept(long long fd) {
    return spec_socket_accept_cb(fd, NULL);
}

long long spec_pal_socket_send(long long fd, long long data_addr, long long len, SpecClosure* on_error) {
    if (fd < 0) {
        _spec_emit_str_error(on_error, "Socket error: Socket is closed or invalid");
        return -1;
    }
    if (!data_addr || len <= 0) return 0;
    const void* ptr = (const void*)(intptr_t)data_addr;
#if defined(_WIN32)
    int n = send((SOCKET)fd, (const char*)ptr, (int)len, 0);
    if (n == SOCKET_ERROR) {
        _spec_emit_last_sock_error(on_error, "Socket error: send() failed");
        return -1;
    }
    return (long long)n;
#else
    ssize_t n = send((int)fd, ptr, (size_t)len, 0);
    if (n < 0) {
        _spec_emit_last_sock_error(on_error, "Socket error: send() failed");
        return -1;
    }
    return (long long)n;
#endif
}

long long spec_pal_socket_recv(long long fd, long long dst_addr, long long max_bytes, SpecClosure* on_error) {
    if (fd < 0) {
        _spec_emit_str_error(on_error, "Socket error: Socket is closed or invalid");
        return -1;
    }
    if (!dst_addr || max_bytes <= 0) return 0;
    void* ptr = (void*)(intptr_t)dst_addr;
#if defined(_WIN32)
    int n = recv((SOCKET)fd, (char*)ptr, (int)max_bytes, 0);
    if (n < 0) {
        _spec_emit_last_sock_error(on_error, "Socket error: recv() failed");
        return -1;
    }
    return (long long)n;
#else
    ssize_t n = recv((int)fd, ptr, (size_t)max_bytes, 0);
    if (n < 0) {
        _spec_emit_last_sock_error(on_error, "Socket error: recv() failed");
        return -1;
    }
    return (long long)n;
#endif
}

long long spec_socket_send_str_cb(long long fd, String str, SpecClosure* on_error) {
    if (fd < 0) {
        _spec_emit_str_error(on_error, "Socket error: Socket is closed or invalid");
        return -1;
    }
    if (!str || str->length == 0) return 0;
    const char* cs = spec_buf_to_cstring((SpecBuf*)str);
    size_t len = strlen(cs);
#if defined(_WIN32)
    int n = send((SOCKET)fd, cs, (int)len, 0);
    if (n == SOCKET_ERROR) {
        _spec_emit_last_sock_error(on_error, "Socket error: send() failed");
        return -1;
    }
    return (long long)n;
#else
    ssize_t n = send((int)fd, cs, len, 0);
    if (n < 0) {
        _spec_emit_last_sock_error(on_error, "Socket error: send() failed");
        return -1;
    }
    return (long long)n;
#endif
}

long long spec_socket_send_str(long long fd, String str) {
    return spec_socket_send_str_cb(fd, str, NULL);
}

long long spec_socket_close(long long fd) {
    if (fd < 0) return 0;
#if defined(_WIN32)
    closesocket((SOCKET)fd);
#else
    close((int)fd);
#endif
    return 0;
}

long long spec_socket_poll(long long fd, long long mode, long long timeout_ms) {
    if (fd < 0) return -1;
#if defined(_WIN32)
    WSAPOLLFD pfd;
    pfd.fd = (SOCKET)fd;
    pfd.events = 0;
    if (mode & 1) pfd.events |= POLLIN;
    if (mode & 2) pfd.events |= POLLOUT;
    pfd.revents = 0;
    int ret = WSAPoll(&pfd, 1, (INT)timeout_ms);
    if (ret > 0) return (pfd.revents & (POLLIN | POLLOUT)) ? 1 : 0;
    return (ret == 0) ? 0 : -1;
#else
    struct pollfd pfd;
    pfd.fd = (int)fd;
    pfd.events = 0;
    if (mode & 1) pfd.events |= POLLIN;
    if (mode & 2) pfd.events |= POLLOUT;
    pfd.revents = 0;
    int ret = poll(&pfd, 1, (int)timeout_ms);
    if (ret > 0) return (pfd.revents & (POLLIN | POLLOUT)) ? 1 : 0;
    return (ret == 0) ? 0 : -1;
#endif
}

long long spec_socket_set_timeout(long long fd, long long timeout_ms) {
    if (fd < 0) return -1;
#if defined(_WIN32)
    DWORD tv = (timeout_ms > 0) ? (DWORD)timeout_ms : 0;
    setsockopt((SOCKET)fd, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof(tv));
    setsockopt((SOCKET)fd, SOL_SOCKET, SO_SNDTIMEO, (const char*)&tv, sizeof(tv));
#else
    struct timeval tv;
    tv.tv_sec = timeout_ms / 1000;
    tv.tv_usec = (timeout_ms % 1000) * 1000;
    setsockopt((int)fd, SOL_SOCKET, SO_RCVTIMEO, (const void*)&tv, sizeof(tv));
    setsockopt((int)fd, SOL_SOCKET, SO_SNDTIMEO, (const void*)&tv, sizeof(tv));
#endif
    return 0;
}
''';
	}
}
