static __thread char _spec_last_win_err[256] = "";

static inline void _spec_set_win_error(const char* msg) {
    const char* m = msg ? msg : "Window error";
    snprintf(_spec_last_win_err, sizeof(_spec_last_win_err), "%s", m);
}

long long spec_pal_window_last_error(void) {
    return (long long)(intptr_t)_spec_last_win_err;
}

#if defined(__linux__)

/* Minimal Wayland + libdecor ABI declarations loaded dynamically via dlopen
 * so binaries without windowing have zero link-time dependencies. */
struct wl_display;
struct wl_registry;
struct wl_compositor;
struct wl_shm;
struct wl_shm_pool;
struct wl_buffer;
struct wl_surface;
struct wl_proxy;
struct wl_interface;

struct libdecor;
struct libdecor_frame;
struct libdecor_state;
struct libdecor_configuration;

struct spec_wl_registry_listener {
    void (*global)(void* data, struct wl_registry* registry, uint32_t name, const char* interface, uint32_t version);
    void (*global_remove)(void* data, struct wl_registry* registry, uint32_t name);
};

struct spec_libdecor_interface {
    void (*error)(struct libdecor* context, int error, const char* message);
    void (*reserved0)(void);
    void (*reserved1)(void);
    void (*reserved2)(void);
    void (*reserved3)(void);
    void (*reserved4)(void);
    void (*reserved5)(void);
    void (*reserved6)(void);
    void (*reserved7)(void);
    void (*reserved8)(void);
    void (*reserved9)(void);
};

struct spec_libdecor_frame_interface {
    void (*configure)(struct libdecor_frame* frame, struct libdecor_configuration* configuration, void* user_data);
    void (*close)(struct libdecor_frame* frame, void* user_data);
    void (*commit)(struct libdecor_frame* frame, void* user_data);
    void (*dismiss_popup)(struct libdecor_frame* frame, const char* seat_name, void* user_data);
    void (*reserved0)(void);
    void (*reserved1)(void);
    void (*reserved2)(void);
    void (*reserved3)(void);
    void (*reserved4)(void);
    void (*reserved5)(void);
    void (*reserved6)(void);
    void (*reserved7)(void);
    void (*reserved8)(void);
    void (*reserved9)(void);
};

static void* _spec_wl_so = NULL;
static void* _spec_decor_so = NULL;

static struct wl_display* (*_wl_display_connect)(const char*) = NULL;
static void (*_wl_display_disconnect)(struct wl_display*) = NULL;
static int (*_wl_display_roundtrip)(struct wl_display*) = NULL;
static int (*_wl_display_flush)(struct wl_display*) = NULL;
static struct wl_proxy* (*_wl_proxy_marshal_flags)(struct wl_proxy*, uint32_t, const struct wl_interface*, uint32_t, uint32_t, ...) = NULL;
static int (*_wl_proxy_add_listener)(struct wl_proxy*, void (**)(void), void*) = NULL;
static void (*_wl_proxy_destroy)(struct wl_proxy*) = NULL;
static uint32_t (*_wl_proxy_get_version)(struct wl_proxy*) = NULL;

static const struct wl_interface* _wl_registry_iface = NULL;
static const struct wl_interface* _wl_compositor_iface = NULL;
static const struct wl_interface* _wl_shm_iface = NULL;
static const struct wl_interface* _wl_shm_pool_iface = NULL;
static const struct wl_interface* _wl_buffer_iface = NULL;
static const struct wl_interface* _wl_surface_iface = NULL;

