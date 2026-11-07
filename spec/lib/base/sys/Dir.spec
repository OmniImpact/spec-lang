#! Package base:sys
#! Public wrapper over the sysinternal filesystem-directory floor.
##
## Same-name wrapper rule: only base:sys may call base:sysinternal; the
## floor is addressed by its full qualified chain here.

Class is Dir{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['spec', 'base', 'sysinternal', Dir]
	];

	## Names of the entries in directory [path] ('.' and '..' excluded).
	## Order is filesystem-dependent; consumers must not rely on it.
	##
	## @param path: Directory to list.
	## @return: Entry names.
	Function of Array of String is dirList(String is path){
		return base:sysinternal:Dir:dirList(path: path);
	}

	## Directory containing the running spec executable.
	##
	## @return: The executable's directory.
	Function of String is exeDir(){
		return base:sysinternal:Dir:exeDir();
	}

	## Size of the file at [path] in bytes, or -1 when it does not exist.
	##
	## @param path: File to measure.
	## @return: Size in bytes, or -1.
	Function of Int is fileSize(String is path){
		return base:sysinternal:Dir:fileSize(path: path);
	}
}
