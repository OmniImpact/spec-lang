#! Package base:sys
#! The console output wrapper: the Spec-side names over the console
#! floor's C names.

## Standard output. `line` writes with a trailing newline; `consOut`
## writes inline and flushes — the console-out half of the console I/O
## pair (`consOut`/`consIn`). The explicit console names keep the
## generic I/O verbs (`read`/`write`) unambiguous for File under the
## merged as-import scope.

Class is Output{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Console]
	];

	## Writes text to standard output followed by a newline.
	##
	## @param text: Text string to print.
	Function is line(String is text){
		base:sysinternal:Console:print_line(text: text);
	}

	## Writes text to standard output without a trailing newline and
	## flushes stdout.
	##
	## @param text: Text string to write inline.
	Function is consOut(String is text){
		base:sysinternal:Console:print(text: text);
	}
}
