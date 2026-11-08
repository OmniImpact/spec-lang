#!/usr/bin/env python3
"""FUNCTIONS.md Part II: migrate statement-form `if` to Conditional:branch.

A real scanner — string/comment aware (with backslash escapes), paren- and
brace-matched, line-anchored (statement ifs always start a line). Idempotent:
already-migrated files are left untouched. RuntimePrelude.spec (raw C) is
excluded by the caller.

Usage: migrate_if.py <file.spec> [more.spec ...]
       migrate_if.py --check <file.spec>   # report counts only
"""
import sys, re

USING_ENTRY = "['base', 'sys', as Conditional()]"

def scan_mask(s):
    """Per-char mask: 1 inside a string literal, 2 inside a comment."""
    n = len(s)
    mask = [0] * n
    i = 0
    instr = False
    quote = ''
    triple = False
    while i < n:
        c = s[i]
        if instr:
            mask[i] = 1
            if triple:
                # raw heredoc: the first closing triple ends it
                if s[i:i+3] == quote:
                    mask[i+1] = 1
                    mask[i+2] = 1
                    i += 3
                    instr = False
                    triple = False
                    continue
                i += 1
                continue
            if c == '\\' and i + 1 < n:
                mask[i + 1] = 1
                i += 2
                continue
            if c == quote:
                instr = False
            i += 1
            continue
        if s[i:i+3] == "'''":
            instr = True
            triple = True
            quote = "'''"
            mask[i] = 1
            mask[i+1] = 1
            mask[i+2] = 1
            i += 3
            continue
        if c == '`':
            # template string: raw to the matching backtick (holes were
            # expression-migrated already)
            j = i + 1
            while j < n and s[j] != '`':
                if s[j] == '\\' and j + 1 < n:
                    j += 1
                j += 1
            for k in range(i, min(j + 1, n)):
                mask[k] = 1
            i = j + 1
            continue
        if c in ('\'', '"'):
            instr = True
            quote = c
            mask[i] = 1
            i += 1
            continue
        if c == '#':
            while i < n and s[i] != '\n':
                mask[i] = 2
                i += 1
            continue
        i += 1
    return mask

def line_starts(s):
    """Indices where a line begins (only whitespace before on that line)."""
    starts = []
    bol = True
    for i, c in enumerate(s):
        if bol:
            starts.append(i)
            bol = False
        if c == '\n':
            bol = True
    return set(starts)

def is_line_start(s, starts, i):
    """True when only whitespace precedes i on its line."""
    j = s.rfind('\n', 0, i) + 1
    return s[j:i].strip() == ''

def match_delim(s, mask, open_idx, open_c, close_c):
    depth = 0
    i = open_idx
    while i < len(s):
        if mask[i] == 0:
            if s[i] == open_c:
                depth += 1
            elif s[i] == close_c:
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1

def skip_ws_comments(s, mask, i):
    while i < len(s):
        if mask[i] == 2:
            i += 1
            continue
        if mask[i] == 0 and s[i] in ' \t\r\n':
            i += 1
            continue
        return i
    return i

IF_RE = re.compile(r'\bif\b')

def find_if_statements(s, mask):
    """Spans (start, end) of statement-form if statements, outermost-first."""
    starts = line_starts(s)
    spans = []
    for m in IF_RE.finditer(s):
        i = m.start()
        if mask[i] != 0:
            continue
        # word boundary on the left
        if i > 0 and (s[i-1].isalnum() or s[i-1] in '_:'):
            continue
        # statement position: only whitespace since line start
        if not is_line_start(s, starts, i):
            continue
        # followed by optional ws then '('
        j = skip_ws_comments(s, mask, m.end())
        if j >= len(s) or s[j] != '(':
            continue
        # skip ones already inside a migrated wrapper: preceding non-ws on
        # the same span cannot happen (line-anchored) — fine.
        spans.append(i)
    return spans

def parse_if(s, mask, i):
    """Parse one if statement at keyword index i. Returns dict or None."""
    j = skip_ws_comments(s, mask, s.index('(', i))
    cond_open = j
    cond_close = match_delim(s, mask, cond_open, '(', ')')
    if cond_close < 0:
        return None
    k = skip_ws_comments(s, mask, cond_close + 1)
    if k >= len(s) or s[k] != '{':
        return None
    then_close = match_delim(s, mask, k, '{', '}')
    if then_close < 0:
        return None
    e = skip_ws_comments(s, mask, then_close + 1)
    else_kind = None
    else_open = -1
    if e < len(s) and s.startswith('else', e) and mask[e] == 0:
        e2 = skip_ws_comments(s, mask, e + 4)
        if e2 < len(s):
            if s[e2] == '{':
                else_kind = 'block'
                else_open = e2
            elif s.startswith('if', e2) and mask[e2] == 0 and (e2 + 2 >= len(s) or not (s[e2+2].isalnum() or s[e2+2] == '_')):
                else_kind = 'if'
                else_open = e2
    return {
        'kw': i,
        'cond_open': cond_open, 'cond_close': cond_close,
        'then_open': k, 'then_close': then_close,
        'else_kind': else_kind, 'else_open': else_open,
    }

def end_of_if(s, mask, info):
    """End index (exclusive) of the whole if statement."""
    if info['else_kind'] == 'block':
        return match_delim(s, mask, info['else_open'], '{', '}') + 1
    if info['else_kind'] == 'if':
        sub = parse_if(s, mask, info['else_open'])
        if sub is None:
            return info['then_close'] + 1
        return end_of_if(s, mask, sub)
    return info['then_close'] + 1

