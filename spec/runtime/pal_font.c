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
static long long _spec_default_font_handle = -1;

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

long long spec_pal_font_load(long long path_cstr) {
    if (!path_cstr) {
        _spec_set_font_error("Null font path");
        return -1;
    }
    const char* path = (const char*)(intptr_t)path_cstr;
    FILE* fp = fopen(path, "rb");
    if (!fp) {
        _spec_set_font_error("Failed to open font file");
        return -1;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        _spec_set_font_error("Failed to seek font file");
        return -1;
    }
    long sz = ftell(fp);
    if (sz <= 0) {
        fclose(fp);
        _spec_set_font_error("Empty font file");
        return -1;
    }
    rewind(fp);
    unsigned char* data = (unsigned char*)malloc((size_t)sz);
    if (!data) {
        fclose(fp);
        _spec_set_font_error("Out of memory reading font");
        return -1;
    }
    if (fread(data, 1, (size_t)sz, fp) != (size_t)sz) {
        free(data);
        fclose(fp);
        _spec_set_font_error("Failed to read font data");
        return -1;
    }
    fclose(fp);

    SpecFont* f = (SpecFont*)calloc(1, sizeof(SpecFont));
    if (!f) {
        free(data);
        _spec_set_font_error("Out of memory");
        return -1;
    }
    f->ttf_data = data;
    int offset = stbtt_GetFontOffsetForIndex(data, 0);
    if (!stbtt_InitFont(&f->info, data, offset)) {
        free(data);
        free(f);
        _spec_set_font_error("stbtt_InitFont failed");
        return -1;
    }
    long long h = _spec_alloc_font_slot(f);
    if (h <= 0) {
        free(data);
        free(f);
        _spec_set_font_error("Out of font slots");
        return -1;
    }
    return h;
}

long long spec_pal_font_close(long long handle) {
    if (handle <= 0 || handle == _spec_default_font_handle) return 0;
    size_t idx = (size_t)(handle - 1);
    if (idx >= _spec_fonts_cap || !_spec_fonts[idx]) return 0;
    SpecFont* f = _spec_fonts[idx];
    _spec_fonts[idx] = NULL;
    if (f->ttf_data) free(f->ttf_data);
    free(f);
    return 0;
}

static uint32_t _spec_utf8_next(const char** p) {
    const unsigned char* s = (const unsigned char*)(*p);
    if (!s || !*s) return 0;
    unsigned char c0 = s[0];
    if (c0 < 0x80) {
        *p += 1;
        return c0;
    } else if ((c0 & 0xE0) == 0xC0 && s[1]) {
        *p += 2;
        return ((uint32_t)(c0 & 0x1F) << 6) | (uint32_t)(s[1] & 0x3F);
    } else if ((c0 & 0xF0) == 0xE0 && s[1] && s[2]) {
        *p += 3;
        return ((uint32_t)(c0 & 0x0F) << 12) | ((uint32_t)(s[1] & 0x3F) << 6) | (uint32_t)(s[2] & 0x3F);
    } else if ((c0 & 0xF8) == 0xF0 && s[1] && s[2] && s[3]) {
        *p += 4;
        return ((uint32_t)(c0 & 0x07) << 18) | ((uint32_t)(s[1] & 0x3F) << 12) |
               ((uint32_t)(s[2] & 0x3F) << 6) | (uint32_t)(s[3] & 0x3F);
    }
    *p += 1;
    return c0;
}