static struct libdecor* (*_libdecor_new)(struct wl_display*, struct spec_libdecor_interface*) = NULL;
static void (*_libdecor_unref)(struct libdecor*) = NULL;
static struct libdecor_frame* (*_libdecor_decorate)(struct libdecor*, struct wl_surface*, struct spec_libdecor_frame_interface*, void*) = NULL;
static void (*_libdecor_frame_unref)(struct libdecor_frame*) = NULL;
static void (*_libdecor_frame_set_title)(struct libdecor_frame*, const char*) = NULL;
static void (*_libdecor_frame_set_app_id)(struct libdecor_frame*, const char*) = NULL;
static void (*_libdecor_frame_set_visibility)(struct libdecor_frame*, bool) = NULL;
static void (*_libdecor_frame_map)(struct libdecor_frame*) = NULL;
static void (*_libdecor_frame_commit)(struct libdecor_frame*, struct libdecor_state*, struct libdecor_configuration*) = NULL;
static int (*_libdecor_dispatch)(struct libdecor*, int) = NULL;
static struct libdecor_state* (*_libdecor_state_new)(int, int) = NULL;
static void (*_libdecor_state_free)(struct libdecor_state*) = NULL;
static bool (*_libdecor_configuration_get_content_size)(struct libdecor_configuration*, struct libdecor_frame*, int*, int*) = NULL;

static bool _spec_win_init_libs(void) {
    if (_spec_wl_so && _spec_decor_so) return true;
    _spec_wl_so = dlopen("libwayland-client.so.0", RTLD_LAZY | RTLD_LOCAL);
    if (!_spec_wl_so) {
        _spec_set_win_error("Failed to load libwayland-client.so.0");
        return false;
    }
    _spec_decor_so = dlopen("libdecor-0.so.0", RTLD_LAZY | RTLD_LOCAL);
    if (!_spec_decor_so) {
        _spec_set_win_error("Failed to load libdecor-0.so.0");
        return false;
    }

    _wl_display_connect = dlsym(_spec_wl_so, "wl_display_connect");
    _wl_display_disconnect = dlsym(_spec_wl_so, "wl_display_disconnect");
    _wl_display_roundtrip = dlsym(_spec_wl_so, "wl_display_roundtrip");
    _wl_display_flush = dlsym(_spec_wl_so, "wl_display_flush");
    _wl_proxy_marshal_flags = dlsym(_spec_wl_so, "wl_proxy_marshal_flags");
    _wl_proxy_add_listener = dlsym(_spec_wl_so, "wl_proxy_add_listener");
    _wl_proxy_destroy = dlsym(_spec_wl_so, "wl_proxy_destroy");
    _wl_proxy_get_version = dlsym(_spec_wl_so, "wl_proxy_get_version");

    _wl_registry_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_registry_interface");
    _wl_compositor_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_compositor_interface");
    _wl_shm_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_shm_interface");
    _wl_shm_pool_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_shm_pool_interface");
    _wl_buffer_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_buffer_interface");
    _wl_surface_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_surface_interface");

    _libdecor_new = dlsym(_spec_decor_so, "libdecor_new");
    _libdecor_unref = dlsym(_spec_decor_so, "libdecor_unref");
    _libdecor_decorate = dlsym(_spec_decor_so, "libdecor_decorate");
    _libdecor_frame_unref = dlsym(_spec_decor_so, "libdecor_frame_unref");
    _libdecor_frame_set_title = dlsym(_spec_decor_so, "libdecor_frame_set_title");
    _libdecor_frame_set_app_id = dlsym(_spec_decor_so, "libdecor_frame_set_app_id");
    _libdecor_frame_set_visibility = dlsym(_spec_decor_so, "libdecor_frame_set_visibility");
    _libdecor_frame_map = dlsym(_spec_decor_so, "libdecor_frame_map");
    _libdecor_frame_commit = dlsym(_spec_decor_so, "libdecor_frame_commit");
    _libdecor_dispatch = dlsym(_spec_decor_so, "libdecor_dispatch");
    _libdecor_state_new = dlsym(_spec_decor_so, "libdecor_state_new");
    _libdecor_state_free = dlsym(_spec_decor_so, "libdecor_state_free");
    _libdecor_configuration_get_content_size = dlsym(_spec_decor_so, "libdecor_configuration_get_content_size");

    if (!_wl_display_connect || !_wl_proxy_marshal_flags || !_wl_surface_iface ||
        !_libdecor_new || !_libdecor_decorate || !_libdecor_dispatch || !_libdecor_state_new) {
        _spec_set_win_error("Missing required Wayland/libdecor symbols");
        return false;
    }
    return true;
}

