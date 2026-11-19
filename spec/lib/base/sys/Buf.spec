#! Package base:sys
#! Generic byte-buffer operations implemented in pure Spec over Mem.

Class is Buf{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		['base', 'struct', Array]
	];

	## Number of bytes held by this buffer.
	##
	## @return: Byte count.
	Function of Int is length(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return 0; });
		return Mem:loadI64(ptr: addr, byteOffset: 8);
	}

	## Number of bytes held by this buffer (explicit byte-length alias for [length]).
	##
	## @return: Byte count.
	Function of Int is byteLength(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return 0; });
		return Mem:loadI64(ptr: addr, byteOffset: 8);
	}

	## Raw byte value (0..255) at [index], or [default] when out of bounds.
	##
	## @param index: Zero-based byte index.
	## @param default: Fallback when [index] is out of bounds.
	## @return: The byte value, or [default].
	Function of Int is byteAt(Int is index, Int is default: -1){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return default; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ index < 0 || index >= len }, { return default; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:loadByte(ptr: data, byteOffset: index);
	}

	## Count occurrences of [byteVal] in this buffer.
	##
	## @param byteVal: Target byte value.
	## @return: Occurrence count.
	Function of Int is countByte(Int is byteVal){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return 0; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return 0; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is target: byteVal & 255;
		local Int is count: 0;
		local Int is i: 0;
		while({ i < len }, {
			if({ Mem:loadByte(ptr: data, byteOffset: i) == target }, {
				count: count + 1;
			});
			i: i + 1;
		});
		return count;
	}

	## Appends the bytes of [src] to the end of [dst] in place. [dst] must
	## be a mutable (non-interned) buffer — the accumulator's sole owner.
	##
	## @param dst: The buffer grown in place.
	## @param src: The bytes appended.
	Function is bufAppendBuf(Buf is dst, Buf is src){
		local Int is dAddr: Mem:objToAddr(obj: dst);
		local Int is sAddr: Mem:objToAddr(obj: src);
		if({ dAddr == 0 || sAddr == 0 }, { return; });
		local Int is sLen: Mem:loadI64(ptr: sAddr, byteOffset: 8);
		if({ sLen <= 0 }, { return; });
		local Int is dLen: Mem:loadI64(ptr: dAddr, byteOffset: 8);
		local Int is dCap: Mem:loadI64(ptr: dAddr, byteOffset: 16);
		local Int is need: sLen + 1;
		local Int is dData: Mem:loadI64(ptr: dAddr, byteOffset: 0);
		if({ dData != dAddr + 36 }, {
			local Int is oldCk: Mem:loadI64(ptr: dAddr, byteOffset: 40);
			if({ oldCk > 0 }, {
				Mem:free(ptr: oldCk);
				Mem:storeI64(ptr: dAddr, byteOffset: 40, val: 0);
			});
		});
		if({ dLen + need > dCap }, {
			local Int is cap: if({ dCap == 0 }, { 16 }, { dCap * 2 });
			while({ cap < dLen + need }, {
				cap: cap * 2;
			});
			if({ dData == dAddr + 36 }, {
				local Int is newData: Mem:alloc(bytes: cap);
				if({ dLen > 0 }, { Mem:copy(dst: newData, src: dData, bytes: dLen); });
				Mem:storeI64(ptr: dAddr, byteOffset: 40, val: 0);
				Mem:storeI64(ptr: dAddr, byteOffset: 48, val: 0);
				dData: newData;
			}, {
				dData: Mem:realloc(ptr: dData, bytes: cap);
			});
			Mem:storeI64(ptr: dAddr, byteOffset: 0, val: dData);
			Mem:storeI64(ptr: dAddr, byteOffset: 16, val: cap);
		});
		local Int is sData: Mem:loadI64(ptr: sAddr, byteOffset: 0);
		if({ dAddr == sAddr }, {
			Mem:copy(dst: dData + dLen, src: dData, bytes: sLen);
		}, {
			Mem:copy(dst: dData + dLen, src: sData, bytes: sLen);
		});
		local Int is newLen: dLen + sLen;
		Mem:storeI64(ptr: dAddr, byteOffset: 8, val: newLen);
		Mem:storeByte(ptr: dData, byteOffset: newLen, val: 0);
	}
}
