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
struct wl_seat;
struct wl_keyboard;
struct wl_pointer;
struct wl_touch;
struct wl_data_device_manager;
struct wl_data_device;
struct wl_data_source;
struct wl_data_offer;
struct wl_proxy;
struct wl_interface;

struct spec_wl_message {
    const char* name;
    const char* signature;
    const struct wl_interface** types;
};

struct spec_wl_interface_def {
    const char* name;
    int version;
    int method_count;
    const struct spec_wl_message* methods;
    int event_count;
    const struct spec_wl_message* events;
};

struct libdecor;
struct libdecor_frame;
struct libdecor_state;
struct libdecor_configuration;

struct spec_wl_registry_listener {
    void (*global)(void* data, struct wl_registry* registry, uint32_t name, const char* interface, uint32_t version);
    void (*global_remove)(void* data, struct wl_registry* registry, uint32_t name);
};

struct spec_wl_seat_listener {
    void (*capabilities)(void* data, struct wl_seat* seat, uint32_t capabilities);
    void (*name)(void* data, struct wl_seat* seat, const char* name);
};

struct spec_wl_keyboard_listener {
    void (*keymap)(void* data, struct wl_keyboard* kb, uint32_t format, int32_t fd, uint32_t size);
    void (*enter)(void* data, struct wl_keyboard* kb, uint32_t serial, struct wl_surface* surface, void* keys);
    void (*leave)(void* data, struct wl_keyboard* kb, uint32_t serial, struct wl_surface* surface);
    void (*key)(void* data, struct wl_keyboard* kb, uint32_t serial, uint32_t time, uint32_t key, uint32_t state);
    void (*modifiers)(void* data, struct wl_keyboard* kb, uint32_t serial, uint32_t mods_depressed, uint32_t mods_latched, uint32_t mods_locked, uint32_t group);
    void (*repeat_info)(void* data, struct wl_keyboard* kb, int32_t rate, int32_t delay);
};

struct spec_wl_pointer_listener {
    void (*enter)(void* data, struct wl_pointer* ptr, uint32_t serial, struct wl_surface* surface, int32_t sx, int32_t sy);
    void (*leave)(void* data, struct wl_pointer* ptr, uint32_t serial, struct wl_surface* surface);
    void (*motion)(void* data, struct wl_pointer* ptr, uint32_t time, int32_t sx, int32_t sy);
    void (*button)(void* data, struct wl_pointer* ptr, uint32_t serial, uint32_t time, uint32_t button, uint32_t state);
    void (*axis)(void* data, struct wl_pointer* ptr, uint32_t time, uint32_t axis, int32_t value);
    void (*frame)(void* data, struct wl_pointer* ptr);
    void (*axis_source)(void* data, struct wl_pointer* ptr, uint32_t axis_source);
    void (*axis_stop)(void* data, struct wl_pointer* ptr, uint32_t time, uint32_t axis);
    void (*axis_discrete)(void* data, struct wl_pointer* ptr, uint32_t axis, int32_t discrete);
    void (*axis_value120)(void* data, struct wl_pointer* ptr, uint32_t axis, int32_t value120);
    void (*axis_relative_direction)(void* data, struct wl_pointer* ptr, uint32_t axis, uint32_t direction);
};

struct spec_wl_touch_listener {
    void (*down)(void* data, struct wl_touch* touch, uint32_t serial, uint32_t time, struct wl_surface* surface, int32_t id, int32_t sx, int32_t sy);
    void (*up)(void* data, struct wl_touch* touch, uint32_t serial, uint32_t time, int32_t id);
    void (*motion)(void* data, struct wl_touch* touch, uint32_t time, int32_t id, int32_t sx, int32_t sy);
    void (*frame)(void* data, struct wl_touch* touch);
    void (*cancel)(void* data, struct wl_touch* touch);
    void (*shape)(void* data, struct wl_touch* touch, int32_t id, int32_t major, int32_t minor);
    void (*orientation)(void* data, struct wl_touch* touch, int32_t id, int32_t orientation);
};

struct spec_wl_data_offer_listener {
    void (*offer)(void* data, struct wl_data_offer* offer, const char* mime_type);
    void (*source_actions)(void* data, struct wl_data_offer* offer, uint32_t source_actions);
    void (*action)(void* data, struct wl_data_offer* offer, uint32_t dnd_action);
};

struct spec_wl_data_source_listener {
    void (*target)(void* data, struct wl_data_source* source, const char* mime_type);
    void (*send)(void* data, struct wl_data_source* source, const char* mime_type, int32_t fd);
    void (*cancelled)(void* data, struct wl_data_source* source);
    void (*dnd_drop_performed)(void* data, struct wl_data_source* source);
    void (*dnd_finished)(void* data, struct wl_data_source* source);
    void (*action)(void* data, struct wl_data_source* source, uint32_t dnd_action);
};

struct spec_wl_data_device_listener {
    void (*data_offer)(void* data, struct wl_data_device* dev, struct wl_data_offer* id);
    void (*enter)(void* data, struct wl_data_device* dev, uint32_t serial, struct wl_surface* surface, int32_t x, int32_t y, struct wl_data_offer* id);
    void (*leave)(void* data, struct wl_data_device* dev);
    void (*motion)(void* data, struct wl_data_device* dev, uint32_t time, int32_t x, int32_t y);
    void (*drop)(void* data, struct wl_data_device* dev);
    void (*selection)(void* data, struct wl_data_device* dev, struct wl_data_offer* id);
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
static void* _spec_xkb_so = NULL;

static void* (*_xkb_context_new)(int) = NULL;
static void (*_xkb_context_unref)(void*) = NULL;
static void* (*_xkb_keymap_new_from_string)(void*, const char*, int, int) = NULL;
static void (*_xkb_keymap_unref)(void*) = NULL;
static void* (*_xkb_state_new)(void*) = NULL;
static void (*_xkb_state_unref)(void*) = NULL;
static int (*_xkb_state_update_mask)(void*, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t) = NULL;
static uint32_t (*_xkb_state_key_get_one_sym)(void*, uint32_t) = NULL;
static int (*_xkb_state_key_get_utf8)(void*, uint32_t, char*, size_t) = NULL;
static int (*_xkb_state_mod_name_is_active)(void*, const char*, int) = NULL;

static struct wl_display* (*_wl_display_connect)(const char*) = NULL;
static void (*_wl_display_disconnect)(struct wl_display*) = NULL;
static int (*_wl_display_roundtrip)(struct wl_display*) = NULL;
static int (*_wl_display_flush)(struct wl_display*) = NULL;
static int (*_wl_display_dispatch_pending)(struct wl_display*) = NULL;
static int (*_wl_display_prepare_read)(struct wl_display*) = NULL;
static int (*_wl_display_read_events)(struct wl_display*) = NULL;
static void (*_wl_display_cancel_read)(struct wl_display*) = NULL;
static int (*_wl_display_get_fd)(struct wl_display*) = NULL;
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
static const struct wl_interface* _wl_seat_iface = NULL;
static const struct wl_interface* _wl_keyboard_iface = NULL;
static const struct wl_interface* _wl_pointer_iface = NULL;
static const struct wl_interface* _wl_touch_iface = NULL;
static const struct wl_interface* _wl_data_device_manager_iface = NULL;
static const struct wl_interface* _wl_data_device_iface = NULL;
static const struct wl_interface* _wl_data_source_iface = NULL;
static const struct wl_interface* _wl_data_offer_iface = NULL;
static const struct wl_interface* _wl_output_iface = NULL;

/* Minimal xdg-shell + xdg-decoration ABI interfaces (loaded zero-dep) */
static const struct wl_interface* _spec_xdg_surface_types[2] = { NULL, NULL };
static const struct wl_interface* _spec_xdg_toplevel_types[1] = { NULL };
static const struct wl_interface* _spec_zxdg_deco_types[2] = { NULL, NULL };
static const struct wl_interface* _spec_null_types[4] = { NULL, NULL, NULL, NULL };

static const struct spec_wl_message _spec_xdg_wm_base_reqs[] = {
    { "destroy", "", _spec_null_types },
    { "create_positioner", "n", _spec_null_types },
    { "get_xdg_surface", "no", _spec_xdg_surface_types },
    { "pong", "u", _spec_null_types }
};
static const struct spec_wl_message _spec_xdg_wm_base_evts[] = {
    { "ping", "u", _spec_null_types }
};
static const struct spec_wl_interface_def _spec_xdg_wm_base_iface_def = {
    "xdg_wm_base", 1, 4, _spec_xdg_wm_base_reqs, 1, _spec_xdg_wm_base_evts
};

static const struct spec_wl_message _spec_xdg_surface_reqs[] = {
    { "destroy", "", _spec_null_types },
    { "get_toplevel", "n", _spec_xdg_toplevel_types },
    { "get_popup", "n?oo", _spec_null_types },
    { "set_window_geometry", "iiii", _spec_null_types },
    { "ack_configure", "u", _spec_null_types }
};
static const struct spec_wl_message _spec_xdg_surface_evts[] = {
    { "configure", "u", _spec_null_types }
};
static const struct spec_wl_interface_def _spec_xdg_surface_iface_def = {
    "xdg_surface", 1, 5, _spec_xdg_surface_reqs, 1, _spec_xdg_surface_evts
};

static const struct spec_wl_message _spec_xdg_toplevel_reqs[] = {
    { "destroy", "", _spec_null_types },
    { "set_parent", "?o", _spec_null_types },
    { "set_title", "s", _spec_null_types },
    { "set_app_id", "s", _spec_null_types },
    { "show_window_menu", "ouii", _spec_null_types },
    { "move", "ou", _spec_null_types },
    { "resize", "ouu", _spec_null_types },
    { "set_max_size", "ii", _spec_null_types },
    { "set_min_size", "ii", _spec_null_types },
    { "set_maximized", "", _spec_null_types },
    { "unset_maximized", "", _spec_null_types },
    { "set_fullscreen", "?o", _spec_null_types },
    { "unset_fullscreen", "", _spec_null_types },
    { "set_minimized", "", _spec_null_types }
};
static const struct spec_wl_message _spec_xdg_toplevel_evts[] = {
    { "configure", "iia", _spec_null_types },
    { "close", "", _spec_null_types },
    { "configure_bounds", "ii", _spec_null_types },
    { "wm_capabilities", "a", _spec_null_types }
};
static const struct spec_wl_interface_def _spec_xdg_toplevel_iface_def = {
    "xdg_toplevel", 1, 14, _spec_xdg_toplevel_reqs, 4, _spec_xdg_toplevel_evts
};

static const struct spec_wl_message _spec_zxdg_deco_mgr_reqs[] = {
    { "destroy", "", _spec_null_types },
    { "get_toplevel_decoration", "no", _spec_zxdg_deco_types }
};
static const struct spec_wl_interface_def _spec_zxdg_deco_mgr_iface_def = {
    "zxdg_decoration_manager_v1", 1, 2, _spec_zxdg_deco_mgr_reqs, 0, NULL
};

static const struct spec_wl_message _spec_zxdg_deco_reqs[] = {
    { "destroy", "", _spec_null_types },
    { "set_mode", "u", _spec_null_types },
    { "unset_mode", "", _spec_null_types }
};
static const struct spec_wl_message _spec_zxdg_deco_evts[] = {
    { "configure", "u", _spec_null_types }
};
static const struct spec_wl_interface_def _spec_zxdg_deco_iface_def = {
    "zxdg_toplevel_decoration_v1", 1, 3, _spec_zxdg_deco_reqs, 1, _spec_zxdg_deco_evts
};

static const struct wl_interface* _spec_wp_cursor_dev_types[2] = { NULL, NULL };
static const struct spec_wl_message _spec_wp_cursor_mgr_reqs[] = {
    { "destroy", "", _spec_null_types },
    { "get_pointer", "no", _spec_wp_cursor_dev_types },
    { "get_tablet_tool_v2", "no", _spec_null_types }
};
static const struct spec_wl_interface_def _spec_wp_cursor_mgr_iface_def = {
    "wp_cursor_shape_manager_v1", 1, 3, _spec_wp_cursor_mgr_reqs, 0, NULL
};

static const struct wl_interface* _spec_xdg_icon_create_types[1] = { NULL };
static const struct wl_interface* _spec_xdg_icon_set_types[2] = { NULL, NULL };
static const struct wl_interface* _spec_xdg_icon_buf_types[2] = { NULL, NULL };
static const struct spec_wl_message _spec_xdg_icon_mgr_reqs[] = {
    { "destroy", "", _spec_null_types },
    { "create_icon", "n", _spec_xdg_icon_create_types },
    { "set_icon", "oo", _spec_xdg_icon_set_types }
};
static const struct spec_wl_message _spec_xdg_icon_mgr_evts[] = {
    { "icon_size", "i", _spec_null_types },
    { "done", "", _spec_null_types }
};
static const struct spec_wl_interface_def _spec_xdg_icon_mgr_iface_def = {
    "xdg_toplevel_icon_manager_v1", 1, 3, _spec_xdg_icon_mgr_reqs, 2, _spec_xdg_icon_mgr_evts
};
static const struct spec_wl_message _spec_xdg_icon_reqs[] = {
    { "destroy", "", _spec_null_types },
    { "set_name", "s", _spec_null_types },
    { "add_buffer", "oi", _spec_xdg_icon_buf_types }
};
static const struct spec_wl_interface_def _spec_xdg_icon_iface_def = {
    "xdg_toplevel_icon_v1", 1, 3, _spec_xdg_icon_reqs, 0, NULL
};
static const struct spec_wl_message _spec_wp_cursor_dev_reqs[] = {
    { "destroy", "", _spec_null_types },
    { "set_shape", "uu", _spec_null_types }
};
static const struct spec_wl_interface_def _spec_wp_cursor_dev_iface_def = {
    "wp_cursor_shape_device_v1", 1, 2, _spec_wp_cursor_dev_reqs, 0, NULL
};

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
    if (_spec_wl_so) return true;
    _spec_wl_so = dlopen("libwayland-client.so.0", RTLD_LAZY | RTLD_LOCAL);
    if (!_spec_wl_so) {
        _spec_set_win_error("Failed to load libwayland-client.so.0");
        return false;
    }