typedef struct SpecWaylandWindow {
    bool in_use;
    bool configured;
    bool should_close;
    int width;
    int height;
    struct wl_display* display;
    struct wl_registry* registry;
    struct wl_compositor* compositor;
    struct wl_shm* shm;
    struct wl_surface* surface;
    struct wl_shm_pool* shm_pool;
    struct wl_buffer* buffer;
    void* shm_data;
    size_t shm_size;
    int shm_fd;
    struct libdecor* decor;
    struct libdecor_frame* frame;
} SpecWaylandWindow;

static SpecWaylandWindow** _spec_windows = NULL;
static size_t _spec_windows_cap = 0;

static long long _spec_alloc_window_slot(SpecWaylandWindow* win) {
    for (size_t i = 0; i < _spec_windows_cap; i++) {
        if (!_spec_windows[i]) {
            _spec_windows[i] = win;
            return (long long)(i + 1);
        }
    }
    size_t new_cap = _spec_windows_cap == 0 ? 8 : _spec_windows_cap * 2;
    SpecWaylandWindow** next = (SpecWaylandWindow**)realloc(_spec_windows, new_cap * sizeof(SpecWaylandWindow*));
    if (!next) return -1;
    for (size_t i = _spec_windows_cap; i < new_cap; i++) next[i] = NULL;
    _spec_windows = next;
    size_t idx = _spec_windows_cap;
    _spec_windows_cap = new_cap;
    _spec_windows[idx] = win;
    return (long long)(idx + 1);
}

static SpecWaylandWindow* _spec_get_window(long long handle) {
    if (handle <= 0) return NULL;
    size_t idx = (size_t)(handle - 1);
    if (idx >= _spec_windows_cap) return NULL;
    return _spec_windows[idx];
}

static void _spec_wl_reg_global(void* data, struct wl_registry* reg, uint32_t name, const char* iface, uint32_t version) {
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (strcmp(iface, "wl_compositor") == 0 && _wl_compositor_iface) {
        uint32_t v = version < 4 ? version : 4;
        w->compositor = (struct wl_compositor*)_wl_proxy_marshal_flags(
            (struct wl_proxy*)reg, 0 /* WL_REGISTRY_BIND */, _wl_compositor_iface, v, 0,
            name, iface, v, NULL);
    } else if (strcmp(iface, "wl_shm") == 0 && _wl_shm_iface) {
        w->shm = (struct wl_shm*)_wl_proxy_marshal_flags(
            (struct wl_proxy*)reg, 0 /* WL_REGISTRY_BIND */, _wl_shm_iface, 1, 0,
            name, iface, 1, NULL);
    }
}

static void _spec_wl_reg_remove(void* data, struct wl_registry* reg, uint32_t name) {
    (void)data; (void)reg; (void)name;
}

static const struct spec_wl_registry_listener _spec_reg_listener = {
    _spec_wl_reg_global,
    _spec_wl_reg_remove
};

static void _spec_decor_error(struct libdecor* ctx, int err, const char* msg) {
    (void)ctx; (void)err;
    _spec_set_win_error(msg ? msg : "libdecor error");
}

static struct spec_libdecor_interface _spec_decor_iface = {
    _spec_decor_error, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
};

static void _spec_release_shm(SpecWaylandWindow* w) {
    if (w->buffer) {
        _wl_proxy_destroy((struct wl_proxy*)w->buffer);
        w->buffer = NULL;
    }
    if (w->shm_pool) {
        _wl_proxy_destroy((struct wl_proxy*)w->shm_pool);
        w->shm_pool = NULL;
    }
    if (w->shm_data && w->shm_data != MAP_FAILED && w->shm_size > 0) {
        munmap(w->shm_data, w->shm_size);
        w->shm_data = NULL;
        w->shm_size = 0;
    }
    if (w->shm_fd >= 0) {
        close(w->shm_fd);
        w->shm_fd = -1;
    }
}

