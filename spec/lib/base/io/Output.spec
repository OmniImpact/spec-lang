#! Package base:io
#! Terminal console output, interactive prompts, and file operations.

## Manages standard output console stream printing.
##
## Runtime-managed (TRANSITION.md section 2): calls compile to the runtime's
## stdout writers; no struct or methods are emitted for the class.

Class is Output{
	namespace: ['base', 'io'];

	## Writes text to standard output followed by a newline.
	##
	## @param text: Text string to print.
	Function is line(String is text){
	}

	## Writes text to standard output without a trailing newline and flushes stdout.
	##
	## @param text: Text string to print inline.
	Function is print(String is text){
	}

	## Alias for [print]; writes text to standard output without a trailing newline.
	##
	## @param text: Text string to write inline.
	Function is write(String is text){
	}
}
