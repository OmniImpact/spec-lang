#! Package base:sys
#! The diagnostics wrapper over the console floor's error-line primitive.

Class is Stderr{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', Console]
	];

	## Writes text to standard error followed by a newline.
	##
	## @param text: Text string to write.
	Function is line(String is text){
		local Int is sAddr: Mem:objToAddr(obj: text);
		local Int is dAddr: if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 0) }, { 0 });
		local Int is len: if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 8) }, { 0 });
		base:sysinternal:Console:pal_error_line(data_addr: dAddr, len: len);
	}
}
