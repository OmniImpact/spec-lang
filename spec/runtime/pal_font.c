#if defined(__has_include) && __has_include(<stb/stb_truetype.h>)
#define STB_TRUETYPE_IMPLEMENTATION
#include <stb/stb_truetype.h>
#define SPEC_HAS_STB_TRUETYPE 1
#else
#define SPEC_HAS_STB_TRUETYPE 0
#endif

static __thread char _spec_last_font_err[256] = "";

static inline void _spec_set_font_error(const char* msg) {
    const char* m = msg ? msg : "Font error";
    snprintf(_spec_last_font_err, sizeof(_spec_last_font_err), "%s", m);
}

long long spec_pal_font_last_error(void) {
    return (long long)(intptr_t)_spec_last_font_err;
}

#if SPEC_HAS_STB_TRUETYPE

typedef struct SpecFont {
    unsigned char* ttf_data;
    stbtt_fontinfo info;
} SpecFont;

static SpecFont** _spec_fonts = NULL;
static size_t _spec_fonts_cap = 0;

static long long _spec_alloc_font_slot(SpecFont* f) {
    for (size_t i = 0; i < _spec_fonts_cap; i++) {
        if (!_spec_fonts[i]) {
            _spec_fonts[i] = f;
            return (long long)(i + 1);
        }
    }
    size_t new_cap = _spec_fonts_cap == 0 ? 8 : _spec_fonts_cap * 2;
    SpecFont** next = (SpecFont**)realloc(_spec_fonts, new_cap * sizeof(SpecFont*));
    if (!next) return -1;
    for (size_t i = _spec_fonts_cap; i < new_cap; i++) next[i] = NULL;
    _spec_fonts = next;
    size_t idx = _spec_fonts_cap;
    _spec_fonts_cap = new_cap;
    _spec_fonts[idx] = f;
    return (long long)(idx + 1);
}

static SpecFont* _spec_get_font(long long handle) {
    if (handle <= 0) return NULL;
    size_t idx = (size_t)(handle - 1);
    if (idx >= _spec_fonts_cap) return NULL;
    return _spec_fonts[idx];
}

long long spec_pal_font_init_memory(long long data_ptr, long long data_len) {
    if (!data_ptr || data_len <= 0) {
        _spec_set_font_error("Empty font buffer");
        return -1;
    }
    unsigned char* copy = (unsigned char*)malloc((size_t)data_len);
    if (!copy) {
        _spec_set_font_error("Out of memory");
        return -1;
    }
    memcpy(copy, (const void*)(intptr_t)data_ptr, (size_t)data_len);

    SpecFont* f = (SpecFont*)calloc(1, sizeof(SpecFont));
    if (!f) {
        free(copy);
        _spec_set_font_error("Out of memory");
        return -1;
    }
    f->ttf_data = copy;
    int offset = stbtt_GetFontOffsetForIndex(copy, 0);
    if (!stbtt_InitFont(&f->info, copy, offset)) {
        free(copy);
        free(f);
        _spec_set_font_error("stbtt_InitFont failed");
        return -1;
    }
    long long h = _spec_alloc_font_slot(f);
    if (h <= 0) {
        free(copy);
        free(f);
        _spec_set_font_error("Out of font slots");
        return -1;
    }
    return h;
}

long long spec_pal_font_close(long long handle) {
    if (handle <= 0) return 0;
    size_t idx = (size_t)(handle - 1);
    if (idx >= _spec_fonts_cap || !_spec_fonts[idx]) return 0;
    SpecFont* f = _spec_fonts[idx];
    _spec_fonts[idx] = NULL;
    if (f->ttf_data) free(f->ttf_data);
    free(f);
    return 0;
}

double spec_pal_font_scale(long long handle, long long pixel_height) {
    SpecFont* f = _spec_get_font(handle);
    if (!f || pixel_height <= 0) return 0.0;
    return (double)stbtt_ScaleForPixelHeight(&f->info, (float)pixel_height);
}

long long spec_pal_font_vmetrics(long long handle, long long out_3_i32_ptr) {
    SpecFont* f = _spec_get_font(handle);
    if (!f || !out_3_i32_ptr) return 0;
    int a = 0, d = 0, g = 0;
    stbtt_GetFontVMetrics(&f->info, &a, &d, &g);
    int32_t* out = (int32_t*)(intptr_t)out_3_i32_ptr;
    out[0] = (int32_t)a;
    out[1] = (int32_t)d;
    out[2] = (int32_t)g;
    return 1;
}

