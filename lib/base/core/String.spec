#! Package base:core
#! The String type: a refcounted, NUL-terminated byte buffer with a cached length.
##
## String is a transparent builtin class. The type system and class registry
## know its method surface (signatures below), but no C struct, vtable, or
## constructor is emitted for the class: a String value IS the managed buffer
## (`SpecBuf*`), and method calls dispatch through the runtime's C floor
## (`spec_string_*`). Method bodies arrive when the sysinternal binding lands.

Class is String{

	## Number of bytes in this string.
	Function of Int is length(){
		return Buf:bufLength(self);
	}

	## One-character string at [index], or [default] when out of bounds.
	Function of String is charAt(Int is index, String is default){
		if (index < 0 || index >= Buf:bufLength(b: self)) {
			return Buf:stringCopy(b: default);
		}
		return String:fromCharCode(code: Buf:bufGetByte(b: self, idx: index, def: -1));
	}

	## Bytes from [start] (inclusive) to [end] (exclusive), clamped to bounds.
	Function of String is substring(Int is start, Int is end){
		local Int is s: start;
		local Int is e: end;
		if (s < 0) {
			s: 0;
		}
		if (e > Buf:bufLength(b: self)) {
			e: Buf:bufLength(b: self);
		}
		return Buf:stringSubstring(b: self, start: s, end: e);
	}

	## True when this string begins with [prefix].
	Function of Boolean is startsWith(String is prefix){
		local Int is pl: Buf:bufLength(b: prefix);
		if (pl == 0) {
			return true;
		}
		if (pl > Buf:bufLength(b: self)) {
			return false;
		}
		return Buf:stringSubstring(b: self, start: 0, end: pl) == prefix;
	}

	## True when this string ends with [suffix].
	Function of Boolean is endsWith(String is suffix){
		local Int is sl: Buf:bufLength(b: suffix);
		if (sl == 0) {
			return true;
		}
		local Int is bl: Buf:bufLength(b: self);
		if (sl > bl) {
			return false;
		}
		return Buf:stringSubstring(b: self, start: bl - sl, end: bl) == suffix;
	}

	## True when [needle] occurs anywhere in this string (empty needle: true).
	Function of Boolean is contains(String is needle){
		return self:indexOf(search: needle, default: -1) >= 0;
	}

	## First occurrence of [needle] at or after the start, or [default].
	Function of Int is indexOf(String is search, Int is default){
		return Buf:stringIndexOf(b: self, needle: search, def: default);
	}

	## Every [search] occurrence replaced by [replacement].
	Function of String is replaceAll(String is search, String is replacement){
		return Buf:stringReplaceAll(b: self, search: search, replacement: replacement);
	}

	## Splits on [delimiter]; the trailing part is always present.
	Function of Array of String is split(String is delimiter){
		return Buf:stringSplit(b: self, delimiter: delimiter);
	}

	## Lines of this string (split on '\n', '\r' stripped).
	Function of Array of String is lines(){
		return Buf:stringLines(b: self);
	}

	## Whitespace-trimmed copy (' ', '\t', '\n', '\r').
	Function of String is trim(){
		return Buf:stringTrim(b: self);
	}

	## Number of leading [search] repetitions.
	Function of Int is countLeading(String is search){
		return Buf:stringCountLeading(b: self, search: search);
	}

	## True when every byte is a digit and the string is non-empty.
	Function of Boolean is isDigit(){
		return Buf:stringIsDigit(b: self);
	}

	## True when every byte is a letter and the string is non-empty.
	Function of Boolean is isAlpha(){
		return Buf:stringIsAlpha(b: self);
	}

	## True when every byte is whitespace and the string is non-empty.
	Function of Boolean is isWhitespace(){
		return Buf:stringIsWhitespace(b: self);
	}

	## One-character string for [code] (0-255); empty when out of range.
	Function of String is fromCharCode(Int is code){
	}

	## Parses this string as an integer in [base] (2-36), accepting 0x/0b/0o
	## prefixes and _ separators. Returns [default] on any invalid input.
	Function of Int is parseInt(Int is base: 10, Int is default: -1){
		return Buf:parseBase(b: self, base: base, def: default);
	}
}