static bool _spec_ensure_shm_buffer(SpecWaylandWindow* w, int width, int height) {
    if (width <= 0) width = 800;
    if (height <= 0) height = 600;
    if (w->buffer && w->width == width && w->height == height) return true;

    _spec_release_shm(w);
    int stride = width * 4;
    size_t size = (size_t)stride * (size_t)height;

    char tmpl[] = "/tmp/spec_suit_shm_XXXXXX";
    int fd = mkstemp(tmpl);
    if (fd < 0) return false;
    unlink(tmpl);
    if (ftruncate(fd, (off_t)size) < 0) {
        close(fd);
        return false;
    }
    void* ptr = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (ptr == MAP_FAILED) {
        close(fd);
        return false;
    }

    uint32_t* px = (uint32_t*)ptr;
    size_t count = (size_t)width * (size_t)height;
    for (size_t i = 0; i < count; i++) {
        px[i] = 0xFF181C24u;
    }

    uint32_t shm_ver = _wl_proxy_get_version((struct wl_proxy*)w->shm);
    struct wl_shm_pool* pool = (struct wl_shm_pool*)_wl_proxy_marshal_flags(
        (struct wl_proxy*)w->shm, 0 /* WL_SHM_CREATE_POOL */, _wl_shm_pool_iface, shm_ver, 0,
        NULL, fd, (int32_t)size);
    if (!pool) {
        munmap(ptr, size);
        close(fd);
        return false;
    }

    uint32_t pool_ver = _wl_proxy_get_version((struct wl_proxy*)pool);
    struct wl_buffer* buf = (struct wl_buffer*)_wl_proxy_marshal_flags(
        (struct wl_proxy*)pool, 0 /* WL_SHM_POOL_CREATE_BUFFER */, _wl_buffer_iface, pool_ver, 0,
        NULL, 0, width, height, stride, 0 /* WL_SHM_FORMAT_ARGB8888 */);
    if (!buf) {
        _wl_proxy_destroy((struct wl_proxy*)pool);
        munmap(ptr, size);
        close(fd);
        return false;
    }

    w->width = width;
    w->height = height;
    w->shm_fd = fd;
    w->shm_data = ptr;
    w->shm_size = size;
    w->shm_pool = pool;
    w->buffer = buf;
    return true;
}

static void _spec_surface_present(SpecWaylandWindow* w) {
    if (!w->surface || !w->buffer) return;
    uint32_t sv = _wl_proxy_get_version((struct wl_proxy*)w->surface);
    _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 1 /* WL_SURFACE_ATTACH */, NULL, sv, 0, w->buffer, 0, 0);
    if (sv >= 4) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 9 /* WL_SURFACE_DAMAGE_BUFFER */, NULL, sv, 0, 0, 0, w->width, w->height);
    }
    _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 6 /* WL_SURFACE_COMMIT */, NULL, sv, 0);
}

static void _spec_frame_configure(struct libdecor_frame* frame, struct libdecor_configuration* cfg, void* user_data) {
    SpecWaylandWindow* w = (SpecWaylandWindow*)user_data;
    int cw = w->width;
    int ch = w->height;
    if (_libdecor_configuration_get_content_size && cfg) {
        int gw = 0, gh = 0;
        if (_libdecor_configuration_get_content_size(cfg, frame, &gw, &gh) && gw > 0 && gh > 0) {
            cw = gw;
            ch = gh;
        }
    }
    if (cw <= 0) cw = 800;
    if (ch <= 0) ch = 600;

    _spec_ensure_shm_buffer(w, cw, ch);
    uint32_t sv = _wl_proxy_get_version((struct wl_proxy*)w->surface);
    if (w->buffer) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 1 /* WL_SURFACE_ATTACH */, NULL, sv, 0, w->buffer, 0, 0);
        if (sv >= 4) {
            _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 9 /* WL_SURFACE_DAMAGE_BUFFER */, NULL, sv, 0, 0, 0, w->width, w->height);
        }
    }
    struct libdecor_state* st = _libdecor_state_new(cw, ch);
    _libdecor_frame_commit(frame, st, cfg);
    _libdecor_state_free(st);
    w->configured = true;
}

