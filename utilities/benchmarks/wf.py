# =============================================================================
# Word/log-line frequency benchmark — Python 3 (dict + split).
# Usage: python3 wf.py [count]
# =============================================================================
import sys
import time


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
    if count < 1:
        count = 1

    services = (
        "auth", "api", "billing", "cache",
        "db", "edge", "feed", "gateway",
        "ingest", "jobs", "kv", "logs",
        "metrics", "notify", "proxy", "search",
    )
    levels = ("INFO", "WARN", "ERR")

    st = 0x9E3779B9
    for _ in range(3):
        st = (st ^ ((st << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
        st = (st ^ (st >> 17)) & 0xFFFFFFFF
        st = (st ^ ((st << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF

    counts: dict[str, int] = {}
    t0 = time.perf_counter()

    for _ in range(count):
        st = (st ^ ((st << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
        st = (st ^ (st >> 17)) & 0xFFFFFFFF
        st = (st ^ ((st << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
        r1 = st & 15

        st = (st ^ ((st << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
        st = (st ^ (st >> 17)) & 0xFFFFFFFF
        st = (st ^ ((st << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
        r2 = (st & 0x7FFFFFFF) % 3

        st = (st ^ ((st << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
        st = (st ^ (st >> 17)) & 0xFFFFFFFF
        st = (st ^ ((st << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
        r3 = (st & 0x7FFFFFFF) % 500

        line = f"{services[r1]}:{levels[r2]}:{r3}"
        parts = line.split(":")
        code = int(parts[2])
        bucket = code & 63
        key = f"{parts[0]}:{parts[1]}:{bucket}"
        counts[key] = counts.get(key, 0) + 1

    total = sum(counts.values())
    max_count = max(counts.values()) if counts else 0

    ms = (time.perf_counter() - t0) * 1000.0
    if ms < 1.0:
        ms = 1.0
    rate = count / (ms / 1000.0)
    print(f"unique={len(counts)} total={total} max={max_count} count={count} ms={ms:.0f} rate={rate:.4e}")


if __name__ == "__main__":
    main()
