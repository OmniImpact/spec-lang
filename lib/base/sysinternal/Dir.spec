#! Package base:sysinternal
#! Filesystem directory floor: package discovery primitives.
##
## Body-less, interface-style declarations bound to the runtime's C floor
## by the naming convention. Used by the Loader's package resolution.

Class is Dir{
	replace Array of String is namespace: ['base', 'sysinternal'];

	## Names of the entries in directory [path] ('.' and '..' excluded).
	## Order is filesystem-dependent; consumers must not rely on it.
	Function of Array of String is dirList(String is path);

	## Directory containing the running spec executable.
	Function of String is exeDir();

	## Size of the file at [path] in bytes, or -1 when it does not exist.
	Function of Int is fileSize(String is path);
}
