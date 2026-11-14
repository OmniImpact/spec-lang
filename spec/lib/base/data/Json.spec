#! Package base:data
#! JSON parser, stringifier, and pretty printer.

Class is Json{
	namespace: ['base', 'data'];

	replace Array of Array of String is using: [
		['base', 'data', JsonNull],
		['base', 'data', JsonBool],
		['base', 'data', JsonNumber],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Buf()],
		['base', 'sys', as Introspection()]
	];

	local Int is parsePos: 0;
	local Int is textLen: 0;
	local Boolean is parseFailed: false;
	local String is parseError: '';

	## Returns a JSON null instance.
	Function of JsonNull is nullValue(){
		return JsonNull:init();
	}

	## True if the value represents JSON null.
	Function of Boolean is isNull(Any is value){
		local String is t: Introspection:typeIdentity(obj: value);
		return t == 'base:data:JsonNull' || t == 'JsonNull';
	}

	## Wraps a boolean in a JsonBool.
	Function of JsonBool is bool(Boolean is b){
		return JsonBool:init(value: b);
	}

	## Wraps an integer in a JsonNumber.
	Function of JsonNumber is number(Int is n){
		return JsonNumber:init(rawText: n as String, isFloating: false);
	}

	## Wraps a float in a JsonNumber.
	Function of JsonNumber is numberFloat(Float is f){
		return JsonNumber:init(rawText: f as String, isFloating: true);
	}

	## Wraps raw numeric text in a JsonNumber.
	Function of JsonNumber is numberRaw(String is rawText, Boolean is isFloating){
		return JsonNumber:init(rawText: rawText, isFloating: isFloating);
	}

	## Safely extracts a String from an Any value holding a String.
	Function of String is asString(Any is val){
		return Buf:stringCopy(b: val);
	}

	Function of String is toStr(Any is val){
		return Buf:stringCopy(b: val);
	}

	## Whether the most recent parse operation encountered a syntax error.
	Function of Boolean is hasError(){
		return self:parseFailed;
	}

	## The diagnostic message for the most recent parse failure.
	Function of String is errorMessage(){
		return self:parseError;
	}

	## Looks up an integer value from a parsed JSON map.
	Function of Int is getInt(Map is obj, String is key, Int is default: 0){
		if({ !obj:has(key: key) }, {
			return default;
		});
		local Any is val: obj:get(key: key, default: '');
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'base:data:JsonNumber' || t == 'JsonNumber' }, {
			local JsonNumber is n: val as JsonNumber;
			return n:toInt(default: default);
		});
		if({ t == 'String' }, {
			local String is s: self:toStr(val: val);
			return s:parseInt(base: 10, default: default);
		});
		return default;
	}

	## Looks up a floating point value from a parsed JSON map.
	Function of Float is getFloat(Map is obj, String is key, Float is default: 0.0){
		if({ !obj:has(key: key) }, {
			return default;
		});
		local Any is val: obj:get(key: key, default: '');
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'base:data:JsonNumber' || t == 'JsonNumber' }, {
			local JsonNumber is n: val as JsonNumber;
			return n:toFloat(default: default);
		});
		if({ t == 'String' }, {
			local String is s: self:toStr(val: val);
			local JsonNumber is tempNum: JsonNumber:init(rawText: s, isFloating: true);
			return tempNum:toFloat(default: default);
		});
		return default;
	}

	## Looks up a string value from a parsed JSON map.
	Function of String is getString(Map is obj, String is key, String is default: ''){
		if({ !obj:has(key: key) }, {
			return default;
		});
		local Any is val: obj:get(key: key, default: '');
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'String' }, {
			return self:toStr(val: val);
		});
		if({ t == 'base:data:JsonNumber' || t == 'JsonNumber' }, {
			local JsonNumber is n: val as JsonNumber;
			return n:toString();
		});
		if({ t == 'base:data:JsonBool' || t == 'JsonBool' }, {
			local JsonBool is b: val as JsonBool;
			return b:toString();
		});
		return default;
	}

	## Looks up a boolean value from a parsed JSON map.
	Function of Boolean is getBool(Map is obj, String is key, Boolean is default: false){
		if({ !obj:has(key: key) }, {
			return default;
		});
		local Any is val: obj:get(key: key, default: '');
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'base:data:JsonBool' || t == 'JsonBool' }, {
			local JsonBool is b: val as JsonBool;
			return b:value();
		});
		if({ t == 'String' }, {
			local String is s: self:toStr(val: val);
			if({ s == 'true' }, {
				return true;
			});
			if({ s == 'false' }, {
				return false;
			});
		});
		return default;
	}

	## Looks up a nested Map from a parsed JSON map.
	Function of Map is getObject(Map is obj, String is key){
		if({ !obj:has(key: key) }, {
			return Map:init();
		});
		local Any is val: obj:get(key: key, default: Map:init());
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'Map' }, {
			return val as Map;
		});
		return Map:init();
	}

	## Looks up a nested Array from a parsed JSON map.
	Function of Array is getArray(Map is obj, String is key){
		if({ !obj:has(key: key) }, {
			return [];
		});
		local Any is val: obj:get(key: key, default: []);
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'Array' }, {
			return val as Array;
		});
		return [];
	}

	## Looks up an integer value from a parsed JSON array.
	Function of Int is getIntAt(Array is arr, Int is index, Int is default: 0){
		if({ index < 0 || index >= arr:length() }, {
			return default;
		});
		local Any is val: arr:get(index: index, default: '');
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'base:data:JsonNumber' || t == 'JsonNumber' }, {
			local JsonNumber is n: val as JsonNumber;
			return n:toInt(default: default);
		});
		if({ t == 'String' }, {
			local String is s: self:toStr(val: val);
			return s:parseInt(base: 10, default: default);
		});
		return default;
	}

	## Looks up a string value from a parsed JSON array.
	Function of String is getStringAt(Array is arr, Int is index, String is default: ''){
		if({ index < 0 || index >= arr:length() }, {
			return default;
		});
		local Any is val: arr:get(index: index, default: '');
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'String' }, {
			return self:toStr(val: val);
		});
		if({ t == 'base:data:JsonNumber' || t == 'JsonNumber' }, {
			local JsonNumber is n: val as JsonNumber;
			return n:toString();
		});
		if({ t == 'base:data:JsonBool' || t == 'JsonBool' }, {
			local JsonBool is b: val as JsonBool;
			return b:toString();
		});
		return default;
	}

	## Looks up a boolean value from a parsed JSON array.
	Function of Boolean is getBoolAt(Array is arr, Int is index, Boolean is default: false){
		if({ index < 0 || index >= arr:length() }, {
			return default;
		});
		local Any is val: arr:get(index: index, default: '');
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'base:data:JsonBool' || t == 'JsonBool' }, {
			local JsonBool is b: val as JsonBool;
			return b:value();
		});
		if({ t == 'String' }, {
			local String is s: self:toStr(val: val);
			if({ s == 'true' }, {
				return true;
			});
			if({ s == 'false' }, {
				return false;
			});
		});
		return default;
	}

	## Looks up a float value from a parsed JSON array.
	Function of Float is getFloatAt(Array is arr, Int is index, Float is default: 0.0){
		if({ index < 0 || index >= arr:length() }, {
			return default;
		});
		local Any is val: arr:get(index: index, default: '');
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'base:data:JsonNumber' || t == 'JsonNumber' }, {
			local JsonNumber is n: val as JsonNumber;
			return n:toFloat(default: default);
		});
		if({ t == 'String' }, {
			local String is s: self:toStr(val: val);
			local JsonNumber is tempNum: JsonNumber:init(rawText: s, isFloating: true);
			return tempNum:toFloat(default: default);
		});
		return default;
	}

	## Looks up a nested Map from a parsed JSON array.
	Function of Map is getObjectAt(Array is arr, Int is index){
		if({ index < 0 || index >= arr:length() }, {
			return Map:init();
		});
		local Any is val: arr:get(index: index, default: Map:init());
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'Map' }, {
			return val as Map;
		});
		return Map:init();
	}

	## Looks up a nested Array from a parsed JSON array.
	Function of Array is getArrayAt(Array is arr, Int is index){
		if({ index < 0 || index >= arr:length() }, {
			return [];
		});
		local Any is val: arr:get(index: index, default: []);
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'Array' }, {
			return val as Array;
		});
		return [];
	}

	## Advances parse position past ASCII whitespace.
	Function is skipWhitespace(String is text){
		local Boolean is checking: true;
		while({ checking && (self:parsePos < self:textLen) }, {
			local Int is b: Buf:bufGetByte(b: text, idx: self:parsePos, def: -1);
			if({ b == 32 || b == 9 || b == 10 || b == 13 }, {
				self:parsePos: self:parsePos + 1;
			}, {
				checking: false;
			});
		});
	}

	## Converts a Unicode code point to a UTF-8 encoded String.
	Function of String is codePointToUtf8(Int is cp){
		if({ cp < 128 }, {
			return String:fromCharCode(code: cp);
		});
		if({ cp < 2048 }, {
			local Int is b1: 192 + (cp / 64);
			local Int is b2: 128 + (cp % 64);
			return String:fromCharCode(code: b1) . String:fromCharCode(code: b2);
		});
		local Int is b1: 224 + (cp / 4096);
		local Int is b2: 128 + ((cp / 64) % 64);
		local Int is b3: 128 + (cp % 64);
		return String:fromCharCode(code: b1) . String:fromCharCode(code: b2) . String:fromCharCode(code: b3);
	}

	## Parses a JSON string literal at the current position.
	Function of String is parseString(String is text){
		self:parsePos: self:parsePos + 1;
		local Int is startPos: self:parsePos;
		local String is out: '';
		local Boolean is scanning: true;
		local Boolean is closed: false;

		while({ scanning && (self:parsePos < self:textLen) }, {
			local Int is b: Buf:bufGetByte(b: text, idx: self:parsePos, def: -1);
			if({ b < 0 }, {
				self:parseFailed: true;
				self:parseError: 'Unexpected end of input inside string literal';
				scanning: false;
			});
			if({ scanning && b == 92 }, {
				if({ self:parsePos > startPos }, {
					out: out . text:substring(start: startPos, end: self:parsePos);
				});
				self:parsePos: self:parsePos + 1;
				local Int is esc: Buf:bufGetByte(b: text, idx: self:parsePos, def: -1);
				if({ esc == 34 }, {
					out: out . '"';
				});
				if({ esc == 92 }, {
					out: out . '\\';
				});
				if({ esc == 47 }, {
					out: out . '/';
				});
				if({ esc == 98 }, {
					out: out . String:fromCharCode(code: 8);
				});
				if({ esc == 102 }, {
					out: out . String:fromCharCode(code: 12);
				});
				if({ esc == 110 }, {
					out: out . "\n";
				});
				if({ esc == 114 }, {
					out: out . String:fromCharCode(code: 13);
				});
				if({ esc == 116 }, {
					out: out . "\t";
				});
				if({ esc == 117 }, {
					if({ self:parsePos + 4 < self:textLen }, {
						local String is hexStr: text:substring(start: self:parsePos + 1, end: self:parsePos + 5);
						local Int is cp: hexStr:parseInt(base: 16, default: 0);
						out: out . self:codePointToUtf8(cp: cp);
						self:parsePos: self:parsePos + 4;
					}, {
						self:parseFailed: true;
						self:parseError: 'Incomplete \\uXXXX escape sequence';
						scanning: false;
					});
				});
				self:parsePos: self:parsePos + 1;
				startPos: self:parsePos;
			}, {
				if({ scanning && b == 34 }, {
					if({ self:parsePos > startPos }, {
						out: out . text:substring(start: startPos, end: self:parsePos);
					});
					self:parsePos: self:parsePos + 1;
					closed: true;
					scanning: false;
				}, {
					if({ scanning }, {
						self:parsePos: self:parsePos + 1;
					});
				});
			});
		});
		if({ !closed && !self:parseFailed }, {
			self:parseFailed: true;
			self:parseError: 'Unclosed string literal';
		});
		return out;
	}

	## Parses a JSON numeric literal at the current position.
	Function of JsonNumber is parseNumber(String is text){
		local Int is start: self:parsePos;
		local Boolean is isFloating: false;

		if({ self:parsePos < self:textLen && Buf:bufGetByte(b: text, idx: self:parsePos, def: -1) == 45 }, {
			self:parsePos: self:parsePos + 1;
		});

		local Boolean is readingInt: true;
		while({ readingInt && (self:parsePos < self:textLen) }, {
			local Int is b: Buf:bufGetByte(b: text, idx: self:parsePos, def: -1);
			if({ b >= 48 && b <= 57 }, {
				self:parsePos: self:parsePos + 1;
			}, {
				readingInt: false;
			});
		});

		if({ self:parsePos < self:textLen && Buf:bufGetByte(b: text, idx: self:parsePos, def: -1) == 46 }, {
			isFloating: true;
			self:parsePos: self:parsePos + 1;
			local Boolean is readingFrac: true;
			while({ readingFrac && (self:parsePos < self:textLen) }, {
				local Int is b: Buf:bufGetByte(b: text, idx: self:parsePos, def: -1);
				if({ b >= 48 && b <= 57 }, {
					self:parsePos: self:parsePos + 1;
				}, {
					readingFrac: false;
				});
			});
		});

		if({ self:parsePos < self:textLen }, {
			local Int is expCh: Buf:bufGetByte(b: text, idx: self:parsePos, def: -1);
			if({ expCh == 101 || expCh == 69 }, {
				isFloating: true;
				self:parsePos: self:parsePos + 1;
				if({ self:parsePos < self:textLen }, {
					local Int is signCh: Buf:bufGetByte(b: text, idx: self:parsePos, def: -1);
					if({ signCh == 43 || signCh == 45 }, {
						self:parsePos: self:parsePos + 1;
					});
				});
				local Boolean is readingExp: true;
				while({ readingExp && (self:parsePos < self:textLen) }, {
					local Int is b: Buf:bufGetByte(b: text, idx: self:parsePos, def: -1);
					if({ b >= 48 && b <= 57 }, {
					self:parsePos: self:parsePos + 1;
					}, {
						readingExp: false;
					});
				});
			});
		});

		local String is numStr: text:substring(start: start, end: self:parsePos);
		if({ numStr == '-' || numStr == '' }, {
			self:parseFailed: true;
			self:parseError: 'Invalid number literal';
		});
		return self:numberRaw(rawText: numStr, isFloating: isFloating);
	}

	## Parses a JSON array at the current position.
	Function of Array is parseArray(String is text){
		local Array of Any is arr: [];
		self:parsePos: self:parsePos + 1;
		self:skipWhitespace(text: text);

		if({ self:parsePos < self:textLen && Buf:bufGetByte(b: text, idx: self:parsePos, def: -1) == 93 }, {
			self:parsePos: self:parsePos + 1;
			return arr;
		});

		local Boolean is parsing: true;
		local Boolean is closed: false;
		while({ parsing && !self:parseFailed && (self:parsePos < self:textLen) }, {
			local Any is item: self:parseValue(text: text);
			arr:add(item: item);
			self:skipWhitespace(text: text);
			local Int is nextCh: Buf:bufGetByte(b: text, idx: self:parsePos, def: -1);
			if({ nextCh == 44 }, {
				self:parsePos: self:parsePos + 1;
			}, {
				if({ nextCh == 93 }, {
					self:parsePos: self:parsePos + 1;
					closed: true;
					parsing: false;
				}, {
					self:parseFailed: true;
					self:parseError: 'Expected \x27,\x27 or \x27]\x27 in array';
					parsing: false;
				});
			});
		});
		if({ !closed && !self:parseFailed }, {
			self:parseFailed: true;
			self:parseError: 'Unclosed array, expected \x27]\x27';
		});
		return arr;
	}

	## Parses a JSON object at the current position.
	Function of Map is parseObject(String is text){
		local Map is obj: Map:init();
		self:parsePos: self:parsePos + 1;
		self:skipWhitespace(text: text);

		if({ self:parsePos < self:textLen && Buf:bufGetByte(b: text, idx: self:parsePos, def: -1) == 125 }, {
			self:parsePos: self:parsePos + 1;
			return obj;
		});

		local Boolean is parsing: true;
		local Boolean is closed: false;
		while({ parsing && !self:parseFailed && (self:parsePos < self:textLen) }, {
			self:skipWhitespace(text: text);
			if({ Buf:bufGetByte(b: text, idx: self:parsePos, def: -1) != 34 }, {
				self:parseFailed: true;
				self:parseError: 'Expected string key in object';
				return obj;
			});
			local String is key: self:parseString(text: text);
			self:skipWhitespace(text: text);
			if({ Buf:bufGetByte(b: text, idx: self:parsePos, def: -1) != 58 }, {
				self:parseFailed: true;
				self:parseError: 'Expected \x27:\x27 after key in object';
				return obj;
			});
			self:parsePos: self:parsePos + 1;
			local Any is val: self:parseValue(text: text);
			obj:set(key: key, value: val);
			self:skipWhitespace(text: text);
			local Int is nextCh: Buf:bufGetByte(b: text, idx: self:parsePos, def: -1);
			if({ nextCh == 44 }, {
				self:parsePos: self:parsePos + 1;
			}, {
				if({ nextCh == 125 }, {
					self:parsePos: self:parsePos + 1;
					closed: true;
					parsing: false;
				}, {
					self:parseFailed: true;
					self:parseError: 'Expected \x27,\x27 or \x27}\x27 in object';
					parsing: false;
				});
			});
		});
		if({ !closed && !self:parseFailed }, {
			self:parseFailed: true;
			self:parseError: 'Unclosed object, expected \x27}\x27';
		});
		return obj;
	}

	## Parses a JSON value at the current position.
	Function of Any is parseValue(String is text){
		self:skipWhitespace(text: text);
		if({ self:parsePos >= self:textLen }, {
			self:parseFailed: true;
			self:parseError: 'Unexpected end of input';
			return self:nullValue();
		});

		local Int is b: Buf:bufGetByte(b: text, idx: self:parsePos, def: -1);
		if({ b == 123 }, {
			return self:parseObject(text: text);
		});
		if({ b == 91 }, {
			return self:parseArray(text: text);
		});
		if({ b == 34 }, {
			return self:parseString(text: text);
		});
		if({ b == 116 }, {
			if({ self:parsePos + 4 <= self:textLen && text:substring(start: self:parsePos, end: self:parsePos + 4) == 'true' }, {
				self:parsePos: self:parsePos + 4;
				return self:bool(b: true);
			});
		});
		if({ b == 102 }, {
			if({ self:parsePos + 5 <= self:textLen && text:substring(start: self:parsePos, end: self:parsePos + 5) == 'false' }, {
				self:parsePos: self:parsePos + 5;
				return self:bool(b: false);
			});
		});
		if({ b == 110 }, {
			if({ self:parsePos + 4 <= self:textLen && text:substring(start: self:parsePos, end: self:parsePos + 4) == 'null' }, {
				self:parsePos: self:parsePos + 4;
				return self:nullValue();
			});
		});
		if({ b == 45 || (b >= 48 && b <= 57) }, {
			return self:parseNumber(text: text);
		});

		self:parseFailed: true;
		self:parseError: 'Unexpected character \x27' . text:substring(start: self:parsePos, end: self:parsePos + 1) . '\x27 at offset ' . (self:parsePos as String);
		return self:nullValue();
	}

	## Parses JSON text into Spec data structures.
	Function of Any is parse(String is text, Any is default: ''){
		self:parsePos: 0;
		self:textLen: text:length();
		self:parseFailed: false;
		self:parseError: '';

		if({ self:textLen == 0 }, {
			self:parseFailed: true;
			self:parseError: 'Empty input';
			return default;
		});

		self:skipWhitespace(text: text);
		if({ self:parsePos >= self:textLen }, {
			self:parseFailed: true;
			self:parseError: 'Empty input';
			return default;
		});

		local Any is res: self:parseValue(text: text);
		self:skipWhitespace(text: text);
		if({ self:parseFailed || (self:parsePos < self:textLen) }, {
			if({ !self:parseFailed }, {
				self:parseFailed: true;
				self:parseError: 'Unexpected trailing data at offset ' . (self:parsePos as String);
			});
			return default;
		});
		return res;
	}

	## Parses JSON text directly into a Map.
	Function of Map is parseObjectText(String is text){
		local Any is res: self:parse(text: text, default: Map:init());
		local String is t: Introspection:typeIdentity(obj: res);
		if({ t == 'Map' }, {
			return res as Map;
		});
		return Map:init();
	}

	## Parses JSON text directly into an Array.
	Function of Array is parseArrayText(String is text){
		local Any is res: self:parse(text: text, default: []);
		local String is t: Introspection:typeIdentity(obj: res);
		if({ t == 'Array' }, {
			return res as Array;
		});
		return [];
	}

	## Converts a single hex digit (0-15) to a lowercase character.
	Function of String is hexDigit(Int is d){
		local String is hexChars: '0123456789abcdef';
		if({ d >= 0 && d < 16 }, {
			return hexChars:substring(start: d, end: d + 1);
		});
		return '0';
	}

	## Escapes string contents according to JSON specification.
	Function of String is escapeString(String is str){
		local Int is len: str:length();
		local String is out: '';
		local Int is i: 0;

		while({ i < len }, {
			local Int is b: Buf:bufGetByte(b: str, idx: i, def: -1);
			if({ b == 34 }, {
				out: out . "\\\"";
			}, {
				if({ b == 92 }, {
					out: out . "\\\\";
				}, {
					if({ b == 10 }, {
						out: out . "\\n";
					}, {
						if({ b == 13 }, {
							out: out . "\\r";
						}, {
							if({ b == 9 }, {
								out: out . "\\t";
							}, {
								if({ b == 8 }, {
									out: out . "\\b";
								}, {
									if({ b == 12 }, {
										out: out . "\\f";
									}, {
										if({ b < 32 }, {
											out: out . "\\u00" . self:hexDigit(d: b / 16) . self:hexDigit(d: b % 16);
										}, {
											out: out . String:fromCharCode(code: b);
										});
									});
								});
							});
						});
					});
				});
			});
			i: i + 1;
		});
		return out;
	}

	## Serializes a Spec value into a compact JSON string.
	Function of String is stringify(Any is value){
		if({ self:isNull(value: value) }, {
			return 'null';
		});

		local String is t: Introspection:typeIdentity(obj: value);
		if({ t == 'base:data:JsonNull' || t == 'JsonNull' }, {
			return 'null';
		});
		if({ t == 'base:data:JsonBool' || t == 'JsonBool' }, {
			local JsonBool is jb: value as JsonBool;
			return jb:toString();
		});
		if({ t == 'base:data:JsonNumber' || t == 'JsonNumber' }, {
			local JsonNumber is jn: value as JsonNumber;
			return jn:toString();
		});
		if({ t == 'String' }, {
			return '"' . self:escapeString(str: self:toStr(val: value)) . '"';
		});
		if({ t == 'Array' }, {
			local Array of Any is arr: value as Array;
			local String is out: '[';
			local Int is len: arr:length();
			local Int is i: 0;
			while({ i < len }, {
				if({ i > 0 }, {
					out: out . ',';
				});
				out: out . self:stringify(value: arr:get(index: i, default: ''));
				i: i + 1;
			});
			return out . ']';
		});
		if({ t == 'Map' }, {
			local Map is m: value as Map;
			local Array of String is keys: m:keys();
			local String is out: '{';
			local Int is len: keys:length();
			local Int is i: 0;
			while({ i < len }, {
				if({ i > 0 }, {
					out: out . ',';
				});
				local String is k: keys:get(index: i, default: '');
				out: out . '"' . self:escapeString(str: k) . '":' . self:stringify(value: m:get(key: k, default: ''));
				i: i + 1;
			});
			return out . '}';
		});
		if({ t == '' }, {
			return 'null';
		});
		return '"' . self:escapeString(str: self:toStr(val: value)) . '"';
	}

	## Generates indentation whitespace.
	Function of String is indentSpaces(Int is level, Int is indentStep){
		local Int is total: level * indentStep;
		local String is sp: '';
		while({ sp:length() < total }, {
			sp: sp . ' ';
		});
		return sp;
	}

	## Recursive formatter for pretty-printed JSON.
	Function of String is formatInner(Any is value, Int is level, Int is indent){
		if({ self:isNull(value: value) }, {
			return 'null';
		});

		local String is t: Introspection:typeIdentity(obj: value);
		if({ t == 'Array' }, {
			local Array of Any is arr: value as Array;
			local Int is aLen: arr:length();
			if({ aLen == 0 }, {
				return '[]';
			});
			local String is out: "[\n";
			local Int is ai: 0;
			while({ ai < aLen }, {
				out: out . self:indentSpaces(level: level + 1, indentStep: indent) . self:formatInner(value: arr:get(index: ai, default: ''), level: level + 1, indent: indent);
				if({ ai + 1 < aLen }, {
					out: out . ',';
				});
				out: out . "\n";
				ai: ai + 1;
			});
			out: out . self:indentSpaces(level: level, indentStep: indent) . ']';
			return out;
		});
		if({ t == 'Map' }, {
			local Map is m: value as Map;
			local Array of String is keys: m:keys();
			local Int is kLen: keys:length();
			if({ kLen == 0 }, {
				return '{}';
			});
			local String is out: "{\n";
			local Int is ki: 0;
			while({ ki < kLen }, {
				local String is k: keys:get(index: ki, default: '');
				out: out . self:indentSpaces(level: level + 1, indentStep: indent) . '"' . self:escapeString(str: k) . '": ' . self:formatInner(value: m:get(key: k, default: ''), level: level + 1, indent: indent);
				if({ ki + 1 < kLen }, {
					out: out . ',';
				});
				out: out . "\n";
				ki: ki + 1;
			});
			out: out . self:indentSpaces(level: level, indentStep: indent) . '}';
			return out;
		});
		return self:stringify(value: value);
	}

	## Formats a Spec value into pretty-printed JSON with indentation.
	Function of String is format(Any is value, Int is indent: 2){
		return self:formatInner(value: value, level: 0, indent: indent);
	}
}
