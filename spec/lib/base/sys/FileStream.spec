#! Package base:sys
#! Streaming binary/text file reader and writer over `base:sys:File` raw stream handles.

Class is FileStream{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'struct', List],
		['base', 'sys', File],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Int is handle: 0;

	local Function of Int is cstrOf(String is s){
		local Int is sAddr: Mem:objToAddr(obj: s);
		if({ sAddr == 0 || Mem:loadI64(ptr: sAddr, byteOffset: 8) == 0 }, { return 0; });
		return Mem:loadI64(ptr: sAddr, byteOffset: 0);
	}

	replace Function is init(){
		:handle: 0;
	}

	Function is destroy(){
		:close();
	}

	## Opens [path] with C stdio [mode] (`'rb'`, `'wb'`, `'ab'`, `'r+b'`).
	Function of Boolean is open(String is path, String is mode: 'rb'){
		:close();
		local Int is pc: :cstrOf(s: path);
		local Int is mc: :cstrOf(s: mode);
		if({ pc == 0 || mc == 0 }, { return false; });
		:handle: File:rawOpen(pathCstr: pc, modeCstr: mc);
		return :handle != 0;
	}

	Function of Boolean is isOpen(){ :handle != 0 }

	## Reads up to [maxBytes] into a `List of Byte`. Empty list on EOF or error.
	Function of List of Byte is readBytes(Int is maxBytes: 4096){
		local List of Byte is out;
		if({ :handle == 0 || maxBytes <= 0 }, { return out; });
		local Int is buf: Mem:alloc(bytes: maxBytes);
		local Int is n: File:rawReadChunk(handle: :handle, dstAddr: buf, maxBytes: maxBytes);
		if({ n <= 0 }, {
			Mem:free(ptr: buf);
			return out;
		});
		out:adoptRawBuffer(dataPtr: buf, length: n, capacity: maxBytes);
		return out;
	}

	## Reads up to [maxBytes] as a UTF-8 String.
	Function of String is readString(Int is maxBytes: 4096){
		local List of Byte is b: :readBytes(maxBytes: maxBytes);
		return b:toString();
	}

	## Writes raw bytes [data] to the stream; returns bytes written or -1 on error.
	Function of Int is writeBytes(List of Byte is data){
		if({ :handle == 0 }, { return -1; });
		local Int is len: data:length();
		if({ len <= 0 }, { return 0; });
		return File:rawWriteChunk(handle: :handle, srcAddr: data:rawDataAddr(), len: len);
	}

	## Writes UTF-8 [text] to the stream; returns bytes written or -1 on error.
	Function of Int is writeString(String is text){
		if({ :handle == 0 }, { return -1; });
		local Int is sAddr: Mem:objToAddr(obj: text);
		if({ sAddr == 0 }, { return 0; });
		local Int is dataPtr: Mem:loadI64(ptr: sAddr, byteOffset: 0);
		local Int is len: Mem:loadI64(ptr: sAddr, byteOffset: 8);
		if({ len <= 0 }, { return 0; });
		return File:rawWriteChunk(handle: :handle, srcAddr: dataPtr, len: len);
	}

	## Seeks to [offset] (`whence`: 0=SET, 1=CUR, 2=END).
	Function of Boolean is seek(Int is offset, Int is whence: 0){
		if({ :handle == 0 }, { return false; });
		return File:rawSeek(handle: :handle, offset: offset, whence: whence) == 0;
	}

	## Returns current byte offset, or -1 if closed/error.
	Function of Int is tell(){
		if({ :handle == 0 }, { return -1; });
		return File:rawTell(handle: :handle);
	}

	Function of Boolean is flush(){
		if({ :handle == 0 }, { return false; });
		return File:rawFlush(handle: :handle) == 0;
	}

	Function is close(){
		if({ :handle != 0 }, {
			File:rawClose(handle: :handle);
			:handle: 0;
		});
	}
}
