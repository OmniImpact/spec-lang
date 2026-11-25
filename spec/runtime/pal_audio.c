static __thread const char* _spec_last_audio_err = "";

long long spec_pal_audio_last_error(void) {
    return (long long)(intptr_t)(_spec_last_audio_err ? _spec_last_audio_err : "Audio error");
}

#if defined(_WIN32)
typedef struct SpecAudioStream {
    bool active;
    long long sample_rate;
    long long channels;
    long long format;
    HWAVEOUT h_wave_out;
} SpecAudioStream;

static SpecAudioStream _spec_audio_streams[8] = {0};

typedef MMRESULT (WINAPI *spec_pfn_waveOutOpen)(LPHWAVEOUT, UINT, LPCWAVEFORMATEX, DWORD_PTR, DWORD_PTR, DWORD);
typedef MMRESULT (WINAPI *spec_pfn_waveOutWrite)(HWAVEOUT, LPWAVEHDR, UINT);
typedef MMRESULT (WINAPI *spec_pfn_waveOutPrepareHeader)(HWAVEOUT, LPWAVEHDR, UINT);
typedef MMRESULT (WINAPI *spec_pfn_waveOutReset)(HWAVEOUT);
typedef MMRESULT (WINAPI *spec_pfn_waveOutClose)(HWAVEOUT);

static HMODULE _spec_winmm_lib = NULL;
static spec_pfn_waveOutOpen _spec_waveOutOpen = NULL;
static spec_pfn_waveOutWrite _spec_waveOutWrite = NULL;
static spec_pfn_waveOutPrepareHeader _spec_waveOutPrepareHeader = NULL;
static spec_pfn_waveOutReset _spec_waveOutReset = NULL;
static spec_pfn_waveOutClose _spec_waveOutClose = NULL;

static bool _spec_init_winmm(void) {
    if (_spec_winmm_lib) return true;
    _spec_winmm_lib = LoadLibraryA("winmm.dll");
    if (!_spec_winmm_lib) return false;
    _spec_waveOutOpen = (spec_pfn_waveOutOpen)(void*)GetProcAddress(_spec_winmm_lib, "waveOutOpen");
    _spec_waveOutWrite = (spec_pfn_waveOutWrite)(void*)GetProcAddress(_spec_winmm_lib, "waveOutWrite");
    _spec_waveOutPrepareHeader = (spec_pfn_waveOutPrepareHeader)(void*)GetProcAddress(_spec_winmm_lib, "waveOutPrepareHeader");
    _spec_waveOutReset = (spec_pfn_waveOutReset)(void*)GetProcAddress(_spec_winmm_lib, "waveOutReset");
    _spec_waveOutClose = (spec_pfn_waveOutClose)(void*)GetProcAddress(_spec_winmm_lib, "waveOutClose");
    return _spec_waveOutOpen && _spec_waveOutWrite && _spec_waveOutPrepareHeader;
}

long long spec_pal_audio_open(long long sample_rate, long long channels, long long format) {
    if (sample_rate <= 0) sample_rate = 44100;
    if (channels <= 0) channels = 2;
    if (format <= 0) format = 1;
    int slot = -1;
    for (int i = 0; i < 8; i++) {
        if (!_spec_audio_streams[i].active) { slot = i; break; }
    }
    if (slot < 0) {
        _spec_last_audio_err = "Audio error: Maximum concurrent audio streams reached";
        return -1;
    }
    if (!_spec_init_winmm()) {
        _spec_last_audio_err = "Audio error: Failed to initialize WinMM";
        return -1;
    }
    WAVEFORMATEX wfx;
    memset(&wfx, 0, sizeof(wfx));
    wfx.wFormatTag = WAVE_FORMAT_PCM;
    wfx.nChannels = (WORD)channels;
    wfx.nSamplesPerSec = (DWORD)sample_rate;
    wfx.wBitsPerSample = 16;
    wfx.nBlockAlign = (WORD)(channels * 2);
    wfx.nAvgBytesPerSec = (DWORD)(sample_rate * wfx.nBlockAlign);
    HWAVEOUT hWave = NULL;
    if (_spec_waveOutOpen(&hWave, WAVE_MAPPER, &wfx, 0, 0, CALLBACK_NULL) != MMSYSERR_NOERROR) {
        _spec_last_audio_err = "Audio error: waveOutOpen failed";
        return -1;
    }
    _spec_audio_streams[slot].h_wave_out = hWave;
    _spec_audio_streams[slot].active = true;
    _spec_audio_streams[slot].sample_rate = sample_rate;
    _spec_audio_streams[slot].channels = channels;
    _spec_audio_streams[slot].format = format;
    return (long long)(slot + 1);
}

