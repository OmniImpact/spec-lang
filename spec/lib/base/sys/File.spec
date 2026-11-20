#! Package base:sys
#! The filesystem wrapper over the scalar file PAL floor.

Class is File{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'core', SpecError],
		['base', 'sys', FileError],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', File]
	];

	local Function of Int is cstrOf(String is s){
		local Int is sAddr: Mem:objToAddr(obj: s);
		if({ sAddr == 0 || Mem:loadI64(ptr: sAddr, byteOffset: 8) == 0 }, {
			return 0;
		});
		return Mem:loadI64(ptr: sAddr, byteOffset: 0);
	}

	local Function of Boolean is hasClosure(Function is cb){
		local Int is addr: Mem:objToAddr(obj: cb);
		if({ addr == 0 }, { return false; });
		return Mem:loadI64(ptr: addr, byteOffset: 0) != 0;
	}

	## Reports a failure through [onError] as the full error currency:
	## a `SpecError of FileError` whose kind is [kind] and whose
	## description is the OS errno text when available, else [fallback].
	local Function is emitLastError(FileError is kind, Function is onError, String is fallback){
		if({ !:hasClosure(cb: onError) }, { return; });
		local String is detail: fallback;
		local Int is ec: base:sysinternal:File:pal_last_error_cstr();
		if({ ec != 0 }, {
			local Int is elen: Mem:cstrLen(cstrAddr: ec);
			detail: Mem:strFromBytes(srcAddr: ec, len: elen);
		});
		onError(SpecError:init(kind: kind, description: detail));
	}

	## Reads the entire contents of a file with optional success and error callback handlers.
	Function of String is fileRead(String is path, Function is onSuccess, Function is onError, String is default: ''){
		local String is defStr: if({ Mem:objToAddr(obj: default) != 0 }, { default }, { '' });
		local Int is pc: :cstrOf(s: path);
		if({ pc == 0 }, {
			if({ :hasClosure(cb: onError) }, { onError(SpecError:init(kind: FileError:INVALID_PATH, description: 'invalid path')); });
			return defStr;
		});
		local Int is lenBuf: Mem:alloc(bytes: 8);
		local Int is bufAddr: base:sysinternal:File:pal_file_read(path_cstr: pc, out_len_addr: lenBuf);
		local Int is len: Mem:loadI64(ptr: lenBuf, byteOffset: 0);
		Mem:free(ptr: lenBuf);
		if({ bufAddr < 0 }, {
			if({ bufAddr == -2 }, {
				if({ :hasClosure(cb: onError) }, { onError(SpecError:init(kind: FileError:OUT_OF_MEMORY, description: 'out of memory')); });
			}, {
				:emitLastError(kind: FileError:IO_ERROR, onError: onError, fallback: 'read failed');
			});
			return defStr;
		});
		local String is res: Mem:strFromBytes(srcAddr: bufAddr, len: len);
		base:sysinternal:File:pal_file_free(ptr: bufAddr);
		if({ :hasClosure(cb: onSuccess) }, {
			onSuccess(res);
		});
		return res;
	}

	## Reads a file asynchronously inside [scope], notifying completion via callbacks and returning the [Task].
	Function of Task of String is fileReadAsync(ThreadScope is scope, String is path, Function is onSuccess, Function is onError, String is default: ''){
		return scope:spawn(task: local Function of String(){
			return :fileRead(path: path, onSuccess: onSuccess, onError: onError, default: default);
		});
	}

	local Function of Boolean is writeInternal(String is path, String is content, Int is append, Function is onSuccess, Function is onError){
		local Int is pc: :cstrOf(s: path);
		if({ pc == 0 }, {
			if({ :hasClosure(cb: onError) }, { onError(SpecError:init(kind: FileError:INVALID_PATH, description: 'invalid path')); });
			return false;
		});
		local Int is cAddr: Mem:objToAddr(obj: content);
		local Int is dAddr: if({ cAddr != 0 }, { Mem:loadI64(ptr: cAddr, byteOffset: 0) }, { 0 });
		local Int is cLen: if({ cAddr != 0 }, { Mem:loadI64(ptr: cAddr, byteOffset: 8) }, { 0 });
		local Int is written: base:sysinternal:File:pal_file_write(path_cstr: pc, data_addr: dAddr, len: cLen, append: append);
		if({ written < 0 }, {
			:emitLastError(kind: FileError:IO_ERROR, onError: onError, fallback: 'write failed');
			return false;
		});
		if({ :hasClosure(cb: onSuccess) }, {
			onSuccess(written);
		});
		return true;
	}

	## Writes string content to a file with optional success and error callback handlers.
	Function of Boolean is fileWrite(String is path, String is content, Function is onSuccess, Function is onError){
		return :writeInternal(path: path, content: content, append: 0, onSuccess: onSuccess, onError: onError);
	}

	## Appends string content to a file with optional success and error callback handlers.
	Function of Boolean is fileAppend(String is path, String is content, Function is onSuccess, Function is onError){
		return :writeInternal(path: path, content: content, append: 1, onSuccess: onSuccess, onError: onError);
	}

	## Writes string content to a file asynchronously inside [scope], notifying completion via callbacks and returning the [Task].
	Function of Task of Boolean is fileWriteAsync(ThreadScope is scope, String is path, String is content, Function is onSuccess, Function is onError){
		return scope:spawn(task: local Function of Boolean(){
			return :fileWrite(path: path, content: content, onSuccess: onSuccess, onError: onError);
		});
	}

	## Tests whether a file or directory exists at the specified path.
	Function of Boolean is fileExists(String is path){
		local Int is pc: :cstrOf(s: path);
		if({ pc == 0 }, { return false; });
		return base:sysinternal:File:pal_file_exists(path_cstr: pc);
	}

	## Deletes a file at the specified filesystem path.
	Function of Boolean is fileRemove(String is path, Function is onError: local Function(String is error){}){
		local Int is pc: :cstrOf(s: path);
		if({ pc == 0 }, {
			if({ :hasClosure(cb: onError) }, { onError(SpecError:init(kind: FileError:INVALID_PATH, description: 'invalid path')); });
			return false;
		});
		if({ base:sysinternal:File:pal_file_remove(path_cstr: pc) }, {
			return true;
		});
		:emitLastError(kind: FileError:IO_ERROR, onError: onError, fallback: 'remove failed');
		return false;
	}

	## Creates a unique temporary file securely and returns its path.
	Function of String is fileTemp(String is template: '/tmp/spec_XXXXXX.c', Function is onError: local Function(String is error){}){
		local Int is tc: :cstrOf(s: template);
		local Int is outAddr: base:sysinternal:File:pal_file_temp(tpl_cstr: tc);
		if({ outAddr == 0 }, {
			:emitLastError(kind: FileError:IO_ERROR, onError: onError, fallback: 'mkstemp failed');
			return '';
		});
		local Int is olen: Mem:cstrLen(cstrAddr: outAddr);
		local String is res: Mem:strFromBytes(srcAddr: outAddr, len: olen);
		base:sysinternal:File:pal_file_free(ptr: outAddr);
		return res;
	}
}
