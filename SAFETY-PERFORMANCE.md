# Safety & Performance Improvements

Tasks ordered by impact:

- [x] **Task 1 (Critical Safety)**: Fix string aliasing in `spec_buf_append_buf` when `dst == src` (self-concatenation use-after-free).
- [x] **Task 2 (Correctness / Safety)**: Fix buffer underflow on negative `from` in `spec_string_index_of_from`, and optimize with vector-friendly `memcmp`.
- [x] **Task 3 (Performance)**: Optimize `spec_string_substring` from byte-by-byte loop to single allocation and `memcpy`.
- [x] **Task 4 (Correctness / Performance)**: Fix `spec_array_add_array` when `a == other` to pre-grow capacity and prevent pointer invalidation during loop.
- [x] **Task 5 (Resource Safety / Leaks)**: Clean up thread-local claim pool stack in spawned worker threads upon termination (`spec_pool_thread_cleanup`).
- [x] **Task 6 (Resource Safety / Leaks)**: Release allocated string in `spec_read_line` after callback invocation.