long long spec_pal_font_hmetrics(long long handle, long long cp, long long out_2_i32_ptr) {
    SpecFont* f = _spec_get_font(handle);
    if (!f || !out_2_i32_ptr) return 0;
    int adv = 0, lsb = 0;
    stbtt_GetCodepointHMetrics(&f->info, (int)cp, &adv, &lsb);
    int32_t* out = (int32_t*)(intptr_t)out_2_i32_ptr;
    out[0] = (int32_t)adv;
    out[1] = (int32_t)lsb;
    return 1;
}

long long spec_pal_font_kern_advance(long long handle, long long cp1, long long cp2) {
    SpecFont* f = _spec_get_font(handle);
    if (!f) return 0;
    return (long long)stbtt_GetCodepointKernAdvance(&f->info, (int)cp1, (int)cp2);
}

long long spec_pal_font_glyph_box(long long handle, long long cp, long long pixel_height, long long out_4_i32_ptr) {
    SpecFont* f = _spec_get_font(handle);
    if (!f || !out_4_i32_ptr || pixel_height <= 0) return 0;
    float s = stbtt_ScaleForPixelHeight(&f->info, (float)pixel_height);
    int x0 = 0, y0 = 0, x1 = 0, y1 = 0;
    stbtt_GetCodepointBitmapBox(&f->info, (int)cp, s, s, &x0, &y0, &x1, &y1);
    int32_t* out = (int32_t*)(intptr_t)out_4_i32_ptr;
    out[0] = (int32_t)x0;
    out[1] = (int32_t)y0;
    out[2] = (int32_t)x1;
    out[3] = (int32_t)y1;
    return 1;
}

long long spec_pal_font_rasterize_glyph(long long handle, long long cp, long long pixel_height, long long dst_ptr, long long gw, long long gh) {
    SpecFont* f = _spec_get_font(handle);
    if (!f || !dst_ptr || pixel_height <= 0 || gw <= 0 || gh <= 0) return 0;
    float s = stbtt_ScaleForPixelHeight(&f->info, (float)pixel_height);
    stbtt_MakeCodepointBitmap(&f->info, (unsigned char*)(intptr_t)dst_ptr, (int)gw, (int)gh, (int)gw, s, s, (int)cp);
    return 1;
}

long long spec_pal_font_glyph_box_subpixel(long long handle, long long cp, long long pixel_height, double shift_x, long long out_4_i32_ptr) {
    SpecFont* f = _spec_get_font(handle);
    if (!f || !out_4_i32_ptr || pixel_height <= 0) return 0;
    float s = stbtt_ScaleForPixelHeight(&f->info, (float)pixel_height);
    int x0 = 0, y0 = 0, x1 = 0, y1 = 0;
    stbtt_GetCodepointBitmapBoxSubpixel(&f->info, (int)cp, s, s, (float)shift_x, 0.0f, &x0, &y0, &x1, &y1);
    int32_t* out = (int32_t*)(intptr_t)out_4_i32_ptr;
    out[0] = (int32_t)x0;
    out[1] = (int32_t)y0;
    out[2] = (int32_t)x1;
    out[3] = (int32_t)y1;
    return 1;
}

long long spec_pal_font_rasterize_glyph_subpixel(long long handle, long long cp, long long pixel_height, double shift_x, long long dst_ptr, long long gw, long long gh) {
    SpecFont* f = _spec_get_font(handle);
    if (!f || !dst_ptr || pixel_height <= 0 || gw <= 0 || gh <= 0) return 0;
    float s = stbtt_ScaleForPixelHeight(&f->info, (float)pixel_height);
    stbtt_MakeCodepointBitmapSubpixel(&f->info, (unsigned char*)(intptr_t)dst_ptr, (int)gw, (int)gh, (int)gw, s, s, (float)shift_x, 0.0f, (int)cp);
    return 1;
}

long long spec_pal_font_has_glyph(long long handle, long long cp) {
    SpecFont* f = _spec_get_font(handle);
    if (!f) return 0;
    return stbtt_FindGlyphIndex(&f->info, (int)cp) != 0 ? 1 : 0;
}

