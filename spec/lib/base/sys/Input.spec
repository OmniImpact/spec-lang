#! Package base:sys
#! The console input wrapper over the console floor's read primitives.

Class is Input{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', InputHandler],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', Console]
	];

	local Function of Boolean is hasClosure(Function is cb){
		local Int is addr: Mem:objToAddr(obj: cb);
		if({ addr == 0 }, { return false; });
		return Mem:loadI64(ptr: addr, byteOffset: 0) != 0;
	}

	## Reads one line of console input and dispatches it to
	## [handler]'s onInput; at end of input nothing is dispatched.
	##
	## @param handler: An [InputHandler] subclass responding to user input events.
	Function is consIn(InputHandler is handler){
		self:readLine(onLine: local Function(String is text){
			handler:onInput(text);
		});
	}

	## Reads one line from standard input and passes it to [onLine].
	Function is readLine(Function is onLine){
		local Int is lenBuf: Mem:alloc(bytes: 8);
		local Int is lineAddr: base:sysinternal:Console:pal_read_line(out_len_addr: lenBuf);
		local Int is len: Mem:loadI64(ptr: lenBuf, byteOffset: 0);
		Mem:free(ptr: lenBuf);
		if({ lineAddr != 0 }, {
			local String is text: Mem:strFromBytes(srcAddr: lineAddr, len: len);
			base:sysinternal:Console:pal_console_free(ptr: lineAddr);
			if({ self:hasClosure(cb: onLine) }, {
				onLine(text);
			});
		});
	}

	## Reads up to [count] raw bytes from standard input.
	Function of String is readBytes(Int is count){
		if({ count <= 0 }, { return ''; });
		local Int is buf: Mem:alloc(bytes: count);
		local Int is got: base:sysinternal:Console:pal_read_bytes(dst_addr: buf, count: count);
		local String is res: Mem:strFromBytes(srcAddr: buf, len: got);
		Mem:free(ptr: buf);
		return res;
	}

	## Switches stdin and stdout to binary mode (required for framed protocols on Windows).
	Function is setBinaryMode(){
		base:sysinternal:Console:console_binary_mode();
	}
}