def indent_of(s, i):
    j = s.rfind('\n', 0, i) + 1
    k = j
    while k < i and s[k] in ' \t':
        k += 1
    return s[j:k]

def reindent(text, base_indent, extra=''):
    """Prefix each line of text with extra; ensure base indent on the first line is preserved."""
    lines = text.split('\n')
    out = []
    for ln in lines:
        if ln.strip() == '':
            out.append(ln)
        else:
            out.append(extra + ln)
    return '\n'.join(out)

def migrate_span(s, mask, info, depth=0):
    """Build the replacement text for one if statement (recursing for else-if)."""
    ind = indent_of(s, info['kw'])
    cond = s[info['cond_open'] + 1:info['cond_close']].strip()
    then_body = s[info['then_open'] + 1:info['then_close']]
    # trim a single leading and trailing newline from the body block
    tb = then_body
    if tb.startswith('\n'):
        tb = tb[1:]
    tb = tb.rstrip()
    parts = []
    parts.append(ind + 'Conditional:branch(check: { ' + cond + ' }, then: {\n')
    parts.append(tb + '\n')
    tail = ind + '});'
    if info['else_kind'] == 'block':
        else_body = s[info['else_open'] + 1:match_delim(s, mask, info['else_open'], '{', '}')]
        eb = else_body
        if eb.startswith('\n'):
            eb = eb[1:]
        eb = eb.rstrip()
        parts.append(ind + '}, otherwise: {\n')
        parts.append(eb + '\n')
    elif info['else_kind'] == 'if':
        sub = parse_if(s, mask, info['else_open'])
        sub_end = end_of_if(s, mask, sub)
        nested = migrate_span(s, mask, sub, depth + 1)
        nested = reindent(nested, ind, '\t')
        parts.append(ind + '}, otherwise: {\n')
        parts.append(nested + '\n')
    parts.append(tail)
    return ''.join(parts)

def migrate_once(s):
    """One pass: rewrite all outermost statement ifs. Returns (new_text, count)."""
    mask = scan_mask(s)
    kws = find_if_statements(s, mask)
    # outermost only: drop keywords nested inside another if's span
    spans = []
    for i in kws:
        info = parse_if(s, mask, i)
        if info is None:
            continue
        spans.append((i, end_of_if(s, mask, info), info))
    outer = []
    for a in spans:
        nested = False
        for b in spans:
            if b is a:
                continue
            if b[0] < a[0] and a[1] <= b[1]:
                nested = True
                break
        if not nested:
            outer.append(a)
    if not outer:
        return s, 0
    out = []
    pos = 0
    count = 0
    for start, end, info in sorted(outer):
        ls = s.rfind('\n', 0, start) + 1  # include the line's own indent in the replacement
        out.append(s[pos:ls])
        out.append(migrate_span(s, mask, info))
        pos = end
        count += 1
    out.append(s[pos:])
    return ''.join(out), count

def ensure_import(s):
    """Add the Conditional instance-import to every using block that lacks it."""
    changed = False
    mask = scan_mask(s)
    needle = 'replace Array of Array of String is using: ['
    d_scan = []
    d = 0
    for i, c in enumerate(s):
        if mask[i] == 0:
            if c == '{':
                d += 1
            elif c == '}':
                d -= 1
        d_scan.append(d)
    idx = 0
    inserts = []
    while True:
        p = s.find(needle, idx)
        if p < 0:
            break
        open_idx = s.index('[', p)
        # match the block's closing ']'
        bd = 0
        close_idx = -1
        i = open_idx
        while i < len(s):
            if mask[i] == 0:
                if s[i] == '[':
                    bd += 1
                elif s[i] == ']':
                    bd -= 1
                    if bd == 0:
                        close_idx = i
                        break
            i += 1
        if close_idx > 0 and 'as Conditional()' not in s[open_idx:close_idx]:
            inserts.append(open_idx + 1)
        idx = p + len(needle)
    for ins in sorted(inserts, reverse=True):
        s = s[:ins] + '\n\t\t' + USING_ENTRY + ',' + s[ins:]
        changed = True
    return s, changed

def add_using_to_classless(s):
    """Files without any using block: insert one after the namespace line."""
    if 'replace Array of Array of String is using' in s:
        return s, False
    m = re.search(r'(\tnamespace: \[[^\]]*\];\n)', s)
    if not m:
        return s, False
    block = '\n\treplace Array of Array of String is using: [\n\t\t' + USING_ENTRY + '\n\t];\n'
    s = s[:m.end(1)] + block + s[m.end(1):]
    return s, True

def process(path, check_only=False):
    s = open(path).read()
    total = 0
    rounds = 0
    while True:
        s2, n = migrate_once(s)
        if n == 0:
            break
        s = s2
        total += n
        rounds += 1
        if rounds > 12:
            print('  !! pass cap hit in', path)
            break
    if total > 0:
        s, a = ensure_import(s)
        s, b = add_using_to_classless(s)
    if check_only:
        print(path, 'sites:', total)
        return total
    if total > 0:
        open(path, 'w').write(s)
    print(path, 'migrated:', total, 'ifs')
    return total

if __name__ == '__main__':
    args = sys.argv[1:]
    check = False
    if args and args[0] == '--check':
        check = True
        args = args[1:]
    t = 0
    for f in args:
        t += process(f, check)
    print('total:', t)
