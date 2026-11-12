# =============================================================================
# GDB pretty-printers and helpers for Spec debug builds.
#
# Source this from gdb, then debug Spec programs at their own level:
#
#   (gdb) source utilities/spec-gdb.py
#   (gdb) print myString     -> "Hello, Spec!"        (SpecBuf rendered as text)
#   (gdb) print myArray      -> [1, 2, 3]  ["a", "b"] (elements sniffed + rendered)
#   (gdb) print myMap        -> {"k": "v", ...}       (key/value pairs)
#   (gdb) print myFn         -> <closure _anon_fn_7>
#   (gdb) speclocals         -> Spec-named locals only: the _spec_*/_ev_*/_it_*/
#                               _mret_*/_env*/_br_* runtime internals stay hidden
#
# Pair with bin/spec --debug builds (see README "Debugging").
#
# Layouts read here are the runtime's own (RuntimePrelude.spec):
#   SpecBuf      { void* data; size_t length; size_t capacity; size_t elem_size; int elem_kind; }
#   SpecArray    { void** items; size_t length; size_t capacity; int elem_kind; bool frozen; mutex }
#   SpecMapEntry { char* key; void* value; bool is_str; SpecMapEntry* next; }
#   SpecMap      { SpecMapEntry** buckets; size_t nbuckets; size_t length; ... }
#   SpecClosure  { void* fn; void* env; void (*destroy_env)(void*); }
#
# Untyped array/map elements sniff as String vs class instance via the
# object's second machine word: a String's SpecBuf.length is a small
# integer there, while a class instance's _vtable pointer is not. Map
# values need no sniff — SpecMapEntry.is_str already knows.
# =============================================================================
import gdb

_PRINT_LIMIT = 64
_STR_PREVIEW = 96
_IDENT_OK = None


def _ident_re():
    global _IDENT_OK
    if _IDENT_OK is None:
        import re
        _IDENT_OK = re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,63}\Z')
    return _IDENT_OK


def _inf():
    return gdb.selected_inferior()


def _read(addr, size):
    if addr == 0 or size <= 0:
        return b''
    return bytes(_inf().read_memory(addr, size))


def _read_u64(addr):
    try:
        return int.from_bytes(_read(addr, 8), 'little')
    except gdb.MemoryError:
        return None


def _read_cstring(addr, maxlen=_STR_PREVIEW):
    if addr == 0:
        return ''
    try:
        raw = _read(addr, maxlen + 1)
    except gdb.MemoryError:
        return None
    nul = raw.find(b'\x00')
    if nul < 0:
        if len(raw) <= maxlen:
            return None  # not a terminated string
        raw = raw[:maxlen]
        nul = maxlen
    try:
        return raw[:nul].decode('utf-8', 'backslashreplace')
    except Exception:
        return None


def _buf_type_ptr():
    try:
        return gdb.lookup_type('SpecBuf').pointer()
    except gdb.error:
        return None


def render_spec_string(ptr):
    """Render a SpecBuf* (String or Byte buffer) as text."""
    if ptr == 0:
        return 'null'
    bt = _buf_type_ptr()
    if bt is None:
        return hex(ptr)
    try:
        b = gdb.Value(ptr).cast(bt).dereference()
        length = int(b['length'])
        data = int(b['data'])
        raw = _read(data, min(length, 512))
        text = raw.decode('utf-8', 'backslashreplace')
        if length > _STR_PREVIEW:
            text = text[:_STR_PREVIEW] + '... (%d bytes)' % length
        return '"%s"' % text
    except (gdb.MemoryError, gdb.error, ValueError):
        return hex(ptr)


def _closure_fn_name(fn_addr):
    try:
        sal = gdb.find_pc_line(fn_addr)
        if sal is not None and sal.symtab is not None:
            return None  # fall through to address form
    except Exception:
        pass
    return None


def render_element(v):
    """Render one untyped SpecArray/SpecMap element: sniff String vs instance."""
    addr = int(v) & 0xFFFFFFFFFFFFFFFF
    if addr == 0:
        return 'null'
    second = _read_u64(addr + 8)
    if second is not None and second < (1 << 24):
        # A class instance's second word is its _vtable pointer (huge);
        # a String's second word is its byte length (small).
        return render_spec_string(addr)
    name_ptr = _read_u64(addr)
    if name_ptr:
        name = _read_cstring(name_ptr)
        if name is not None and _ident_re().fullmatch(name):
            return '<%s @ %s>' % (name, hex(addr))
    return hex(addr)


class SpecBufPrinter(object):
    def __init__(self, val):
        self.val = val

    def to_string(self):
        try:
            return render_spec_string(int(self.val))
        except Exception:
            return str(self.val)


class SpecArrayPrinter(object):
    def __init__(self, val):
        self.val = val

    def display_hint(self):
        return 'array'

    def to_string(self):
        try:
            n = int(self.val.dereference()['length'])
            return 'Array of %d element%s' % (n, '' if n == 1 else 's')
        except Exception:
            return 'Array'

    def children(self):
        try:
            a = self.val.dereference()
            length = int(a['length'])
            items = int(a['items'])
            elem_kind = int(a['elem_kind'])
            n = min(length, _PRINT_LIMIT)
            for i in range(n):
                if elem_kind == 0:  # SPEC_ELEM_NONE: numeric, pointer-sized
                    raw = _read(items + 8 * i, 8)
                    num = int.from_bytes(raw, 'little', signed=True)
                    yield '[%d]' % i, num
                else:
                    elem = _read_u64(items + 8 * i)
                    yield '[%d]' % i, render_element(elem)
            if length > _PRINT_LIMIT:
                yield '[...]', '(%d more)' % (length - _PRINT_LIMIT)
        except Exception as e:
            yield '<error>', str(e)


