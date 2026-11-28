#! Package base:sys
#! The console input wrapper over the console floor's read primitives.

Class is Input{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'sys', InputHandler],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', Console]
	];

	## Reads one line of console input and dispatches it to
	## [handler]'s onInput; at end of input nothing is dispatched.
	##
	## @param handler: An [InputHandler] subclass responding to user input events.
	Function is consIn(InputHandler is handler){
		:readLine(onLine: local Function(String is text){
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
			if({ Mem:hasClosure(cb: onLine) }, {
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

	## Enables or disables raw terminal input mode (registers an exit restore guard).
	Function is setRawMode(Boolean is enabled){
		local Int is flag: 0;
		if({ enabled }, { flag: 1; });
		base:sysinternal:Console:pal_raw_mode(enable: flag);
	}

	## Polls stdin for a single byte up to [timeoutMs] milliseconds (-1 when timed out or EOF).
	Function of Int is pollByte(Int is timeoutMs: 0){
		return base:sysinternal:Console:pal_poll_byte(timeout_ms: timeoutMs);
	}
}
