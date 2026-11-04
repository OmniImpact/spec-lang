#! Package sys
#! The String type: an immutable sequence of bytes backed by [Byte].
#! This is the canonical wrapper — all methods are pure Spec over the byte buffer.

## An immutable sequence of UTF-8 bytes.
##
## Construction: `local String is s: 'hello';` invokes the String constructor,
## which wraps the literal bytes in a [Byte] buffer. All methods are pure Spec
## over that buffer. Strings are immutable — every mutating operation returns
## a new String.
Class is String{

	## The internal byte buffer. Only visible to sys:String methods.
	local [Byte] is data;

	## Constructs from a byte buffer (the canonical construction path).
	Function is init([Byte] is bytes){
		self:data: bytes;
	}

	## Constructs from a literal (the : assignment path — the compiler
	## converts the literal to a [Byte] and calls this constructor).
	Function is initFromLiteral(String is literal){
		local [Byte] is buf;
		buf:appendString(value: literal);
		self:data: buf;
	}

	## Number of bytes.
	Function of Int is length(){
		return self:data:length();
	}

	## Single byte at [index] as a one-byte String, or [default] when out of bounds.
	Function of String is charAt(Int is index, String is default: ''){
		local Byte is b: self:data:get(index: index, default: 0 as Byte);
		if (b as Int == 0 && index >= self:data:length()) {
			return default;
		}
		return String:fromCharCode(code: b as Int);
	}

	## Bytes from [start] up to (exclusive) [end], clamped.
	Function of String is substring(Int is start: 0, Int is end: 0){
		local Int is len: self:data:length();
		local Int is s: if (start < 0) 0 else start;
		local Int is e: if (end > len) len else end;
		if (s >= e) {
			return '';
		}
		local [Byte] is sub;
		local Int is i: s;
		While:condition(
			evaluate: local Function of Boolean(){ return i < e; },
			iteration: local Function(){
				sub:push(item: self:data:get(index: i, default: 0 as Byte));
				i: i + 1;
			}
		);
		return String:fromBytes(bytes: sub);
	}

	## First position of [search], or [default] when absent.
	Function of Int is indexOf(String is search, Int is default: -1){
		local Int is slen: search:length();
		local Int is len: self:data:length();
		if (slen == 0) {
			return 0;
		}
		local Int is pos: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return pos + slen <= len;
			},
			iteration: local Function(){
				if (self:substring(start: pos, end: pos + slen) == search) {
					pos: -2;
					return;
				}
				pos: pos + 1;
			}
		);
		if (pos == -2) {
			return pos + 2;
		}
		return default;
	}

	## True when the string starts with [prefix].
	Function of Boolean is startsWith(String is prefix){
		local Int is plen: prefix:length();
		if (self:length() < plen) {
			return false;
		}
		return self:substring(start: 0, end: plen) == prefix;
	}

	## True when the string ends with [suffix].
	Function of Boolean is endsWith(String is suffix){
		local Int is offset: self:length() - suffix:length();
		if (offset < 0) {
			return false;
		}
		return self:substring(start: offset, end: self:length()) == suffix;
	}

	## True when [needle] occurs anywhere in the string.
	Function of Boolean is contains(String is needle){
		return self:indexOf(search: needle, default: -1) >= 0;
	}

	## Copy with every occurrence of [search] replaced by [replacement].
	Function of String is replaceAll(String is search, String is replacement){
		local Int is slen: search:length();
		if (slen == 0) {
			return self;
		}
		local String is out: '';
		local Int is pos: 0;
		local Int is len: self:length();
		While:condition(
			evaluate: local Function of Boolean(){
				return pos + slen <= len;
			},
			iteration: local Function(){
				if (self:substring(start: pos, end: pos + slen) == search) {
					out: out . replacement;
					pos: pos + slen;
				} else {
					out: out . self:substring(start: pos, end: pos + 1);
					pos: pos + 1;
				}
			}
		);
		out: out . self:substring(start: pos, end: len);
		return out;
	}

	## Segments between occurrences of [delimiter]. An empty delimiter splits
	## into single bytes.
	Function of Array of String is split(String is delimiter){
		local Array of String is parts: [];
		local Int is slen: delimiter:length();
		local Int is len: self:length();
		if (slen == 0) {
			local Int is ci: 0;
			While:condition(
				evaluate: local Function of Boolean(){
					return ci < len;
				},
				iteration: local Function(){
					parts:add(item: self:substring(start: ci, end: ci + 1));
					ci: ci + 1;
				}
			);
			return parts;
		}
		local Int is start: 0;
		local Int is pos: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return pos + slen <= len;
			},
			iteration: local Function(){
				if (self:substring(start: pos, end: pos + slen) == delimiter) {
					parts:add(item: self:substring(start: start, end: pos));
					pos: pos + slen;
					start: pos;
				} else {
					pos: pos + 1;
				}
			}
		);
		parts:add(item: self:substring(start: start, end: len));
		return parts;
	}

	## Copy without leading and trailing whitespace.
	Function of String is trim(){
		local Int is start: 0;
		local Int is end: self:length();
		While:condition(
			evaluate: local Function of Boolean(){
				return start < end && self:substring(start: start, end: start + 1):isWhitespace();
			},
			iteration: local Function(){
				start: start + 1;
			}
		);
		While:condition(
			evaluate: local Function of Boolean(){
				return end > start && self:substring(start: end - 1, end: end):isWhitespace();
			},
			iteration: local Function(){
				end: end - 1;
			}
		);
		return self:substring(start: start, end: end);
	}

	## Lines between "\n" separators, each stripped of a trailing "\r".
	Function of Array of String is lines(){
		local Array of String is out: [];
		local Array of String is raw: self:split(delimiter: "\n");
		local Int is keep: raw:length();
		if (keep > 0 && raw:get(index: keep - 1, default: '') == '') {
			keep: keep - 1;
		}
		local Int is i: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return i < keep;
			},
			iteration: local Function(){
				local String is line: raw:get(index: i, default: '');
				local Int is ln: line:length();
				if (ln > 0 && line:substring(start: ln - 1, end: ln) == "\r") {
					line: line:substring(start: 0, end: ln - 1);
				}
				out:add(item: line);
				i: i + 1;
			}
		);
		return out;
	}

	## Number of leading occurrences of [search].
	Function of Int is countLeading(String is search){
		local Int is slen: search:length();
		if (slen == 0) {
			return 0;
		}
		local Int is count: 0;
		local Int is pos: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return self:substring(start: pos, end: pos + slen) == search;
			},
			iteration: local Function(){
				count: count + 1;
				pos: pos + slen;
			}
		);
		return count;
	}

	## True when the string is exactly one decimal digit.
	Function of Boolean is isDigit(){
		local String is c: self:substring(start: 0, end: 1);
		return c == '0' || c == '1' || c == '2' || c == '3' || c == '4' || c == '5' || c == '6' || c == '7' || c == '8' || c == '9';
	}

	## True when the string is exactly one ASCII letter.
	Function of Boolean is isAlpha(){
		local String is c: self:substring(start: 0, end: 1);
		return c == 'a' || c == 'b' || c == 'c' || c == 'd' || c == 'e' || c == 'f' || c == 'g' || c == 'h' || c == 'i' || c == 'j' || c == 'k' || c == 'l' || c == 'm' || c == 'n' || c == 'o' || c == 'p' || c == 'q' || c == 'r' || c == 's' || c == 't' || c == 'u' || c == 'v' || c == 'w' || c == 'x' || c == 'y' || c == 'z' || c == 'A' || c == 'B' || c == 'C' || c == 'D' || c == 'E' || c == 'F' || c == 'G' || c == 'H' || c == 'I' || c == 'J' || c == 'K' || c == 'L' || c == 'M' || c == 'N' || c == 'O' || c == 'P' || c == 'Q' || c == 'R' || c == 'S' || c == 'T' || c == 'U' || c == 'V' || c == 'W' || c == 'X' || c == 'Y' || c == 'Z';
	}

	## True when the string is exactly one whitespace byte.
	Function of Boolean is isWhitespace(){
		local String is c: self:substring(start: 0, end: 1);
		return c == " " || c == "\t" || c == "\n" || c == "\r";
	}

	## Returns the string itself (strings are already values).
	replace Function of String is toString(){
		return self;
	}

	## Returns the type name.
	Function of String is typeName(){
		return 'String';
	}

}
