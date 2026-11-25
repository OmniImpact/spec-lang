#! Package base:sysinternal
#! The process floor: execution, timing, and atomics bound to C by the
#! naming convention. The C names are the internal provenance — the
#! base:sys Process wrapper decides what WE call them on the Spec side.

Class is Process{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Executes an external system command [cmd_cstr] with C-string argument vector
	## at [argv_addr] of length [nargs] and returns the process exit status code.
	## Bound to `spec_pal_process_execute_cstr`.
	Function of Int is pal_process_execute_cstr(Int is cmd_cstr, Int is argv_addr, Int is nargs);

	## Returns the raw command-line arguments passed to the program (`argv[1..]`).
	## Bound to `spec_process_raw_args`.
	Function of Array of String is process_raw_args();

	## Spawns [cmd_cstr] directly with C-string argument vector at [argv_addr] of length
	## [nargs] (without a shell) and writes 4 `i64` metrics (exit, wall_us, cpu_us, rss_kb)
	## into [out_addr]. Bound to `spec_pal_process_measure_cstr`.
	Function is pal_process_measure_cstr(Int is cmd_cstr, Int is argv_addr, Int is nargs, Int is out_addr);

	## Suspends the current thread for [milliseconds]. Bound to `spec_process_sleep`.
	Function is process_sleep(Int is milliseconds);

	## Terminates the current process with the given exit status.
	## Bound to `spec_process_exit`.
	Function is process_exit(Int is status);

	## Returns the current process ID. Bound to `spec_process_get_pid`.
	Function of Int is process_get_pid();

	## Returns the C-string address of environment variable [key_cstr], or 0 if unset.
	## Bound to `spec_pal_getenv`.
	Function of Int is pal_getenv(Int is key_cstr);

	## Returns the C-string address of the operating system name ('linux', 'macos', 'windows', or 'unknown').
	## Bound to `spec_pal_os_name`.
	Function of Int is pal_os_name();

	## Returns monotonic wall-clock milliseconds since an arbitrary epoch.
	## Bound to `spec_clock_ms`.
	Function of Int is clock_ms();

	## Returns cumulative process CPU time (user + kernel) in microseconds.
	## Bound to `spec_cpu_time_us`.
	Function of Int is cpu_time_us();

	## Returns the current resident memory in kilobytes. Bound to `spec_mem_current_kb`.
	Function of Int is mem_current_kb();

	## Returns the peak resident memory in kilobytes. Bound to `spec_mem_peak_kb`.
	Function of Int is mem_peak_kb();

	## Returns the number of hardware threads available. Bound to `spec_thread_count`.
	Function of Int is thread_count();

	## Atomically adds [value] to the slot at [slot] and returns the previous value.
	## Bound to `spec_atomic_add`.
	Function of Int is atomic_add(Int is slot, Int is value);

	## Runs the resource monitor sampling loop until `monitor_stop` is called.
	## Bound to `spec_monitor_start`.
	Function is monitor_start();

	## Stops the resource monitor loop and computes summary metrics.
	## Bound to `spec_monitor_stop`.
	Function is monitor_stop();

	## Returns the average memory in kilobytes across samples.
	## Bound to `spec_monitor_avg_mem_kb`.
	Function of Int is monitor_avg_mem_kb();

	## Returns the peak memory in kilobytes.
	## Bound to `spec_monitor_peak_mem_kb`.
	Function of Int is monitor_peak_mem_kb();

	## Returns the average CPU usage percentage (can exceed 100% across cores).
	## Bound to `spec_monitor_avg_cpu_pct`.
	Function of Int is monitor_avg_cpu_pct();

	## Returns the peak interval CPU usage percentage.
	## Bound to `spec_monitor_peak_cpu_pct`.
	Function of Int is monitor_peak_cpu_pct();

	## Atomically writes [value] into the slot at [slot].
	## Bound to `spec_atomic_put`.
	Function is atomic_put(Int is slot, Int is value);

	## Atomically reads the slot at [slot]. Bound to `spec_atomic_get`.
	Function of Int is atomic_get(Int is slot);

	## Returns 1 when hardware SIMD vectors (SSE2/AVX2/NEON) are available, else 0.
	## Bound to `spec_pal_cpu_has_simd`.
	Function of Int is pal_cpu_has_simd();

	## Returns 1 when x86 AVX2 is supported at runtime, else 0.
	## Bound to `spec_pal_cpu_has_avx2`.
	Function of Int is pal_cpu_has_avx2();
}
