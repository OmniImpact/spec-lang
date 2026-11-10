#! Package base:sysinternal
#! The console floor: the stdout/stderr/stdin primitives bound to C by
#! the naming convention. The C names are the internal provenance —
#! what WE call these on the Spec side is decided by the base:sys
#! wrappers (Output's line/consOut, Stderr's line, Input's consIn).

Class is Console{
	namespace: ['base', 'sysinternal'];

	## Writes text to standard output without a trailing newline and
	## flushes stdout. Bound to `spec_print`.
	##
	## @param text: Text string to write inline.
	Function is print(String is text);

	## Writes text to standard output followed by a newline. Bound to
	## `spec_print_line`.
	##
	## @param text: Text string to write.
	Function is print_line(String is text);

	## Writes text to standard error followed by a newline. Bound to
	## `spec_error_line`.
	##
	## @param text: Text string to write.
	Function is error_line(String is text);

	## Reads one line from standard input (the trailing newline
	## stripped) and hands it to [on_line]; at end of input nothing is
	## handed over. Bound to `spec_read_line`.
	##
	## @param on_line: The closure receiving the line.
	Function is read_line(Function is on_line);
}