    _wl_display_connect = dlsym(_spec_wl_so, "wl_display_connect");
    _wl_display_disconnect = dlsym(_spec_wl_so, "wl_display_disconnect");
    _wl_display_roundtrip = dlsym(_spec_wl_so, "wl_display_roundtrip");
    _wl_display_flush = dlsym(_spec_wl_so, "wl_display_flush");
    _wl_display_dispatch_pending = dlsym(_spec_wl_so, "wl_display_dispatch_pending");
    _wl_display_prepare_read = dlsym(_spec_wl_so, "wl_display_prepare_read");
    _wl_display_read_events = dlsym(_spec_wl_so, "wl_display_read_events");
    _wl_display_cancel_read = dlsym(_spec_wl_so, "wl_display_cancel_read");
    _wl_display_get_fd = dlsym(_spec_wl_so, "wl_display_get_fd");
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
    _wl_seat_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_seat_interface");
    _wl_keyboard_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_keyboard_interface");
    _wl_pointer_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_pointer_interface");
    _wl_touch_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_touch_interface");
    _wl_data_device_manager_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_data_device_manager_interface");
    _wl_data_device_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_data_device_interface");
    _wl_data_source_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_data_source_interface");
    _wl_data_offer_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_data_offer_interface");
    _wl_output_iface = (const struct wl_interface*)dlsym(_spec_wl_so, "wl_output_interface");

    _spec_xdg_surface_types[0] = (const struct wl_interface*)&_spec_xdg_surface_iface_def;
    _spec_xdg_surface_types[1] = _wl_surface_iface;
    _spec_xdg_toplevel_types[0] = (const struct wl_interface*)&_spec_xdg_toplevel_iface_def;
    _spec_zxdg_deco_types[0] = (const struct wl_interface*)&_spec_zxdg_deco_iface_def;
    _spec_zxdg_deco_types[1] = (const struct wl_interface*)&_spec_xdg_toplevel_iface_def;
    _spec_wp_cursor_dev_types[0] = (const struct wl_interface*)&_spec_wp_cursor_dev_iface_def;
    _spec_wp_cursor_dev_types[1] = _wl_pointer_iface;
    _spec_xdg_icon_create_types[0] = (const struct wl_interface*)&_spec_xdg_icon_iface_def;
    _spec_xdg_icon_set_types[0] = (const struct wl_interface*)&_spec_xdg_toplevel_iface_def;
    _spec_xdg_icon_set_types[1] = (const struct wl_interface*)&_spec_xdg_icon_iface_def;
    _spec_xdg_icon_buf_types[0] = _wl_buffer_iface;

    if (!_spec_xkb_so) {
        _spec_xkb_so = dlopen("libxkbcommon.so.0", RTLD_LAZY | RTLD_LOCAL);
        if (_spec_xkb_so) {
            _xkb_context_new = dlsym(_spec_xkb_so, "xkb_context_new");
            _xkb_context_unref = dlsym(_spec_xkb_so, "xkb_context_unref");
            _xkb_keymap_new_from_string = dlsym(_spec_xkb_so, "xkb_keymap_new_from_string");
            _xkb_keymap_unref = dlsym(_spec_xkb_so, "xkb_keymap_unref");
            _xkb_state_new = dlsym(_spec_xkb_so, "xkb_state_new");
            _xkb_state_unref = dlsym(_spec_xkb_so, "xkb_state_unref");
            _xkb_state_update_mask = dlsym(_spec_xkb_so, "xkb_state_update_mask");
            _xkb_state_key_get_one_sym = dlsym(_spec_xkb_so, "xkb_state_key_get_one_sym");
            _xkb_state_key_get_utf8 = dlsym(_spec_xkb_so, "xkb_state_key_get_utf8");
            _xkb_state_mod_name_is_active = dlsym(_spec_xkb_so, "xkb_state_mod_name_is_active");
        }
    }

    if (!_wl_display_connect || !_wl_proxy_marshal_flags || !_wl_surface_iface) {
        _spec_set_win_error("Missing required Wayland symbols");
        return false;
    }
    return true;
}

static bool _spec_win_init_libdecor(void) {
    if (_spec_decor_so) return true;
    _spec_decor_so = dlopen("libdecor-0.so.0", RTLD_LAZY | RTLD_LOCAL);
    if (!_spec_decor_so) {
        _spec_set_win_error("Failed to load libdecor-0.so.0");
        return false;
    }
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
    if (!_libdecor_new || !_libdecor_decorate || !_libdecor_dispatch || !_libdecor_state_new) {
        _spec_set_win_error("Missing required libdecor symbols");
        return false;
    }
    return true;
}

typedef struct SpecInputEvent {
    int32_t kind;
    int32_t a;
    int32_t b;
    int32_t c;
    int32_t d;
} SpecInputEvent;

