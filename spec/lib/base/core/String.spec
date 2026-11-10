#! Package base:core
#! The String type: a refcounted, NUL-terminated byte buffer with a cached length.
##
## String is a transparent runtime-managed class.
## The type system and class registry know its method surface below, but no
## C struct, vtable, or constructor is emitted for the class: a String value
## IS the managed buffer (`SpecBuf*`). The bodies here run directly over the
## sysinternal byte-buffer floor; the generator routes the hot methods to
## routes the hot methods to their `spec_string_*` floor equivalents, and
## these bodies as the only implementation when the floor interception retires.

Class is String{
	namespace: ['base', 'core'];

	replace Array of Array of String is using: [
		['base', 'sys', as Buf()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	## Declared casts: a String produces an Int through its parser.
	castable: [
		[Int, parseInt]
	];

	## Number of bytes in this string.
	##
	## @return: Byte count.
	Function of Int is length(){
		return Buf:bufLength(b: self);
	}

	## One-character string at [index], or [default] when out of bounds.
	##
	## @param index: Zero-based byte index.
	## @param default: Fallback when out of bounds.
	## @return: The character, or [default].
	Function of String is charAt(Int is index, String is default){
		Conditional:if(check: { index < 0 || index >= Buf:bufLength(b: self) }, then: {
			return Buf:stringCopy(b: default);
		});
		return String:fromCharCode(code: Buf:bufGetByte(b: self, idx: index, def: -1));
	}

	## Bytes from [start] (inclusive) to [end] (exclusive), clamped to bounds.
	##
	## @param start: Inclusive start index.
	## @param end: Exclusive end index.
	## @return: The sub-string.
	Function of String is substring(Int is start, Int is end){
		local Int is s: start;
		local Int is e: end;
		Conditional:if(check: { s < 0 }, then: {
			s: 0;
		});
		Conditional:if(check: { e > Buf:bufLength(b: self) }, then: {
			e: Buf:bufLength(b: self);
		});
		return Buf:stringSubstring(b: self, start: s, end: e);
	}

	## True when this string begins with [prefix].
	##
	## @param prefix: The prefix to test.
	## @return: true when present.
	Function of Boolean is startsWith(String is prefix){
		local Int is pl: Buf:bufLength(b: prefix);
		Conditional:if(check: { pl == 0 }, then: {
			return true;
		});
		Conditional:if(check: { pl > Buf:bufLength(b: self) }, then: {
			return false;
		});
		return Buf:stringSubstring(b: self, start: 0, end: pl) == prefix;
	}

	## True when this string ends with [suffix].
	##
	## @param suffix: The suffix to test.
	## @return: true when present.
	Function of Boolean is endsWith(String is suffix){
		local Int is sl: Buf:bufLength(b: suffix);
		Conditional:if(check: { sl == 0 }, then: {
			return true;
		});
		local Int is bl: Buf:bufLength(b: self);
		Conditional:if(check: { sl > bl }, then: {
			return false;
		});
		return Buf:stringSubstring(b: self, start: bl - sl, end: bl) == suffix;
	}

	## True when [needle] occurs anywhere in this string (empty needle: true).
	##
	## @param needle: Sequence to locate.
	## @return: true when present.
	Function of Boolean is contains(String is needle){
		return self:indexOf(search: needle, default: -1) >= 0;
	}

	## First occurrence of [needle] at or after the start, or [default].
	##
	## @param search: Sequence to locate.
	## @param default: Fallback when absent (conventionally -1).
	## @return: The index, or [default].
	Function of Int is indexOf(String is search, Int is default){
		return Buf:stringIndexOf(b: self, needle: search, def: default);
	}

	## Every [search] occurrence replaced by [replacement].
	##
	## @param search: Sequence to replace.
	## @param replacement: Replacement sequence.
	## @return: The replaced copy.
	Function of String is replaceAll(String is search, String is replacement){
		local Int is slen: Buf:bufLength(b: search);
		Conditional:if(check: { slen == 0 }, then: {
			return Buf:stringCopy(b: self);
		});
		local Int is total: Buf:bufLength(b: self);
		local String is out: '';
		local Int is pos: 0;
		local Boolean is running: true;
		while(
			evaluate: local Function of Boolean(){
				return running;
			},
			iteration: local Function(){
				local Int is idx: Buf:stringIndexOfFrom(b: self, needle: search, from: pos, def: -1);
				Conditional:if(check: { idx < 0 }, then: {
					running: false;
				}, else: {
					out: out . self:substring(start: pos, end: idx) . replacement;
					pos: idx + slen;
				});
			}
		);
		out: out . self:substring(start: pos, end: total);
		return out;
	}

	## Splits on [delimiter]; the trailing part is always present.
	##
	## @param delimiter: Split boundary.
	## @return: The parts.
	Function of Array of String is split(String is delimiter){
		local Array of String is res: [];
		local Int is slen: Buf:bufLength(b: self);
		Conditional:if(check: { slen == 0 }, then: {
			return res;
		});
		local Int is dlen: Buf:bufLength(b: delimiter);
		Conditional:if(check: { dlen == 0 }, then: {
			local Int is i: 0;
			while(
				evaluate: local Function of Boolean(){
					return i < slen;
				},
				iteration: local Function(){
					res:add(item: self:substring(start: i, end: i + 1));
					i: i + 1;
				}
			);
			return res;
		});
		local Int is pos: 0;
		local Boolean is running: true;
		while(
			evaluate: local Function of Boolean(){
				return running;
			},
			iteration: local Function(){
				local Int is idx: Buf:stringIndexOfFrom(b: self, needle: delimiter, from: pos, def: -1);
				Conditional:if(check: { idx < 0 }, then: {
					running: false;
				}, else: {
					res:add(item: self:substring(start: pos, end: idx));
					pos: idx + dlen;
				});
			}
		);
		res:add(item: self:substring(start: pos, end: slen));
		return res;
	}

	## Lines of this string (split on '\n', trailing '\r' stripped).
	##
	## @return: The lines.
	Function of Array of String is lines(){
		local Array of String is res: [];
		local Int is len: Buf:bufLength(b: self);
		Conditional:if(check: { len == 0 }, then: {
			return res;
		});
		local Int is start: 0;
		local Int is i: 0;
		while(
			evaluate: local Function of Boolean(){
				return i < len;
			},
			iteration: local Function(){
				local Int is b: Buf:bufGetByte(b: self, idx: i, def: -1);
				Conditional:if(check: { b == 10 }, then: {
					local Int is endIdx: i;
					Conditional:if(check: { endIdx > start }, then: {
						local Int is prev: Buf:bufGetByte(b: self, idx: endIdx - 1, def: -1);
						Conditional:if(check: { prev == 13 }, then: {
							endIdx: endIdx - 1;
						});
					});
					res:add(item: self:substring(start: start, end: endIdx));
					start: i + 1;
				});
				i: i + 1;
			}
		);
		Conditional:if(check: { start < len }, then: {
			local Int is endIdx: len;
			local Int is prev: Buf:bufGetByte(b: self, idx: endIdx - 1, def: -1);
			Conditional:if(check: { prev == 13 }, then: {
				endIdx: endIdx - 1;
			});
			res:add(item: self:substring(start: start, end: endIdx));
		});
		return res;
	}

	## Whitespace-trimmed copy (' ', '\t', '\n', '\r').
	##
	## @return: The trimmed copy.
	Function of String is trim(){
		local Int is len: Buf:bufLength(b: self);
		Conditional:if(check: { len == 0 }, then: {
			return '';
		});
		local Int is s: 0;
		local Boolean is sTrimming: true;
		while(
			evaluate: local Function of Boolean(){
				return sTrimming && (s < len);
			},
			iteration: local Function(){
				local Int is b: Buf:bufGetByte(b: self, idx: s, def: -1);
				Conditional:if(check: { b == 32 || b == 9 || b == 10 || b == 13 }, then: {
					s: s + 1;
				}, else: {
					sTrimming: false;
				});
			}
		);
		Conditional:if(check: { s >= len }, then: {
			return '';
		});
		local Int is e: len;
		local Boolean is eTrimming: true;
		while(
			evaluate: local Function of Boolean(){
				return eTrimming && (e > s);
			},
			iteration: local Function(){
				local Int is b: Buf:bufGetByte(b: self, idx: e - 1, def: -1);
				Conditional:if(check: { b == 32 || b == 9 || b == 10 || b == 13 }, then: {
					e: e - 1;
				}, else: {
					eTrimming: false;
				});
			}
		);
		return self:substring(start: s, end: e);
	}

	## Number of leading [search] repetitions.
	##
	## @param search: The repetition unit.
	## @return: Repetition count.
	Function of Int is countLeading(String is search){
		local Int is slen: Buf:bufLength(b: search);
		local Int is blen: Buf:bufLength(b: self);
		Conditional:if(check: { slen == 0 || blen == 0 }, then: {
			return 0;
		});
		local Int is count: 0;
		local Int is pos: 0;
		local Boolean is matching: true;
		while(
			evaluate: local Function of Boolean(){
				return matching && (pos + slen <= blen);
			},
			iteration: local Function(){
				Conditional:if(check: { Buf:stringSubstring(b: self, start: pos, end: pos + slen) == search }, then: {
					count: count + 1;
					pos: pos + slen;
				}, else: {
					matching: false;
				});
			}
		);
		return count;
	}

	## True when every byte is a digit and the string is non-empty.
	##
	## @return: true when all digits.
	Function of Boolean is isDigit(){
		local Int is n: Buf:bufLength(b: self);
		Conditional:if(check: { n == 0 }, then: {
			return false;
		});
		local Int is i: 0;
		local Boolean is ok: true;
		while(
			evaluate: local Function of Boolean(){
				return ok && (i < n);
			},
			iteration: local Function(){
				local Int is b: Buf:bufGetByte(b: self, idx: i, def: -1);
				Conditional:if(check: { b < 48 || b > 57 }, then: {
					ok: false;
				});
				i: i + 1;
			}
		);
		return ok;
	}

	## True when every byte is a letter and the string is non-empty.
	##
	## @return: true when all letters.
	Function of Boolean is isAlpha(){
		local Int is n: Buf:bufLength(b: self);
		Conditional:if(check: { n == 0 }, then: {
			return false;
		});
		local Int is i: 0;
		local Boolean is ok: true;
		while(
			evaluate: local Function of Boolean(){
				return ok && (i < n);
			},
			iteration: local Function(){
				local Int is b: Buf:bufGetByte(b: self, idx: i, def: -1);
				local Boolean is isUpper: (b >= 65 && b <= 90);
				local Boolean is isLower: (b >= 97 && b <= 122);
				Conditional:if(check: { !isUpper && !isLower }, then: {
					ok: false;
				});
				i: i + 1;
			}
		);
		return ok;
	}

	## True when every byte is whitespace and the string is non-empty.
	##
	## @return: true when all whitespace.
	Function of Boolean is isWhitespace(){
		local Int is n: Buf:bufLength(b: self);
		Conditional:if(check: { n == 0 }, then: {
			return false;
		});
		local Int is i: 0;
		local Boolean is ok: true;
		while(
			evaluate: local Function of Boolean(){
				return ok && (i < n);
			},
			iteration: local Function(){
				local Int is b: Buf:bufGetByte(b: self, idx: i, def: -1);
				Conditional:if(check: { b != 32 && b != 9 && b != 10 && b != 13 && b != 11 && b != 12 }, then: {
					ok: false;
				});
				i: i + 1;
			}
		);
		return ok;
	}

	## One-character string for [code] (0-255); empty when out of range.
	##
	## @param code: The byte value.
	## @return: The single-character string.
	Function of String is fromCharCode(Int is code){
	}

	## Parses this string as an integer in [base] (2-36), accepting 0x/0b/0o
	## prefixes and _ separators. Returns [default] on any invalid input.
	##
	## @param base: Number base (2-36).
	## @param default: Fallback on invalid input.
	## @return: The parsed value, or [default].
	Function of Int is parseInt(Int is base: 10, Int is default: -1){
		local Int is len: Buf:bufLength(b: self);
		Conditional:if(check: { len == 0 }, then: {
			return default;
		});
		local Int is b: base;
		local Int is start: 0;
		Conditional:if(check: { len >= 2 && Buf:bufGetByte(b: self, idx: 0, def: -1) == 48 }, then: {
			local Int is prefixCh: Buf:bufGetByte(b: self, idx: 1, def: -1);
			Conditional:if(check: { prefixCh == 120 || prefixCh == 88 }, then: {
				b: 16;
				start: 2;
			}, else: {
				Conditional:if(check: { prefixCh == 98 || prefixCh == 66 }, then: {
					b: 2;
					start: 2;
				}, else: {
					Conditional:if(check: { prefixCh == 111 || prefixCh == 79 }, then: {
						b: 8;
						start: 2;
					});
				});
			});
		});
		Conditional:if(check: { b < 2 || b > 36 }, then: {
			return default;
		});
		local Boolean is neg: false;
		Conditional:if(check: { start < len && Buf:bufGetByte(b: self, idx: start, def: -1) == 45 }, then: {
			neg: true;
			start: start + 1;
		});
		Conditional:if(check: { start >= len }, then: {
			return default;
		});
		local Int is val: 0;
		local Int is i: start;
		local Boolean is ok: true;
		local Boolean is anyDigits: false;
		while(
			evaluate: local Function of Boolean(){
				return ok && (i < len);
			},
			iteration: local Function(){
				local Int is ch: Buf:bufGetByte(b: self, idx: i, def: -1);
				Conditional:if(check: { ch != 95 }, then: {
					local Int is digit: -1;
					Conditional:if(check: { ch >= 48 && ch <= 57 }, then: {
						digit: ch - 48;
					}, else: {
						Conditional:if(check: { ch >= 97 && ch <= 122 }, then: {
							digit: ch - 97 + 10;
						}, else: {
							Conditional:if(check: { ch >= 65 && ch <= 90 }, then: {
								digit: ch - 65 + 10;
							});
						});
					});
					Conditional:if(check: { digit < 0 || digit >= b }, then: {
						ok: false;
					}, else: {
						val: (val * b) + digit;
						anyDigits: true;
					});
				});
				i: i + 1;
			}
		);
		Conditional:if(check: { !ok || !anyDigits }, then: {
			return default;
		});
		Conditional:if(check: { neg }, then: {
			return -val;
		});
		return val;
	}
}