long long spec_pal_audio_write(long long handle, long long data_addr, long long len_ll) {
    long long idx = handle - 1;
    if (idx < 0 || idx >= 8 || !_spec_audio_streams[idx].active) {
        _spec_last_audio_err = "Audio error: Audio stream is closed or invalid";
        return -1;
    }
    if (!data_addr || len_ll <= 0) return 0;
    const void* data_ptr = (const void*)(intptr_t)data_addr;
    size_t len = (size_t)len_ll;
    HWAVEOUT hWave = _spec_audio_streams[idx].h_wave_out;
    WAVEHDR* hdr = (WAVEHDR*)spec_xmalloc(sizeof(WAVEHDR));
    memset(hdr, 0, sizeof(WAVEHDR));
    hdr->lpData = (LPSTR)spec_xmalloc(len);
    memcpy(hdr->lpData, data_ptr, len);
    hdr->dwBufferLength = (DWORD)len;
    if (_spec_waveOutPrepareHeader) _spec_waveOutPrepareHeader(hWave, hdr, sizeof(WAVEHDR));
    if (_spec_waveOutWrite) _spec_waveOutWrite(hWave, hdr, sizeof(WAVEHDR));
    return (long long)len;
}

long long spec_audio_drain(long long handle) {
    long long idx = handle - 1;
    if (idx < 0 || idx >= 8 || !_spec_audio_streams[idx].active) return 0;
    Sleep(50);
    return 0;
}

void spec_audio_close(long long handle) {
    long long idx = handle - 1;
    if (idx < 0 || idx >= 8 || !_spec_audio_streams[idx].active) return;
    if (_spec_waveOutReset) _spec_waveOutReset(_spec_audio_streams[idx].h_wave_out);
    if (_spec_waveOutClose) _spec_waveOutClose(_spec_audio_streams[idx].h_wave_out);
    memset(&_spec_audio_streams[idx], 0, sizeof(SpecAudioStream));
}
#elif defined(__APPLE__) && defined(__MACH__)
typedef struct SpecAudioStream {
    bool active;
    long long sample_rate;
    long long channels;
    long long format;
    AudioQueueRef aq_queue;
} SpecAudioStream;

static SpecAudioStream _spec_audio_streams[8] = {0};

typedef OSStatus (*spec_pfn_AudioQueueNewOutput)(const AudioStreamBasicDescription*, AudioQueueOutputCallback, void*, CFRunLoopRef, CFStringRef, UInt32, AudioQueueRef*);
typedef OSStatus (*spec_pfn_AudioQueueStart)(AudioQueueRef, const AudioTimeStamp*);
typedef OSStatus (*spec_pfn_AudioQueueStop)(AudioQueueRef, Boolean);
typedef OSStatus (*spec_pfn_AudioQueueDispose)(AudioQueueRef, Boolean);
typedef OSStatus (*spec_pfn_AudioQueueAllocateBuffer)(AudioQueueRef, UInt32, AudioQueueBufferRef*);
typedef OSStatus (*spec_pfn_AudioQueueEnqueueBuffer)(AudioQueueRef, AudioQueueBufferRef, UInt32, const AudioStreamPacketDescription*);
typedef OSStatus (*spec_pfn_AudioQueueFreeBuffer)(AudioQueueRef, AudioQueueBufferRef);

static void* _spec_audiotoolbox_lib = NULL;
static spec_pfn_AudioQueueNewOutput _spec_AudioQueueNewOutput = NULL;
static spec_pfn_AudioQueueStart _spec_AudioQueueStart = NULL;
static spec_pfn_AudioQueueStop _spec_AudioQueueStop = NULL;
static spec_pfn_AudioQueueDispose _spec_AudioQueueDispose = NULL;
static spec_pfn_AudioQueueAllocateBuffer _spec_AudioQueueAllocateBuffer = NULL;
static spec_pfn_AudioQueueEnqueueBuffer _spec_AudioQueueEnqueueBuffer = NULL;
static spec_pfn_AudioQueueFreeBuffer _spec_AudioQueueFreeBuffer = NULL;