typedef struct SpecWaylandWindow {
    bool in_use;
    bool configured;
    bool should_close;
    bool use_vulkan;
    bool use_xdg;
    int width;
    int height;
    int pending_w;
    int pending_h;
    int output_scale;
    int output_phys_w_mm;
    int output_mode_w;
    struct wl_display* display;
    struct wl_registry* registry;
    struct wl_compositor* compositor;
    struct wl_shm* shm;
    struct wl_surface* surface;
    void* xdg_wm_base;
    void* xdg_surface;
    void* xdg_toplevel;
    void* decor_mgr;
    void* xdg_decoration;
    void* icon_mgr;
    struct wl_seat* seat;
    struct wl_keyboard* keyboard;
    struct wl_pointer* pointer;
    struct wl_touch* touch;
    bool pointer_on_surface;
    bool touch_on_surface;
    SpecInputEvent* ev_queue;
    int ev_head;
    int ev_tail;
    int ev_cap;
    int pointer_x;
    int pointer_y;
    bool has_click;
    bool has_right_click;
    bool pointer_down;
    int click_x;
    int click_y;
    int right_click_x;
    int right_click_y;
    int scroll_x;
    int scroll_y;
    uint32_t last_ptr_serial;
    uint32_t last_input_serial;
    struct wl_data_device_manager* data_mgr;
    struct wl_data_device* data_device;
    struct wl_data_source* data_source;
    struct wl_data_offer* current_offer;
    struct wl_data_offer* pending_offer;
    bool pending_has_utf8;
    bool pending_has_plain;
    bool offer_has_utf8;
    bool offer_has_plain;
    char* clipboard_out;
    char* clipboard_in;
    void* cursor_mgr;
    void* cursor_dev;
    void* xkb_ctx;
    void* xkb_keymap;
    void* xkb_state;
    int mods;
    int* char_queue;
    size_t char_len;
    size_t char_cap;
    struct wl_shm_pool* shm_pool;
    struct wl_buffer* buffer;
    void* shm_data;
    size_t shm_size;
    int shm_fd;
    int* key_queue;
    size_t key_len;
    size_t key_cap;
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

static void _spec_push_key(SpecWaylandWindow* w, int code) {
    if (!w || code <= 0) return;
    if (w->key_len >= w->key_cap) {
        size_t new_cap = w->key_cap == 0 ? 16 : w->key_cap * 2;
        int* next = (int*)realloc(w->key_queue, new_cap * sizeof(int));
        if (!next) return;
        w->key_queue = next;
        w->key_cap = new_cap;
    }
    w->key_queue[w->key_len++] = code;
}

static int _spec_evdev_to_ascii(uint32_t key) {
    switch (key) {
        case 1: return 27;     /* KEY_ESC */
        case 14: return 8;     /* KEY_BACKSPACE */
        case 15: return 9;     /* KEY_TAB */
        case 28: return 13;    /* KEY_ENTER */
        case 102: return 1005; /* KEY_HOME */
        case 103: return 1001; /* KEY_UP */
        case 104: return 1007; /* KEY_PAGEUP */
        case 105: return 1003; /* KEY_LEFT */
        case 106: return 1004; /* KEY_RIGHT */
        case 107: return 1006; /* KEY_END */
        case 108: return 1002; /* KEY_DOWN */
        case 109: return 1008; /* KEY_PAGEDOWN */
        case 111: return 127;  /* KEY_DELETE */
        case 16: return 'q';
        case 17: return 'w';
        case 18: return 'e';
        case 30: return 'a';
        case 31: return 's';
        case 32: return 'd';
        default: return 0;
    }
}

static void _spec_push_char(SpecWaylandWindow* w, int cp) {
    if (!w || cp <= 0) return;
    if (w->char_len >= w->char_cap) {
        size_t new_cap = w->char_cap == 0 ? 16 : w->char_cap * 2;
        int* next = (int*)realloc(w->char_queue, new_cap * sizeof(int));
        if (!next) return;
        w->char_queue = next;
        w->char_cap = new_cap;
    }
    w->char_queue[w->char_len++] = cp;
}

static void _spec_push_event(SpecWaylandWindow* w, int32_t kind, int32_t a, int32_t b, int32_t c, int32_t d) {
    if (!w) return;
    if (!w->ev_queue) {
        w->ev_cap = 64;
        w->ev_queue = (SpecInputEvent*)malloc(sizeof(SpecInputEvent) * (size_t)w->ev_cap);
        if (!w->ev_queue) return;
        w->ev_head = 0;
        w->ev_tail = 0;
    }
    int count = (w->ev_tail - w->ev_head + w->ev_cap) % w->ev_cap;
    if (count + 1 >= w->ev_cap) {
        int new_cap = w->ev_cap * 2;
        SpecInputEvent* next = (SpecInputEvent*)malloc(sizeof(SpecInputEvent) * (size_t)new_cap);
        if (!next) return;
        for (int i = 0; i < count; i++) {
            next[i] = w->ev_queue[(w->ev_head + i) % w->ev_cap];
        }
        free(w->ev_queue);
        w->ev_queue = next;
        w->ev_cap = new_cap;
        w->ev_head = 0;
        w->ev_tail = count;
    }
    w->ev_queue[w->ev_tail].kind = kind;
    w->ev_queue[w->ev_tail].a = a;
    w->ev_queue[w->ev_tail].b = b;
    w->ev_queue[w->ev_tail].c = c;
    w->ev_queue[w->ev_tail].d = d;
    w->ev_tail = (w->ev_tail + 1) % w->ev_cap;
}

static void _spec_kb_keymap(void* data, struct wl_keyboard* kb, uint32_t fmt, int32_t fd, uint32_t sz) {
    (void)kb;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && fmt == 1 /* WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1 */ && fd >= 0 && sz > 0 &&
        _xkb_context_new && _xkb_keymap_new_from_string && _xkb_state_new) {
        char* map_str = (char*)mmap(NULL, (size_t)sz, PROT_READ, MAP_PRIVATE, fd, 0);
        if (map_str != MAP_FAILED) {
            if (w->xkb_state && _xkb_state_unref) { _xkb_state_unref(w->xkb_state); w->xkb_state = NULL; }
            if (w->xkb_keymap && _xkb_keymap_unref) { _xkb_keymap_unref(w->xkb_keymap); w->xkb_keymap = NULL; }
            if (!w->xkb_ctx) w->xkb_ctx = _xkb_context_new(0);
            if (w->xkb_ctx) {
                w->xkb_keymap = _xkb_keymap_new_from_string(w->xkb_ctx, map_str, 1, 0);
                if (w->xkb_keymap) w->xkb_state = _xkb_state_new(w->xkb_keymap);
            }
            munmap(map_str, (size_t)sz);
        }
    }
    if (fd >= 0) close(fd);
}
static void _spec_kb_enter(void* data, struct wl_keyboard* kb, uint32_t serial, struct wl_surface* s, void* keys) {
    (void)kb; (void)keys;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w) {
        w->last_input_serial = serial;
        if (s == w->surface) _spec_push_event(w, 11, 1, 0, 0, 0);
    }
}
static void _spec_kb_leave(void* data, struct wl_keyboard* kb, uint32_t serial, struct wl_surface* s) {
    (void)kb; (void)serial;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && s == w->surface) _spec_push_event(w, 11, 0, 0, 0, 0);
}
static void _spec_kb_key(void* data, struct wl_keyboard* kb, uint32_t serial, uint32_t time, uint32_t key, uint32_t state) {
    (void)kb; (void)time;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (!w) return;
    w->last_input_serial = serial;
    if (state == 1 || state == 2) {
        int nav = _spec_evdev_to_ascii(key);
        if (w->xkb_state && _xkb_state_key_get_one_sym && _xkb_state_key_get_utf8) {
            uint32_t xkb_code = key + 8U;
            uint32_t sym = _xkb_state_key_get_one_sym(w->xkb_state, xkb_code);
            if (sym == 0xff1b) nav = 27;       /* XKB_KEY_Escape */
            else if (sym == 0xff0d) nav = 13;  /* XKB_KEY_Return */
            else if (sym == 0xff08) nav = 8;   /* XKB_KEY_BackSpace */
            else if (sym == 0xff09) nav = 9;   /* XKB_KEY_Tab */
            else if (sym == 0xffff) nav = 127; /* XKB_KEY_Delete */
            else if (sym == 0xff52) nav = 1001;/* Up */
            else if (sym == 0xff54) nav = 1002;/* Down */
            else if (sym == 0xff51) nav = 1003;/* Left */
            else if (sym == 0xff53) nav = 1004;/* Right */
            else if (sym == 0xff50) nav = 1005;/* Home */
            else if (sym == 0xff57) nav = 1006;/* End */
            else if (sym == 0xff55) nav = 1007;/* Page_Up */
            else if (sym == 0xff56) nav = 1008;/* Page_Down */
            else if (sym >= 32 && sym < 127) nav = (int)sym;

            char ubuf[16];
            int ulen = _xkb_state_key_get_utf8(w->xkb_state, xkb_code, ubuf, sizeof(ubuf));
            if (ulen > 0 && !(w->mods & 2) && (unsigned char)ubuf[0] >= 32 && (unsigned char)ubuf[0] != 127) {
                uint32_t cp = (unsigned char)ubuf[0];
                if (ulen >= 2 && (cp & 0xE0) == 0xC0) cp = ((cp & 0x1F) << 6) | ((unsigned char)ubuf[1] & 0x3F);
                else if (ulen >= 3 && (cp & 0xF0) == 0xE0) cp = ((cp & 0x0F) << 12) | (((unsigned char)ubuf[1] & 0x3F) << 6) | ((unsigned char)ubuf[2] & 0x3F);
                else if (ulen >= 4 && (cp & 0xF8) == 0xF0) cp = ((cp & 0x07) << 18) | (((unsigned char)ubuf[1] & 0x3F) << 12) | (((unsigned char)ubuf[2] & 0x3F) << 6) | ((unsigned char)ubuf[3] & 0x3F);
                _spec_push_char(w, (int)cp);
                _spec_push_event(w, 5, (int32_t)cp, (int32_t)w->mods, 0, 0);
            }
        }
        if (nav > 0) {
            _spec_push_key(w, nav);
            _spec_push_event(w, 4, (int32_t)nav, (int32_t)state, (int32_t)w->mods, 0);
        }
    } else if (state == 0) {
        int nav = _spec_evdev_to_ascii(key);
        if (w->xkb_state && _xkb_state_key_get_one_sym) {
            uint32_t sym = _xkb_state_key_get_one_sym(w->xkb_state, key + 8U);
            if (sym >= 32 && sym < 127) nav = (int)sym;
        }
        if (nav > 0) _spec_push_event(w, 4, (int32_t)nav, 0, (int32_t)w->mods, 0);
    }
}
static void _spec_kb_mods(void* data, struct wl_keyboard* kb, uint32_t serial, uint32_t d, uint32_t l, uint32_t lo, uint32_t g) {
    (void)kb; (void)serial;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (!w || !w->xkb_state || !_xkb_state_update_mask) return;
    _xkb_state_update_mask(w->xkb_state, d, l, lo, 0, 0, g);
    if (_xkb_state_mod_name_is_active) {
        int m = 0;
        if (_xkb_state_mod_name_is_active(w->xkb_state, "Shift", 3) > 0) m |= 1;
        if (_xkb_state_mod_name_is_active(w->xkb_state, "Control", 3) > 0) m |= 2;
        if (_xkb_state_mod_name_is_active(w->xkb_state, "Mod1", 3) > 0) m |= 4;
        if (_xkb_state_mod_name_is_active(w->xkb_state, "Mod4", 3) > 0) m |= 8;
        w->mods = m;
    }
}
static void _spec_kb_repeat(void* data, struct wl_keyboard* kb, int32_t rate, int32_t delay) {
    (void)data; (void)kb; (void)rate; (void)delay;
}

static const struct spec_wl_keyboard_listener _spec_kb_listener = {
    _spec_kb_keymap,
    _spec_kb_enter,
    _spec_kb_leave,
    _spec_kb_key,
    _spec_kb_mods,
    _spec_kb_repeat
};