#if defined(__linux__)
long long spec_pal_font_default_path(long long out_buf, long long out_cap) {
    if (!out_buf || out_cap <= 1) return 0;
    void* fc = dlopen("libfontconfig.so.1", RTLD_LAZY | RTLD_LOCAL);
    if (!fc) return 0;
    typedef int (*PFN_FcInit)(void);
    typedef void* (*PFN_FcNameParse)(const unsigned char*);
    typedef int (*PFN_FcConfigSubstitute)(void*, void*, int);
    typedef void (*PFN_FcDefaultSubstitute)(void*);
    typedef void* (*PFN_FcFontMatch)(void*, void*, int*);
    typedef int (*PFN_FcPatternGetString)(const void*, const char*, int, unsigned char**);
    typedef void (*PFN_FcPatternDestroy)(void*);

    PFN_FcInit pFcInit = (PFN_FcInit)dlsym(fc, "FcInit");
    PFN_FcNameParse pFcNameParse = (PFN_FcNameParse)dlsym(fc, "FcNameParse");
    PFN_FcConfigSubstitute pFcConfigSubstitute = (PFN_FcConfigSubstitute)dlsym(fc, "FcConfigSubstitute");
    PFN_FcDefaultSubstitute pFcDefaultSubstitute = (PFN_FcDefaultSubstitute)dlsym(fc, "FcDefaultSubstitute");
    PFN_FcFontMatch pFcFontMatch = (PFN_FcFontMatch)dlsym(fc, "FcFontMatch");
    PFN_FcPatternGetString pFcPatternGetString = (PFN_FcPatternGetString)dlsym(fc, "FcPatternGetString");
    PFN_FcPatternDestroy pFcPatternDestroy = (PFN_FcPatternDestroy)dlsym(fc, "FcPatternDestroy");
    if (!pFcInit || !pFcNameParse || !pFcConfigSubstitute || !pFcDefaultSubstitute ||
        !pFcFontMatch || !pFcPatternGetString || !pFcPatternDestroy) {
        dlclose(fc);
        return 0;
    }

    pFcInit();
    void* pat = pFcNameParse((const unsigned char*)"sans");
    if (!pat) { dlclose(fc); return 0; }
    pFcConfigSubstitute(NULL, pat, 0);
    pFcDefaultSubstitute(pat);
    int res = 0;
    void* match = pFcFontMatch(NULL, pat, &res);
    pFcPatternDestroy(pat);
    if (!match) { dlclose(fc); return 0; }

    unsigned char* file = NULL;
    long long written = 0;
    if (pFcPatternGetString(match, "file", 0, &file) == 0 && file) {
        size_t len = strlen((const char*)file);
        if (len > (size_t)(out_cap - 1)) len = (size_t)(out_cap - 1);
        memcpy((char*)(intptr_t)out_buf, file, len);
        ((char*)(intptr_t)out_buf)[len] = '\0';
        written = (long long)len;
    }
    pFcPatternDestroy(match);
    dlclose(fc);
    return written;
}

long long spec_pal_font_find_path(long long mono, long long bold, long long italic, long long out_buf, long long out_cap) {
    (void)mono; (void)bold; (void)italic; (void)out_buf; (void)out_cap;
    return 0;
}
#elif defined(_WIN32)
typedef struct {
    char path[MAX_PATH * 2];
    bool is_mono;
    bool is_bold;
    bool is_italic;
    int score;
} SpecWinFontEntry;

static SpecWinFontEntry* _spec_win_font_cache = NULL;
static int _spec_win_font_count = 0;
static bool _spec_win_font_scanned = false;

static uint16_t _spec_be16(const unsigned char* p) {
    return (uint16_t)(((uint16_t)p[0] << 8) | (uint16_t)p[1]);
}

