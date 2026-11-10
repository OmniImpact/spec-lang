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
}
