#! Package base:sys
#! Provides system interaction, process execution, and execution frames.

## Dispatches external system commands and manages operating system subprocesses.
Class is Process{

	replace local Array of String is using: [
		base:struct:Array
	];

	## Spawns a child process executing [command] with [args], waiting for completion.
	##
	## @param command: System binary or executable name to invoke.
	## @param args: Command-line arguments passed to the process.
	## @return: Process exit status code (`0` for success).
	## @example:
	## ```spec
	## local Int is code: Process:execute(command: "ls", args: ["-la"]);
	## ```
	replace Function of Int is execute(String is command, Array of String is args){
	}

	## Suspends execution of the current process for the specified duration.
	##
	## @param milliseconds: Duration to sleep in milliseconds.
	## @example:
	## ```spec
	## Process:sleep(milliseconds: 100);
	## ```
	replace Function is sleep(Int is milliseconds){
	}

	## Returns the operating system process identifier (PID) of the current process.
	##
	## @return: Current process ID integer.
	replace Function of Int is getPid(){
	}

	## Terminates the current process with the given exit status.
	##
	## @param status: Process exit code (0 = success).
	replace Function is exit(Int is status){
	}

	## Suspends the calling thread for the given duration.
	##
	## @param milliseconds: Sleep duration in milliseconds.
	replace Function is sleep(Int is milliseconds){
	}

}