static void _spec_frame_close(struct libdecor_frame* frame, void* user_data) {
    (void)frame;
    SpecWaylandWindow* w = (SpecWaylandWindow*)user_data;
    w->should_close = true;
}

static void _spec_frame_commit(struct libdecor_frame* frame, void* user_data) {
    (void)frame;
    SpecWaylandWindow* w = (SpecWaylandWindow*)user_data;
    if (w->surface) {
        uint32_t sv = _wl_proxy_get_version((struct wl_proxy*)w->surface);
        _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 6 /* WL_SURFACE_COMMIT */, NULL, sv, 0);
    }
}

static void _spec_frame_dismiss_popup(struct libdecor_frame* frame, const char* seat, void* user_data) {
    (void)frame; (void)seat; (void)user_data;
}

static struct spec_libdecor_frame_interface _spec_frame_iface = {
    _spec_frame_configure,
    _spec_frame_close,
    _spec_frame_commit,
    _spec_frame_dismiss_popup,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
};

long long spec_pal_window_close(long long handle) {
    if (handle <= 0) return 0;
    size_t idx = (size_t)(handle - 1);
    if (idx >= _spec_windows_cap || !_spec_windows[idx]) return 0;
    SpecWaylandWindow* w = _spec_windows[idx];
    _spec_windows[idx] = NULL;

    _spec_release_shm(w);
    if (w->frame && _libdecor_frame_unref) _libdecor_frame_unref(w->frame);
    if (w->decor && _libdecor_unref) _libdecor_unref(w->decor);
    if (w->surface && _wl_proxy_destroy) _wl_proxy_destroy((struct wl_proxy*)w->surface);
    if (w->shm && _wl_proxy_destroy) _wl_proxy_destroy((struct wl_proxy*)w->shm);
    if (w->compositor && _wl_proxy_destroy) _wl_proxy_destroy((struct wl_proxy*)w->compositor);
    if (w->registry && _wl_proxy_destroy) _wl_proxy_destroy((struct wl_proxy*)w->registry);
    if (w->display && _wl_display_disconnect) _wl_display_disconnect(w->display);
    free(w);
    return 0;
}