static void _spec_ptr_enter(void* data, struct wl_pointer* ptr, uint32_t serial, struct wl_surface* surface, int32_t sx, int32_t sy) {
    (void)ptr; (void)serial;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && surface == w->surface) {
        w->pointer_on_surface = true;
        w->last_ptr_serial = serial;
        w->pointer_x = sx >> 8;
        w->pointer_y = sy >> 8;
        _spec_push_event(w, 10, 1, w->pointer_x, w->pointer_y, 0);
    } else if (w) {
        w->pointer_on_surface = false;
    }
}
static void _spec_ptr_leave(void* data, struct wl_pointer* ptr, uint32_t serial, struct wl_surface* surface) {
    (void)ptr; (void)serial;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && surface == w->surface) {
        w->pointer_on_surface = false;
        _spec_push_event(w, 10, 0, w->pointer_x, w->pointer_y, 0);
    }
}
static void _spec_ptr_motion(void* data, struct wl_pointer* ptr, uint32_t time, int32_t sx, int32_t sy) {
    (void)ptr; (void)time;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && w->pointer_on_surface) {
        w->pointer_x = sx >> 8;
        w->pointer_y = sy >> 8;
        _spec_push_event(w, 1, w->pointer_x, w->pointer_y, 0, 0);
    }
}
static void _spec_ptr_button(void* data, struct wl_pointer* ptr, uint32_t serial, uint32_t time, uint32_t button, uint32_t state) {
    (void)ptr; (void)time;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (!w) return;
    w->last_input_serial = serial;
    if (w->pointer_on_surface || state == 0U) {
        _spec_push_event(w, 2, (int32_t)button, (int32_t)state, w->pointer_x, w->pointer_y);
    }
    if (button == 0x110U /* BTN_LEFT */) {
        if (state == 1U /* PRESSED */ && w->pointer_on_surface) {
            w->pointer_down = true;
            w->has_click = true;
            w->click_x = w->pointer_x;
            w->click_y = w->pointer_y;
        } else if (state == 0U /* RELEASED */) {
            w->pointer_down = false;
        }
    } else if (button == 0x111U /* BTN_RIGHT */ && state == 1U /* PRESSED */ && w->pointer_on_surface) {
        w->has_right_click = true;
        w->right_click_x = w->pointer_x;
        w->right_click_y = w->pointer_y;
    }
}
static void _spec_ptr_axis(void* d, struct wl_pointer* p, uint32_t t, uint32_t a, int32_t v) {
    (void)p; (void)t;
    SpecWaylandWindow* w = (SpecWaylandWindow*)d;
    if (w && w->pointer_on_surface) {
        _spec_push_event(w, 3, (int32_t)a, v >> 8, 0, 0);
        if (a == 0 /* WL_POINTER_AXIS_VERTICAL_SCROLL */) {
            w->scroll_y += (v >> 8);
        } else if (a == 1 /* WL_POINTER_AXIS_HORIZONTAL_SCROLL */) {
            w->scroll_x += (v >> 8);
        }
    }
}
static void _spec_ptr_frame(void* d, struct wl_pointer* p) { (void)d;(void)p; }
static void _spec_ptr_axis_src(void* d, struct wl_pointer* p, uint32_t s) { (void)d;(void)p;(void)s; }
static void _spec_ptr_axis_stop(void* d, struct wl_pointer* p, uint32_t t, uint32_t a) { (void)d;(void)p;(void)t;(void)a; }
static void _spec_ptr_axis_disc(void* d, struct wl_pointer* p, uint32_t a, int32_t di) { (void)d;(void)p;(void)a;(void)di; }
static void _spec_ptr_axis_v120(void* d, struct wl_pointer* p, uint32_t a, int32_t v) { (void)d;(void)p;(void)a;(void)v; }
static void _spec_ptr_axis_rel(void* d, struct wl_pointer* p, uint32_t a, uint32_t dir) { (void)d;(void)p;(void)a;(void)dir; }

static const struct spec_wl_pointer_listener _spec_ptr_listener = {
    _spec_ptr_enter,
    _spec_ptr_leave,
    _spec_ptr_motion,
    _spec_ptr_button,
    _spec_ptr_axis,
    _spec_ptr_frame,
    _spec_ptr_axis_src,
    _spec_ptr_axis_stop,
    _spec_ptr_axis_disc,
    _spec_ptr_axis_v120,
    _spec_ptr_axis_rel
};

static void _spec_touch_down(void* data, struct wl_touch* touch, uint32_t serial, uint32_t time, struct wl_surface* surface, int32_t id, int32_t sx, int32_t sy) {
    (void)touch; (void)time;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w) {
        w->last_input_serial = serial;
        if (surface == w->surface) {
            w->touch_on_surface = true;
            _spec_push_event(w, 6, id, sx >> 8, sy >> 8, 0);
        }
    }
}
static void _spec_touch_up(void* data, struct wl_touch* touch, uint32_t serial, uint32_t time, int32_t id) {
    (void)touch; (void)serial; (void)time;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && w->touch_on_surface) {
        _spec_push_event(w, 7, id, 0, 0, 0);
    }
}
static void _spec_touch_motion(void* data, struct wl_touch* touch, uint32_t time, int32_t id, int32_t sx, int32_t sy) {
    (void)touch; (void)time;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && w->touch_on_surface) {
        _spec_push_event(w, 8, id, sx >> 8, sy >> 8, 0);
    }
}
static void _spec_touch_frame(void* data, struct wl_touch* touch) { (void)data; (void)touch; }
static void _spec_touch_cancel(void* data, struct wl_touch* touch) {
    (void)touch;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w) {
        w->touch_on_surface = false;
        _spec_push_event(w, 9, 0, 0, 0, 0);
    }
}
static void _spec_touch_shape(void* data, struct wl_touch* touch, int32_t id, int32_t maj, int32_t min) { (void)data; (void)touch; (void)id; (void)maj; (void)min; }
static void _spec_touch_orientation(void* data, struct wl_touch* touch, int32_t id, int32_t ori) { (void)data; (void)touch; (void)id; (void)ori; }

static const struct spec_wl_touch_listener _spec_touch_listener = {
    _spec_touch_down,
    _spec_touch_up,
    _spec_touch_motion,
    _spec_touch_frame,
    _spec_touch_cancel,
    _spec_touch_shape,
    _spec_touch_orientation
};

static void _spec_seat_caps(void* data, struct wl_seat* seat, uint32_t caps) {
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if ((caps & 1u /* WL_SEAT_CAPABILITY_POINTER */) && !w->pointer && _wl_pointer_iface) {
        uint32_t sv = _wl_proxy_get_version((struct wl_proxy*)seat);
        w->pointer = (struct wl_pointer*)_wl_proxy_marshal_flags(
            (struct wl_proxy*)seat, 0 /* WL_SEAT_GET_POINTER */, _wl_pointer_iface, sv, 0, NULL);
        if (w->pointer) {
            _wl_proxy_add_listener((struct wl_proxy*)w->pointer, (void (**)(void))&_spec_ptr_listener, w);
        }
    }
    if ((caps & 2u /* WL_SEAT_CAPABILITY_KEYBOARD */) && !w->keyboard && _wl_keyboard_iface) {
        uint32_t sv = _wl_proxy_get_version((struct wl_proxy*)seat);
        w->keyboard = (struct wl_keyboard*)_wl_proxy_marshal_flags(
            (struct wl_proxy*)seat, 1 /* WL_SEAT_GET_KEYBOARD */, _wl_keyboard_iface, sv, 0, NULL);
        if (w->keyboard) {
            _wl_proxy_add_listener((struct wl_proxy*)w->keyboard, (void (**)(void))&_spec_kb_listener, w);
        }
    }
    if ((caps & 4u /* WL_SEAT_CAPABILITY_TOUCH */) && !w->touch && _wl_touch_iface) {
        uint32_t sv = _wl_proxy_get_version((struct wl_proxy*)seat);
        w->touch = (struct wl_touch*)_wl_proxy_marshal_flags(
            (struct wl_proxy*)seat, 2 /* WL_SEAT_GET_TOUCH */, _wl_touch_iface, sv, 0, NULL);
        if (w->touch) {
            _wl_proxy_add_listener((struct wl_proxy*)w->touch, (void (**)(void))&_spec_touch_listener, w);
        }
    }
}

static void _spec_seat_name(void* data, struct wl_seat* seat, const char* name) {
    (void)data; (void)seat; (void)name;
}

static const struct spec_wl_seat_listener _spec_seat_listener = {
    _spec_seat_caps,
    _spec_seat_name
};

static void _spec_data_offer_offer(void* data, struct wl_data_offer* offer, const char* mime_type) {
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (!w || !mime_type || offer != w->pending_offer) return;
    if (strcmp(mime_type, "text/plain;charset=utf-8") == 0) w->pending_has_utf8 = true;
    else if (strcmp(mime_type, "text/plain") == 0 || strcmp(mime_type, "UTF8_STRING") == 0) w->pending_has_plain = true;
}
static void _spec_data_offer_source_actions(void* d, struct wl_data_offer* o, uint32_t a) { (void)d;(void)o;(void)a; }
static void _spec_data_offer_action(void* d, struct wl_data_offer* o, uint32_t a) { (void)d;(void)o;(void)a; }
static const struct spec_wl_data_offer_listener _spec_data_offer_listener = {
    _spec_data_offer_offer,
    _spec_data_offer_source_actions,
    _spec_data_offer_action
};

static void _spec_data_dev_offer(void* data, struct wl_data_device* dev, struct wl_data_offer* id) {
    (void)dev;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (!w || !id) return;
    if (w->pending_offer && w->pending_offer != w->current_offer) {
        _wl_proxy_destroy((struct wl_proxy*)w->pending_offer);
    }
    w->pending_offer = id;
    w->pending_has_utf8 = false;
    w->pending_has_plain = false;
    _wl_proxy_add_listener((struct wl_proxy*)id, (void (**)(void))&_spec_data_offer_listener, w);
}
static void _spec_data_dev_enter(void* d, struct wl_data_device* dev, uint32_t s, struct wl_surface* sf, int32_t x, int32_t y, struct wl_data_offer* id) {
    (void)d;(void)dev;(void)s;(void)sf;(void)x;(void)y;
    if (id) _wl_proxy_destroy((struct wl_proxy*)id);
}
static void _spec_data_dev_leave(void* d, struct wl_data_device* dev) { (void)d;(void)dev; }
static void _spec_data_dev_motion(void* d, struct wl_data_device* dev, uint32_t t, int32_t x, int32_t y) { (void)d;(void)dev;(void)t;(void)x;(void)y; }
static void _spec_data_dev_drop(void* d, struct wl_data_device* dev) { (void)d;(void)dev; }
static void _spec_data_dev_selection(void* data, struct wl_data_device* dev, struct wl_data_offer* id) {
    (void)dev;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (!w) return;
    if (w->current_offer && w->current_offer != id) {
        _wl_proxy_destroy((struct wl_proxy*)w->current_offer);
    }
    w->current_offer = id;
    if (id && id == w->pending_offer) {
        w->offer_has_utf8 = w->pending_has_utf8;
        w->offer_has_plain = w->pending_has_plain;
        w->pending_offer = NULL;
    } else {
        w->offer_has_utf8 = false;
        w->offer_has_plain = false;
    }
}
static const struct spec_wl_data_device_listener _spec_data_device_listener = {
    _spec_data_dev_offer,
    _spec_data_dev_enter,
    _spec_data_dev_leave,
    _spec_data_dev_motion,
    _spec_data_dev_drop,
    _spec_data_dev_selection
};

