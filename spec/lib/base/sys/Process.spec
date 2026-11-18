#! Package base:sys
#! The process wrapper: the Spec-side names over the process floor's
#! C names (spec_pal_process_execute_cstr and friends).

## Dispatches external system commands, timing, memory and thread
## introspection, and lock-free atomic slots. Every method delegates
## to the process floor.

Class is Process{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', as Conditional()],
		['base', 'sys', as HashTable()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Vector()],
		['base', 'sysinternal', Process]
	];

	local Function of Int is cstrAddr(String is s){
		local Int is sAddr: Mem:objToAddr(obj: s);
		return if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 0) }, { 0 });
	}

	local Function of Int is buildCArgv(Array of String is args){
		local Int is n: args:length();
		if({ n <= 0 }, { return 0; });
		local Int is buf: Mem:alloc(bytes: n * 8);
		local Int is i: 0;
		while({ i < n }, {
			local String is s: args:get(index: i, default: '');
			Mem:storeI64(ptr: buf, byteOffset: i * 8, val: :cstrAddr(s: s));
			i: i + 1;
		});
		return buf;
	}

	## Spawns a child process executing [command] with [args], waiting for completion.
	##
	## @param command: System binary or executable name to invoke.
	## @param args: Command-line arguments passed to the process.
	## @return: Process exit status code (`0` for success).
	Function of Int is execute(String is command, Array of String is args){
		local Int is n: args:length();
		local Int is argvBuf: :buildCArgv(args: args);
		local Int is code: base:sysinternal:Process:pal_process_execute_cstr(cmd_cstr: :cstrAddr(s: command), argv_addr: argvBuf, nargs: n);
		if({ argvBuf != 0 }, { Mem:free(ptr: argvBuf); });
		return code;
	}

	## Returns the raw command-line arguments passed to the program (`argv[1..]`).
	##
	## @return: Array of argument strings in exact CLI order.
	Function of Array of String is rawArgs(){
		return base:sysinternal:Process:process_raw_args();
	}

	## Spawns [command] directly with [args] (without a shell) and measures
	## exit code, wall time (`wall_us`), CPU time (`cpu_us`), and peak RSS (`rss_kb`).
	##
	## @param command: Executable name or path.
	## @param args: Command-line arguments passed to the child process.
	## @return: Map with stringified integer keys `'exit'`, `'wall_us'`, `'cpu_us'`, `'rss_kb'`.
	Function of Map of String to String is measure(String is command, Array of String is args){
		local Int is n: args:length();
		local Int is argvBuf: :buildCArgv(args: args);
		local Int is outBuf: Mem:alloc(bytes: 32);
		base:sysinternal:Process:pal_process_measure_cstr(cmd_cstr: :cstrAddr(s: command), argv_addr: argvBuf, nargs: n, out_addr: outBuf);
		if({ argvBuf != 0 }, { Mem:free(ptr: argvBuf); });
		local Map of String to String is m: Map:init();
		m:set(key: 'exit', value: Mem:loadI64(ptr: outBuf, byteOffset: 0) as String);
		m:set(key: 'wall_us', value: Mem:loadI64(ptr: outBuf, byteOffset: 8) as String);
		m:set(key: 'cpu_us', value: Mem:loadI64(ptr: outBuf, byteOffset: 16) as String);
		m:set(key: 'rss_kb', value: Mem:loadI64(ptr: outBuf, byteOffset: 24) as String);
		Mem:free(ptr: outBuf);
		return m;
	}

	## Suspends execution of the current process for the specified duration.
	##
	## @param milliseconds: Duration to sleep in milliseconds.
	Function is sleep(Int is milliseconds){
		base:sysinternal:Process:process_sleep(milliseconds: milliseconds);
	}

	## Returns the current process ID.
	##
	## @return: Current process ID.
	Function of Int is getPid(){
		return base:sysinternal:Process:process_get_pid();
	}

	## Returns the environment variable value for [key], or [default] if unset.
	##
	## @param key: The environment variable name.
	## @param default: Fallback value if the variable is not set.
	## @return: The environment variable value.
	Function of String is getEnv(String is key, String is default){
		local Int is valCstr: base:sysinternal:Process:pal_getenv(key_cstr: :cstrAddr(s: key));
		if({ valCstr == 0 }, { return default; });
		return Mem:strFromBytes(srcAddr: valCstr, len: Mem:cstrLen(cstrAddr: valCstr));
	}

	## Returns the operating system name ('linux', 'macos', 'windows', or 'unknown').
	##
	## @return: Operating system name string.
	Function of String is osName(){
		local Int is cstr: base:sysinternal:Process:pal_os_name();
		if({ cstr == 0 }, { return 'unknown'; });
		return Mem:strFromBytes(srcAddr: cstr, len: Mem:cstrLen(cstrAddr: cstr));
	}

	## Terminates the current process with the given exit status.
	##
	## @param status: Process exit code (0 = success).
	Function is exit(Int is status){
		base:sysinternal:Process:process_exit(status: status);
	}

	## Returns monotonic wall-clock milliseconds since an arbitrary epoch.
	##
	## @return: Monotonic clock reading in milliseconds.
	Function of Int is clockMs(){
		return base:sysinternal:Process:clock_ms();
	}

	## Returns the peak resident memory used by this process, in kilobytes.
	##
	## @return: Peak memory in KB.
	Function of Int is peakMemoryKb(){
		return base:sysinternal:Process:mem_peak_kb();
	}

	## Returns the number of hardware threads available to the runtime.
	##
	## @return: Hardware thread count.
	Function of Int is threadCount(){
		return base:sysinternal:Process:thread_count();
	}

	## Atomically adds [value] to the slot at [slot] and returns the previous value.
	Function of Int is atomicAdd(Int is slot, Int is value){
		return base:sysinternal:Process:atomic_add(slot: slot, value: value);
	}

	## Atomically writes [value] into the slot at [slot].
	Function is atomicPut(Int is slot, Int is value){
		base:sysinternal:Process:atomic_put(slot: slot, value: value);
	}

	## Atomically reads the slot at [slot].
	Function of Int is atomicGet(Int is slot){
		return base:sysinternal:Process:atomic_get(slot: slot);
	}

	## Starts the background resource monitor task inside [scope] (samples RSS and CPU).
	Function is monitorStart(ThreadScope is scope){
		scope:spawn(task: local Function(){
			if({ !scope:isCancelled() }, {
				base:sysinternal:Process:monitor_start();
			});
		});
	}

	## Stops the background resource monitor thread and computes final metrics.
	Function is monitorStop(){
		base:sysinternal:Process:monitor_stop();
	}

	## Returns the average memory usage in kilobytes.
	Function of Int is monitorAvgMemKb(){
		return base:sysinternal:Process:monitor_avg_mem_kb();
	}

	## Returns the peak memory usage in kilobytes.
	Function of Int is monitorPeakMemKb(){
		return base:sysinternal:Process:monitor_peak_mem_kb();
	}

	## Returns the average CPU usage percentage (sum of cores, can exceed 100%).
	Function of Int is monitorAvgCpuPct(){
		return base:sysinternal:Process:monitor_avg_cpu_pct();
	}

	## Returns the peak interval CPU usage percentage (sum of cores, can exceed 100%).
	Function of Int is monitorPeakCpuPct(){
		return base:sysinternal:Process:monitor_peak_cpu_pct();
	}

	## Freezes a map for lock-free concurrent reads across worker threads.
	Function is mapFreeze(Any is m){
		HashTable:mapFreeze(m: m);
	}

	## Freezes an array for lock-free concurrent reads across worker threads.
	Function is arrayFreeze(Any is a){
		Vector:vecFreeze(v: a);
	}
}