long long spec_pal_window_open(long long title_cstr, long long width, long long height, long long decorated) {
    if (!_spec_win_init_libs()) return -1;
    const char* title = title_cstr ? (const char*)(intptr_t)title_cstr : "Suit";
    if (width <= 0) width = 800;
    if (height <= 0) height = 600;

    SpecWaylandWindow* w = (SpecWaylandWindow*)calloc(1, sizeof(SpecWaylandWindow));
    if (!w) {
        _spec_set_win_error("Out of memory");
        return -1;
    }
    w->in_use = true;
    w->shm_fd = -1;
    w->width = (int)width;
    w->height = (int)height;

    w->display = _wl_display_connect(NULL);
    if (!w->display) {
        _spec_set_win_error("Failed to connect to Wayland display");
        free(w);
        return -1;
    }

    uint32_t dv = _wl_proxy_get_version((struct wl_proxy*)w->display);
    w->registry = (struct wl_registry*)_wl_proxy_marshal_flags(
        (struct wl_proxy*)w->display, 1 /* WL_DISPLAY_GET_REGISTRY */, _wl_registry_iface, dv, 0, NULL);
    _wl_proxy_add_listener((struct wl_proxy*)w->registry, (void (**)(void))&_spec_reg_listener, w);
    _wl_display_roundtrip(w->display);

    if (!w->compositor || !w->shm) {
        _spec_set_win_error("Wayland compositor or wl_shm unavailable");
        if (w->registry) _wl_proxy_destroy((struct wl_proxy*)w->registry);
        _wl_display_disconnect(w->display);
        free(w);
        return -1;
    }

    uint32_t cv = _wl_proxy_get_version((struct wl_proxy*)w->compositor);
    w->surface = (struct wl_surface*)_wl_proxy_marshal_flags(
        (struct wl_proxy*)w->compositor, 0 /* WL_COMPOSITOR_CREATE_SURFACE */, _wl_surface_iface, cv, 0, NULL);
    if (!w->surface) {
        _spec_set_win_error("Failed to create wl_surface");
        if (w->shm) _wl_proxy_destroy((struct wl_proxy*)w->shm);
        if (w->compositor) _wl_proxy_destroy((struct wl_proxy*)w->compositor);
        if (w->registry) _wl_proxy_destroy((struct wl_proxy*)w->registry);
        _wl_display_disconnect(w->display);
        free(w);
        return -1;
    }

    w->decor = _libdecor_new(w->display, &_spec_decor_iface);
    if (!w->decor) {
        _spec_set_win_error("libdecor_new failed");
        _wl_proxy_destroy((struct wl_proxy*)w->surface);
        _wl_proxy_destroy((struct wl_proxy*)w->shm);
        _wl_proxy_destroy((struct wl_proxy*)w->compositor);
        _wl_proxy_destroy((struct wl_proxy*)w->registry);
        _wl_display_disconnect(w->display);
        free(w);
        return -1;
    }

    w->frame = _libdecor_decorate(w->decor, w->surface, &_spec_frame_iface, w);
    if (!w->frame) {
        _spec_set_win_error("libdecor_decorate failed");
        _libdecor_unref(w->decor);
        _wl_proxy_destroy((struct wl_proxy*)w->surface);
        _wl_proxy_destroy((struct wl_proxy*)w->shm);
        _wl_proxy_destroy((struct wl_proxy*)w->compositor);
        _wl_proxy_destroy((struct wl_proxy*)w->registry);
        _wl_display_disconnect(w->display);
        free(w);
        return -1;
    }

    if (_libdecor_frame_set_app_id) _libdecor_frame_set_app_id(w->frame, "spec.suit");
    if (_libdecor_frame_set_title) _libdecor_frame_set_title(w->frame, title);
    if (!decorated && _libdecor_frame_set_visibility) _libdecor_frame_set_visibility(w->frame, false);
    _libdecor_frame_map(w->frame);
    _wl_display_flush(w->display);

    int guard = 0;
    while (!w->configured && !w->should_close && guard < 200) {
        if (_libdecor_dispatch(w->decor, 16) < 0) break;
        guard++;
    }
    _spec_surface_present(w);
    _wl_display_flush(w->display);

    long long handle = _spec_alloc_window_slot(w);
    if (handle <= 0) {
        _libdecor_frame_unref(w->frame);
        _libdecor_unref(w->decor);
        _wl_proxy_destroy((struct wl_proxy*)w->surface);
        _wl_proxy_destroy((struct wl_proxy*)w->shm);
        _wl_proxy_destroy((struct wl_proxy*)w->compositor);
        _wl_proxy_destroy((struct wl_proxy*)w->registry);
        _wl_display_disconnect(w->display);
        free(w);
        return -1;
    }
    return handle;
}

long long spec_pal_window_poll(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || w->should_close) return 0;
    if (_libdecor_dispatch(w->decor, 16) < 0) {
        w->should_close = true;
        return 0;
    }
    _wl_display_flush(w->display);
    return w->should_close ? 0 : 1;
}

#else

long long spec_pal_window_open(long long title_cstr, long long width, long long height, long long decorated) {
    (void)title_cstr; (void)width; (void)height; (void)decorated;
    _spec_set_win_error("Native windowing is currently implemented for Linux Wayland only");
    return -1;
}

long long spec_pal_window_poll(long long handle) {
    (void)handle;
    return 0;
}

long long spec_pal_window_close(long long handle) {
    (void)handle;
    return 0;
}

#endif
