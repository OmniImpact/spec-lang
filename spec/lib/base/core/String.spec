#! Package base:core
#! The String type: full Unicode support layered on top of Str (`Buf -> Str -> String`).
##
## String inherits the fast byte/ASCII and UTF-8 validation/sanitization methods
## from `Str` (`Buf -> Str -> String`), and adds full Unicode code-point decoding,
## encoding (`fromCodePoint`), Unicode case conversion (`toLower`/`toUpper`), and
## lazy sparse checkpoint indexing (`K = 32` runes at `SpecBuf` offset 40) for
## bounded-O(1) character/rune operations (`runeCount`, `runeAt`, `codePointAtRune`,
## `sliceRunes`, `codePoints`).

Class of Str is String{
	namespace: ['base', 'core'];

	replace Array of Array of String is using: [
		['base', 'core', Str],
		['base', 'sys', as Buf()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	## Declared casts: a String produces an Int through its parser.
	castable: [
		[Int, parseInt]
	];

	## Encodes Unicode scalar value [code] (`U+0000..U+10FFFF`, excluding
	## surrogates `0xD800..0xDFFF`) into a 1–4 byte UTF-8 string. Invalid code
	## points produce the UTF-8 replacement character `U+FFFD`.
	##
	## @param code: Unicode code point.
	## @return: UTF-8 string for [code] (or `U+FFFD` if invalid).
	Function of String is fromCodePoint(Int is code){
		local Int is cp: code;
		if({ cp < 0 || cp > 1114111 || (cp >= 55296 && cp <= 57343) }, {
			cp: 65533;
		});
		local Int is scratch: Mem:tlsGetI64(slot: 2);
		if({ scratch == 0 }, {
			scratch: Mem:alloc(bytes: 256);
			Mem:tlsSetI64(slot: 2, val: scratch);
		});
		if({ cp <= 127 }, {
			Mem:storeByte(ptr: scratch, byteOffset: 0, val: cp);
			Mem:storeByte(ptr: scratch, byteOffset: 1, val: 0);
			return Mem:strFromBytes(srcAddr: scratch, len: 1);
		});
		if({ cp <= 2047 }, {
			Mem:storeByte(ptr: scratch, byteOffset: 0, val: 192 | (cp >> 6));
			Mem:storeByte(ptr: scratch, byteOffset: 1, val: 128 | (cp & 63));
			Mem:storeByte(ptr: scratch, byteOffset: 2, val: 0);
			return Mem:strFromBytes(srcAddr: scratch, len: 2);
		});
		if({ cp <= 65535 }, {
			Mem:storeByte(ptr: scratch, byteOffset: 0, val: 224 | (cp >> 12));
			Mem:storeByte(ptr: scratch, byteOffset: 1, val: 128 | ((cp >> 6) & 63));
			Mem:storeByte(ptr: scratch, byteOffset: 2, val: 128 | (cp & 63));
			Mem:storeByte(ptr: scratch, byteOffset: 3, val: 0);
			return Mem:strFromBytes(srcAddr: scratch, len: 3);
		});
		Mem:storeByte(ptr: scratch, byteOffset: 0, val: 240 | (cp >> 18));
		Mem:storeByte(ptr: scratch, byteOffset: 1, val: 128 | ((cp >> 12) & 63));
		Mem:storeByte(ptr: scratch, byteOffset: 2, val: 128 | ((cp >> 6) & 63));
		Mem:storeByte(ptr: scratch, byteOffset: 3, val: 128 | (cp & 63));
		Mem:storeByte(ptr: scratch, byteOffset: 4, val: 0);
		return Mem:strFromBytes(srcAddr: scratch, len: 4);
	}

	## Decodes the UTF-8 code point starting at [byteIndex], returning [default]
	## when [byteIndex] is out of bounds or `0xFFFD` (`65533`) on an ill-formed
	## byte sequence.
	##
	## @param byteIndex: Zero-based byte offset.
	## @param default: Fallback when out of bounds.
	## @return: Decoded Unicode scalar value, `65533`, or [default].
	Function of Int is codePointAt(Int is byteIndex, Int is default: -1){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return default; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ byteIndex < 0 || byteIndex >= len }, { return default; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is b0: Mem:loadByte(ptr: data, byteOffset: byteIndex);
		if({ b0 < 128 }, { return b0; });
		local Int is vlen: :validUtf8SeqLen(data: data, idx: byteIndex, len: len);
		if({ vlen == 2 }, {
			local Int is b1: Mem:loadByte(ptr: data, byteOffset: byteIndex + 1);
			return ((b0 & 31) << 6) | (b1 & 63);
		});
		if({ vlen == 3 }, {
			local Int is b1: Mem:loadByte(ptr: data, byteOffset: byteIndex + 1);
			local Int is b2: Mem:loadByte(ptr: data, byteOffset: byteIndex + 2);
			return ((b0 & 15) << 12) | ((b1 & 63) << 6) | (b2 & 63);
		});
		if({ vlen == 4 }, {
			local Int is b1: Mem:loadByte(ptr: data, byteOffset: byteIndex + 1);
			local Int is b2: Mem:loadByte(ptr: data, byteOffset: byteIndex + 2);
			local Int is b3: Mem:loadByte(ptr: data, byteOffset: byteIndex + 3);
			return ((b0 & 7) << 18) | ((b1 & 63) << 12) | ((b2 & 63) << 6) | (b3 & 63);
		});
		return 65533;
	}

	## Lazily builds and publishes the sparse checkpoint table (`K = 32` runes)
	## at offset 40 of `SpecBuf` for strings with `byteLength() > 64`.
	## Returns `-1` when verified pure ASCII, `> 0` for the checkpoint table
	## address on non-ASCII strings, or `0` for short strings (`<= 64` bytes).
	local Function of Int is ensureCheckpoints(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return 0; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 64 }, { return 0; });
		local Int is ck: Mem:atomicLoadI64(addr: addr + 40);
		if({ ck != 0 }, { return ck; });

		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is runes: 0;
		local Int is i: 0;
		while({ i < len }, {
			local Int is b0: Mem:loadByte(ptr: data, byteOffset: i);
			if({ b0 < 128 }, {
				i: i + 1;
			}, {
				local Int is vlen: :validUtf8SeqLen(data: data, idx: i, len: len);
				i: i + if({ vlen > 0 }, { vlen }, { 1 });
			});
			runes: runes + 1;
		});
		if({ runes == len }, {
			Mem:atomicCasI64(addr: addr + 40, expected: 0, desired: -1);
			return -1;
		});

		local Int is numCk: (runes >> 5) + 1;
		local Int is newCk: Mem:alloc(bytes: 16 + (numCk * 4));
		Mem:storeI64(ptr: newCk, byteOffset: 0, val: runes);
		Mem:storeI64(ptr: newCk, byteOffset: 8, val: numCk);
		local Int is rIdx: 0;
		i: 0;
		while({ i < len }, {
			if({ (rIdx & 31) == 0 }, {
				Mem:storeI32(ptr: newCk, byteOffset: 16 + ((rIdx >> 5) * 4), val: i);
			});
			local Int is b0: Mem:loadByte(ptr: data, byteOffset: i);
			if({ b0 < 128 }, {
				i: i + 1;
			}, {
				local Int is vlen: :validUtf8SeqLen(data: data, idx: i, len: len);
				i: i + if({ vlen > 0 }, { vlen }, { 1 });
			});
			rIdx: rIdx + 1;
		});
		if({ Mem:atomicCasI64(addr: addr + 40, expected: 0, desired: newCk) }, {
			return newCk;
		});
		Mem:free(ptr: newCk);
		return Mem:atomicLoadI64(addr: addr + 40);
	}

	## Number of UTF-8 code points (runes) in this string.
	## Uses lazy sparse checkpoints on strings > 64 bytes for O(1) repeat queries.
	##
	## @return: Code-point count.
	Function of Int is runeCount(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return 0; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return 0; });
		if({ len > 64 }, {
			local Int is ck: :ensureCheckpoints();
			if({ ck == -1 }, { return len; });
			if({ ck > 0 }, { return Mem:loadI64(ptr: ck, byteOffset: 0); });
		});
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is count: 0;
		local Int is i: 0;
		while({ i < len }, {
			local Int is b0: Mem:loadByte(ptr: data, byteOffset: i);
			if({ b0 < 128 }, {
				i: i + 1;
			}, {
				local Int is vlen: :validUtf8SeqLen(data: data, idx: i, len: len);
				i: i + if({ vlen > 0 }, { vlen }, { 1 });
			});
			count: count + 1;
		});
		return count;
	}

	## Maps a zero-based code-point index [runeIndex] to its byte offset in bounded
	## O(1) time using lazy sparse checkpoints (`K = 32`).
	##
	## @param runeIndex: Zero-based code-point index.
	## @return: Byte offset in `0..byteLength()`.
	Function of Int is runeToByteOffset(Int is runeIndex){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 || runeIndex <= 0 }, { return 0; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return 0; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is bPos: 0;
		local Int is rem: runeIndex;
		if({ len > 64 }, {
			local Int is ck: :ensureCheckpoints();
			if({ ck == -1 }, {
				return if({ runeIndex >= len }, { len }, { runeIndex });
			});
			if({ ck > 0 }, {
				local Int is totalRunes: Mem:loadI64(ptr: ck, byteOffset: 0);
				if({ runeIndex >= totalRunes }, { return len; });
				local Int is chunk: runeIndex >> 5;
				rem: runeIndex & 31;
				bPos: Mem:loadI32(ptr: ck, byteOffset: 16 + (chunk * 4));
			});
		});
		while({ rem > 0 && bPos < len }, {
			local Int is b0: Mem:loadByte(ptr: data, byteOffset: bPos);
			if({ b0 < 128 }, {
				bPos: bPos + 1;
			}, {
				local Int is vlen: :validUtf8SeqLen(data: data, idx: bPos, len: len);
				bPos: bPos + if({ vlen > 0 }, { vlen }, { 1 });
			});
			rem: rem - 1;
		});
		return bPos;
	}

	## Returns the Unicode code point at zero-based code-point index [runeIndex],
	## or [default] when out of bounds. Accelerated by lazy sparse checkpoints.
	##
	## @param runeIndex: Zero-based code-point index.
	## @param default: Fallback when out of bounds.
	## @return: Decoded code point, or [default].
	Function of Int is codePointAtRune(Int is runeIndex, Int is default: -1){
		if({ runeIndex < 0 }, { return default; });
		local Int is total: :runeCount();
		if({ runeIndex >= total }, { return default; });
		local Int is bOff: :runeToByteOffset(runeIndex: runeIndex);
		return :codePointAt(byteIndex: bOff, default: default);
	}

	## Returns the single UTF-8 character substring at zero-based code-point
	## index [runeIndex], or [default] when out of bounds.
	##
	## @param runeIndex: Zero-based code-point index.
	## @param default: Fallback when out of bounds.
	## @return: UTF-8 character string, or [default].
	Function of String is runeAt(Int is runeIndex, String is default: ''){
		if({ runeIndex < 0 }, { return Buf:stringCopy(b: default); });
		local Int is total: :runeCount();
		if({ runeIndex >= total }, { return Buf:stringCopy(b: default); });
		local Int is bStart: :runeToByteOffset(runeIndex: runeIndex);
		local Int is bLen: :codePointByteLen(byteIndex: bStart);
		return :substring(start: bStart, end: bStart + bLen);
	}

	## Code-point slice from [start] (inclusive) to [end] (exclusive), clamped
	## to `0..runeCount()`. Accelerated by lazy sparse checkpoints on long strings.
	##
	## @param start: Inclusive code-point start index.
	## @param end: Exclusive code-point end index.
	## @return: UTF-8 substring covering runes `[start, end)`.
	Function of String is sliceRunes(Int is start, Int is end){
		local Int is s: if({ start < 0 }, { 0 }, { start });
		local Int is e: end;
		if({ e <= s }, { return ''; });
		local Int is bStart: :runeToByteOffset(runeIndex: s);
		local Int is bEnd: :runeToByteOffset(runeIndex: e);
		if({ bStart >= bEnd }, { return ''; });
		return :substring(start: bStart, end: bEnd);
	}

	## Decodes all UTF-8 code points in this string into an [Array] of [Int].
	##
	## @return: Array of Unicode scalar values.
	Function of Array of Int is codePoints(){
		local Array of Int is res: [];
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return res; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return res; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is i: 0;
		while({ i < len }, {
			local Int is b0: Mem:loadByte(ptr: data, byteOffset: i);
			if({ b0 < 128 }, {
				res:add(item: b0);
				i: i + 1;
			}, {
				local Int is vlen: :validUtf8SeqLen(data: data, idx: i, len: len);
				if({ vlen == 0 }, {
					res:add(item: 65533);
					i: i + 1;
				}, {
					res:add(item: :codePointAt(byteIndex: i, default: 65533));
					i: i + vlen;
				});
			});
		});
		return res;
	}

	## Lowercase copy of this string (uses `Str`'s fast ASCII path when all bytes
	## are `< 128`, or maps Unicode case when non-ASCII bytes are present).
	replace Function of String is toLower(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return ''; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return ''; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Boolean is allAscii: true;
		local Int is i: 0;
		while({ allAscii && i < len }, {
			if({ Mem:loadByte(ptr: data, byteOffset: i) >= 128 }, {
				allAscii: false;
			});
			i: i + 1;
		});
		if({ allAscii }, {
			local Int is tmp: Mem:alloc(bytes: len + 1);
			i: 0;
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
		});
		local String is out: '';
		i: 0;
		while({ i < len }, {
			local Int is b0: Mem:loadByte(ptr: data, byteOffset: i);
			if({ b0 < 128 }, {
				if({ b0 >= 65 && b0 <= 90 }, {
					out: out . :fromCharCode(code: b0 + 32);
				}, {
					out: out . :fromCharCode(code: b0);
				});
				i: i + 1;
			}, {
				local Int is vlen: :validUtf8SeqLen(data: data, idx: i, len: len);
				if({ vlen == 0 }, {
					out: out . String:fromCodePoint(code: 65533);
					i: i + 1;
				}, {
					local Int is cp: :codePointAt(byteIndex: i, default: 65533);
					local Int is mapped: cp;
					if({ (cp >= 192 && cp <= 214) || (cp >= 216 && cp <= 222) || (cp >= 913 && cp <= 937 && cp != 930) || (cp >= 1040 && cp <= 1071) || (cp >= 65313 && cp <= 65338) }, {
						mapped: cp + 32;
					}, {
						if({ cp >= 256 && cp <= 310 && (cp & 1) == 0 }, {
							mapped: cp + 1;
						});
						if({ cp >= 1024 && cp <= 1039 }, {
							mapped: cp + 80;
						});
					});
					out: out . String:fromCodePoint(code: mapped);
					i: i + vlen;
				});
			});
		});
		return out;
	}

	## Uppercase copy of this string (uses `Str`'s fast ASCII path when all bytes
	## are `< 128`, or maps Unicode case when non-ASCII bytes are present).
	replace Function of String is toUpper(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return ''; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return ''; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Boolean is allAscii: true;
		local Int is i: 0;
		while({ allAscii && i < len }, {
			if({ Mem:loadByte(ptr: data, byteOffset: i) >= 128 }, {
				allAscii: false;
			});
			i: i + 1;
		});
		if({ allAscii }, {
			local Int is tmp: Mem:alloc(bytes: len + 1);
			i: 0;
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
		});
		local String is out: '';
		i: 0;
		while({ i < len }, {
			local Int is b0: Mem:loadByte(ptr: data, byteOffset: i);
			if({ b0 < 128 }, {
				if({ b0 >= 97 && b0 <= 122 }, {
					out: out . :fromCharCode(code: b0 - 32);
				}, {
					out: out . :fromCharCode(code: b0);
				});
				i: i + 1;
			}, {
				local Int is vlen: :validUtf8SeqLen(data: data, idx: i, len: len);
				if({ vlen == 0 }, {
					out: out . String:fromCodePoint(code: 65533);
					i: i + 1;
				}, {
					local Int is cp: :codePointAt(byteIndex: i, default: 65533);
					local Int is mapped: cp;
					if({ (cp >= 224 && cp <= 246) || (cp >= 248 && cp <= 254) || (cp >= 945 && cp <= 969 && cp != 962) || (cp >= 1072 && cp <= 1103) || (cp >= 65345 && cp <= 65370) }, {
						mapped: cp - 32;
					}, {
						if({ cp == 962 }, {
							mapped: 931;
						});
						if({ cp >= 257 && cp <= 311 && (cp & 1) == 1 }, {
							mapped: cp - 1;
						});
						if({ cp >= 1104 && cp <= 1119 }, {
							mapped: cp - 80;
						});
					});
					out: out . String:fromCodePoint(code: mapped);
					i: i + vlen;
				});
			});
		});
		return out;
	}

	## Concatenation of this string and [other].
	##
	## @param other: String to append.
	## @return: Newly allocated string containing this string followed by [other].
	replace Function of String is concat(String is other){
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
