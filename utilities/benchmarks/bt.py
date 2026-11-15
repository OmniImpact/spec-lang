# =============================================================================
# Binary-trees benchmark — Python 3 (single-threaded).
# Usage: python3 bt.py [threads] [max_depth]
# =============================================================================
import sys
import time


class Node:
    __slots__ = ("left", "right")

    def __init__(self, left, right):
        self.left = left
        self.right = right


def make_tree(depth: int) -> Node:
    if depth <= 0:
        return Node(None, None)
    return Node(make_tree(depth - 1), make_tree(depth - 1))


def check_tree(n: Node) -> int:
    if n.left is None:
        return 1
    return 1 + check_tree(n.left) + check_tree(n.right)


def main() -> None:
    t = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 14
    min_depth = 4
    if max_depth < min_depth + 2:
        max_depth = min_depth + 2

    t0 = time.perf_counter()
    total_checks = 0

    stretch = make_tree(max_depth + 1)
    total_checks += check_tree(stretch)
    del stretch

    long_lived = make_tree(max_depth)

    for d in range(min_depth, max_depth + 1, 2):
        iterations = 1 << (max_depth - d + min_depth)
        for _ in range(iterations):
            total_checks += check_tree(make_tree(d))

    total_checks += check_tree(long_lived)

    ms = (time.perf_counter() - t0) * 1000.0
    if ms < 1.0:
        ms = 1.0
    rate = total_checks / (ms / 1000.0)
    print(f"checksum={total_checks} threads={t} depth={max_depth} ms={ms:.0f} rate={rate:.4e}")


if __name__ == "__main__":
    main()
