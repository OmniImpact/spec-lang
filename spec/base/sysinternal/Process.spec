#! Package base:sysinternal
#! The process floor: execution, timing, and atomics bound to C by the
#! naming convention. The C names are the internal provenance — the
#! base:sys Process wrapper decides what WE call them on the Spec side.

Class is Process{
	namespace: ['base', 'sysinternal'];

	## Executes an external system command with arguments and returns
	## the process exit status code (`0` for success). Bound to
	## `spec_process_execute`.
	##
	## @param command: The command to execute.
	## @param args: The command's arguments.
	## @return: The exit status code.
	Function of Int is process_execute(String is command, Array of String is args);

	## Suspends the current thread for [milliseconds]. Bound to
	## `spec_process_sleep`.
	##
	## @param milliseconds: The sleep duration.
	Function is process_sleep(Int is milliseconds);

	## Terminates the current process with the given exit status.
	## Bound to `spec_process_exit`.
	##
	## @param status: Process exit code (0 = success).
	Function is process_exit(Int is status);

	## Returns the current process ID. Bound to `spec_process_get_pid`.
	##
	## @return: Current process ID.
	Function of Int is process_get_pid();

	## Returns monotonic wall-clock milliseconds since an arbitrary
	## epoch. Bound to `spec_clock_ms`.
	##
	## @return: Monotonic clock reading in milliseconds.
	Function of Int is clock_ms();

	## Returns the peak resident memory in kilobytes. Bound to
	## `spec_mem_peak_kb`.
	##
	## @return: Peak memory in KB.
	Function of Int is mem_peak_kb();

	## Returns the number of hardware threads available. Bound to
	## `spec_thread_count`.
	##
	## @return: The hardware thread count.
	Function of Int is thread_count();

	## Atomically adds [value] to the slot at [slot] and returns the
	## previous value. Bound to `spec_atomic_add`.
	##
	## @param slot: The atomic slot index.
	## @param value: The addend.
	## @return: The previous slot value.
	Function of Int is atomic_add(Int is slot, Int is value);

	## Starts the background resource monitor thread (samples RSS and CPU).
	## Bound to `spec_monitor_start`.
	Function is monitor_start();

	## Stops the resource monitor thread and computes summary metrics.
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

	## Atomically writes [value] into the slot at [slot]. Bound to
	## `spec_atomic_put`.
	##
	## @param slot: The atomic slot index.
	## @param value: The value to write.
	Function is atomic_put(Int is slot, Int is value);

	## Atomically reads the slot at [slot]. Bound to `spec_atomic_get`.
	##
	## @param slot: The atomic slot index.
	## @return: The slot value.
	Function of Int is atomic_get(Int is slot);
}
