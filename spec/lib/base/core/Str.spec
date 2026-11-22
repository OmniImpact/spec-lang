#! Package base:core
#! The Str type: a lightweight, UTF-8-safe byte string over Buf.
##
## Str sits between raw `Buf` and full-Unicode `String` (`Buf -> Str -> String`).
## It provides the fast byte/ASCII string operations plus UTF-8 validation,
## sanitization (`sanitizeUtf8`), and boundary-safe byte slicing (`sliceUtf8`)
## without any Unicode table or checkpoint overhead.

Class of Buf is Str{
	namespace: ['base', 'core'];

	## Runtime binding: the implementations for this class's
	## declaration-only methods live in the runtime floor; the backend
	## emits no struct, vtable, or constructor for it.
	binding: true;

	replace Array of Array of String is using: [
		['base', 'sys', Buf],
		['base', 'sys', as Buf()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	## Declared casts: a Str produces an Int through its parser.
	castable: [
		[Int, parseInt]
	];

	## Number of bytes in this string.
	##
	## @return: Byte count.
	replace Function of Int is length(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return 0; });
		return Mem:loadI64(ptr: addr, byteOffset: 8);
	}

	## Returns whether this string has zero bytes.
	##
	## @return: `true` if empty, `false` otherwise.
	Function of Boolean is isEmpty(){
		return :length() == 0;
	}

	## Number of bytes in this string (explicit byte-length alias for [length]).
	##
	## @return: Byte count.
	replace Function of Int is byteLength(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return 0; });
		return Mem:loadI64(ptr: addr, byteOffset: 8);
	}

	## Raw byte value (0..255) at [index], or [default] when out of bounds.
	##
	## @param index: Zero-based byte index.
	## @param default: Fallback when out of bounds.
	## @return: Byte value, or [default].
	replace Function of Int is byteAt(Int is index, Int is default: -1){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return default; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ index < 0 || index >= len }, { return default; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:loadByte(ptr: data, byteOffset: index);
	}

	## Raw byte value (0..255) at [index], or [default] when out of bounds.
	##
	## @param index: Zero-based byte index.
	## @param default: Fallback when out of bounds.
	## @return: Byte value, or [default].
	Function of Int is charCodeAt(Int is index, Int is default: -1){
		return :byteAt(index: index, default: default);
	}

	## Refcounted copy of this string.
	##
	## @return: An owned copy sharing no storage with this string.
	Function of String is copy(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return Mem:strFromBytes(srcAddr: 0, len: 0); });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return Mem:strFromBytes(srcAddr: 0, len: 0); });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:strFromBytes(srcAddr: data, len: len);
	}

	## Returns the process-interned form of this string: equal contents yield
	## the SAME string object. Interned strings are immortal.
	##
	## @return: The interned string.
	Function of String is intern(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return ''; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:internStr(s: Mem:strFromBytes(srcAddr: data, len: len));
	}

	## Byte-for-byte equality of strings [a] and [b].
	##
	## @param a: First string.
	## @param b: Second string.
	## @return: true when [a] and [b] have identical length and bytes.
	Function of Boolean is stringEquals(Str is a, Str is b){
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
	Function of Int is stringCompare(Str is a, Str is b){
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

	## One-byte string at [index], or [default] when out of bounds.
	##
	## @param index: Zero-based byte index.
	## @param default: Fallback when out of bounds.
	## @return: The character, or [default].
	Function of String is charAt(Int is index, String is default: ''){
		if({ index < 0 || index >= :length() }, {
			return default:copy();
		});
		return :fromCharCode(code: :byteAt(index: index, default: -1));
	}

	## Bytes from [start] (inclusive) to [end] (exclusive), clamped to bounds.
	##
	## @param start: Inclusive start byte index.
	## @param end: Exclusive end byte index.
	## @return: The sub-string.
	Function of String is substring(Int is start, Int is end){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return Mem:strFromBytes(srcAddr: 0, len: 0); });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is s: if({ start < 0 }, { 0 }, { start });
		local Int is e: if({ end > len }, { len }, { end });
		if({ s >= e }, { return Mem:strFromBytes(srcAddr: 0, len: 0); });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:strFromBytes(srcAddr: data + s, len: e - s);
	}

	local Function of Int is asciiLowerByte(Int is b){
		if({ b >= 65 && b <= 90 }, {
			return b + 32;
		});
		return b;
	}

	local Function of Boolean is bytesEqualAt(Int is hayPtr, Int is hayOffset, Int is ndPtr, Int is len, Boolean is caseSensitive){
		if({ caseSensitive }, {
			return Mem:cmp(a: hayPtr + hayOffset, b: ndPtr, bytes: len) == 0;
		});
		local Int is j: 0;
		while({ j < len }, {
			local Int is a: :asciiLowerByte(b: Mem:loadByte(ptr: hayPtr, byteOffset: hayOffset + j));
			local Int is b: :asciiLowerByte(b: Mem:loadByte(ptr: ndPtr, byteOffset: j));
			if({ a != b }, {
				return false;
			});
			j: j + 1;
		});
		return true;
	}

	## True when this string equals [other] (optionally case-insensitive for ASCII).
	Function of Boolean is equals(Str is other, Boolean is caseSensitive: true){
		if({ caseSensitive }, {
			return : == other;
		});
		local Int is len: :length();
		if({ len != other:length() }, {
			return false;
		});
		if({ len == 0 }, {
			return true;
		});
		local Int is aAddr: Mem:objToAddr(obj: :);
		local Int is bAddr: Mem:objToAddr(obj: other);
		if({ aAddr == 0 || bAddr == 0 }, { return false; });
		return :bytesEqualAt(
			hayPtr: Mem:loadI64(ptr: aAddr, byteOffset: 0),
			hayOffset: 0,
			ndPtr: Mem:loadI64(ptr: bAddr, byteOffset: 0),
			len: len,
			caseSensitive: false
		);
	}

	## True when this string begins with [prefix].
	##
	## @param prefix: The prefix to test.
	## @param caseSensitive: Whether ASCII case must match.
	## @return: true when present.
	Function of Boolean is startsWith(Str is prefix, Boolean is caseSensitive: true){
		local Int is pl: prefix:length();
		if({ pl == 0 }, {
			return true;
		});
		if({ pl > :length() }, {
			return false;
		});
		if({ caseSensitive }, {
			return :substring(start: 0, end: pl) == prefix;
		});
		return :substring(start: 0, end: pl):equals(other: prefix, caseSensitive: false);
	}

	## True when this string ends with [suffix].
	##
	## @param suffix: The suffix to test.
	## @param caseSensitive: Whether ASCII case must match.
	## @return: true when present.
	Function of Boolean is endsWith(Str is suffix, Boolean is caseSensitive: true){
		local Int is sl: suffix:length();
		if({ sl == 0 }, {
			return true;
		});
		local Int is bl: :length();
		if({ sl > bl }, {
			return false;
		});
		if({ caseSensitive }, {
			return :substring(start: bl - sl, end: bl) == suffix;
		});
		return :substring(start: bl - sl, end: bl):equals(other: suffix, caseSensitive: false);
	}

	## True when [needle] occurs anywhere in this string (empty needle: true).
	##
	## @param needle: Sequence to locate.
	## @param caseSensitive: Whether ASCII case must match.
	## @return: true when present.
	Function of Boolean is contains(Str is needle, Boolean is caseSensitive: true){
		return :indexOf(search: needle, default: -1, caseSensitive: caseSensitive) >= 0;
	}

	## First occurrence of [search] at or after [from], or [default] when absent.
	##
	## @param search: Byte sequence to locate.
	## @param from: Zero-based start position.
	## @param default: Fallback when absent (conventionally -1).
	## @param caseSensitive: Whether ASCII case must match.
	## @return: The index, or [default].
	Function of Int is indexOfFrom(Str is search, Int is from, Int is default: -1, Boolean is caseSensitive: true){
		local Int is bAddr: Mem:objToAddr(obj: :);
		local Int is nAddr: Mem:objToAddr(obj: search);
		if({ bAddr == 0 || nAddr == 0 }, { return default; });
		local Int is start: from;
		if({ start < 0 }, { start: 0; });
		local Int is slen: Mem:loadI64(ptr: bAddr, byteOffset: 8);
		local Int is nlen: Mem:loadI64(ptr: nAddr, byteOffset: 8);
		if({ nlen == 0 }, {
			if({ start <= slen }, { return start; });
			return default;
		});
		if({ start + nlen > slen }, { return default; });
		local Int is hay: Mem:loadI64(ptr: bAddr, byteOffset: 0);
		local Int is nd: Mem:loadI64(ptr: nAddr, byteOffset: 0);
		local Int is firstByte: Mem:loadByte(ptr: nd, byteOffset: 0);
		if({ !caseSensitive }, {
			firstByte: :asciiLowerByte(b: firstByte);
		});
		local Int is i: start;
		while({ i + nlen <= slen }, {
			local Int is hb: Mem:loadByte(ptr: hay, byteOffset: i);
			if({ !caseSensitive }, {
				hb: :asciiLowerByte(b: hb);
			});
			if({ hb == firstByte }, {
				if({ :bytesEqualAt(hayPtr: hay, hayOffset: i, ndPtr: nd, len: nlen, caseSensitive: caseSensitive) }, {
					return i;
				});
			});
			i: i + 1;
		});
		return default;
	}

	## First occurrence of [search] at or after the start, or [default].
	##
	## @param search: Sequence to locate.
	## @param default: Fallback when absent (conventionally -1).
	## @param caseSensitive: Whether ASCII case must match.
	## @return: The index, or [default].
	Function of Int is indexOf(Str is search, Int is default: -1, Boolean is caseSensitive: true){
		return :indexOfFrom(search: search, from: 0, default: default, caseSensitive: caseSensitive);
	}

	## First byte index of [needle] at or after [from], or [default] when absent.
	Function of Int is find(Str is needle, Int is from: 0, Int is default: -1, Boolean is caseSensitive: true){
		return :indexOfFrom(search: needle, from: from, default: default, caseSensitive: caseSensitive);
	}

	## All non-overlapping occurrences of [needle] in this string.
	Function of Array of String is findAll(Str is needle, Boolean is caseSensitive: true){
		local Array of String is out: [];
		local Int is nlen: needle:length();
		if({ nlen == 0 }, {
			return out;
		});
		local Int is pos: 0;
		local Int is idx: :indexOfFrom(search: needle, from: pos, default: -1, caseSensitive: caseSensitive);
		while({ idx >= 0 }, {
			out:add(item: :substring(start: idx, end: idx + nlen));
			pos: idx + nlen;
			idx: :indexOfFrom(search: needle, from: pos, default: -1, caseSensitive: caseSensitive);
		});
		return out;
	}

	## Number of non-overlapping occurrences of [needle] in this string.
	Function of Int is count(Str is needle, Boolean is caseSensitive: true){
		local Int is nlen: needle:length();
		if({ nlen == 0 }, {
			return 0;
		});
		local Int is total: 0;
		local Int is pos: 0;
		local Int is idx: :indexOfFrom(search: needle, from: pos, default: -1, caseSensitive: caseSensitive);
		while({ idx >= 0 }, {
			total: total + 1;
			pos: idx + nlen;
			idx: :indexOfFrom(search: needle, from: pos, default: -1, caseSensitive: caseSensitive);
		});
		return total;
	}

	## First [search] occurrence replaced by [replacement].
	Function of String is replaceFirst(Str is search, Str is replacement, Boolean is caseSensitive: true){
		local Int is slen: search:length();
		if({ slen == 0 }, {
			return :copy();
		});
		local Int is idx: :indexOfFrom(search: search, from: 0, default: -1, caseSensitive: caseSensitive);
		if({ idx < 0 }, {
			return :copy();
		});
		return :substring(start: 0, end: idx) . replacement . :substring(start: idx + slen, end: :length());
	}

	## First [search] occurrence replaced using [replacer] `(Str is match, Int is start, Int is end) -> Str`.
	Function of String is replaceWith(Str is search, Function of Str is replacer, Boolean is caseSensitive: true){
		local Int is slen: search:length();
		if({ slen == 0 }, {
			return :copy();
		});
		local Int is idx: :indexOfFrom(search: search, from: 0, default: -1, caseSensitive: caseSensitive);
		if({ idx < 0 }, {
			return :copy();
		});
		local Str is m: :substring(start: idx, end: idx + slen);
		local Str is rep: replacer(m, idx, idx + slen);
		return :substring(start: 0, end: idx) . rep . :substring(start: idx + slen, end: :length());
	}

	## Every [search] occurrence replaced by [replacement].
	##
	## @param search: Sequence to replace.
	## @param replacement: Replacement sequence.
	## @param caseSensitive: Whether ASCII case must match.
	## @return: The replaced copy.
	Function of String is replaceAll(Str is search, Str is replacement, Boolean is caseSensitive: true){
		local Int is slen: search:length();
		if({ slen == 0 }, {
			return :copy();
		});
		local Int is total: :length();
		local String is out: '';
		local Int is pos: 0;
		local Boolean is running: true;
		while({ running }, {
			local Int is idx: :indexOfFrom(search: search, from: pos, default: -1, caseSensitive: caseSensitive);
			if({ idx < 0 }, {
				running: false;
			}, {
				out: out . :substring(start: pos, end: idx) . replacement;
				pos: idx + slen;
			});
		});
		out: out . :substring(start: pos, end: total);
		return out;
	}

	## Every [search] occurrence replaced using [replacer] `(Str is match, Int is start, Int is end) -> Str`.
	Function of String is replaceAllWith(Str is search, Function of Str is replacer, Boolean is caseSensitive: true){
		local Int is slen: search:length();
		if({ slen == 0 }, {
			return :copy();
		});
		local Int is total: :length();
		local String is out: '';
		local Int is pos: 0;
		local Boolean is running: true;
		while({ running }, {
			local Int is idx: :indexOfFrom(search: search, from: pos, default: -1, caseSensitive: caseSensitive);
			if({ idx < 0 }, {
				running: false;
			}, {
				local Str is m: :substring(start: idx, end: idx + slen);
				local Str is rep: replacer(m, idx, idx + slen);
				out: out . :substring(start: pos, end: idx) . rep;
				pos: idx + slen;
			});
		});
		out: out . :substring(start: pos, end: total);
		return out;
	}

	## Splits on [delimiter] (at most [limit] parts when `limit > 0`); the trailing part is always present.
	##
	## @param delimiter: Split boundary.
	## @param limit: Maximum number of parts (`-1` for unlimited).
	## @param caseSensitive: Whether ASCII case must match.
	## @return: The parts.
	Function of Array of String is split(Str is delimiter, Int is limit: -1, Boolean is caseSensitive: true){
		local Array of String is res: [];
		local Int is slen: :length();
		if({ slen == 0 }, {
			return res;
		});
		if({ limit == 1 }, {
			res:add(item: :copy());
			return res;
		});
		local Int is dlen: delimiter:length();
		if({ dlen == 0 }, {
			local Int is i: 0;
			while({ i < slen }, {
				if({ limit > 0 && res:length() + 1 >= limit }, {
					res:add(item: :substring(start: i, end: slen));
					return res;
				});
				res:add(item: :substring(start: i, end: i + 1));
				i: i + 1;
			});
			return res;
		});
		local Int is pos: 0;
		local Int is idx: :indexOfFrom(search: delimiter, from: 0, default: -1, caseSensitive: caseSensitive);
		while({ idx >= 0 }, {
			if({ limit > 0 && res:length() + 1 >= limit }, {
				res:add(item: :substring(start: pos, end: slen));
				return res;
			});
			res:add(item: :substring(start: pos, end: idx));
			pos: idx + dlen;
			idx: :indexOfFrom(search: delimiter, from: pos, default: -1, caseSensitive: caseSensitive);
		});
		res:add(item: :substring(start: pos, end: slen));
		return res;
	}

	## Lines of this string (split on '\n', trailing '\r' stripped).
	##
	## @return: The lines.
	Function of Array of String is lines(){
		local Array of String is res: [];
		local Int is len: :length();
		if({ len == 0 }, {
			return res;
		});
		local Int is start: 0;
		local Int is i: 0;
		repeat(count: len, worker: {
			local Int is b: :byteAt(index: i, default: -1);
			if({ b == 10 }, {
				local Int is endIdx: i;
				if({ endIdx > start }, {
					local Int is prev: :byteAt(index: endIdx - 1, default: -1);
					if({ prev == 13 }, {
						endIdx: endIdx - 1;
					});
				});
				res:add(item: :substring(start: start, end: endIdx));
				start: i + 1;
			});
			i: i + 1;
		});
		if({ start < len }, {
			local Int is endIdx: len;
			local Int is prev: :byteAt(index: endIdx - 1, default: -1);
			if({ prev == 13 }, {
				endIdx: endIdx - 1;
			});
			res:add(item: :substring(start: start, end: endIdx));
		});
		return res;
	}

	## Count occurrences of [byteVal] in this string.
	replace Function of Int is countByte(Int is byteVal){
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

	## Total number of lines in this string without allocating line arrays.
	Function of Int is lineCount(){
		local Int is len: :length();
		if({ len == 0 }, {
			return 0;
		});
		local Int is nl: :countByte(byteVal: 10);
		local Int is lastByte: :byteAt(index: len - 1, default: -1);
		if({ lastByte != 10 }, {
			nl: nl + 1;
		});
		return nl;
	}

	## Whitespace-trimmed copy (' ', '\t', '\n', '\r').
	##
	## @return: The trimmed copy.
	Function of String is trim(){
		local Int is len: :length();
		if({ len == 0 }, {
			return '';
		});
		local Int is s: 0;
		local Boolean is sTrimming: true;
		while({ sTrimming && (s < len) }, {
			local Int is b: :byteAt(index: s, default: -1);
			if({ b == 32 || b == 9 || b == 10 || b == 13 }, {
				s: s + 1;
			}, {
				sTrimming: false;
			});
		});
		if({ s >= len }, {
			return '';
		});
		local Int is e: len;
		local Boolean is eTrimming: true;
		while({ eTrimming && (e > s) }, {
			local Int is b: :byteAt(index: e - 1, default: -1);
			if({ b == 32 || b == 9 || b == 10 || b == 13 }, {
				e: e - 1;
			}, {
				eTrimming: false;
			});
		});
		return :substring(start: s, end: e);
	}

	local Function of String is padBuild(Int is needed, Str is fill){
		local Int is flen: fill:length();
		if({ needed <= 0 || flen == 0 }, {
			return '';
		});
		local String is out: '';
		local Int is remaining: needed;
		while({ remaining >= flen }, {
			out: out . fill;
			remaining: remaining - flen;
		});
		if({ remaining > 0 }, {
			out: out . fill:substring(start: 0, end: remaining);
		});
		return out;
	}

	## Pads the start of this string with [fill] until its byte length reaches [width].
	Function of String is padStart(Int is width, Str is fill: ' '){
		local Int is needed: width - :length();
		if({ needed <= 0 || fill:length() == 0 }, {
			return :copy();
		});
		return :padBuild(needed: needed, fill: fill) . :;
	}

	## Pads the end of this string with [fill] until its byte length reaches [width].
	Function of String is padEnd(Int is width, Str is fill: ' '){
		local Int is needed: width - :length();
		if({ needed <= 0 || fill:length() == 0 }, {
			return :copy();
		});
		return : . :padBuild(needed: needed, fill: fill);
	}

	## Number of leading [search] repetitions.
	##
	## @param search: The repetition unit.
	## @return: Repetition count.
	Function of Int is countLeading(Str is search){
		local Int is slen: search:length();
		local Int is blen: :length();
		if({ slen == 0 || blen == 0 }, {
			return 0;
		});
		local Int is count: 0;
		local Int is pos: 0;
		local Boolean is matching: true;
		while({ matching && (pos + slen <= blen) }, {
			if({ :substring(start: pos, end: pos + slen) == search }, {
				count: count + 1;
				pos: pos + slen;
			}, {
				matching: false;
			});
		});
		return count;
	}

	## True when every byte is an ASCII digit and the string is non-empty.
	##
	## @return: true when all digits.
	Function of Boolean is isDigit(){
		local Int is n: :length();
		if({ n == 0 }, {
			return false;
		});
		local Int is i: 0;
		local Boolean is ok: true;
		while({ ok && (i < n) }, {
			local Int is b: :byteAt(index: i, default: -1);
			if({ b < 48 || b > 57 }, {
				ok: false;
			});
			i: i + 1;
		});
		return ok;
	}

	## True when every byte is an ASCII letter and the string is non-empty.
	##
	## @return: true when all letters.
	Function of Boolean is isAlpha(){
		local Int is n: :length();
		if({ n == 0 }, {
			return false;
		});
		local Int is i: 0;
		local Boolean is ok: true;
		while({ ok && (i < n) }, {
			local Int is b: :byteAt(index: i, default: -1);
			local Boolean is isUpper: (b >= 65 && b <= 90);
			local Boolean is isLower: (b >= 97 && b <= 122);
			if({ !isUpper && !isLower }, {
				ok: false;
			});
			i: i + 1;
		});
		return ok;
	}

	## True when every byte is ASCII whitespace and the string is non-empty.
	##
	## @return: true when all whitespace.
	Function of Boolean is isWhitespace(){
		local Int is n: :length();
		if({ n == 0 }, {
			return false;
		});
		local Int is i: 0;
		local Boolean is ok: true;
		while({ ok && (i < n) }, {
			local Int is b: :byteAt(index: i, default: -1);
			if({ b != 32 && b != 9 && b != 10 && b != 13 && b != 11 && b != 12 }, {
				ok: false;
			});
			i: i + 1;
		});
		return ok;
	}

	## One-byte string for [code] (0-255); empty when out of range.
	##
	## @param code: The byte value.
	## @return: The single-byte string.
	Function of String is fromCharCode(Int is code){
		if({ code < 0 || code > 255 }, {
			return '';
		});
		local Int is scratch: Mem:tlsGetI64(slot: 2);
		if({ scratch == 0 }, {
			scratch: Mem:alloc(bytes: 256);
			Mem:tlsSetI64(slot: 2, val: scratch);
		});
		Mem:storeByte(ptr: scratch, byteOffset: 0, val: code);
		Mem:storeByte(ptr: scratch, byteOffset: 1, val: 0);
		return Mem:strFromBytes(srcAddr: scratch, len: 1);
	}

	## Returns the newline string ("\n").
	##
	## @return: Single newline character string.
	Function of String is newline(){
		return "\n";
	}

	## Parses this string as an integer in [base] (2-36), accepting 0x/0b/0o
	## prefixes and _ separators. Returns [default] on any invalid input.
	##
	## @param base: Number base (2-36).
	## @param default: Fallback on invalid input.
	## @return: The parsed value, or [default].
	Function of Int is parseInt(Int is base: 10, Int is default: -1){
		local Int is len: :length();
		if({ len == 0 }, {
			return default;
		});
		local Int is b: base;
		local Int is start: 0;
		if({ len >= 2 && :byteAt(index: 0, default: -1) == 48 }, {
			local Int is prefixCh: :byteAt(index: 1, default: -1);
			if({ prefixCh == 120 || prefixCh == 88 }, {
				b: 16;
				start: 2;
			}, {
				if({ prefixCh == 98 || prefixCh == 66 }, {
					b: 2;
					start: 2;
				}, {
					if({ prefixCh == 111 || prefixCh == 79 }, {
						b: 8;
						start: 2;
					});
				});
			});
		});
		if({ b < 2 || b > 36 }, {
			return default;
		});
		local Boolean is neg: false;
		if({ start < len && :byteAt(index: start, default: -1) == 45 }, {
			neg: true;
			start: start + 1;
		});
		if({ start >= len }, {
			return default;
		});
		local Int is val: 0;
		local Int is i: start;
		local Boolean is ok: true;
		local Boolean is anyDigits: false;
		while({ ok && (i < len) }, {
			local Int is ch: :byteAt(index: i, default: -1);
			if({ ch != 95 }, {
				local Int is digit: -1;
				if({ ch >= 48 && ch <= 57 }, {
					digit: ch - 48;
				}, {
					if({ ch >= 97 && ch <= 122 }, {
						digit: ch - 97 + 10;
					}, {
						if({ ch >= 65 && ch <= 90 }, {
							digit: ch - 65 + 10;
						});
					});
				});
				if({ digit < 0 || digit >= b }, {
					ok: false;
				}, {
					val: (val * b) + digit;
					anyDigits: true;
				});
			});
			i: i + 1;
		});
		if({ !ok || !anyDigits }, {
			return default;
		});
		if({ neg }, {
			return -val;
		});
		return val;
	}

	## Fast ASCII lowercase copy of this string (leaves non-ASCII bytes intact).
	Function of String is toLower(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return ''; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return ''; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is tmp: Mem:alloc(bytes: len + 1);
		local Int is i: 0;
		while({ i < len }, {
			local Int is b: Mem:loadByte(ptr: data, byteOffset: i);
			if({ b >= 65 && b <= 90 }, {
				Mem:storeByte(ptr: tmp, byteOffset: i, val: b + 32);
			}, {
				Mem:storeByte(ptr: tmp, byteOffset: i, val: b);
			});
			i: i + 1;
		});
		Mem:storeByte(ptr: tmp, byteOffset: len, val: 0);
		local String is res: Mem:strFromBytes(srcAddr: tmp, len: len);
		Mem:free(ptr: tmp);
		return res;
	}

	## Fast ASCII uppercase copy of this string (leaves non-ASCII bytes intact).
	Function of String is toUpper(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return ''; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return ''; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is tmp: Mem:alloc(bytes: len + 1);
		local Int is i: 0;
		while({ i < len }, {
			local Int is b: Mem:loadByte(ptr: data, byteOffset: i);
			if({ b >= 97 && b <= 122 }, {
				Mem:storeByte(ptr: tmp, byteOffset: i, val: b - 32);
			}, {
				Mem:storeByte(ptr: tmp, byteOffset: i, val: b);
			});
			i: i + 1;
		});
		Mem:storeByte(ptr: tmp, byteOffset: len, val: 0);
		local String is res: Mem:strFromBytes(srcAddr: tmp, len: len);
		Mem:free(ptr: tmp);
		return res;
	}

	## Validates the UTF-8 byte sequence starting at [idx] in [data] of length [len].
	## Returns 1..4 when strictly valid UTF-8, or 0 when ill-formed.
	contained Function of Int is validUtf8SeqLen(Int is data, Int is idx, Int is len){
		if({ idx < 0 || idx >= len }, { return 0; });
		local Int is b0: Mem:loadByte(ptr: data, byteOffset: idx);
		if({ b0 < 128 }, { return 1; });
		if({ b0 >= 194 && b0 <= 223 }, {
			if({ idx + 1 >= len }, { return 0; });
			local Int is b1: Mem:loadByte(ptr: data, byteOffset: idx + 1);
			if({ (b1 & 192) != 128 }, { return 0; });
			return 2;
		});
		if({ b0 >= 224 && b0 <= 239 }, {
			if({ idx + 2 >= len }, { return 0; });
			local Int is b1: Mem:loadByte(ptr: data, byteOffset: idx + 1);
			local Int is b2: Mem:loadByte(ptr: data, byteOffset: idx + 2);
			if({ (b1 & 192) != 128 || (b2 & 192) != 128 }, { return 0; });
			local Int is cp: ((b0 & 15) << 12) | ((b1 & 63) << 6) | (b2 & 63);
			if({ cp < 2048 || (cp >= 55296 && cp <= 57343) }, { return 0; });
			return 3;
		});
		if({ b0 >= 240 && b0 <= 244 }, {
			if({ idx + 3 >= len }, { return 0; });
			local Int is b1: Mem:loadByte(ptr: data, byteOffset: idx + 1);
			local Int is b2: Mem:loadByte(ptr: data, byteOffset: idx + 2);
			local Int is b3: Mem:loadByte(ptr: data, byteOffset: idx + 3);
			if({ (b1 & 192) != 128 || (b2 & 192) != 128 || (b3 & 192) != 128 }, { return 0; });
			local Int is cp: ((b0 & 7) << 18) | ((b1 & 63) << 12) | ((b2 & 63) << 6) | (b3 & 63);
			if({ cp < 65536 || cp > 1114111 }, { return 0; });
			return 4;
		});
		return 0;
	}

	## Byte length (1..4) of the UTF-8 sequence starting at [byteIndex], or 0
	## when [byteIndex] is out of bounds. Ill-formed sequences return 1 so
	## byte-advancing loops always make forward progress.
	##
	## @param byteIndex: Zero-based byte offset.
	## @return: Sequence length in bytes (1..4), or 0 when out of bounds.
	Function of Int is codePointByteLen(Int is byteIndex){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return 0; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ byteIndex < 0 || byteIndex >= len }, { return 0; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is vlen: :validUtf8SeqLen(data: data, idx: byteIndex, len: len);
		if({ vlen > 0 }, { return vlen; });
		return 1;
	}

	## True when all bytes in this string form valid UTF-8 scalar values.
	##
	## @return: true when valid UTF-8.
	Function of Boolean is isValidUtf8(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return true; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return true; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is i: 0;
		while({ i < len }, {
			local Int is b0: Mem:loadByte(ptr: data, byteOffset: i);
			if({ b0 < 128 }, {
				i: i + 1;
			}, {
				local Int is vlen: :validUtf8SeqLen(data: data, idx: i, len: len);
				if({ vlen == 0 }, { return false; });
				i: i + vlen;
			});
		});
		return true;
	}

	## Returns a valid UTF-8 copy of this string, replacing any ill-formed
	## byte sequence with the UTF-8 replacement character `U+FFFD`.
	##
	## @return: Sanitized UTF-8 string.
	Function of String is sanitizeUtf8(){
		if({ :isValidUtf8() }, {
			return :copy();
		});
		local Int is addr: Mem:objToAddr(obj: :);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is scratch: Mem:tlsGetI64(slot: 2);
		if({ scratch == 0 }, {
			scratch: Mem:alloc(bytes: 256);
			Mem:tlsSetI64(slot: 2, val: scratch);
		});
		Mem:storeByte(ptr: scratch, byteOffset: 0, val: 239);
		Mem:storeByte(ptr: scratch, byteOffset: 1, val: 191);
		Mem:storeByte(ptr: scratch, byteOffset: 2, val: 189);
		Mem:storeByte(ptr: scratch, byteOffset: 3, val: 0);
		local String is repl: Mem:strFromBytes(srcAddr: scratch, len: 3);
		local String is out: '';
		local Int is runStart: 0;
		local Int is i: 0;
		while({ i < len }, {
			local Int is vlen: :validUtf8SeqLen(data: data, idx: i, len: len);
			if({ vlen > 0 }, {
				i: i + vlen;
			}, {
				if({ i > runStart }, {
					out: out . :substring(start: runStart, end: i);
				});
				out: out . repl;
				i: i + 1;
				runStart: i;
			});
		});
		if({ runStart < len }, {
			out: out . :substring(start: runStart, end: len);
		});
		return out;
	}

	## UTF-8 boundary-safe byte slice from [start] to [end]: snaps any boundary
	## that lands on a UTF-8 continuation byte (`10xxxxxx`) forward to the next
	## code-point boundary so multi-byte characters are never torn.
	##
	## @param start: Inclusive byte start index.
	## @param end: Exclusive byte end index.
	## @return: Boundary-aligned UTF-8 substring.
	Function of String is sliceUtf8(Int is start, Int is end){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return ''; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is s: if({ start < 0 }, { 0 }, { start });
		local Int is e: if({ end > len }, { len }, { end });
		if({ s >= e }, { return ''; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		while({ s > 0 && (Mem:loadByte(ptr: data, byteOffset: s) & 192) == 128 }, {
			s: s - 1;
		});
		while({ e > s && (Mem:loadByte(ptr: data, byteOffset: e) & 192) == 128 }, {
			e: e - 1;
		});
		if({ s >= e }, { return ''; });
		return :substring(start: s, end: e);
	}

	## Concatenation of this string and [other].
	##
	## @param other: String to append.
	## @return: Newly allocated string containing this string followed by [other].
	Function of String is concat(Str is other){
		local Int is aAddr: Mem:objToAddr(obj: :);
		local Int is bAddr: Mem:objToAddr(obj: other);
		local Int is aLen: if({ aAddr == 0 }, { 0 }, { Mem:loadI64(ptr: aAddr, byteOffset: 8) });
		local Int is bLen: if({ bAddr == 0 }, { 0 }, { Mem:loadI64(ptr: bAddr, byteOffset: 8) });
		local Int is total: aLen + bLen;
		if({ total == 0 }, { return ''; });
		if({ aLen == 0 }, { return other:copy(); });
		if({ bLen == 0 }, { return :copy(); });
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
		Buf:bufAppendBuf(dst: out, src: other);
		return out;
	}
}
