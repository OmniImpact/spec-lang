#! Package base:compiler:pal
#! Emits the file I/O C PAL (`spec_file_read*`, `spec_file_write*`, `spec_file_append`,
#! `spec_file_exists`, `spec_file_remove*`, `spec_file_temp*`).

Class is PalFile{
	namespace: ['base', 'compiler', 'pal'];

	replace Function is init(){
	}

	Function of String is emitHeader(){
		return '''typedef struct {
    String path;
    String content;
    String def;
    SpecClosure* on_success_read;
    SpecClosure* on_success_write;
    SpecClosure* on_error;
} SpecFileTask;

static void* spec_file_read_worker(void* arg) {
    SpecFileTask* task = (SpecFileTask*)arg;
    String res = spec_file_read(task->path, task->def, task->on_success_read, task->on_error);
    if (res) spec_release(res);
    if (task->path) spec_release(task->path);
    if (task->def) spec_release(task->def);
    if (task->on_success_read) spec_release(task->on_success_read);
    if (task->on_error) spec_release(task->on_error);
    free(task);
    spec_pool_thread_cleanup();
    spec_async_task_finished();
    return NULL;
}

static void* spec_file_write_worker(void* arg) {
    SpecFileTask* task = (SpecFileTask*)arg;
    spec_file_write(task->path, task->content, task->on_success_write, task->on_error);
    if (task->path) spec_release(task->path);
    if (task->content) spec_release(task->content);
    if (task->on_success_write) spec_release(task->on_success_write);
    if (task->on_error) spec_release(task->on_error);
    free(task);
    spec_pool_thread_cleanup();
    spec_async_task_finished();
    return NULL;
}
''';
	}

	Function of String is emitBody(){
		return '''String spec_file_read(String path, String def, SpecClosure* on_success, SpecClosure* on_error) {
    if (!path || path->length == 0) {
        if (on_error) spec_call_closure_str(on_error, spec_string_intern("File error: Empty or invalid file path provided"));
        return def ? def : spec_string_intern("");
    }
    const char* pc = spec_buf_to_cstring((SpecBuf*)path);
    FILE* f = fopen(pc, "rb");
    if (!f) {
        if (on_error) spec_call_closure_str(on_error, spec_string_from_bytes(strerror(errno), strlen(strerror(errno))));
        return def ? def : spec_string_intern("");
    }
    if (fseek(f, 0, SEEK_END) != 0) {
        fclose(f);
        if (on_error) spec_call_closure_str(on_error, spec_string_from_bytes(strerror(errno), strlen(strerror(errno))));
        return def ? def : spec_string_intern("");
    }
    long size = ftell(f);
    if (size < 0) {
        fclose(f);
        if (on_error) spec_call_closure_str(on_error, spec_string_from_bytes(strerror(errno), strlen(strerror(errno))));
        return def ? def : spec_string_intern("");
    }
    fseek(f, 0, SEEK_SET);
    char* buf = (char*)malloc((size_t)size + 1);
    if (!buf) {
        fclose(f);
        if (on_error) spec_call_closure_str(on_error, spec_string_intern("File error: Memory allocation failed during read"));
        return def ? def : spec_string_intern("");
    }
    size_t read_bytes = fread(buf, 1, size, f);
    fclose(f);
    String out = spec_string_from_bytes(buf, read_bytes);
    free(buf);
    if (on_success) spec_call_closure_str(on_success, out);
    return out;
}

bool spec_file_write(String path, String content, SpecClosure* on_success, SpecClosure* on_error) {
    if (!path || path->length == 0) {
        if (on_error) spec_call_closure_str(on_error, spec_string_intern("File error: Empty or invalid file path provided"));
        return false;
    }
    const char* pc = spec_buf_to_cstring((SpecBuf*)path);
#if defined(_WIN32)
    if (pc && (strncmp(pc, "/tmp/", 5) == 0 || strncmp(pc, "\\tmp\\", 5) == 0)) {
        CreateDirectoryA("/tmp", NULL);
    }
#endif
    size_t len = content ? ((SpecBuf*)content)->length : 0;
    const char* cc = len ? (const char*)((SpecBuf*)content)->data : "";
    FILE* f = fopen(pc, "wb");
    if (!f) {
        if (on_error) spec_call_closure_str(on_error, spec_string_from_bytes(strerror(errno), strlen(strerror(errno))));
        return false;
    }
    size_t written = fwrite(cc, 1, len, f);
    if (fclose(f) != 0) written = (size_t)-1;
    if (written != len) {
        if (on_error) spec_call_closure_str(on_error, spec_string_from_bytes(strerror(errno), strlen(strerror(errno))));
        return false;
    }
    if (on_success) spec_call_closure_int(on_success, (long long)written);
    return true;
}

bool spec_file_append(String path, String content, SpecClosure* on_success, SpecClosure* on_error) {
    if (!path || path->length == 0) {
        if (on_error) spec_call_closure_str(on_error, spec_string_intern("File error: Empty or invalid file path provided"));
        return false;
    }
    const char* pc = spec_buf_to_cstring((SpecBuf*)path);
#if defined(_WIN32)
    if (pc && (strncmp(pc, "/tmp/", 5) == 0 || strncmp(pc, "\\tmp\\", 5) == 0)) {
        CreateDirectoryA("/tmp", NULL);
    }
#endif
    size_t len = content ? ((SpecBuf*)content)->length : 0;
    if (len == 0) {
        if (on_success) spec_call_closure_int(on_success, 0);
        return true;
    }
    const char* cc = (const char*)((SpecBuf*)content)->data;
    FILE* f = fopen(pc, "ab");
    if (!f) {
        if (on_error) spec_call_closure_str(on_error, spec_string_from_bytes(strerror(errno), strlen(strerror(errno))));
        return false;
    }
    size_t written = fwrite(cc, 1, len, f);
    if (fclose(f) != 0) written = (size_t)-1;
    if (written != len) {
        if (on_error) spec_call_closure_str(on_error, spec_string_from_bytes(strerror(errno), strlen(strerror(errno))));
        return false;
    }
    if (on_success) spec_call_closure_int(on_success, (long long)written);
    return true;
}

void spec_file_read_async(String path, String def, SpecClosure* on_success, SpecClosure* on_error) {
    SpecFileTask* task = (SpecFileTask*)spec_xmalloc(sizeof(SpecFileTask));
    memset(task, 0, sizeof(SpecFileTask));
    task->path = path ? (String)spec_retain((void*)path) : NULL;
    task->def = def ? (String)spec_retain((void*)def) : NULL;
    task->on_success_read = (SpecClosure*)spec_retain(on_success);
    task->on_error = (SpecClosure*)spec_retain(on_error);
    spec_async_task_started();
    pthread_t tid;
    if (pthread_create(&tid, NULL, spec_file_read_worker, task) != 0) {
        spec_file_read_worker(task);
        return;
    }
    pthread_detach(tid);
}

void spec_file_write_async(String path, String content, SpecClosure* on_success, SpecClosure* on_error) {
    SpecFileTask* task = (SpecFileTask*)spec_xmalloc(sizeof(SpecFileTask));
    memset(task, 0, sizeof(SpecFileTask));
    task->path = path ? (String)spec_retain((void*)path) : NULL;
    task->content = content ? (String)spec_retain((void*)content) : NULL;
    task->on_success_write = (SpecClosure*)spec_retain(on_success);
    task->on_error = (SpecClosure*)spec_retain(on_error);
    spec_async_task_started();
    pthread_t tid;
    if (pthread_create(&tid, NULL, spec_file_write_worker, task) != 0) {
        spec_file_write_worker(task);
        return;
    }
    pthread_detach(tid);
}

bool spec_file_exists(String path) {
    if (!path) return false;
    FILE* f = fopen(spec_buf_to_cstring((SpecBuf*)path), "r");
    if (f) {
        fclose(f);
        return true;
    }
    return false;
}

bool spec_file_remove_cb(String path, SpecClosure* on_error) {
    if (!path || path->length == 0) {
        _spec_emit_str_error(on_error, "File error: Empty or invalid file path provided");
        return false;
    }
    if (remove(spec_buf_to_cstring((SpecBuf*)path)) != 0) {
        _spec_emit_str_error(on_error, strerror(errno));
        return false;
    }
    return true;
}

bool spec_file_remove(String path) {
    return spec_file_remove_cb(path, NULL);
}

String spec_file_temp_cb(String template, SpecClosure* on_error) {
#if defined(_WIN32)
    CreateDirectoryA("/tmp", NULL);
#endif
    if (!template || template->length == 0) template = spec_string_intern("/tmp/spec_XXXXXX");
    const char* tpl = spec_buf_to_cstring((SpecBuf*)template);
    size_t len = strlen(tpl);
    char* buf = (char*)spec_xmalloc(len + 32);
    strcpy(buf, tpl);
    char suffix[64];
    suffix[0] = '\0';
    char* xpos = strstr(buf, "XXXXXX");
    if (!xpos) {
        strcat(buf, "_XXXXXX");
    } else {
        if (strlen(xpos + 6) < sizeof(suffix)) {
            strcpy(suffix, xpos + 6);
        }
        xpos[6] = '\0';
    }
    int fd = mkstemp(buf);
#if defined(_WIN32)
    if (fd == -1 && (strncmp(tpl, "/tmp/", 5) == 0 || strcmp(tpl, "/tmp") == 0)) {
        char temp_dir[MAX_PATH];
        DWORD td_len = GetTempPathA(MAX_PATH, temp_dir);
        if (td_len > 0 && td_len < MAX_PATH) {
            const char* base = strrchr(tpl, '/');
            const char* b2 = strrchr(tpl, '\\');
            if (b2 && (!base || b2 > base)) base = b2;
            if (base) base++; else base = tpl;
            free(buf);
            buf = (char*)spec_xmalloc(strlen(temp_dir) + strlen(base) + 32);
            sprintf(buf, "%s%s", temp_dir, base);
            suffix[0] = '\0';
            xpos = strstr(buf, "XXXXXX");
            if (!xpos) {
                strcat(buf, "_XXXXXX");
            } else {
                if (strlen(xpos + 6) < sizeof(suffix)) {
                    strcpy(suffix, xpos + 6);
                }
                xpos[6] = '\0';
            }
            fd = mkstemp(buf);
        }
    }
#endif
    if (fd == -1) {
        int saved_errno = errno;
        free(buf);
        _spec_emit_str_error(on_error, strerror(saved_errno));
        return spec_string_intern("");
    }
    close(fd);
    if (suffix[0] != '\0') {
        size_t final_len = strlen(buf) + strlen(suffix) + 1;
        char* final_path = (char*)spec_xmalloc(final_len);
        sprintf(final_path, "%s%s", buf, suffix);
        if (rename(buf, final_path) != 0) {
            int saved_errno = errno;
            free(final_path);
            free(buf);
            _spec_emit_str_error(on_error, strerror(saved_errno));
            return spec_string_intern("");
        }
        String res = spec_string_from_chars(final_path);
        free(final_path);
        free(buf);
        return res;
    }
    String res = spec_string_from_chars(buf);
    free(buf);
    return res;
}

String spec_file_temp(String template) {
    return spec_file_temp_cb(template, NULL);
}
''';
	}
}