long long spec_pal_font_draw_text(
    long long handle,
    long long pixels_addr,
    long long buf_w,
    long long buf_h,
    long long x,
    long long y,
    long long text_cstr,
    long long pixel_height,
    long long argb_color
) {
    SpecFont* f = _spec_get_font(handle);
    if (!f || !pixels_addr || buf_w <= 0 || buf_h <= 0 || !text_cstr || pixel_height <= 0) return 0;

    uint32_t* dst = (uint32_t*)(intptr_t)pixels_addr;
    const char* p = (const char*)(intptr_t)text_cstr;
    float scale = stbtt_ScaleForPixelHeight(&f->info, (float)pixel_height);

    int ascent = 0, descent = 0, line_gap = 0;
    stbtt_GetFontVMetrics(&f->info, &ascent, &descent, &line_gap);
    int baseline = (int)y + (int)roundf((float)ascent * scale);
    float xpos = (float)x;

    uint32_t fg_r = ((uint32_t)argb_color >> 16) & 0xFFu;
    uint32_t fg_g = ((uint32_t)argb_color >> 8) & 0xFFu;
    uint32_t fg_b = (uint32_t)argb_color & 0xFFu;
    uint32_t fg_a = ((uint32_t)argb_color >> 24) & 0xFFu;
    if (fg_a == 0) fg_a = 255u;

    size_t scratch_cap = 0;
    unsigned char* scratch = NULL;
    uint32_t prev_cp = 0;
    float tracking = (float)pixel_height * 0.045f;

    while (*p) {
        uint32_t cp = _spec_utf8_next(&p);
        if (cp == 0) break;
        if (cp == '\n') {
            xpos = (float)x;
            baseline += (int)roundf((float)(ascent - descent + line_gap) * scale);
            prev_cp = 0;
            continue;
        }
        if (prev_cp) {
            xpos += (float)stbtt_GetCodepointKernAdvance(&f->info, (int)prev_cp, (int)cp) * scale;
        }
        int adv = 0, lsb = 0;
        stbtt_GetCodepointHMetrics(&f->info, (int)cp, &adv, &lsb);

        int x0 = 0, y0 = 0, x1 = 0, y1 = 0;
        stbtt_GetCodepointBitmapBox(&f->info, (int)cp, scale, scale, &x0, &y0, &x1, &y1);
        int gw = x1 - x0;
        int gh = y1 - y0;
        if (gw > 0 && gh > 0) {
            size_t needed = (size_t)gw * (size_t)gh;
            if (needed > scratch_cap) {
                unsigned char* next = (unsigned char*)realloc(scratch, needed);
                if (next) {
                    scratch = next;
                    scratch_cap = needed;
                }
            }
            if (scratch && needed <= scratch_cap) {
                stbtt_MakeCodepointBitmap(&f->info, scratch, gw, gh, gw, scale, scale, (int)cp);
                int dst_x0 = (int)floorf(xpos) + x0;
                int dst_y0 = baseline + y0;
                for (int gy = 0; gy < gh; gy++) {
                    int py = dst_y0 + gy;
                    if (py < 0 || py >= (int)buf_h) continue;
                    uint32_t* row = dst + (size_t)py * (size_t)buf_w;
                    const unsigned char* g_row = scratch + (size_t)gy * (size_t)gw;
                    for (int gx = 0; gx < gw; gx++) {
                        int px = dst_x0 + gx;
                        if (px < 0 || px >= (int)buf_w) continue;
                        uint32_t cov = g_row[gx];
                        if (cov == 0) continue;
                        cov = cov + (cov * (255u - cov)) / 384u;
                        if (cov > 255u) cov = 255u;
                        uint32_t a = (cov * fg_a) / 255u;
                        uint32_t inv_a = 255u - a;
                        uint32_t bg = row[px];
                        uint32_t bg_a = (bg >> 24) & 0xFFu;
                        uint32_t bg_r = (bg >> 16) & 0xFFu;
                        uint32_t bg_g = (bg >> 8) & 0xFFu;
                        uint32_t bg_b = bg & 0xFFu;
                        uint32_t out_a = a + (bg_a * inv_a) / 255u;
                        uint32_t r = (fg_r * a + bg_r * inv_a) / 255u;
                        uint32_t g = (fg_g * a + bg_g * inv_a) / 255u;
                        uint32_t b = (fg_b * a + bg_b * inv_a) / 255u;
                        row[px] = (out_a << 24) | (r << 16) | (g << 8) | b;
                    }
                }
            }
        }
        xpos += (float)adv * scale + tracking;
        prev_cp = cp;
    }

    if (scratch) free(scratch);
    return 1;
}

