#! Package base:sys
#! The console output wrapper: the Spec-side names over the console floor.

Class is Output{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', Console]
	];

	## Writes text to standard output followed by a newline.
	##
	## @param text: Text string to print.
	Function is line(String is text){
		local Int is sAddr: Mem:objToAddr(obj: text);
		local Int is dAddr: if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 0) }, { 0 });
		local Int is len: if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 8) }, { 0 });
		base:sysinternal:Console:pal_print_line(data_addr: dAddr, len: len);
	}

	## Writes text to standard output without a trailing newline and
	## flushes stdout.
	##
	## @param text: Text string to write inline.
	Function is consOut(String is text){
		local Int is sAddr: Mem:objToAddr(obj: text);
		local Int is dAddr: if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 0) }, { 0 });
		local Int is len: if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 8) }, { 0 });
		base:sysinternal:Console:pal_print(data_addr: dAddr, len: len);
	}
}
