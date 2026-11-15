#!/usr/bin/env python3
"""
Lightweight DAP stdio proxy around `gdb -i dap` for Spec debug builds.

Filters out compiler-generated C locals/fields (names starting with `_`) and
hides raw C struct expansion on pretty-printed Spec strings, arrays, maps, and
closures so the IDE Variables pane shows Spec-level values cleanly.
"""
import json
import os
import subprocess
import sys
import threading


def read_dap(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        if b":" in line:
            k, v = line.decode("ascii", "replace").split(":", 1)
            headers[k.strip().lower()] = v.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = stream.read(length)
    if not body:
        return None
    return json.loads(body.decode("utf-8", "replace"))


def write_dap(stream, msg):
    data = json.dumps(msg, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    stream.write(header + data)
    stream.flush()


_OPAQUE_TYPE_PREFIXES = (
    "SpecBuf",
    "SpecArray",
    "SpecMap",
    "SpecClosure",
    "volatile SpecBuf",
    "volatile SpecArray",
    "volatile SpecMap",
    "volatile SpecClosure",
)


_INTERNAL_GLOBAL_SUFFIXES = (
    "_spec_meta",
    "_spec_bases",
    "_spec_methods",
    "_vtable",
    "_held_getters",
    "_once",
)


def filter_variables(variables):
    out = []
    for var in variables:
        name = var.get("name", "")
        if name.startswith("_"):
            continue
        if name.startswith("spec_") and name.endswith("_registry"):
            continue
        if name.endswith(_INTERNAL_GLOBAL_SUFFIXES):
            continue
        vtype = (var.get("type") or "").strip()
        if any(vtype.startswith(p) for p in _OPAQUE_TYPE_PREFIXES):
            var = dict(var)
            var["variablesReference"] = 0
        out.append(var)
    return out


def main():
    gdb_cmd = ["gdb", "-i", "dap"]
    args = sys.argv[1:]
    if args:
        gdb_cmd.extend(args)

    proc = subprocess.Popen(
        gdb_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
    )

    write_lock = threading.Lock()

    def pump_stdin():
        try:
            while True:
                msg = read_dap(sys.stdin.buffer)
                if msg is None:
                    break
                write_dap(proc.stdin, msg)
        except Exception:
            pass
        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass

    t = threading.Thread(target=pump_stdin, daemon=True)
    t.start()

    try:
        while True:
            msg = read_dap(proc.stdout)
            if msg is None:
                break
            if (
                msg.get("type") == "response"
                and msg.get("command") == "variables"
                and msg.get("success")
                and isinstance(msg.get("body"), dict)
                and isinstance(msg["body"].get("variables"), list)
            ):
                msg["body"]["variables"] = filter_variables(msg["body"]["variables"])
            with write_lock:
                write_dap(sys.stdout.buffer, msg)
    finally:
        proc.wait()
        try:
            sys.stdout.buffer.flush()
        except Exception:
            pass
    os._exit(proc.returncode or 0)


if __name__ == "__main__":
    main()
