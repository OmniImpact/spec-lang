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

long long spec_pal_font_default_path(long long out_buf, long long out_cap) {
#if defined(__linux__)
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
#else
    (void)out_buf; (void)out_cap;
    return 0;
#endif
}

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
long long spec_pal_font_default_path(long long out_buf, long long out_cap) { (void)out_buf; (void)out_cap; return 0; }

#endif
