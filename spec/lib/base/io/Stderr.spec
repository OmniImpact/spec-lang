#! Package base:io
#! Standard error stream writers.

## Manages standard error console stream printing.
##
## Runtime-managed: calls compile to the runtime's
## stderr writers; no struct or methods are emitted for the class.

Class is Stderr{
	namespace: ['base', 'io'];

	## Writes text to standard error followed by a newline.
	##
	## @param text: Text string to print.
	Function is line(String is text){
	}

	## Writes text to standard error without a trailing newline.
	##
	## @param text: Text string to write inline.
	Function is print(String is text){
	}
}
