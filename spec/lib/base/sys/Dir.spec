#! Package base:sys
#! Public wrapper over the sysinternal filesystem-directory floor.

Class is Dir{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'sys', FileError],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', Dir]
	];

	local Function of Int is cstrOf(String is s){
		local Int is sAddr: Mem:objToAddr(obj: s);
		if({ sAddr == 0 || Mem:loadI64(ptr: sAddr, byteOffset: 8) == 0 }, {
			return 0;
		});
		return Mem:loadI64(ptr: sAddr, byteOffset: 0);
	}

	## Names of the entries in directory [path] ('.' and '..' excluded).
	## Order is filesystem-dependent; consumers must not rely on it.
	##
	## @param path: Directory to list.
	## @param onError: Optional callback receiving the failure as the full
	##   error currency: `Function(SpecError of FileError)`. Absent the
	##   callback, failures return the empty listing (Never Null).
	## @return: Entry names.
	Function of Array of String is dirList(String is path, Function is onError: local Function(SpecError of FileError is error){}){
		local Array of String is out: Array();
		local Int is pc: :cstrOf(s: path);
		if({ pc == 0 }, {
			if({ Mem:hasClosure(cb: onError) }, {
				onError(SpecError:init(kind: FileError:INVALID_PATH, description: 'invalid path'));
			});
			return out;
		});
		local Int is handle: base:sysinternal:Dir:pal_dir_open_cstr(path_cstr: pc);
		if({ handle == 0 }, {
			local Int is ec: base:sysinternal:Dir:pal_last_error_cstr();
			local Int is elen: Mem:cstrLen(cstrAddr: ec);
			if({ Mem:hasClosure(cb: onError) }, {
				onError(SpecError:init(kind: FileError:IO_ERROR, description: Mem:strFromBytes(srcAddr: ec, len: elen)));
			});
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
		local Int is buf: Mem:alloc(bytes: 4096);
		local Int is n: base:sysinternal:Dir:pal_exe_dir(buf_addr: buf, buf_size: 4096);
		local String is res: if({ n > 0 }, { Mem:strFromBytes(srcAddr: buf, len: n) }, { '' });
		Mem:free(ptr: buf);
		return res;
	}

	## Full path of the running spec executable.
	##
	## @return: The executable's file path, or empty if unavailable.
	Function of String is exePath(){
		local Int is buf: Mem:alloc(bytes: 4096);
		local Int is n: base:sysinternal:Dir:pal_exe_path(buf_addr: buf, buf_size: 4096);
		local String is res: if({ n > 0 }, { Mem:strFromBytes(srcAddr: buf, len: n) }, { '' });
		Mem:free(ptr: buf);
		return res;
	}

	## Size of the file at [path] in bytes, or -1 when it does not exist.
	##
	## @param path: File to measure.
	## @return: Size in bytes, or -1.
	Function of Int is fileSize(String is path){
		local Int is pc: :cstrOf(s: path);
		if({ pc == 0 }, { return -1; });
		return base:sysinternal:Dir:pal_file_size_cstr(path_cstr: pc);
	}

	## Returns `true` when [path] exists and is a directory.
	Function of Boolean is isDir(String is path){
		local Int is pc: :cstrOf(s: path);
		if({ pc == 0 }, { return false; });
		local Int is handle: base:sysinternal:Dir:pal_dir_open_cstr(path_cstr: pc);
		if({ handle == 0 }, { return false; });
		base:sysinternal:Dir:pal_dir_close(handle: handle);
		return true;
	}

	## Creates a single directory at [path]; returns `true` on success.
	Function of Boolean is makeDir(String is path){
		local Int is pc: :cstrOf(s: path);
		if({ pc == 0 }, { return false; });
		return base:sysinternal:Dir:pal_dir_mkdir(path_cstr: pc);
	}

	## Creates [path] and any missing parent directories; returns `true` if [path] exists as a directory.
	Function of Boolean is makeDirAll(String is path){
		if({ path == '' }, { return false; });
		if({ :isDir(path: path) }, { return true; });
		local String is norm: path:replaceAll(search: "\\", replacement: '/');
		local Boolean is isAbs: norm:startsWith(prefix: '/');
		local Array of String is parts: norm:split(delimiter: '/');
		local String is cur: if({ isAbs }, { '' }, { '.' });
		local Int is i: 0;
		while({ i < parts:length() }, {
			local String is seg: parts:get(index: i, default: '');
			if({ seg != '' }, {
				if({ cur == '' }, {
					cur: '/' . seg;
				}, {
					if({ cur == '.' }, { cur: seg; }, { cur: cur . '/' . seg; });
				});
				if({ !:isDir(path: cur) }, {
					:makeDir(path: cur);
				});
			});
			i: i + 1;
		});
		return :isDir(path: path);
	}

	## Removes an empty directory at [path]; returns `true` on success.
	Function of Boolean is removeDir(String is path){
		local Int is pc: :cstrOf(s: path);
		if({ pc == 0 }, { return false; });
		return base:sysinternal:Dir:pal_dir_rmdir(path_cstr: pc);
	}
}
