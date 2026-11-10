#! Package base:sys
#! The process wrapper: the Spec-side names over the process floor's
#! C names (spec_process_execute and friends).

## Dispatches external system commands, timing, memory and thread
## introspection, and lock-free atomic slots. Every method delegates
## to the process floor.

Class is Process{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sysinternal', Process]
	];

	## Spawns a child process executing [command] with [args], waiting for completion.
	##
	## @param command: System binary or executable name to invoke.
	## @param args: Command-line arguments passed to the process.
	## @return: Process exit status code (`0` for success).
	## @example:
	## ```spec
	## local Int is code: Process:execute(command: 'ls', args: ['-la']);
	## ```
	Function of Int is execute(String is command, Array of String is args){
		return base:sysinternal:Process:process_execute(command: command, args: args);
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

	## Terminates the current process with the given exit status.
	##
	## @param status: Process exit code (0 = success).
	Function is exit(Int is status){
		base:sysinternal:Process:process_exit(status: status);
	}

	## Returns monotonic wall-clock milliseconds since an arbitrary epoch.
	##
	## Suitable for measuring elapsed time (differences of two calls).
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
	##
	## @param slot: Atomic slot index.
	## @param value: Addend.
	## @return: Previous slot value.
	Function of Int is atomicAdd(Int is slot, Int is value){
		return base:sysinternal:Process:atomic_add(slot: slot, value: value);
	}

	## Atomically writes [value] into the slot at [slot].
	##
	## @param slot: Atomic slot index.
	## @param value: Value to write.
	Function is atomicPut(Int is slot, Int is value){
		base:sysinternal:Process:atomic_put(slot: slot, value: value);
	}

	## Atomically reads the slot at [slot].
	##
	## @param slot: Atomic slot index.
	## @return: Slot value.
	Function of Int is atomicGet(Int is slot){
		return base:sysinternal:Process:atomic_get(slot: slot);
	}
}