static bool _spec_init_audiotoolbox(void) {
    if (_spec_audiotoolbox_lib) return true;
    _spec_audiotoolbox_lib = dlopen("/System/Library/Frameworks/AudioToolbox.framework/AudioToolbox", RTLD_LAZY);
    if (!_spec_audiotoolbox_lib) return false;
    _spec_AudioQueueNewOutput = (spec_pfn_AudioQueueNewOutput)dlsym(_spec_audiotoolbox_lib, "AudioQueueNewOutput");
    _spec_AudioQueueStart = (spec_pfn_AudioQueueStart)dlsym(_spec_audiotoolbox_lib, "AudioQueueStart");
    _spec_AudioQueueStop = (spec_pfn_AudioQueueStop)dlsym(_spec_audiotoolbox_lib, "AudioQueueStop");
    _spec_AudioQueueDispose = (spec_pfn_AudioQueueDispose)dlsym(_spec_audiotoolbox_lib, "AudioQueueDispose");
    _spec_AudioQueueAllocateBuffer = (spec_pfn_AudioQueueAllocateBuffer)dlsym(_spec_audiotoolbox_lib, "AudioQueueAllocateBuffer");
    _spec_AudioQueueEnqueueBuffer = (spec_pfn_AudioQueueEnqueueBuffer)dlsym(_spec_audiotoolbox_lib, "AudioQueueEnqueueBuffer");
    _spec_AudioQueueFreeBuffer = (spec_pfn_AudioQueueFreeBuffer)dlsym(_spec_audiotoolbox_lib, "AudioQueueFreeBuffer");
    return _spec_AudioQueueNewOutput && _spec_AudioQueueStart && _spec_AudioQueueAllocateBuffer;
}

static void _spec_audio_queue_cb(void* custom_data, AudioQueueRef queue, AudioQueueBufferRef buffer) {
    (void)custom_data;
    if (_spec_AudioQueueFreeBuffer) _spec_AudioQueueFreeBuffer(queue, buffer);
}

long long spec_pal_audio_open(long long sample_rate, long long channels, long long format) {
    if (sample_rate <= 0) sample_rate = 44100;
    if (channels <= 0) channels = 2;
    if (format <= 0) format = 1;
    int slot = -1;
    for (int i = 0; i < 8; i++) {
        if (!_spec_audio_streams[i].active) { slot = i; break; }
    }
    if (slot < 0) {
        _spec_last_audio_err = "Audio error: Maximum concurrent audio streams reached";
        return -1;
    }
    if (!_spec_init_audiotoolbox()) {
        _spec_last_audio_err = "Audio error: Failed to initialize AudioToolbox";
        return -1;
    }
    AudioStreamBasicDescription desc;
    memset(&desc, 0, sizeof(desc));
    desc.mSampleRate = (Float64)sample_rate;
    desc.mFormatID = kAudioFormatLinearPCM;
    desc.mFormatFlags = kLinearPCMFormatFlagIsSignedInteger | kAudioFormatFlagIsPacked;
    desc.mBytesPerPacket = (UInt32)(channels * 2);
    desc.mFramesPerPacket = 1;
    desc.mBytesPerFrame = (UInt32)(channels * 2);
    desc.mChannelsPerFrame = (UInt32)channels;
    desc.mBitsPerChannel = 16;
    AudioQueueRef queue = NULL;
    if (_spec_AudioQueueNewOutput(&desc, _spec_audio_queue_cb, NULL, NULL, NULL, 0, &queue) != noErr) {
        _spec_last_audio_err = "Audio error: AudioQueueNewOutput failed";
        return -1;
    }
    _spec_AudioQueueStart(queue, NULL);
    _spec_audio_streams[slot].aq_queue = queue;
    _spec_audio_streams[slot].active = true;
    _spec_audio_streams[slot].sample_rate = sample_rate;
    _spec_audio_streams[slot].channels = channels;
    _spec_audio_streams[slot].format = format;
    return (long long)(slot + 1);
}

