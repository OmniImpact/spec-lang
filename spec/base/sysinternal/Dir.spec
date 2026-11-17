#! Package base:sysinternal
#! Filesystem directory floor: package discovery primitives.
##
## Body-less, interface-style declarations bound to the runtime's C floor
## by the naming convention. Used by the Loader's package resolution.

Class is Dir{
	namespace: ['base', 'sysinternal'];

	## Opens directory [path] for reading. Bound to `spec_pal_dir_open`.
	Function of Int is pal_dir_open(String is path);

	## Reads the next entry name C-string address (or 0 on end). Bound to `spec_pal_dir_next`.
	Function of Int is pal_dir_next(Int is handle);

	## Closes directory handle [handle]. Bound to `spec_pal_dir_close`.
	Function is pal_dir_close(Int is handle);

	## Last OS error string (`strerror(errno)`). Bound to `spec_pal_last_error`.
	Function of String is pal_last_error();

	## Directory containing the running spec executable.
	##
	## @return: The executable's directory.
	Function of String is exeDir();

	## Size of the file at [path] in bytes, or -1 when it does not exist.
	##
	## @param path: File to measure.
	## @return: Size in bytes, or -1.
	Function of Int is fileSize(String is path);
}
