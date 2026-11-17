#! Package base:sys
#! Public wrapper over the sysinternal filesystem-directory floor.
##
## Same-name wrapper rule: only base:sys may call base:sysinternal; the
## floor is addressed by its full qualified chain here.

Class is Dir{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', Dir]
	];

	## Names of the entries in directory [path] ('.' and '..' excluded).
	## Order is filesystem-dependent; consumers must not rely on it.
	##
	## @param path: Directory to list.
	## @param onError: Optional callback receiving error description on failure: `Function(String is error)`.
	## @return: Entry names.
	Function of Array of String is dirList(String is path, Function is onError: local Function(String is error){}){
		local Array of String is out: [];
		local Int is pathAddr: Mem:objToAddr(obj: path);
		if({ pathAddr == 0 || Mem:loadI64(ptr: pathAddr, byteOffset: 0) == 0 }, {
			onError('invalid path');
			return out;
		});
		local Int is handle: base:sysinternal:Dir:pal_dir_open(path: path);
		if({ handle == 0 }, {
			local String is errMsg: base:sysinternal:Dir:pal_last_error();
			onError(errMsg);
			return out;
		});
		local Int is nameAddr: base:sysinternal:Dir:pal_dir_next(handle: handle);
		while({ nameAddr != 0 }, {
			local Int is nlen: Mem:cstrLen(cstrAddr: nameAddr);
			out:add(item: Mem:strFromBytes(srcAddr: nameAddr, len: nlen));
			nameAddr: base:sysinternal:Dir:pal_dir_next(handle: handle);
		});
		base:sysinternal:Dir:pal_dir_close(handle: handle);
		return out;
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
