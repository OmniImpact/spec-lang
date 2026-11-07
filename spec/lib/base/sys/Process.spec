#! Package base:sys
#! System interaction, process execution, and execution frames.

## Dispatches external system commands and manages operating system subprocesses.
##
## Runtime-managed (TRANSITION.md section 2): every method binds to the
## runtime's process/syscall floor; the declaration is the API surface.

Class is Process{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', Array]
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
	}

	## Suspends execution of the current process for the specified duration.
	##
	## @param milliseconds: Duration to sleep in milliseconds.
	## @example:
	## ```spec
	## Process:sleep(milliseconds: 100);
	## ```
	Function is sleep(Int is milliseconds){
	}

	## Returns the operating system process identifier (PID) of the current process.
	##
	## @return: Current process ID.
	Function of Int is getPid(){
	}

	## Terminates the current process with the given exit status.
	##
	## @param status: Process exit code (0 = success).
	Function is exit(Int is status){
	}

	## Returns monotonic wall-clock milliseconds since an arbitrary epoch.
	##
	## Suitable for measuring elapsed time (differences of two calls).
	##
	## @return: Monotonic clock reading in milliseconds.
	Function of Int is clockMs(){
	}

	## Returns the peak resident set size of the current process.
	##
	## @return: Peak memory usage in kilobytes, or 0 when unavailable.
	Function of Int is peakMemoryKb(){
	}

	## Returns the number of OS threads currently owned by the process.
	##
	## @return: Live thread count, or 1 when unavailable.
	Function of Int is threadCount(){
	}

	## Atomically adds [value] to the shared slot and returns the new total.
	##
	## @param slot: Slot index (0..63).
	## @param value: Amount to add.
	## @return: The slot's new value.
	Function of Int is atomicAdd(Int is slot, Int is value){
	}

	## Atomically stores [value] into the shared slot (last writer wins).
	##
	## @param slot: Slot index (0..63).
	## @param value: Value to store.
	## @return: The stored value.
	Function of Int is atomicPut(Int is slot, Int is value){
	}

	## Atomically reads the shared slot's current value.
	##
	## @param slot: Slot index (0..63).
	## @return: The slot's current value.
	Function of Int is atomicGet(Int is slot){
	}
}