class SpecMapPrinter(object):
    def __init__(self, val):
        self.val = val

    def display_hint(self):
        return 'map'

    def to_string(self):
        try:
            n = int(self.val.dereference()['length'])
            return 'Map of %d entr%s' % (n, 'y' if n == 1 else 'ies')
        except Exception:
            return 'Map'

    def children(self):
        # gdb 17's map rendering pairs CONSECUTIVE children as (key, value):
        # child N's value becomes an entry's key, child N+1's its value.
        # Names are decorative; string values get quoted by gdb itself, so
        # yield raw text and let the formatter decide the spelling.
        try:
            m = self.val.dereference()
            nbuckets = int(m['nbuckets'])
            buckets = int(m['buckets'])
            val_kind = int(m['val_kind'])
            emitted = 0
            for bi in range(nbuckets):
                entry = _read_u64(buckets + 8 * bi)
                while entry and emitted < _PRINT_LIMIT:
                    key_ptr = _read_u64(entry)
                    key = _read_cstring(key_ptr, 512) or ''
                    val_ptr = _read_u64(entry + 8)
                    is_str = _read(entry + 16, 1) != b'\x00'
                    yield 'k%d' % emitted, gdb.Value(key)
                    if is_str:
                        # spec_map_set xstrdup's string values — plain char*.
                        text = _read_cstring(val_ptr, 512)
                        yield 'v%d' % emitted, gdb.Value(
                            text if text is not None else hex(val_ptr))
                    elif val_kind == 1:  # SPEC_ELEM_OBJECT: instance or String
                        yield 'v%d' % emitted, gdb.Value(render_element(val_ptr))
                    else:  # numeric: pointer-sized integer
                        raw = _read(val_ptr, 8)
                        yield 'v%d' % emitted, gdb.Value(
                            int.from_bytes(raw, 'little', signed=True))
                    emitted += 1
                    entry = _read_u64(entry + 24)
            # The summary already reports the true length; no truncation
            # marker — under the flat pairing contract a lone trailing
            # child would mis-pair.
        except Exception as e:
            yield '<error>', str(e)


class SpecClosurePrinter(object):
    def __init__(self, val):
        self.val = val

    def to_string(self):
        try:
            c = self.val.dereference()
            fn = int(c['fn'])
            env = int(c['env'])
            return '<closure fn=%s env=%s>' % (hex(fn), hex(env))
        except Exception:
            return '<closure>'


def _match_printer(val):
    try:
        # Debug-emission locals are volatile-qualified (and may pick up
        # const through casts) — normalize before matching.
        t = str(val.type.strip_typedefs())
        for qual in ('volatile ', 'const ', 'volatile', 'const'):
            t = t.replace(qual, '')
        t = t.strip()
    except Exception:
        return None
    if t in ('SpecBuf *', 'SpecBuf'):
        return SpecBufPrinter(val)
    if t in ('SpecArray *',):
        return SpecArrayPrinter(val)
    if t in ('SpecMap *',):
        return SpecMapPrinter(val)
    if t in ('SpecClosure *',):
        return SpecClosurePrinter(val)
    return None


def _spec_pretty_printer(val):
    try:
        return _match_printer(val)
    except Exception:
        return None


class SpecLocalsCommand(gdb.Command):
    """List Spec-named locals of the current frame.

    Hides the runtime's own machinery (_spec_pool_mark, _ev_N/_it_N inline
    loop cells, _mret_N yield accumulators, _env pointers) — only the names
    your Spec source declares are shown. Usage: speclocals
    """

    def __init__(self):
        super(SpecLocalsCommand, self).__init__('speclocals', gdb.COMMAND_DATA)

    def invoke(self, arg, from_tty):
        frame = gdb.selected_frame()
        try:
            block = frame.block()
        except Exception:
            print('no frame selected')
            return
        shown = 0
        seen = set()
        inner = block
        while block is not None:
            for sym in block:
                if sym.name in seen or sym.name.startswith('_'):
                    continue
                seen.add(sym.name)
                try:
                    val = sym.value(frame)
                except Exception:
                    continue
                printer = _spec_pretty_printer(val)
                if printer is not None:
                    text = str(printer.to_string())
                else:
                    text = str(val)
                    # A typed object pointer (self, fields) renders as its
                    # class identity instead of a bare address.
                    try:
                        if str(val.type).strip().endswith('*') and int(val) != 0:
                            text = render_element(val)
                    except Exception:
                        pass
                kind = 'arg' if sym.is_argument else 'local'
                print('%-12s %-28s = %s' % (kind, sym.name, text))
                shown += 1
            if block.function is not None:
                break  # stop at the function's top-level block
            block = block.superblock
        if shown == 0:
            print('(no Spec-named locals in scope)')


def _register():
    if getattr(gdb, '_spec_printers_registered', False):
        return
    gdb.pretty_printers.append(_spec_pretty_printer)
    SpecLocalsCommand()
    gdb._spec_printers_registered = True
    print('Spec debug helpers loaded: pretty-printers active, '
          'speclocals command available.')


_register()
