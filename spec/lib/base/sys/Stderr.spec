#! Package base:sys
#! The diagnostics wrapper over the console floor's error-line
#! primitive.

## Standard error. Diagnostics and program status write here; normal
## output goes to Output.

Class is Stderr{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Console]
	];

	## Writes text to standard error followed by a newline.
	##
	## @param text: Text string to write.
	Function is line(String is text){
		base:sysinternal:Console:error_line(text: text);
	}
}