static void _spec_data_source_target(void* d, struct wl_data_source* s, const char* m) { (void)d;(void)s;(void)m; }
static void _spec_data_source_send(void* data, struct wl_data_source* source, const char* mime_type, int32_t fd) {
    (void)source; (void)mime_type;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && w->clipboard_out && fd >= 0) {
        size_t len = strlen(w->clipboard_out);
        size_t off = 0;
        while (off < len) {
            ssize_t n = write(fd, w->clipboard_out + off, len - off);
            if (n <= 0) break;
            off += (size_t)n;
        }
    }
    if (fd >= 0) close(fd);
}
static void _spec_data_source_cancelled(void* data, struct wl_data_source* source) {
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && w->data_source == source) w->data_source = NULL;
    if (source) _wl_proxy_destroy((struct wl_proxy*)source);
}
static void _spec_data_source_dnd_drop(void* d, struct wl_data_source* s) { (void)d;(void)s; }
static void _spec_data_source_dnd_fin(void* d, struct wl_data_source* s) { (void)d;(void)s; }
static void _spec_data_source_action(void* d, struct wl_data_source* s, uint32_t a) { (void)d;(void)s;(void)a; }
static const struct spec_wl_data_source_listener _spec_data_source_listener = {
    _spec_data_source_target,
    _spec_data_source_send,
    _spec_data_source_cancelled,
    _spec_data_source_dnd_drop,
    _spec_data_source_dnd_fin,
    _spec_data_source_action
};

static void _spec_ensure_data_device(SpecWaylandWindow* w) {
    if (!w || w->data_device || !w->data_mgr || !w->seat || !_wl_data_device_iface) return;
    uint32_t v = _wl_proxy_get_version((struct wl_proxy*)w->data_mgr);
    w->data_device = (struct wl_data_device*)_wl_proxy_marshal_flags(
        (struct wl_proxy*)w->data_mgr, 1 /* GET_DATA_DEVICE */, _wl_data_device_iface, v, 0,
        NULL, w->seat);
    if (w->data_device) {
        _wl_proxy_add_listener((struct wl_proxy*)w->data_device, (void (**)(void))&_spec_data_device_listener, w);
    }
}

struct spec_wl_output_listener {
    void (*geometry)(void* data, void* output, int32_t x, int32_t y, int32_t phys_w, int32_t phys_h, int32_t subpixel, const char* make, const char* model, int32_t transform);
    void (*mode)(void* data, void* output, uint32_t flags, int32_t width, int32_t height, int32_t refresh);
    void (*done)(void* data, void* output);
    void (*scale)(void* data, void* output, int32_t factor);
};

static void _spec_output_geometry(void* data, void* output, int32_t x, int32_t y, int32_t phys_w, int32_t phys_h, int32_t subpixel, const char* make, const char* model, int32_t transform) {
    (void)output; (void)x; (void)y; (void)phys_h; (void)subpixel; (void)make; (void)model; (void)transform;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && phys_w > 0 && w->output_phys_w_mm == 0) w->output_phys_w_mm = phys_w;
}

static void _spec_output_mode(void* data, void* output, uint32_t flags, int32_t width, int32_t height, int32_t refresh) {
    (void)output; (void)height; (void)refresh;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && (flags & 1) && width > 0 && w->output_mode_w == 0) w->output_mode_w = width;
}

static void _spec_output_done(void* data, void* output) {
    (void)data; (void)output;
}

static void _spec_output_scale(void* data, void* output, int32_t factor) {
    (void)output;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && factor > w->output_scale) w->output_scale = factor;
}

static const struct spec_wl_output_listener _spec_output_listener = {
    _spec_output_geometry,
    _spec_output_mode,
    _spec_output_done,
    _spec_output_scale
};

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
    } else if (strcmp(iface, "wl_seat") == 0 && _wl_seat_iface && !w->seat) {
        uint32_t v = version < 5 ? version : 5;
        w->seat = (struct wl_seat*)_wl_proxy_marshal_flags(
            (struct wl_proxy*)reg, 0 /* WL_REGISTRY_BIND */, _wl_seat_iface, v, 0,
            name, iface, v, NULL);
        if (w->seat) {
            _wl_proxy_add_listener((struct wl_proxy*)w->seat, (void (**)(void))&_spec_seat_listener, w);
            _spec_ensure_data_device(w);
        }
    } else if (strcmp(iface, "wl_data_device_manager") == 0 && _wl_data_device_manager_iface && !w->data_mgr) {
        uint32_t v = version < 3 ? version : 3;
        w->data_mgr = (struct wl_data_device_manager*)_wl_proxy_marshal_flags(
            (struct wl_proxy*)reg, 0 /* WL_REGISTRY_BIND */, _wl_data_device_manager_iface, v, 0,
            name, iface, v, NULL);
        _spec_ensure_data_device(w);
    } else if (strcmp(iface, "wl_output") == 0 && _wl_output_iface) {
        uint32_t v = version < 2 ? version : 2;
        void* out = _wl_proxy_marshal_flags(
            (struct wl_proxy*)reg, 0 /* WL_REGISTRY_BIND */, _wl_output_iface, v, 0,
            name, iface, v, NULL);
        if (out) {
            _wl_proxy_add_listener((struct wl_proxy*)out, (void (**)(void))&_spec_output_listener, w);
        }
    } else if (strcmp(iface, "xdg_wm_base") == 0 && !w->xdg_wm_base) {
        w->xdg_wm_base = _wl_proxy_marshal_flags(
            (struct wl_proxy*)reg, 0 /* WL_REGISTRY_BIND */,
            (const struct wl_interface*)&_spec_xdg_wm_base_iface_def, 1, 0,
            name, iface, 1, NULL);
    } else if (strcmp(iface, "zxdg_decoration_manager_v1") == 0 && !w->decor_mgr) {
        w->decor_mgr = _wl_proxy_marshal_flags(
            (struct wl_proxy*)reg, 0 /* WL_REGISTRY_BIND */,
            (const struct wl_interface*)&_spec_zxdg_deco_mgr_iface_def, 1, 0,
            name, iface, 1, NULL);
    } else if (strcmp(iface, "wp_cursor_shape_manager_v1") == 0 && !w->cursor_mgr) {
        w->cursor_mgr = _wl_proxy_marshal_flags(
            (struct wl_proxy*)reg, 0 /* WL_REGISTRY_BIND */,
            (const struct wl_interface*)&_spec_wp_cursor_mgr_iface_def, 1, 0,
            name, iface, 1, NULL);
    } else if (strcmp(iface, "xdg_toplevel_icon_manager_v1") == 0 && !w->icon_mgr) {
        w->icon_mgr = _wl_proxy_marshal_flags(
            (struct wl_proxy*)reg, 0 /* WL_REGISTRY_BIND */,
            (const struct wl_interface*)&_spec_xdg_icon_mgr_iface_def, 1, 0,
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

    struct wl_buffer* old_buf = w->buffer;
    struct wl_shm_pool* old_pool = w->shm_pool;
    void* old_data = w->shm_data;
    size_t old_size = w->shm_size;
    int old_fd = w->shm_fd;
    int old_w = w->width;
    int old_h = w->height;

    w->buffer = NULL;
    w->shm_pool = NULL;
    w->shm_data = NULL;
    w->shm_size = 0;
    w->shm_fd = -1;

    int stride = width * 4;
    size_t size = (size_t)stride * (size_t)height;

    char tmpl[] = "/tmp/spec_suit_shm_XXXXXX";
    int fd = mkstemp(tmpl);
    if (fd < 0) {
        w->buffer = old_buf; w->shm_pool = old_pool; w->shm_data = old_data; w->shm_size = old_size; w->shm_fd = old_fd;
        return false;
    }
    unlink(tmpl);
    if (ftruncate(fd, (off_t)size) < 0 || posix_fallocate(fd, 0, (off_t)size) != 0) {
        close(fd);
        w->buffer = old_buf; w->shm_pool = old_pool; w->shm_data = old_data; w->shm_size = old_size; w->shm_fd = old_fd;
        return false;
    }
    void* ptr = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (ptr == MAP_FAILED) {
        close(fd);
        w->buffer = old_buf; w->shm_pool = old_pool; w->shm_data = old_data; w->shm_size = old_size; w->shm_fd = old_fd;
        return false;
    }

    uint32_t* px = (uint32_t*)ptr;
    size_t count = (size_t)width * (size_t)height;
    uint32_t fill = 0xFF181C24u;
    bool has_old_pixels = (old_data && old_data != MAP_FAILED && old_w > 0 && old_h > 0 &&
        old_size >= (size_t)old_h * (size_t)old_w * 4);
    if (has_old_pixels) {
        const uint32_t* opx = (const uint32_t*)old_data;
        fill = opx[(size_t)(old_h - 1) * (size_t)old_w + (size_t)(old_w - 1)];
    }
    for (size_t i = 0; i < count; i++) {
        px[i] = fill;
    }
    if (has_old_pixels) {
        const uint32_t* opx = (const uint32_t*)old_data;
        int copy_w = old_w < width ? old_w : width;
        int copy_h = old_h < height ? old_h : height;
        for (int row = 0; row < copy_h; row++) {
            memcpy(px + (size_t)row * (size_t)width, opx + (size_t)row * (size_t)old_w, (size_t)copy_w * 4);
        }
    }

    if (old_buf) _wl_proxy_destroy((struct wl_proxy*)old_buf);
    if (old_pool) _wl_proxy_destroy((struct wl_proxy*)old_pool);
    if (old_data && old_data != MAP_FAILED && old_size > 0) munmap(old_data, old_size);
    if (old_fd >= 0) close(old_fd);

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

    if (!w->use_vulkan) {
        _spec_ensure_shm_buffer(w, cw, ch);
        uint32_t sv = _wl_proxy_get_version((struct wl_proxy*)w->surface);
        if (w->buffer) {
            _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 1 /* WL_SURFACE_ATTACH */, NULL, sv, 0, w->buffer, 0, 0);
            if (sv >= 4) {
                _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 9 /* WL_SURFACE_DAMAGE_BUFFER */, NULL, sv, 0, 0, 0, w->width, w->height);
            }
        }
    } else {
        w->width = cw;
        w->height = ch;
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

static void _spec_xdg_wm_ping(void* data, void* wm_base, uint32_t serial) {
    (void)data;
    uint32_t v = _wl_proxy_get_version((struct wl_proxy*)wm_base);
    _wl_proxy_marshal_flags((struct wl_proxy*)wm_base, 3 /* XDG_WM_BASE_PONG */, NULL, v, 0, serial);
}
static const struct { void (*ping)(void*, void*, uint32_t); } _spec_xdg_wm_listener = { _spec_xdg_wm_ping };

static void _spec_xdg_surf_configure(void* data, void* xdg_surf, uint32_t serial) {
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    uint32_t v = _wl_proxy_get_version((struct wl_proxy*)xdg_surf);
    _wl_proxy_marshal_flags((struct wl_proxy*)xdg_surf, 4 /* XDG_SURFACE_ACK_CONFIGURE */, NULL, v, 0, serial);
    if (!w) return;
    int cw = w->pending_w > 0 ? w->pending_w : w->width;
    int ch = w->pending_h > 0 ? w->pending_h : w->height;
    if (cw <= 0) cw = 800;
    if (ch <= 0) ch = 600;
    if (!w->use_vulkan) {
        if (!w->configured || cw != w->width || ch != w->height) {
            _spec_ensure_shm_buffer(w, cw, ch);
            if (w->buffer) {
                uint32_t sv = _wl_proxy_get_version((struct wl_proxy*)w->surface);
                _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 1 /* WL_SURFACE_ATTACH */, NULL, sv, 0, w->buffer, 0, 0);
                if (sv >= 4) {
                    _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 9 /* WL_SURFACE_DAMAGE_BUFFER */, NULL, sv, 0, 0, 0, w->width, w->height);
                }
            }
        }
    } else {
        w->width = cw;
        w->height = ch;
    }
    if (w->surface && (!w->use_vulkan || !w->configured)) {
        uint32_t sv = _wl_proxy_get_version((struct wl_proxy*)w->surface);
        _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 6 /* WL_SURFACE_COMMIT */, NULL, sv, 0);
    }
    w->configured = true;
}
static const struct { void (*configure)(void*, void*, uint32_t); } _spec_xdg_surf_listener = { _spec_xdg_surf_configure };

