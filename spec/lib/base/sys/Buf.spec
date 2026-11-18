#! Package base:sys
#! Public byte-buffer and string operations implemented in pure Spec over Mem.

Class is Buf{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		['base', 'struct', Array]
	];

	## Number of bytes held by the buffer [b].
	##
	## @param b: The buffer.
	## @return: Byte count.
	Function of Int is bufLength(String is b){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, { return 0; });
		return Mem:loadI64(ptr: addr, byteOffset: 8);
	}

	## Byte value at [idx], or [def] when out of bounds.
	##
	## @param b: The buffer.
	## @param idx: Zero-based byte index.
	## @param def: Fallback when [idx] is out of bounds.
	## @return: The byte value, or [def].
	Function of Int is bufGetByte(String is b, Int is idx, Int is def){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, { return def; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, { return def; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:loadByte(ptr: data, byteOffset: idx);
	}

	## Count occurrences of [byteVal] in buffer [b].
	##
	## @param b: The buffer.
	## @param byteVal: Target byte value.
	## @return: Occurrence count.
	Function of Int is bufCountByte(String is b, Int is byteVal){
		local Int is addr: Mem:objToAddr(obj: b);
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

	## Refcounted copy of buffer [b].
	##
	## @param b: The buffer.
	## @return: An owned copy sharing no storage with [b].
	Function of String is stringCopy(String is b){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, { return Mem:strFromBytes(srcAddr: 0, len: 0); });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return Mem:strFromBytes(srcAddr: 0, len: 0); });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:strFromBytes(srcAddr: data, len: len);
	}

	## Concatenation of strings [a] and [b].
	##
	## @param a: First string.
	## @param b: Second string.
	## @return: Newly allocated string containing [a] followed by [b].
	Function of String is stringConcat(String is a, String is b){
		local Int is aAddr: Mem:objToAddr(obj: a);
		local Int is bAddr: Mem:objToAddr(obj: b);
		local Int is aLen: if({ aAddr == 0 }, { 0 }, { Mem:loadI64(ptr: aAddr, byteOffset: 8) });
		local Int is bLen: if({ bAddr == 0 }, { 0 }, { Mem:loadI64(ptr: bAddr, byteOffset: 8) });
		local Int is total: aLen + bLen;
		if({ total == 0 }, { return ''; });
		if({ aLen == 0 }, { return :stringCopy(b: b); });
		if({ bLen == 0 }, { return :stringCopy(b: a); });
		local Int is aData: Mem:loadI64(ptr: aAddr, byteOffset: 0);
		local Int is bData: Mem:loadI64(ptr: bAddr, byteOffset: 0);
		if({ total <= 256 }, {
			local Int is scratch: Mem:tlsGetI64(slot: 2);
			if({ scratch == 0 }, {
				scratch: Mem:alloc(bytes: 256);
				Mem:tlsSetI64(slot: 2, val: scratch);
			});
			Mem:copy(dst: scratch, src: aData, bytes: aLen);
			Mem:copy(dst: scratch + aLen, src: bData, bytes: bLen);
			return Mem:strFromBytes(srcAddr: scratch, len: total);
		});
		local String is out: Mem:strFromBytes(srcAddr: aData, len: aLen);
		:bufAppendBuf(dst: out, src: b);
		return out;
	}

	## Byte-for-byte equality of strings [a] and [b].
	##
	## @param a: First string.
	## @param b: Second string.
	## @return: true when [a] and [b] have identical length and bytes.
	Function of Boolean is stringEquals(String is a, String is b){
		local Int is aAddr: Mem:objToAddr(obj: a);
		local Int is bAddr: Mem:objToAddr(obj: b);
		if({ aAddr == bAddr }, { return true; });
		if({ aAddr == 0 || bAddr == 0 }, { return false; });
		local Int is aLen: Mem:loadI64(ptr: aAddr, byteOffset: 8);
		local Int is bLen: Mem:loadI64(ptr: bAddr, byteOffset: 8);
		if({ aLen != bLen }, { return false; });
		if({ aLen == 0 }, { return true; });
		local Int is aData: Mem:loadI64(ptr: aAddr, byteOffset: 0);
		local Int is bData: Mem:loadI64(ptr: bAddr, byteOffset: 0);
		return Mem:cmp(a: aData, b: bData, bytes: aLen) == 0;
	}

	## Lexicographical byte comparison of strings [a] and [b].
	##
	## @param a: First string.
	## @param b: Second string.
	## @return: Negative when [a] < [b], 0 when equal, positive when [a] > [b].
	Function of Int is stringCompare(String is a, String is b){
		local Int is aAddr: Mem:objToAddr(obj: a);
		local Int is bAddr: Mem:objToAddr(obj: b);
		if({ aAddr == bAddr }, { return 0; });
		if({ aAddr == 0 }, { return if({ bAddr != 0 }, { -1 }, { 0 }); });
		if({ bAddr == 0 }, { return 1; });
		local Int is aLen: Mem:loadI64(ptr: aAddr, byteOffset: 8);
		local Int is bLen: Mem:loadI64(ptr: bAddr, byteOffset: 8);
		local Int is n: if({ aLen < bLen }, { aLen }, { bLen });
		if({ n > 0 }, {
			local Int is aData: Mem:loadI64(ptr: aAddr, byteOffset: 0);
			local Int is bData: Mem:loadI64(ptr: bAddr, byteOffset: 0);
			local Int is c: Mem:cmp(a: aData, b: bData, bytes: n);
			if({ c != 0 }, { return c; });
		});
		return aLen - bLen;
	}

	## Returns the process-interned form of [s]: equal contents yield
	## the SAME string object. Interned strings are immortal.
	##
	## @param s: The string.
	## @return: The interned string.
	Function of String is intern(String is s){
		return Mem:internStr(s: s);
	}

	## Bytes [start] (inclusive) to [end] (exclusive) of buffer [b].
	##
	## @param b: The buffer.
	## @param start: Inclusive start index.
	## @param end: Exclusive end index.
	## @return: The sub-buffer.
	Function of String is stringSubstring(String is b, Int is start, Int is end){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, { return Mem:strFromBytes(srcAddr: 0, len: 0); });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is s: if({ start < 0 }, { 0 }, { start });
		local Int is e: if({ end > len }, { len }, { end });
		if({ s >= e }, { return Mem:strFromBytes(srcAddr: 0, len: 0); });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:strFromBytes(srcAddr: data + s, len: e - s);
	}

	## First index of [needle] within buffer [b], or [def] when absent.
	##
	## @param b: The buffer.
	## @param needle: Byte sequence to locate.
	## @param def: Fallback when absent (conventionally -1).
	## @return: The index, or [def].
	Function of Int is stringIndexOf(String is b, String is needle, Int is def){
		return :stringIndexOfFrom(b: b, needle: needle, from: 0, def: def);
	}

	## First index of [needle] within buffer [b] at or after [from], or [def] when absent.
	##
	## @param b: The buffer.
	## @param needle: Byte sequence to locate.
	## @param from: Zero-based start position.
	## @param def: Fallback when absent (conventionally -1).
	## @return: The index, or [def].
	Function of Int is stringIndexOfFrom(String is b, String is needle, Int is from, Int is def){
		local Int is bAddr: Mem:objToAddr(obj: b);
		local Int is nAddr: Mem:objToAddr(obj: needle);
		if({ bAddr == 0 || nAddr == 0 }, { return def; });
		local Int is start: from;
		if({ start < 0 }, { start: 0; });
		local Int is slen: Mem:loadI64(ptr: bAddr, byteOffset: 8);
		local Int is nlen: Mem:loadI64(ptr: nAddr, byteOffset: 8);
		if({ nlen == 0 }, {
			if({ start <= slen }, { return start; });
			return def;
		});
		if({ start + nlen > slen }, { return def; });
		local Int is hay: Mem:loadI64(ptr: bAddr, byteOffset: 0);
		local Int is nd: Mem:loadI64(ptr: nAddr, byteOffset: 0);
		local Int is firstByte: Mem:loadByte(ptr: nd, byteOffset: 0);
		local Int is i: start;
		while({ i + nlen <= slen }, {
			if({ Mem:loadByte(ptr: hay, byteOffset: i) == firstByte }, {
				if({ Mem:cmp(a: hay + i, b: nd, bytes: nlen) == 0 }, {
					return i;
				});
			});
			i: i + 1;
		});
		return def;
	}

	## Buffer [b] with every [search] occurrence replaced by [replacement].
	##
	## @param b: The buffer.
	## @param search: Sequence to replace.
	## @param replacement: Replacement sequence.
	## @return: The replaced copy.
	Function of String is stringReplaceAll(String is b, String is search, String is replacement){
		return b:replaceAll(search: search, replacement: replacement);
	}

	## Buffer [b] with leading/trailing space, tab, newline, CR removed.
	##
	## @param b: The buffer.
	## @return: The trimmed copy.
	Function of String is stringTrim(String is b){
		return b:trim();
	}

	## True when [b] is non-empty and every byte is a digit.
	##
	## @param b: The buffer.
	## @return: true when all digits.
	Function of Boolean is stringIsDigit(String is b){
		return b:isDigit();
	}

	## True when [b] is non-empty and every byte is a letter.
	##
	## @param b: The buffer.
	## @return: true when all letters.
	Function of Boolean is stringIsAlpha(String is b){
		return b:isAlpha();
	}

	## True when [b] is non-empty and every byte is whitespace.
	##
	## @param b: The buffer.
	## @return: true when all whitespace.
	Function of Boolean is stringIsWhitespace(String is b){
		return b:isWhitespace();
	}

	## Number of leading [search] repetitions in buffer [b].
	##
	## @param b: The buffer.
	## @param search: The repetition unit.
	## @return: Repetition count.
	Function of Int is stringCountLeading(String is b, String is search){
		return b:countLeading(search: search);
	}

	## Parts of buffer [b] split on [delimiter]; the trailing part is
	## always present. Empty delimiter: every byte is its own part.
	##
	## @param b: The buffer.
	## @param delimiter: Split boundary.
	## @return: The parts.
	Function of Array of String is stringSplit(String is b, String is delimiter){
		return b:split(delimiter: delimiter);
	}

	## Lines of buffer [b] (split on newline, trailing CR stripped).
	##
	## @param b: The buffer.
	## @return: The lines.
	Function of Array of String is stringLines(String is b){
		return b:lines();
	}

	## Appends the bytes of [src] to the end of [dst] in place. [dst] must
	## be a mutable (non-interned) buffer — the accumulator's sole owner.
	##
	## @param dst: The buffer grown in place.
	## @param src: The bytes appended.
	Function is bufAppendBuf(String is dst, String is src){
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
			if({ oldCk != 0 }, {
				if({ oldCk > 0 }, {
					Mem:free(ptr: oldCk);
				});
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

	## Parses buffer [b] as an integer in [base] (2-36), accepting 0x/0b/0o
	## prefixes and _ separators. Returns [def] on any invalid input.
	##
	## @param b: The buffer.
	## @param base: Number base (2-36).
	## @param def: Fallback on invalid input.
	## @return: The parsed value, or [def].
	Function of Int is parseBase(String is b, Int is base, Int is def){
		return b:parseInt(base: base, default: def);
	}

	## Decimal string representation of signed integer [v].
	##
	## @param v: Integer value.
	## @return: Decimal string.
	Function of String is intToString(Int is v){
		if({ v == 0 }, { return '0'; });
		local Int is buf: Mem:tlsGetI64(slot: 1);
		if({ buf == 0 }, {
			buf: Mem:alloc(bytes: 32);
			Mem:tlsSetI64(slot: 1, val: buf);
		});
		local Int is idx: 32;
		local Boolean is neg: v < 0;
		local Int is u: v;
		if({ neg }, {
			local Int is rem0: 0 - (u % 10);
			u: 0 - (u / 10);
			idx: idx - 1;
			Mem:storeByte(ptr: buf, byteOffset: idx, val: 48 + rem0);
		});
		while({ u > 0 }, {
			local Int is rem: u % 10;
			u: u / 10;
			idx: idx - 1;
			Mem:storeByte(ptr: buf, byteOffset: idx, val: 48 + rem);
		});
		if({ neg }, {
			idx: idx - 1;
			Mem:storeByte(ptr: buf, byteOffset: idx, val: 45);
		});
		return Mem:strFromBytes(srcAddr: buf + idx, len: 32 - idx);
	}

	## Formats integer [v] in [base] (2-36), zero-padded to at least [digits] digits.
	Function of String is intToBase(Int is v, Int is base, Int is digits){
		local Int is b: if({ base < 2 || base > 36 }, { 10 }, { base });
		local Int is minDig: if({ digits < 0 }, { 0 }, { digits });
		local Int is cap: if({ minDig + 4 > 80 }, { minDig + 4 }, { 80 });
		local Int is scratch: Mem:alloc(bytes: cap);
		local Int is idx: cap;
		local Boolean is neg: v < 0;
		local Int is u: v;
		if({ u == 0 }, {
			idx: idx - 1;
			Mem:storeByte(ptr: scratch, byteOffset: idx, val: 48);
		}, {
			if({ neg }, {
				local Int is rem0: 0 - (u % b);
				u: 0 - (u / b);
				idx: idx - 1;
				local Int is ch0: if({ rem0 < 10 }, { 48 + rem0 }, { 87 + rem0 });
				Mem:storeByte(ptr: scratch, byteOffset: idx, val: ch0);
			});
			while({ u > 0 }, {
				local Int is rem: u % b;
				u: u / b;
				idx: idx - 1;
				local Int is ch: if({ rem < 10 }, { 48 + rem }, { 87 + rem });
				Mem:storeByte(ptr: scratch, byteOffset: idx, val: ch);
			});
		});
		while({ (cap - idx) < minDig && idx > 1 }, {
			idx: idx - 1;
			Mem:storeByte(ptr: scratch, byteOffset: idx, val: 48);
		});
		if({ neg && idx > 0 }, {
			idx: idx - 1;
			Mem:storeByte(ptr: scratch, byteOffset: idx, val: 45);
		});
		local String is out: Mem:strFromBytes(srcAddr: scratch + idx, len: cap - idx);
		Mem:free(ptr: scratch);
		return out;
	}
}