long long spec_pal_font_measure_width(long long handle, long long text_cstr, long long pixel_height) {
    SpecFont* f = _spec_get_font(handle);
    if (!f || !text_cstr || pixel_height <= 0) return 0;
    float scale = stbtt_ScaleForPixelHeight(&f->info, (float)pixel_height);
    float tracking = (float)pixel_height * 0.045f;
    const char* p = (const char*)(intptr_t)text_cstr;
    float xpos = 0.0f;
    int prev_cp = 0;
    while (*p) {
        int cp = _spec_utf8_next(&p);
        if (prev_cp) {
            xpos += (float)stbtt_GetCodepointKernAdvance(&f->info, prev_cp, cp) * scale;
        }
        int adv = 0, lsb = 0;
        stbtt_GetCodepointHMetrics(&f->info, cp, &adv, &lsb);
        xpos += (float)adv * scale + tracking;
        prev_cp = cp;
    }
    return (long long)(xpos + 0.5f);
}

#if defined(__linux__)
static long long _spec_font_try_fontconfig(void) {
    void* fc = dlopen("libfontconfig.so.1", RTLD_LAZY | RTLD_LOCAL);
    if (!fc) return -1;
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
        return -1;
    }

    pFcInit();
    void* pat = pFcNameParse((const unsigned char*)"sans");
    if (!pat) { dlclose(fc); return -1; }
    pFcConfigSubstitute(NULL, pat, 0 /* FcMatchPattern */);
    pFcDefaultSubstitute(pat);
    int res = 0;
    void* match = pFcFontMatch(NULL, pat, &res);
    pFcPatternDestroy(pat);
    if (!match) { dlclose(fc); return -1; }

    unsigned char* file = NULL;
    long long h = -1;
    if (pFcPatternGetString(match, "file", 0, &file) == 0 && file) {
        h = spec_pal_font_load((long long)(intptr_t)file);
    }
    pFcPatternDestroy(match);
    dlclose(fc);
    return h;
}
#endif

long long spec_pal_font_load_default(void) {
#if defined(__linux__)
    if (_spec_default_font_handle > 0) return _spec_default_font_handle;
    long long h = _spec_font_try_fontconfig();
    if (h > 0) {
        _spec_default_font_handle = h;
        return h;
    }
    static const char* fallbacks[] = {
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
        NULL
    };
    for (int i = 0; fallbacks[i]; i++) {
        h = spec_pal_font_load((long long)(intptr_t)fallbacks[i]);
        if (h > 0) {
            _spec_default_font_handle = h;
            return h;
        }
    }
    _spec_set_font_error("No default system sans font found on Linux");
    return -1;
#elif defined(__APPLE__)
    /* TODO: Resolve default system sans font via CoreText (CTFontCreateUIFontForLanguage). */
    _spec_set_font_error("Default system font not yet implemented on macOS");
    return -1;
#elif defined(_WIN32)
    /* TODO: Resolve default system sans font via DirectWrite or SHGetFolderPath + segoeui.ttf. */
    _spec_set_font_error("Default system font not yet implemented on Windows");
    return -1;
#else
    _spec_set_font_error("Default system font not supported on this platform");
    return -1;
#endif
}

#else

long long spec_pal_font_load(long long path_cstr) {
    (void)path_cstr;
    _spec_set_font_error("stb_truetype.h not available at compile time");
    return -1;
}

long long spec_pal_font_close(long long handle) {
    (void)handle;
    return 0;
}

long long spec_pal_font_draw_text(
    long long handle,
    long long pixels_addr,
    long long buf_w,
    long long buf_h,
    long long x,
    long long y,
    long long text_cstr,
    long long pixel_height,
    long long argb_color
) {
    (void)handle; (void)pixels_addr; (void)buf_w; (void)buf_h;
    (void)x; (void)y; (void)text_cstr; (void)pixel_height; (void)argb_color;
    return 0;
}

long long spec_pal_font_measure_width(long long handle, long long text_cstr, long long pixel_height) {
    (void)handle; (void)text_cstr; (void)pixel_height;
    return 0;
}

long long spec_pal_font_load_default(void) {
    _spec_set_font_error("stb_truetype.h not available at compile time");
    return -1;
}

#endif
