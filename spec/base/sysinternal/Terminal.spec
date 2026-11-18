#! Package base:sysinternal
#! The terminal-metric floor: the ioctl-backed size queries bound to C
#! by the naming convention. The base:sys Ansi wrapper decides what
#! WE call them on the Spec side.

Class is Terminal{
	namespace: ['base', 'sysinternal'];

	## Returns the console width in columns, or 0 when stdout is not a
	## terminal. Bound to `spec_term_width`.
	##
	## @return: Width in columns.
	Function of Int is term_width();

	## Returns the console height in rows, or 0 when stdout is not a
	## terminal. Bound to `spec_term_height`.
	##
	## @return: Height in rows.
	Function of Int is term_height();

	## Returns 1 when stdout is an interactive terminal, 0 otherwise.
	## Bound to `spec_term_is_tty`.
	Function of Int is term_is_tty();

	## Enables UTF-8 and virtual terminal escape processing on Windows,
	## or returns `term_is_tty()` on POSIX. Bound to `spec_term_enable_vt`.
	Function of Int is term_enable_vt();
}