long long spec_pal_audio_write(long long handle, long long data_addr, long long len_ll) {
    long long idx = handle - 1;
    if (idx < 0 || idx >= 8 || !_spec_audio_streams[idx].active) {
        _spec_last_audio_err = "Audio error: Audio stream is closed or invalid";
        return -1;
    }
    if (!data_addr || len_ll <= 0) return 0;
    const void* data_ptr = (const void*)(intptr_t)data_addr;
    size_t len = (size_t)len_ll;
    AudioQueueRef queue = _spec_audio_streams[idx].aq_queue;
    AudioQueueBufferRef buffer = NULL;
    if (_spec_AudioQueueAllocateBuffer && _spec_AudioQueueAllocateBuffer(queue, (UInt32)len, &buffer) == noErr) {
        memcpy(buffer->mAudioData, data_ptr, len);
        buffer->mAudioDataByteSize = (UInt32)len;
        if (_spec_AudioQueueEnqueueBuffer) _spec_AudioQueueEnqueueBuffer(queue, buffer, 0, NULL);
        return (long long)len;
    }
    _spec_last_audio_err = "Audio error: Failed to allocate AudioToolbox buffer";
    return -1;
}

long long spec_audio_drain(long long handle) {
    long long idx = handle - 1;
    if (idx < 0 || idx >= 8 || !_spec_audio_streams[idx].active) return 0;
    if (_spec_AudioQueueStop) _spec_AudioQueueStop(_spec_audio_streams[idx].aq_queue, false);
    if (_spec_AudioQueueStart) _spec_AudioQueueStart(_spec_audio_streams[idx].aq_queue, NULL);
    return 0;
}

void spec_audio_close(long long handle) {
    long long idx = handle - 1;
    if (idx < 0 || idx >= 8 || !_spec_audio_streams[idx].active) return;
    if (_spec_AudioQueueDispose) _spec_AudioQueueDispose(_spec_audio_streams[idx].aq_queue, true);
    memset(&_spec_audio_streams[idx], 0, sizeof(SpecAudioStream));
}
#elif defined(__linux__)
typedef struct SpecAudioStream {
    bool active;
    long long sample_rate;
    long long channels;
    long long format;
    void* alsa_handle;
} SpecAudioStream;

static SpecAudioStream _spec_audio_streams[8] = {0};

typedef void* spec_snd_pcm_t;
typedef int (*spec_pfn_snd_pcm_open)(spec_snd_pcm_t**, const char*, int, int);
typedef int (*spec_pfn_snd_pcm_set_params)(spec_snd_pcm_t*, int, int, unsigned int, unsigned int, int, unsigned int);
typedef long (*spec_pfn_snd_pcm_writei)(spec_snd_pcm_t*, const void*, unsigned long);
typedef int (*spec_pfn_snd_pcm_drain)(spec_snd_pcm_t*);
typedef int (*spec_pfn_snd_pcm_close)(spec_snd_pcm_t*);
typedef int (*spec_pfn_snd_pcm_recover)(spec_snd_pcm_t*, int, int);

static void* _spec_alsa_lib = NULL;
static spec_pfn_snd_pcm_open _spec_snd_pcm_open = NULL;
static spec_pfn_snd_pcm_set_params _spec_snd_pcm_set_params = NULL;
static spec_pfn_snd_pcm_writei _spec_snd_pcm_writei = NULL;
static spec_pfn_snd_pcm_drain _spec_snd_pcm_drain = NULL;
static spec_pfn_snd_pcm_close _spec_snd_pcm_close = NULL;
static spec_pfn_snd_pcm_recover _spec_snd_pcm_recover = NULL;

static bool _spec_init_alsa(void) {
    if (_spec_alsa_lib) return true;
    _spec_alsa_lib = dlopen("libasound.so.2", RTLD_LAZY);
    if (!_spec_alsa_lib) _spec_alsa_lib = dlopen("libasound.so", RTLD_LAZY);
    if (!_spec_alsa_lib) {
        fprintf(stderr, "[Spec Audio] ALSA library (libasound.so.2) not found.\n"
                        "Please install the ALSA development package:\n"
                        "  Debian/Ubuntu: sudo apt-get install libasound2-dev\n"
                        "  Fedora/RHEL:   sudo dnf install alsa-lib-devel\n"
                        "  Arch:          sudo pacman -S alsa-lib\n");
        return false;
    }
    _spec_snd_pcm_open = (spec_pfn_snd_pcm_open)dlsym(_spec_alsa_lib, "snd_pcm_open");
    _spec_snd_pcm_set_params = (spec_pfn_snd_pcm_set_params)dlsym(_spec_alsa_lib, "snd_pcm_set_params");
    _spec_snd_pcm_writei = (spec_pfn_snd_pcm_writei)dlsym(_spec_alsa_lib, "snd_pcm_writei");
    _spec_snd_pcm_drain = (spec_pfn_snd_pcm_drain)dlsym(_spec_alsa_lib, "snd_pcm_drain");
    _spec_snd_pcm_close = (spec_pfn_snd_pcm_close)dlsym(_spec_alsa_lib, "snd_pcm_close");
    _spec_snd_pcm_recover = (spec_pfn_snd_pcm_recover)dlsym(_spec_alsa_lib, "snd_pcm_recover");
    return _spec_snd_pcm_open && _spec_snd_pcm_set_params && _spec_snd_pcm_writei;
}