static void _spec_xdg_top_configure(void* data, void* top, int32_t width, int32_t height, void* states) {
    (void)top; (void)states;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w && width > 0 && height > 0) {
        w->pending_w = width;
        w->pending_h = height;
    }
}
static void _spec_xdg_top_close(void* data, void* top) {
    (void)top;
    SpecWaylandWindow* w = (SpecWaylandWindow*)data;
    if (w) w->should_close = true;
}
static void _spec_xdg_top_bounds(void* d, void* t, int32_t w, int32_t h) { (void)d;(void)t;(void)w;(void)h; }
static void _spec_xdg_top_caps(void* d, void* t, void* a) { (void)d;(void)t;(void)a; }
static const struct {
    void (*configure)(void*, void*, int32_t, int32_t, void*);
    void (*close)(void*, void*);
    void (*configure_bounds)(void*, void*, int32_t, int32_t);
    void (*wm_capabilities)(void*, void*, void*);
} _spec_xdg_top_listener = {
    _spec_xdg_top_configure,
    _spec_xdg_top_close,
    _spec_xdg_top_bounds,
    _spec_xdg_top_caps
};

static void _spec_zxdg_deco_configure(void* d, void* deco, uint32_t mode) { (void)d;(void)deco;(void)mode; }
static const struct { void (*configure)(void*, void*, uint32_t); } _spec_zxdg_deco_listener = { _spec_zxdg_deco_configure };

long long spec_pal_window_close(long long handle) {
    if (handle <= 0) return 0;
    size_t idx = (size_t)(handle - 1);
    if (idx >= _spec_windows_cap || !_spec_windows[idx]) return 0;
    SpecWaylandWindow* w = _spec_windows[idx];
    _spec_windows[idx] = NULL;

    _spec_release_shm(w);
    if (w->key_queue) free(w->key_queue);
    if (w->char_queue) free(w->char_queue);
    if (w->ev_queue) free(w->ev_queue);
    if (w->clipboard_out) free(w->clipboard_out);
    if (w->clipboard_in) free(w->clipboard_in);
    if (w->data_source) _wl_proxy_destroy((struct wl_proxy*)w->data_source);
    if (w->current_offer) _wl_proxy_destroy((struct wl_proxy*)w->current_offer);
    if (w->pending_offer && w->pending_offer != w->current_offer) _wl_proxy_destroy((struct wl_proxy*)w->pending_offer);
    if (w->data_device) _wl_proxy_destroy((struct wl_proxy*)w->data_device);
    if (w->data_mgr) _wl_proxy_destroy((struct wl_proxy*)w->data_mgr);
    if (w->touch) _wl_proxy_destroy((struct wl_proxy*)w->touch);
    if (w->xkb_state && _xkb_state_unref) _xkb_state_unref(w->xkb_state);
    if (w->xkb_keymap && _xkb_keymap_unref) _xkb_keymap_unref(w->xkb_keymap);
    if (w->xkb_ctx && _xkb_context_unref) _xkb_context_unref(w->xkb_ctx);
    if (w->cursor_dev && _wl_proxy_destroy) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->cursor_dev, 0 /* DESTROY */, NULL, 1, 1);
    }
    if (w->cursor_mgr && _wl_proxy_destroy) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->cursor_mgr, 0 /* DESTROY */, NULL, 1, 1);
    }
    if (w->xdg_decoration && _wl_proxy_destroy) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->xdg_decoration, 0 /* DESTROY */, NULL, 1, 1 /* WL_MARSHAL_FLAG_DESTROY */);
    }
    if (w->xdg_toplevel && _wl_proxy_destroy) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->xdg_toplevel, 0 /* DESTROY */, NULL, 1, 1);
    }
    if (w->xdg_surface && _wl_proxy_destroy) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->xdg_surface, 0 /* DESTROY */, NULL, 1, 1);
    }
    if (w->decor_mgr && _wl_proxy_destroy) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->decor_mgr, 0 /* DESTROY */, NULL, 1, 1);
    }
    if (w->xdg_wm_base && _wl_proxy_destroy) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->xdg_wm_base, 0 /* DESTROY */, NULL, 1, 1);
    }
    if (w->frame && _libdecor_frame_unref) _libdecor_frame_unref(w->frame);
    if (w->decor && _libdecor_unref) _libdecor_unref(w->decor);
    if (w->pointer && _wl_proxy_destroy) _wl_proxy_destroy((struct wl_proxy*)w->pointer);
    if (w->keyboard && _wl_proxy_destroy) _wl_proxy_destroy((struct wl_proxy*)w->keyboard);
    if (w->seat && _wl_proxy_destroy) _wl_proxy_destroy((struct wl_proxy*)w->seat);
    if (w->surface && _wl_proxy_destroy) _wl_proxy_destroy((struct wl_proxy*)w->surface);
    if (w->shm && _wl_proxy_destroy) _wl_proxy_destroy((struct wl_proxy*)w->shm);
    if (w->compositor && _wl_proxy_destroy) _wl_proxy_destroy((struct wl_proxy*)w->compositor);
    if (w->registry && _wl_proxy_destroy) _wl_proxy_destroy((struct wl_proxy*)w->registry);
    if (w->display && _wl_display_disconnect) _wl_display_disconnect(w->display);
    free(w);
    return 0;
}