static uint32_t _spec_be32(const unsigned char* p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static bool _spec_win_inspect_ttf(const char* path, bool* out_mono, bool* out_bold, bool* out_italic, int* out_score) {
    FILE* fp = fopen(path, "rb");
    if (!fp) return false;
    unsigned char hdr[12];
    if (fread(hdr, 1, 12, fp) != 12) { fclose(fp); return false; }
    uint32_t ver = _spec_be32(hdr);
    if (ver != 0x00010000U && ver != 0x4F54544FU /* OTTO */) { fclose(fp); return false; }
    uint16_t num_tables = _spec_be16(hdr + 4);
    if (num_tables == 0 || num_tables > 64) { fclose(fp); return false; }

    unsigned char tbls[64 * 16];
    if (fread(tbls, 16, num_tables, fp) != num_tables) { fclose(fp); return false; }

    uint32_t off_os2 = 0, len_os2 = 0;
    uint32_t off_post = 0, len_post = 0;
    uint32_t off_head = 0, len_head = 0;
    bool has_cmap = false;

    for (uint16_t i = 0; i < num_tables; i++) {
        const unsigned char* r = tbls + i * 16;
        uint32_t tag = _spec_be32(r);
        uint32_t off = _spec_be32(r + 8);
        uint32_t len = _spec_be32(r + 12);
        if (tag == 0x4F532F32U /* OS/2 */) { off_os2 = off; len_os2 = len; }
        else if (tag == 0x706F7374U /* post */) { off_post = off; len_post = len; }
        else if (tag == 0x68656164U /* head */) { off_head = off; len_head = len; }
        else if (tag == 0x636D6170U /* cmap */) { has_cmap = true; }
    }
    if (!has_cmap || off_os2 == 0 || len_os2 < 68) { fclose(fp); return false; }

    unsigned char os2[68];
    if (fseek(fp, (long)off_os2, SEEK_SET) != 0 || fread(os2, 1, 68, fp) != 68) { fclose(fp); return false; }

    uint16_t weight = _spec_be16(os2 + 4);
    uint16_t width_cls = _spec_be16(os2 + 6);
    unsigned char panose0 = os2[32];
    unsigned char panose1 = os2[33];
    unsigned char panose3 = os2[35];
    uint32_t ur1 = _spec_be32(os2 + 42);
    uint16_t fs_sel = _spec_be16(os2 + 62);

    if (panose0 == 5 || !(ur1 & 1U)) { fclose(fp); return false; }

    uint32_t fixed_pitch = 0;
    if (off_post != 0 && len_post >= 16) {
        unsigned char post[16];
        if (fseek(fp, (long)off_post, SEEK_SET) == 0 && fread(post, 1, 16, fp) == 16) {
            fixed_pitch = _spec_be32(post + 12);
        }
    }

    uint16_t mac_style = 0;
    if (off_head != 0 && len_head >= 48) {
        unsigned char head[48];
        if (fseek(fp, (long)off_head, SEEK_SET) == 0 && fread(head, 1, 48, fp) == 48) {
            mac_style = _spec_be16(head + 44);
        }
    }
    fclose(fp);

    bool is_mono = (fixed_pitch != 0) || (panose3 == 9);
    bool is_bold = ((fs_sel & 0x20U) != 0) || ((mac_style & 0x01U) != 0) || (weight >= 600);
    bool is_italic = ((fs_sel & 0x01U) != 0) || ((mac_style & 0x02U) != 0);

    int score = 100;
    if (panose0 == 2) score += 50;
    else if (panose0 == 4) score -= 20;
    if (width_cls == 5) score += 30;
    if (weight == (is_bold ? 700 : 400)) score += 20;
    if (!is_mono && panose1 >= 11 && panose1 <= 15) score += 25;
    if (is_mono && fixed_pitch != 0 && panose3 == 9) score += 25;

    *out_mono = is_mono;
    *out_bold = is_bold;
    *out_italic = is_italic;
    *out_score = score;
    return true;
}

static void _spec_win_scan_fonts(void) {
    if (_spec_win_font_scanned) return;
    _spec_win_font_scanned = true;
    char win_dir[MAX_PATH];
    UINT wn = GetWindowsDirectoryA(win_dir, MAX_PATH);
    if (wn == 0 || wn >= MAX_PATH) return;

    char pattern[MAX_PATH * 2];
    snprintf(pattern, sizeof(pattern), "%s\\Fonts\\*.ttf", win_dir);
    WIN32_FIND_DATAA fd;
    HANDLE hFind = FindFirstFileA(pattern, &fd);
    if (hFind == INVALID_HANDLE_VALUE) return;

    int cap = 128;
    _spec_win_font_cache = (SpecWinFontEntry*)malloc((size_t)cap * sizeof(SpecWinFontEntry));
    if (!_spec_win_font_cache) { FindClose(hFind); return; }

    do {
        if (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) continue;
        char full[MAX_PATH * 2];
        snprintf(full, sizeof(full), "%s\\Fonts\\%s", win_dir, fd.cFileName);
        bool mono = false, bold = false, italic = false;
        int score = 0;
        if (_spec_win_inspect_ttf(full, &mono, &bold, &italic, &score)) {
            if (_spec_win_font_count >= cap) {
                int new_cap = cap * 2;
                SpecWinFontEntry* next = (SpecWinFontEntry*)realloc(_spec_win_font_cache, (size_t)new_cap * sizeof(SpecWinFontEntry));
                if (!next) break;
                _spec_win_font_cache = next;
                cap = new_cap;
            }
            SpecWinFontEntry* e = &_spec_win_font_cache[_spec_win_font_count++];
            snprintf(e->path, sizeof(e->path), "%s", full);
            e->is_mono = mono;
            e->is_bold = bold;
            e->is_italic = italic;
            e->score = score;
        }
    } while (FindNextFileA(hFind, &fd));
    FindClose(hFind);
}

long long spec_pal_font_find_path(long long mono, long long bold, long long italic, long long out_buf, long long out_cap) {
    if (!out_buf || out_cap <= 1) return 0;
    _spec_win_scan_fonts();
    if (!_spec_win_font_cache || _spec_win_font_count == 0) return 0;
    bool want_mono = mono != 0;
    bool want_bold = bold != 0;
    bool want_italic = italic != 0;
    const SpecWinFontEntry* best = NULL;
    int best_rank = -100000;
    for (int i = 0; i < _spec_win_font_count; i++) {
        const SpecWinFontEntry* e = &_spec_win_font_cache[i];
        if (e->is_mono != want_mono) continue;
        int rank = e->score;
        if (e->is_bold == want_bold) rank += 200;
        if (e->is_italic == want_italic) rank += 200;
        if (rank > best_rank) {
            best_rank = rank;
            best = e;
        }
    }
    if (!best) return 0;
    size_t len = strlen(best->path);
    if (len > (size_t)(out_cap - 1)) len = (size_t)(out_cap - 1);
    memcpy((char*)(intptr_t)out_buf, best->path, len);
    ((char*)(intptr_t)out_buf)[len] = '\0';
    return (long long)len;
}

long long spec_pal_font_default_path(long long out_buf, long long out_cap) {
    return spec_pal_font_find_path(0, 0, 0, out_buf, out_cap);
}
#else
long long spec_pal_font_find_path(long long mono, long long bold, long long italic, long long out_buf, long long out_cap) {
    (void)mono; (void)bold; (void)italic; (void)out_buf; (void)out_cap;
    return 0;
}
long long spec_pal_font_default_path(long long out_buf, long long out_cap) {
    (void)out_buf; (void)out_cap;
    return 0;
}
#endif

#else

long long spec_pal_font_init_memory(long long data_ptr, long long data_len) {
    (void)data_ptr; (void)data_len;
    _spec_set_font_error("stb_truetype.h not available at compile time");
    return -1;
}
long long spec_pal_font_close(long long handle) { (void)handle; return 0; }
double spec_pal_font_scale(long long handle, long long pixel_height) { (void)handle; (void)pixel_height; return 0.0; }
long long spec_pal_font_vmetrics(long long handle, long long out_3_i32_ptr) { (void)handle; (void)out_3_i32_ptr; return 0; }
long long spec_pal_font_hmetrics(long long handle, long long cp, long long out_2_i32_ptr) { (void)handle; (void)cp; (void)out_2_i32_ptr; return 0; }
long long spec_pal_font_kern_advance(long long handle, long long cp1, long long cp2) { (void)handle; (void)cp1; (void)cp2; return 0; }
long long spec_pal_font_glyph_box(long long handle, long long cp, long long pixel_height, long long out_4_i32_ptr) { (void)handle; (void)cp; (void)pixel_height; (void)out_4_i32_ptr; return 0; }
long long spec_pal_font_rasterize_glyph(long long handle, long long cp, long long pixel_height, long long dst_ptr, long long gw, long long gh) { (void)handle; (void)cp; (void)pixel_height; (void)dst_ptr; (void)gw; (void)gh; return 0; }
long long spec_pal_font_glyph_box_subpixel(long long handle, long long cp, long long pixel_height, double shift_x, long long out_4_i32_ptr) { (void)handle; (void)cp; (void)pixel_height; (void)shift_x; (void)out_4_i32_ptr; return 0; }
long long spec_pal_font_rasterize_glyph_subpixel(long long handle, long long cp, long long pixel_height, double shift_x, long long dst_ptr, long long gw, long long gh) { (void)handle; (void)cp; (void)pixel_height; (void)shift_x; (void)dst_ptr; (void)gw; (void)gh; return 0; }
long long spec_pal_font_has_glyph(long long handle, long long cp) { (void)handle; (void)cp; return 0; }
long long spec_pal_font_default_path(long long out_buf, long long out_cap) { (void)out_buf; (void)out_cap; return 0; }
long long spec_pal_font_find_path(long long mono, long long bold, long long italic, long long out_buf, long long out_cap) { (void)mono; (void)bold; (void)italic; (void)out_buf; (void)out_cap; return 0; }

#endif