long long spec_pal_audio_open(long long sample_rate, long long channels, long long format) {
    if (sample_rate <= 0) sample_rate = 44100;
    if (channels <= 0) channels = 2;
    if (format <= 0) format = 1;
    int slot = -1;
    for (int i = 0; i < 8; i++) {
        if (!_spec_audio_streams[i].active) { slot = i; break; }
    }
    if (slot < 0) {
        _spec_last_audio_err = "Audio error: Maximum concurrent audio streams reached";
        return -1;
    }
    if (!_spec_init_alsa()) {
        _spec_last_audio_err = "Audio error: Failed to initialize ALSA";
        return -1;
    }
    spec_snd_pcm_t* pcm = NULL;
    if (_spec_snd_pcm_open(&pcm, "default", 0, 0) != 0) {
        _spec_last_audio_err = "Audio error: Failed to open ALSA PCM device";
        return -1;
    }
    if (_spec_snd_pcm_set_params(pcm, 2, 3, (unsigned int)channels, (unsigned int)sample_rate, 1, 30000) != 0) {
        if (_spec_snd_pcm_close) _spec_snd_pcm_close(pcm);
        _spec_last_audio_err = "Audio error: Failed to configure ALSA PCM parameters";
        return -1;
    }
    _spec_audio_streams[slot].alsa_handle = pcm;
    _spec_audio_streams[slot].active = true;
    _spec_audio_streams[slot].sample_rate = sample_rate;
    _spec_audio_streams[slot].channels = channels;
    _spec_audio_streams[slot].format = format;
    return (long long)(slot + 1);
}

long long spec_pal_audio_write(long long handle, long long data_addr, long long len_ll) {
    long long idx = handle - 1;
    if (idx < 0 || idx >= 8 || !_spec_audio_streams[idx].active) {
        _spec_last_audio_err = "Audio error: Audio stream is closed or invalid";
        return -1;
    }
    if (!data_addr || len_ll <= 0) return 0;
    if (!_spec_snd_pcm_writei) {
        _spec_last_audio_err = "Audio error: ALSA write function unavailable";
        return -1;
    }
    const void* data_ptr = (const void*)(intptr_t)data_addr;
    size_t len = (size_t)len_ll;
    long long bytes_per_frame = _spec_audio_streams[idx].channels * 2;
    unsigned long frames = (unsigned long)(len / (size_t)bytes_per_frame);
    long res = _spec_snd_pcm_writei((spec_snd_pcm_t*)_spec_audio_streams[idx].alsa_handle, data_ptr, frames);
    if (res < 0) {
        if (_spec_snd_pcm_recover) res = _spec_snd_pcm_recover((spec_snd_pcm_t*)_spec_audio_streams[idx].alsa_handle, (int)res, 0);
        if (res == 0) res = _spec_snd_pcm_writei((spec_snd_pcm_t*)_spec_audio_streams[idx].alsa_handle, data_ptr, frames);
    }
    if (res < 0) {
        _spec_last_audio_err = "Audio error: Failed to write ALSA audio samples";
        return res;
    }
    return (long long)(res * bytes_per_frame);
}

long long spec_audio_drain(long long handle) {
    long long idx = handle - 1;
    if (idx < 0 || idx >= 8 || !_spec_audio_streams[idx].active) return 0;
    if (_spec_snd_pcm_drain) _spec_snd_pcm_drain((spec_snd_pcm_t*)_spec_audio_streams[idx].alsa_handle);
    return 0;
}

void spec_audio_close(long long handle) {
    long long idx = handle - 1;
    if (idx < 0 || idx >= 8 || !_spec_audio_streams[idx].active) return;
    if (_spec_snd_pcm_close) _spec_snd_pcm_close((spec_snd_pcm_t*)_spec_audio_streams[idx].alsa_handle);
    memset(&_spec_audio_streams[idx], 0, sizeof(SpecAudioStream));
}
#endif