long long spec_pal_window_open_ex(long long title_cstr, long long width, long long height, long long decorated, long long use_vulkan) {
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
    w->use_vulkan = (use_vulkan != 0);
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

    if (w->xdg_wm_base && w->decor_mgr) {
        w->use_xdg = true;
        w->pending_w = (int)width;
        w->pending_h = (int)height;
        _wl_proxy_add_listener((struct wl_proxy*)w->xdg_wm_base, (void (**)(void))&_spec_xdg_wm_listener, w);

        w->xdg_surface = _wl_proxy_marshal_flags(
            (struct wl_proxy*)w->xdg_wm_base, 2 /* GET_XDG_SURFACE */,
            (const struct wl_interface*)&_spec_xdg_surface_iface_def, 1, 0, NULL, w->surface);
        if (!w->xdg_surface) {
            _spec_set_win_error("Failed to create xdg_surface");
            _wl_display_disconnect(w->display);
            free(w);
            return -1;
        }
        _wl_proxy_add_listener((struct wl_proxy*)w->xdg_surface, (void (**)(void))&_spec_xdg_surf_listener, w);

        w->xdg_toplevel = _wl_proxy_marshal_flags(
            (struct wl_proxy*)w->xdg_surface, 1 /* GET_TOPLEVEL */,
            (const struct wl_interface*)&_spec_xdg_toplevel_iface_def, 1, 0, NULL);
        if (!w->xdg_toplevel) {
            _spec_set_win_error("Failed to create xdg_toplevel");
            _wl_display_disconnect(w->display);
            free(w);
            return -1;
        }
        _wl_proxy_add_listener((struct wl_proxy*)w->xdg_toplevel, (void (**)(void))&_spec_xdg_top_listener, w);
        _wl_proxy_marshal_flags((struct wl_proxy*)w->xdg_toplevel, 2 /* SET_TITLE */, NULL, 1, 0, title);
        _wl_proxy_marshal_flags((struct wl_proxy*)w->xdg_toplevel, 3 /* SET_APP_ID */, NULL, 1, 0, "spec.suit");

        w->xdg_decoration = _wl_proxy_marshal_flags(
            (struct wl_proxy*)w->decor_mgr, 1 /* GET_TOPLEVEL_DECORATION */,
            (const struct wl_interface*)&_spec_zxdg_deco_iface_def, 1, 0, NULL, w->xdg_toplevel);
        if (w->xdg_decoration) {
            _wl_proxy_add_listener((struct wl_proxy*)w->xdg_decoration, (void (**)(void))&_spec_zxdg_deco_listener, w);
            if (decorated) {
                _wl_proxy_marshal_flags((struct wl_proxy*)w->xdg_decoration, 1 /* SET_MODE */, NULL, 1, 0, 2U /* SERVER_SIDE */);
            } else {
                _wl_proxy_marshal_flags((struct wl_proxy*)w->xdg_decoration, 1 /* SET_MODE */, NULL, 1, 0, 1U /* CLIENT_SIDE */);
            }
        }

        uint32_t sv = _wl_proxy_get_version((struct wl_proxy*)w->surface);
        _wl_proxy_marshal_flags((struct wl_proxy*)w->surface, 6 /* WL_SURFACE_COMMIT */, NULL, sv, 0);
        _wl_display_flush(w->display);

        int guard = 0;
        while (!w->configured && !w->should_close && guard < 200) {
            if (_wl_display_roundtrip(w->display) < 0) break;
            guard++;
        }
    } else {
        if (!_spec_win_init_libdecor()) {
            _wl_proxy_destroy((struct wl_proxy*)w->surface);
            _wl_proxy_destroy((struct wl_proxy*)w->shm);
            _wl_proxy_destroy((struct wl_proxy*)w->compositor);
            _wl_proxy_destroy((struct wl_proxy*)w->registry);
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
    }
    if (!w->use_vulkan) {
        _spec_surface_present(w);
    }
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

long long spec_pal_window_open(long long title_cstr, long long width, long long height, long long decorated) {
    return spec_pal_window_open_ex(title_cstr, width, height, decorated, 0);
}

long long spec_pal_window_display_handle(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return w ? (long long)(intptr_t)w->display : 0;
}

long long spec_pal_window_surface_handle(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return w ? (long long)(intptr_t)w->surface : 0;
}

long long spec_pal_window_scale_milli(long long handle) {
    const char* env = getenv("SPEC_UI_SCALE");
    if (!env || !*env) env = getenv("GDK_SCALE");
    if (!env || !*env) env = getenv("QT_SCALE_FACTOR");
    if (env && *env) {
        double v = atof(env);
        if (v > 0.25 && v < 8.0) return (long long)(v * 1000.0 + 0.5);
    }
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w) return 1000;
    if (w->output_scale > 1) return (long long)w->output_scale * 1000;
    if (w->output_phys_w_mm > 0 && w->output_mode_w > 0) {
        double dpi = ((double)w->output_mode_w * 25.4) / (double)w->output_phys_w_mm;
        if (dpi > 110.0) {
            return (long long)((dpi / 96.0) * 1000.0 + 0.5);
        }
    }
    return 1000;
}

long long spec_pal_window_poll_timeout(long long handle, long long timeout_ms) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || w->should_close) return 0;
    int t = timeout_ms < 0 ? 0 : (int)timeout_ms;
    if (w->use_xdg) {
        if (_wl_display_dispatch_pending) {
            if (_wl_display_dispatch_pending(w->display) < 0) {
                w->should_close = true;
                return 0;
            }
        }
        _wl_display_flush(w->display);
        if (_wl_display_prepare_read && _wl_display_read_events && _wl_display_get_fd) {
            if (_wl_display_prepare_read(w->display) == 0) {
                struct pollfd pfd;
                pfd.fd = _wl_display_get_fd(w->display);
                pfd.events = POLLIN;
                pfd.revents = 0;
                int pr = poll(&pfd, 1, t);
                if (pr > 0 && (pfd.revents & POLLIN)) {
                    _wl_display_read_events(w->display);
                    if (_wl_display_dispatch_pending) _wl_display_dispatch_pending(w->display);
                } else {
                    if (_wl_display_cancel_read) _wl_display_cancel_read(w->display);
                }
            } else if (_wl_display_dispatch_pending) {
                _wl_display_dispatch_pending(w->display);
            }
        }
        if (w->should_close) return 0;
        _wl_display_flush(w->display);
        return 1;
    }
    if (_libdecor_dispatch(w->decor, t) < 0) {
        w->should_close = true;
        return 0;
    }
    if (w->should_close) return 0;
    _wl_display_flush(w->display);
    return 1;
}

long long spec_pal_window_poll(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || w->should_close) return 0;
    long long default_ms = w->use_vulkan ? 0 : (w->use_xdg ? 4 : 16);
    return spec_pal_window_poll_timeout(handle, default_ms);
}

long long spec_pal_window_next_key(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || w->key_len == 0) return 0;
    int ch = w->key_queue[0];
    if (w->key_len > 1) {
        memmove(w->key_queue, w->key_queue + 1, (w->key_len - 1) * sizeof(int));
    }
    w->key_len--;
    return (long long)ch;
}

long long spec_pal_window_width(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return w ? (long long)w->width : 0;
}

long long spec_pal_window_height(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return w ? (long long)w->height : 0;
}

long long spec_pal_window_pointer_x(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return w ? (long long)w->pointer_x : 0;
}

long long spec_pal_window_pointer_y(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return w ? (long long)w->pointer_y : 0;
}

long long spec_pal_window_poll_click(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || !w->has_click) return 0;
    w->has_click = false;
    return 1;
}

long long spec_pal_window_click_x(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return w ? (long long)w->click_x : 0;
}

long long spec_pal_window_click_y(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return w ? (long long)w->click_y : 0;
}

long long spec_pal_window_poll_right_click(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || !w->has_right_click) return 0;
    w->has_right_click = false;
    return 1;
}

long long spec_pal_window_right_click_x(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return w ? (long long)w->right_click_x : 0;
}

long long spec_pal_window_right_click_y(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return w ? (long long)w->right_click_y : 0;
}

long long spec_pal_window_poll_event(long long handle, long long out_5_i32_ptr) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || !out_5_i32_ptr || !w->ev_queue || w->ev_head == w->ev_tail) return 0;
    SpecInputEvent ev = w->ev_queue[w->ev_head];
    w->ev_head = (w->ev_head + 1) % w->ev_cap;
    int32_t* out = (int32_t*)(intptr_t)out_5_i32_ptr;
    out[0] = ev.kind;
    out[1] = ev.a;
    out[2] = ev.b;
    out[3] = ev.c;
    out[4] = ev.d;
    return 1;
}

long long spec_pal_window_poll_scroll_y(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w) return 0;
    long long dy = (long long)w->scroll_y;
    w->scroll_y = 0;
    return dy;
}

long long spec_pal_window_poll_scroll_x(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w) return 0;
    long long dx = (long long)w->scroll_x;
    w->scroll_x = 0;
    return dx;
}

long long spec_pal_window_pointer_down(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return (w && w->pointer_down) ? 1 : 0;
}

long long spec_pal_window_set_title(long long handle, long long title_cstr) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || !title_cstr) return 0;
    const char* title = (const char*)(intptr_t)title_cstr;
    if (w->use_xdg && w->xdg_toplevel) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->xdg_toplevel, 2 /* SET_TITLE */, NULL, 1, 0, title);
        _wl_display_flush(w->display);
        return 1;
    }
    if (w->frame && _libdecor_frame_set_title) {
        _libdecor_frame_set_title(w->frame, title);
        _wl_display_flush(w->display);
        return 1;
    }
    return 0;
}

long long spec_pal_window_set_clipboard(long long handle, long long text_cstr) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || !text_cstr) return 0;
    const char* txt = (const char*)(intptr_t)text_cstr;
    free(w->clipboard_out);
    w->clipboard_out = strdup(txt);
    if (!w->clipboard_out) return 0;
    if (!w->data_mgr || !w->data_device || !_wl_data_source_iface) return 0;
    if (w->data_source) {
        _wl_proxy_destroy((struct wl_proxy*)w->data_source);
        w->data_source = NULL;
    }
    uint32_t mgr_v = _wl_proxy_get_version((struct wl_proxy*)w->data_mgr);
    w->data_source = (struct wl_data_source*)_wl_proxy_marshal_flags(
        (struct wl_proxy*)w->data_mgr, 0 /* CREATE_DATA_SOURCE */, _wl_data_source_iface, mgr_v, 0, NULL);
    if (!w->data_source) return 0;
    _wl_proxy_add_listener((struct wl_proxy*)w->data_source, (void (**)(void))&_spec_data_source_listener, w);
    uint32_t src_v = _wl_proxy_get_version((struct wl_proxy*)w->data_source);
    _wl_proxy_marshal_flags((struct wl_proxy*)w->data_source, 0 /* OFFER */, NULL, src_v, 0, "text/plain;charset=utf-8");
    _wl_proxy_marshal_flags((struct wl_proxy*)w->data_source, 0 /* OFFER */, NULL, src_v, 0, "text/plain");
    _wl_proxy_marshal_flags((struct wl_proxy*)w->data_source, 0 /* OFFER */, NULL, src_v, 0, "UTF8_STRING");
    uint32_t dev_v = _wl_proxy_get_version((struct wl_proxy*)w->data_device);
    _wl_proxy_marshal_flags((struct wl_proxy*)w->data_device, 1 /* SET_SELECTION */, NULL, dev_v, 0, w->data_source, w->last_input_serial);
    _wl_display_flush(w->display);
    return 1;
}

long long spec_pal_window_get_clipboard(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w) return 0;
    if (w->data_source && w->clipboard_out) {
        return (long long)(intptr_t)w->clipboard_out;
    }
    if (!w->current_offer || (!w->offer_has_utf8 && !w->offer_has_plain)) return 0;
    const char* mime = w->offer_has_utf8 ? "text/plain;charset=utf-8" : "text/plain";
    int fds[2];
    if (pipe(fds) != 0) return 0;
    uint32_t ov = _wl_proxy_get_version((struct wl_proxy*)w->current_offer);
    _wl_proxy_marshal_flags((struct wl_proxy*)w->current_offer, 1 /* RECEIVE */, NULL, ov, 0, mime, fds[1]);
    close(fds[1]);
    _wl_display_flush(w->display);

    size_t cap = 256;
    size_t len = 0;
    char* buf = (char*)malloc(cap);
    if (!buf) {
        close(fds[0]);
        return 0;
    }
    for (;;) {
        if (len + 1 >= cap) {
            size_t next_cap = cap * 2;
            char* nb = (char*)realloc(buf, next_cap);
            if (!nb) break;
            buf = nb;
            cap = next_cap;
        }
        ssize_t n = read(fds[0], buf + len, cap - 1 - len);
        if (n <= 0) break;
        len += (size_t)n;
    }
    close(fds[0]);
    buf[len] = '\0';
    free(w->clipboard_in);
    w->clipboard_in = buf;
    return (long long)(intptr_t)w->clipboard_in;
}

