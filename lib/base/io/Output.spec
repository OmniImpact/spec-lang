#! Package base:io
#! Provides terminal console output, interactive prompts, and file operations.

## Manages standard output console stream printing.
Class is Output{

	## Writes a string representation to standard output followed by a newline.
	##
	## @param text: Text string to print.
	Function is line(String is text){
	}

	## Writes a string representation to standard output without a trailing newline and flushes stdout.
	##
	## @param text: Text string to print inline.
	Function is print(String is text){
	}

	## Alias for [print]; writes a string representation to standard output without a trailing newline.
	##
	## @param text: Text string to write inline.
	Function is write(String is text){
	}

}
