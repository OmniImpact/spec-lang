#! Package base:sysinternal
#! Filesystem directory floor: package discovery primitives.
##
## Body-less, interface-style declarations bound to the runtime's C floor
## by the naming convention. Used by the Loader's package resolution.

Class is Dir{
	namespace: ['base', 'sysinternal'];

	## Names of the entries in directory [path] ('.' and '..' excluded).
	## Order is filesystem-dependent; consumers must not rely on it.
	##
	## @param path: Directory to list.
	## @return: Entry names.
	Function of Array of String is dirList(String is path);

	## Names of the entries in directory [path] ('.' and '..' excluded),
	## invoking [on_error] with an error description if opening fails.
	## Bound to `spec_dir_list_cb`.
	##
	## @param path: Directory to list.
	## @param on_error: Optional callback receiving error description.
	## @return: Entry names, or empty array on failure.
	Function of Array of String is dir_list_cb(String is path, Function is on_error);

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