long long spec_pal_window_present(long long handle, long long pixels_addr, long long width, long long height) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || !pixels_addr || width <= 0 || height <= 0) return 0;
    if (!w->shm_data || w->width <= 0 || w->height <= 0) return 0;
    const uint32_t* src = (const uint32_t*)(intptr_t)pixels_addr;
    uint32_t* dst = (uint32_t*)w->shm_data;
    int copy_w = (int)width < w->width ? (int)width : w->width;
    int copy_h = (int)height < w->height ? (int)height : w->height;
    for (int y = 0; y < copy_h; y++) {
        memcpy(dst + (size_t)y * (size_t)w->width, src + (size_t)y * (size_t)width, (size_t)copy_w * 4);
    }
    _spec_surface_present(w);
    _wl_display_flush(w->display);
    return 1;
}

long long spec_pal_window_next_char(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || w->char_len == 0) return 0;
    int cp = w->char_queue[0];
    if (w->char_len > 1) {
        memmove(w->char_queue, w->char_queue + 1, (w->char_len - 1) * sizeof(int));
    }
    w->char_len--;
    return (long long)cp;
}

long long spec_pal_window_mods(long long handle) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    return w ? (long long)w->mods : 0;
}

long long spec_pal_window_set_cursor(long long handle, long long kind) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || !w->cursor_mgr || !w->pointer || !w->last_ptr_serial) return 0;
    if (!w->cursor_dev) {
        w->cursor_dev = _wl_proxy_marshal_flags(
            (struct wl_proxy*)w->cursor_mgr, 1 /* GET_POINTER */,
            (const struct wl_interface*)&_spec_wp_cursor_dev_iface_def, 1, 0, NULL, w->pointer);
    }
    if (!w->cursor_dev) return 0;
    uint32_t shape = 1; /* default */
    if (kind == 1) shape = 9;       /* text */
    else if (kind == 2) shape = 4;  /* pointer */
    else if (kind == 3) shape = 26; /* ew_resize */
    else if (kind == 4) shape = 27; /* ns_resize */
    _wl_proxy_marshal_flags((struct wl_proxy*)w->cursor_dev, 1 /* SET_SHAPE */, NULL, 1, 0, w->last_ptr_serial, shape);
    _wl_display_flush(w->display);
    return 1;
}

long long spec_pal_window_set_min_size(long long handle, long long min_w, long long min_h) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w) return 0;
    if (w->use_xdg && w->xdg_toplevel) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->xdg_toplevel, 8 /* SET_MIN_SIZE */, NULL, 1, 0, (int32_t)min_w, (int32_t)min_h);
        _wl_display_flush(w->display);
        return 1;
    }
    return 0;
}

long long spec_pal_window_set_app_id(long long handle, long long app_id_cstr) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || !app_id_cstr) return 0;
    const char* app_id = (const char*)(intptr_t)app_id_cstr;
    if (w->use_xdg && w->xdg_toplevel) {
        _wl_proxy_marshal_flags((struct wl_proxy*)w->xdg_toplevel, 3 /* SET_APP_ID */, NULL, 1, 0, app_id);
        _wl_display_flush(w->display);
        return 1;
    }
    if (w->frame && _libdecor_frame_set_app_id) {
        _libdecor_frame_set_app_id(w->frame, app_id);
        _wl_display_flush(w->display);
        return 1;
    }
    return 0;
}

long long spec_pal_window_set_icon(long long handle, long long pixels_addr, long long width, long long height) {
    SpecWaylandWindow* w = _spec_get_window(handle);
    if (!w || !pixels_addr || width <= 0 || height <= 0) return 0;
    if (!w->icon_mgr || !w->xdg_toplevel || !w->shm || !_wl_shm_pool_iface || !_wl_buffer_iface) return 0;
    int iw = (int)width;
    int ih = (int)height;
    int stride = iw * 4;
    size_t size = (size_t)stride * (size_t)ih;
    char tmpl[] = "/tmp/spec_icon_shm_XXXXXX";
    int fd = mkstemp(tmpl);
    if (fd < 0) return 0;
    unlink(tmpl);
    if (ftruncate(fd, (off_t)size) < 0) { close(fd); return 0; }
    void* ptr = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (ptr == MAP_FAILED) { close(fd); return 0; }
    memcpy(ptr, (const void*)(intptr_t)pixels_addr, size);
    uint32_t shm_ver = _wl_proxy_get_version((struct wl_proxy*)w->shm);
    struct wl_shm_pool* pool = (struct wl_shm_pool*)_wl_proxy_marshal_flags(
        (struct wl_proxy*)w->shm, 0 /* WL_SHM_CREATE_POOL */, _wl_shm_pool_iface, shm_ver, 0,
        NULL, fd, (int32_t)size);
    if (!pool) { munmap(ptr, size); close(fd); return 0; }
    uint32_t pool_ver = _wl_proxy_get_version((struct wl_proxy*)pool);
    struct wl_buffer* wl_buf = (struct wl_buffer*)_wl_proxy_marshal_flags(
        (struct wl_proxy*)pool, 0 /* WL_SHM_POOL_CREATE_BUFFER */, _wl_buffer_iface, pool_ver, 0,
        NULL, 0, iw, ih, stride, 0 /* WL_SHM_FORMAT_ARGB8888 */);
    _wl_proxy_destroy((struct wl_proxy*)pool);
    munmap(ptr, size);
    close(fd);
    if (!wl_buf) return 0;
    void* icon = _wl_proxy_marshal_flags(
        (struct wl_proxy*)w->icon_mgr, 1 /* CREATE_ICON */,
        (const struct wl_interface*)&_spec_xdg_icon_iface_def, 1, 0, NULL);
    if (icon) {
        _wl_proxy_marshal_flags((struct wl_proxy*)icon, 2 /* ADD_BUFFER */, NULL, 1, 0, wl_buf, 1);
        _wl_proxy_marshal_flags((struct wl_proxy*)w->icon_mgr, 2 /* SET_ICON */, NULL, 1, 0, w->xdg_toplevel, icon);
        _wl_proxy_marshal_flags((struct wl_proxy*)icon, 0 /* DESTROY */, NULL, 1, 1);
        _wl_display_flush(w->display);
        return 1;
    }
    _wl_proxy_destroy((struct wl_proxy*)wl_buf);
    return 0;
}

#else

long long spec_pal_window_open(long long title_cstr, long long width, long long height, long long decorated) {
    (void)title_cstr; (void)width; (void)height; (void)decorated;
    _spec_set_win_error("Native windowing is currently implemented for Linux Wayland only");
    return -1;
}

long long spec_pal_window_open_ex(long long title_cstr, long long width, long long height, long long decorated, long long use_vulkan) {
    (void)use_vulkan;
    return spec_pal_window_open(title_cstr, width, height, decorated);
}

long long spec_pal_window_display_handle(long long handle) {
    (void)handle;
    return 0;
}

long long spec_pal_window_surface_handle(long long handle) {
    (void)handle;
    return 0;
}

long long spec_pal_window_scale_milli(long long handle) {
    (void)handle;
    return 1000;
}

long long spec_pal_window_poll_timeout(long long handle, long long timeout_ms) {
    (void)handle;
    (void)timeout_ms;
    return 0;
}

long long spec_pal_window_poll(long long handle) {
    (void)handle;
    return 0;
}

long long spec_pal_window_close(long long handle) {
    (void)handle;
    return 0;
}

long long spec_pal_window_next_key(long long handle) {
    (void)handle;
    return 0;
}

long long spec_pal_window_width(long long handle) {
    (void)handle;
    return 0;
}

long long spec_pal_window_height(long long handle) {
    (void)handle;
    return 0;
}

long long spec_pal_window_pointer_x(long long handle) { (void)handle; return 0; }
long long spec_pal_window_pointer_y(long long handle) { (void)handle; return 0; }
long long spec_pal_window_poll_click(long long handle) { (void)handle; return 0; }
long long spec_pal_window_click_x(long long handle) { (void)handle; return 0; }
long long spec_pal_window_click_y(long long handle) { (void)handle; return 0; }
long long spec_pal_window_poll_right_click(long long handle) { (void)handle; return 0; }
long long spec_pal_window_right_click_x(long long handle) { (void)handle; return 0; }
long long spec_pal_window_right_click_y(long long handle) { (void)handle; return 0; }
long long spec_pal_window_poll_event(long long handle, long long out_5_i32_ptr) { (void)handle; (void)out_5_i32_ptr; return 0; }
long long spec_pal_window_poll_scroll_y(long long handle) { (void)handle; return 0; }
long long spec_pal_window_poll_scroll_x(long long handle) { (void)handle; return 0; }
long long spec_pal_window_pointer_down(long long handle) { (void)handle; return 0; }
long long spec_pal_window_set_title(long long handle, long long title_cstr) { (void)handle; (void)title_cstr; return 0; }
long long spec_pal_window_next_char(long long handle) { (void)handle; return 0; }
long long spec_pal_window_mods(long long handle) { (void)handle; return 0; }
long long spec_pal_window_set_cursor(long long handle, long long kind) { (void)handle; (void)kind; return 0; }
long long spec_pal_window_set_min_size(long long handle, long long min_w, long long min_h) { (void)handle; (void)min_w; (void)min_h; return 0; }
long long spec_pal_window_set_app_id(long long handle, long long app_id_cstr) { (void)handle; (void)app_id_cstr; return 0; }
long long spec_pal_window_set_icon(long long handle, long long pixels_addr, long long width, long long height) { (void)handle; (void)pixels_addr; (void)width; (void)height; return 0; }
long long spec_pal_window_set_clipboard(long long handle, long long text_cstr) { (void)handle; (void)text_cstr; return 0; }
long long spec_pal_window_get_clipboard(long long handle) { (void)handle; return 0; }

long long spec_pal_window_present(long long handle, long long pixels_addr, long long width, long long height) {
    (void)handle; (void)pixels_addr; (void)width; (void)height;
    return 0;
}

#endif
