#! Package base:core
#! The Str type: a lightweight, UTF-8-safe byte string over Buf.
##
## Str sits between raw `Buf` and full-Unicode `String` (`Buf -> Str -> String`).
## It provides the fast byte/ASCII string operations plus UTF-8 validation,
## sanitization (`sanitizeUtf8`), and boundary-safe byte slicing (`sliceUtf8`)
## without any Unicode table or checkpoint overhead.

Class of Buf is Str{
	namespace: ['base', 'core'];

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
	Function of Int is length(){
		return Buf:bufLength(b: :);
	}

	## Number of bytes in this string (explicit byte-length alias for [length]).
	##
	## @return: Byte count.
	Function of Int is byteLength(){
		return Buf:bufLength(b: :);
	}

	## Raw byte value (0..255) at [index], or [default] when out of bounds.
	##
	## @param index: Zero-based byte index.
	## @param default: Fallback when out of bounds.
	## @return: Byte value, or [default].
	Function of Int is charCodeAt(Int is index, Int is default: -1){
		return Buf:bufGetByte(b: :, idx: index, def: default);
	}

	## One-byte string at [index], or [default] when out of bounds.
	##
	## @param index: Zero-based byte index.
	## @param default: Fallback when out of bounds.
	## @return: The character, or [default].
	Function of String is charAt(Int is index, String is default: ''){
		if({ index < 0 || index >= Buf:bufLength(b: :) }, {
			return Buf:stringCopy(b: default);
		});
		return :fromCharCode(code: Buf:bufGetByte(b: :, idx: index, def: -1));
	}

	## Bytes from [start] (inclusive) to [end] (exclusive), clamped to bounds.
	##
	## @param start: Inclusive start byte index.
	## @param end: Exclusive end byte index.
	## @return: The sub-string.
	Function of String is substring(Int is start, Int is end){
		local Int is s: start;
		local Int is e: end;
		if({ s < 0 }, {
			s: 0;
		});
		if({ e > Buf:bufLength(b: :) }, {
			e: Buf:bufLength(b: :);
		});
		return Buf:stringSubstring(b: :, start: s, end: e);
	}

	## True when this string begins with [prefix].
	##
	## @param prefix: The prefix to test.
	## @return: true when present.
	Function of Boolean is startsWith(String is prefix){
		local Int is pl: Buf:bufLength(b: prefix);
		if({ pl == 0 }, {
			return true;
		});
		if({ pl > Buf:bufLength(b: :) }, {
			return false;
		});
		return Buf:stringSubstring(b: :, start: 0, end: pl) == prefix;
	}

	## True when this string ends with [suffix].
	##
	## @param suffix: The suffix to test.
	## @return: true when present.
	Function of Boolean is endsWith(String is suffix){
		local Int is sl: Buf:bufLength(b: suffix);
		if({ sl == 0 }, {
			return true;
		});
		local Int is bl: Buf:bufLength(b: :);
		if({ sl > bl }, {
			return false;
		});
		return Buf:stringSubstring(b: :, start: bl - sl, end: bl) == suffix;
	}

	## True when [needle] occurs anywhere in this string (empty needle: true).
	##
	## @param needle: Sequence to locate.
	## @return: true when present.
	Function of Boolean is contains(String is needle){
		return :indexOf(search: needle, default: -1) >= 0;
	}

	## First occurrence of [needle] at or after the start, or [default].
	##
	## @param search: Sequence to locate.
	## @param default: Fallback when absent (conventionally -1).
	## @return: The index, or [default].
	Function of Int is indexOf(String is search, Int is default: -1){
		return Buf:stringIndexOf(b: :, needle: search, def: default);
	}

	## Every [search] occurrence replaced by [replacement].
	##
	## @param search: Sequence to replace.
	## @param replacement: Replacement sequence.
	## @return: The replaced copy.
	Function of String is replaceAll(String is search, String is replacement){
		local Int is slen: Buf:bufLength(b: search);
		if({ slen == 0 }, {
			return Buf:stringCopy(b: :);
		});
		local Int is total: Buf:bufLength(b: :);
		local String is out: '';
		local Int is pos: 0;
		local Boolean is running: true;
		while({ running }, {
			local Int is idx: Buf:stringIndexOfFrom(b: :, needle: search, from: pos, def: -1);
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

	## Splits on [delimiter]; the trailing part is always present.
	##
	## @param delimiter: Split boundary.
	## @return: The parts.
	Function of Array of String is split(String is delimiter){
		local Array of String is res: [];
		local Int is slen: Buf:bufLength(b: :);
		if({ slen == 0 }, {
			return res;
		});
		local Int is dlen: Buf:bufLength(b: delimiter);
		if({ dlen == 0 }, {
			local Int is i: 0;
			repeat(count: slen, worker: {
				res:add(item: Buf:stringSubstring(b: :, start: i, end: i + 1));
				i: i + 1;
			});
			return res;
		});
		local Int is pos: 0;
		local Int is idx: Buf:stringIndexOfFrom(b: :, needle: delimiter, from: 0, def: -1);
		while({ idx >= 0 }, {
			res:add(item: Buf:stringSubstring(b: :, start: pos, end: idx));
			pos: idx + dlen;
			idx: Buf:stringIndexOfFrom(b: :, needle: delimiter, from: pos, def: -1);
		});
		res:add(item: Buf:stringSubstring(b: :, start: pos, end: slen));
		return res;
	}

	## Lines of this string (split on '\n', trailing '\r' stripped).
	##
	## @return: The lines.
	Function of Array of String is lines(){
		local Array of String is res: [];
		local Int is len: Buf:bufLength(b: :);
		if({ len == 0 }, {
			return res;
		});
		local Int is start: 0;
		local Int is i: 0;
		repeat(count: len, worker: {
			local Int is b: Buf:bufGetByte(b: :, idx: i, def: -1);
			if({ b == 10 }, {
				local Int is endIdx: i;
				if({ endIdx > start }, {
					local Int is prev: Buf:bufGetByte(b: :, idx: endIdx - 1, def: -1);
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
			local Int is prev: Buf:bufGetByte(b: :, idx: endIdx - 1, def: -1);
			if({ prev == 13 }, {
				endIdx: endIdx - 1;
			});
			res:add(item: :substring(start: start, end: endIdx));
		});
		return res;
	}

	## Count occurrences of [byteVal] in this string.
	Function of Int is countByte(Int is byteVal){
		return Buf:bufCountByte(b: :, byteVal: byteVal);
	}

	## Total number of lines in this string without allocating line arrays.
	Function of Int is lineCount(){
		local Int is len: Buf:bufLength(b: :);
		if({ len == 0 }, {
			return 0;
		});
		local Int is nl: Buf:bufCountByte(b: :, byteVal: 10);
		local Int is lastByte: Buf:bufGetByte(b: :, idx: len - 1, def: -1);
		if({ lastByte != 10 }, {
			nl: nl + 1;
		});
		return nl;
	}

	## Whitespace-trimmed copy (' ', '\t', '\n', '\r').
	##
	## @return: The trimmed copy.
	Function of String is trim(){
		local Int is len: Buf:bufLength(b: :);
		if({ len == 0 }, {
			return '';
		});
		local Int is s: 0;
		local Boolean is sTrimming: true;
		while({ sTrimming && (s < len) }, {
			local Int is b: Buf:bufGetByte(b: :, idx: s, def: -1);
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
			local Int is b: Buf:bufGetByte(b: :, idx: e - 1, def: -1);
			if({ b == 32 || b == 9 || b == 10 || b == 13 }, {
				e: e - 1;
			}, {
				eTrimming: false;
			});
		});
		return :substring(start: s, end: e);
	}

	## Number of leading [search] repetitions.
	##
	## @param search: The repetition unit.
	## @return: Repetition count.
	Function of Int is countLeading(String is search){
		local Int is slen: Buf:bufLength(b: search);
		local Int is blen: Buf:bufLength(b: :);
		if({ slen == 0 || blen == 0 }, {
			return 0;
		});
		local Int is count: 0;
		local Int is pos: 0;
		local Boolean is matching: true;
		while({ matching && (pos + slen <= blen) }, {
			if({ Buf:stringSubstring(b: :, start: pos, end: pos + slen) == search }, {
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
		local Int is n: Buf:bufLength(b: :);
		if({ n == 0 }, {
			return false;
		});
		local Int is i: 0;
		local Boolean is ok: true;
		while({ ok && (i < n) }, {
			local Int is b: Buf:bufGetByte(b: :, idx: i, def: -1);
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
		local Int is n: Buf:bufLength(b: :);
		if({ n == 0 }, {
			return false;
		});
		local Int is i: 0;
		local Boolean is ok: true;
		while({ ok && (i < n) }, {
			local Int is b: Buf:bufGetByte(b: :, idx: i, def: -1);
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
		local Int is n: Buf:bufLength(b: :);
		if({ n == 0 }, {
			return false;
		});
		local Int is i: 0;
		local Boolean is ok: true;
		while({ ok && (i < n) }, {
			local Int is b: Buf:bufGetByte(b: :, idx: i, def: -1);
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
		local Int is len: Buf:bufLength(b: :);
		if({ len == 0 }, {
			return default;
		});
		local Int is b: base;
		local Int is start: 0;
		if({ len >= 2 && Buf:bufGetByte(b: :, idx: 0, def: -1) == 48 }, {
			local Int is prefixCh: Buf:bufGetByte(b: :, idx: 1, def: -1);
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
		if({ start < len && Buf:bufGetByte(b: :, idx: start, def: -1) == 45 }, {
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
			local Int is ch: Buf:bufGetByte(b: :, idx: i, def: -1);
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
			return Buf:stringCopy(b: :);
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
		return Buf:stringSubstring(b: :, start: s, end: e);
	}

	## Concatenation of this string and [other].
	##
	## @param other: String to append.
	## @return: Newly allocated string containing this string followed by [other].
	Function of String is concat(String is other){
		local Int is aAddr: Mem:objToAddr(obj: :);
		local Int is bAddr: Mem:objToAddr(obj: other);
		local Int is aLen: if({ aAddr == 0 }, { 0 }, { Mem:loadI64(ptr: aAddr, byteOffset: 8) });
		local Int is bLen: if({ bAddr == 0 }, { 0 }, { Mem:loadI64(ptr: bAddr, byteOffset: 8) });
		local Int is total: aLen + bLen;
		if({ total == 0 }, { return ''; });
		if({ aLen == 0 }, { return Buf:stringCopy(b: other); });
		if({ bLen == 0 }, { return Buf:stringCopy(b: :); });
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
