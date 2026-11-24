#! Package base:data
#! JSON parser, stringifier, and pretty printer.

Class is Json{
	replace [String] is namespace: ['base', 'data'];

	replace [[String]] is using: [
		['base', 'core', Result],
		['base', 'core', SpecError],
		['base', 'data', JsonError],
		['base', 'data', JsonNull],
		['base', 'data', JsonBool],
		['base', 'data', JsonNumber],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Introspection()]
	];

	local Int is parsePos: 0;
	local Int is textLen: 0;

	## The empty JSON object every fallback returns.
	local Function of Map of String to Any is isEmptyMap(){
		local Map of String to Any is out: [:];
		return out;
	}

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
		return (val as String):copy();
	}

	Function of String is toStr(Any is val){
		return (val as String):copy();
	}

	## Raises a SYNTAX_ERROR currency with [msg] as the description
	## (offsets ride it). The parser's internal transport: a malformed
	## document unwinds from deep in the recursion to the public face,
	## which converts it to a result (or a default) at the boundary.
	local Function is syntaxFail(String is msg){
		:raiseError(error: SpecError:init(kind: JsonError:SYNTAX_ERROR, description: msg));
	}

	## Parses a complete JSON document, raising the error currency on any
	## failure. The core the public faces unwrap.
	local Function of Any is parseText(String is text){
		:parsePos: 0;
		:textLen: text:length();

		if({ :textLen == 0 }, {
			:syntaxFail(msg: 'Empty input');
		});

		:skipWhitespace(text: text);
		if({ :parsePos >= :textLen }, {
			:syntaxFail(msg: 'Empty input');
		});

		local Any is res: :parseValue(text: text);
		:skipWhitespace(text: text);
		if({ :parsePos < :textLen }, {
			:syntaxFail(msg: 'Unexpected trailing data at offset ' . (:parsePos as String));
		});
		return res;
	}

	## Parses a JSON document whose root must be an array, returning the
	## Array or the parse failure as the full error currency.
	Function of Result of Array to JsonError is parseArrayResult(String is text){
		local SpecError of JsonError is failErr: SpecError:init(kind: JsonError:SYNTAX_ERROR, description: '');
		local Array is arr: try(
			body: local Function of Array(){
				local Any is v: :parseText(text: text);
				local String is vt: Introspection:typeIdentity(obj: v);
				if({ vt != 'Array' }, {
					:raiseError(error: SpecError:init(kind: JsonError:TYPE_MISMATCH, description: 'document root is not an array'));
				});
				return v as Array;
			},
			guard: local Function of Array(SpecError of JsonError is e){
				failErr: e;
				return Array();
			}
		);
		if({ failErr:description == '' }, {
			local Result of Array to JsonError is okR: Result:Ok(value: arr);
			return okR;
		});
		local Result of Array to JsonError is errR: Result:Err(error: failErr);
		return errR;
	}

	## Parses a JSON document whose root must be an object, returning the
	## Map or the parse failure as the full error currency.
	Function of Result of Map of String to Any to JsonError is parseMapResult(String is text){
		local SpecError of JsonError is failErr: SpecError:init(kind: JsonError:SYNTAX_ERROR, description: '');
		local Map of String to Any is m: try(
			body: local Function of Map of String to Any(){
				local Any is v: :parseText(text: text);
				local String is vt: Introspection:typeIdentity(obj: v);
				if({ vt != 'Map' }, {
					:raiseError(error: SpecError:init(kind: JsonError:TYPE_MISMATCH, description: 'document root is not an object'));
				});
				return v;
			},
			guard: local Function of Map of String to Any(SpecError of JsonError is e){
				failErr: e;
				return :isEmptyMap();
			}
		);
		if({ failErr:description == '' }, {
			local Result of Map of String to Any to JsonError is okR: Result:Ok(value: m);
			return okR;
		});
		local Result of Map of String to Any to JsonError is errR: Result:Err(error: failErr);
		return errR;
	}

	## Looks up an integer value from a parsed JSON map.
	Function of Int is getInt(Map of String to Any is obj, String is key, Int is default: 0){
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
			local String is s: :toStr(val: val);
			return s:parseInt(base: 10, default: default);
		});
		return default;
	}

	## Looks up a floating point value from a parsed JSON map.
	Function of Float is getFloat(Map of String to Any is obj, String is key, Float is default: 0.0){
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
			local String is s: :toStr(val: val);
			local JsonNumber is tempNum: JsonNumber:init(rawText: s, isFloating: true);
			return tempNum:toFloat(default: default);
		});
		return default;
	}

	## Looks up a string value from a parsed JSON map.
	Function of String is getString(Map of String to Any is obj, String is key, String is default: ''){
		if({ !obj:has(key: key) }, {
			return default;
		});
		local Any is val: obj:get(key: key, default: '');
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'String' }, {
			return :toStr(val: val);
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
	Function of Boolean is getBool(Map of String to Any is obj, String is key, Boolean is default: false){
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
			local String is s: :toStr(val: val);
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
	Function of Map of String to Any is getObject(Map of String to Any is obj, String is key){
		if({ !obj:has(key: key) }, {
			return :isEmptyMap();
		});
		local Any is val: obj:get(key: key, default: :isEmptyMap());
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'Map' }, {
			return val;
		});
		return :isEmptyMap();
	}

	## Looks up a nested Array from a parsed JSON map.
	Function of Array is getArray(Map of String to Any is obj, String is key){
		if({ !obj:has(key: key) }, {
			return Array();
		});
		local Any is val: obj:get(key: key, default: Array());
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'Array' }, {
			return val as Array;
		});
		return Array();
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
			local String is s: :toStr(val: val);
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
			return :toStr(val: val);
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
			local String is s: :toStr(val: val);
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
			local String is s: :toStr(val: val);
			local JsonNumber is tempNum: JsonNumber:init(rawText: s, isFloating: true);
			return tempNum:toFloat(default: default);
		});
		return default;
	}

	## Looks up a nested Map from a parsed JSON array.
	Function of Map of String to Any is getObjectAt(Array is arr, Int is index){
		if({ index < 0 || index >= arr:length() }, {
			return :isEmptyMap();
		});
		local Any is val: arr:get(index: index, default: :isEmptyMap());
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'Map' }, {
			return val;
		});
		return :isEmptyMap();
	}

	## Looks up a nested Array from a parsed JSON array.
	Function of Array is getArrayAt(Array is arr, Int is index){
		if({ index < 0 || index >= arr:length() }, {
			return Array();
		});
		local Any is val: arr:get(index: index, default: Array());
		local String is t: Introspection:typeIdentity(obj: val);
		if({ t == 'Array' }, {
			return val as Array;
		});
		return Array();
	}

	## Advances parse position past ASCII whitespace.
	Function is skipWhitespace(String is text){
		local Boolean is checking: true;
		while({ checking && (:parsePos < :textLen) }, {
			local Int is b: text:byteAt(index: :parsePos, default: -1);
			if({ b == 32 || b == 9 || b == 10 || b == 13 }, {
				:parsePos: :parsePos + 1;
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
		:parsePos: :parsePos + 1;
		local Int is startPos: :parsePos;
		local String is out: '';
		local Boolean is scanning: true;
		local Boolean is closed: false;

		while({ scanning && (:parsePos < :textLen) }, {
			local Int is b: text:byteAt(index: :parsePos, default: -1);
			if({ b < 0 }, {
				:syntaxFail(msg: 'Unexpected end of input inside string literal');
			});
			if({ scanning && b == 92 }, {
				if({ :parsePos > startPos }, {
					out: out . text:substring(start: startPos, end: :parsePos);
				});
				:parsePos: :parsePos + 1;
				local Int is esc: text:byteAt(index: :parsePos, default: -1);
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
					if({ :parsePos + 4 < :textLen }, {
						local String is hexStr: text:substring(start: :parsePos + 1, end: :parsePos + 5);
						local Int is cp: hexStr:parseInt(base: 16, default: 0);
						out: out . :codePointToUtf8(cp: cp);
						:parsePos: :parsePos + 4;
					}, {
						:syntaxFail(msg: 'Incomplete \\uXXXX escape sequence');
					});
				});
				:parsePos: :parsePos + 1;
				startPos: :parsePos;
			}, {
				if({ scanning && b == 34 }, {
					if({ :parsePos > startPos }, {
						out: out . text:substring(start: startPos, end: :parsePos);
					});
					:parsePos: :parsePos + 1;
					closed: true;
					scanning: false;
				}, {
					if({ scanning }, {
						:parsePos: :parsePos + 1;
					});
				});
			});
		});
		if({ !closed }, {
			:syntaxFail(msg: 'Unclosed string literal');
		});
		return out;
	}

	## Parses a JSON numeric literal at the current position.
	Function of JsonNumber is parseNumber(String is text){
		local Int is start: :parsePos;
		local Boolean is isFloating: false;

		if({ :parsePos < :textLen && text:byteAt(index: :parsePos, default: -1) == 45 }, {
			:parsePos: :parsePos + 1;
		});

		local Boolean is readingInt: true;
		while({ readingInt && (:parsePos < :textLen) }, {
			local Int is b: text:byteAt(index: :parsePos, default: -1);
			if({ b >= 48 && b <= 57 }, {
				:parsePos: :parsePos + 1;
			}, {
				readingInt: false;
			});
		});

		if({ :parsePos < :textLen && text:byteAt(index: :parsePos, default: -1) == 46 }, {
			isFloating: true;
			:parsePos: :parsePos + 1;
			local Boolean is readingFrac: true;
			while({ readingFrac && (:parsePos < :textLen) }, {
				local Int is b: text:byteAt(index: :parsePos, default: -1);
				if({ b >= 48 && b <= 57 }, {
					:parsePos: :parsePos + 1;
				}, {
					readingFrac: false;
				});
			});
		});

		if({ :parsePos < :textLen }, {
			local Int is expCh: text:byteAt(index: :parsePos, default: -1);
			if({ expCh == 101 || expCh == 69 }, {
				isFloating: true;
				:parsePos: :parsePos + 1;
				if({ :parsePos < :textLen }, {
					local Int is signCh: text:byteAt(index: :parsePos, default: -1);
					if({ signCh == 43 || signCh == 45 }, {
						:parsePos: :parsePos + 1;
					});
				});
				local Boolean is readingExp: true;
				while({ readingExp && (:parsePos < :textLen) }, {
					local Int is b: text:byteAt(index: :parsePos, default: -1);
					if({ b >= 48 && b <= 57 }, {
					:parsePos: :parsePos + 1;
					}, {
						readingExp: false;
					});
				});
			});
		});

		local String is numStr: text:substring(start: start, end: :parsePos);
		if({ numStr == '-' || numStr == '' }, {
			:syntaxFail(msg: 'Invalid number literal');
		});
		return :numberRaw(rawText: numStr, isFloating: isFloating);
	}

	## Parses a JSON array at the current position.
	Function of Array is parseArray(String is text){
		local Array of Any is arr: Array();
		:parsePos: :parsePos + 1;
		:skipWhitespace(text: text);

		if({ :parsePos < :textLen && text:byteAt(index: :parsePos, default: -1) == 93 }, {
			:parsePos: :parsePos + 1;
			return arr;
		});

		local Boolean is parsing: true;
		local Boolean is closed: false;
		while({ parsing && (:parsePos < :textLen) }, {
			local Any is item: :parseValue(text: text);
			arr:add(item: item);
			:skipWhitespace(text: text);
			local Int is nextCh: text:byteAt(index: :parsePos, default: -1);
			if({ nextCh == 44 }, {
				:parsePos: :parsePos + 1;
			}, {
				if({ nextCh == 93 }, {
					:parsePos: :parsePos + 1;
					closed: true;
					parsing: false;
				}, {
					:syntaxFail(msg: 'Expected \x27,\x27 or \x27]\x27 in array');
				});
			});
		});
		if({ !closed }, {
			:syntaxFail(msg: 'Unclosed array, expected \x27]\x27');
		});
		return arr;
	}

	## Parses a JSON object at the current position.
	Function of Map of String to Any is parseObject(String is text){
		local Map of String to Any is obj: [:];
		:parsePos: :parsePos + 1;
		:skipWhitespace(text: text);

		if({ :parsePos < :textLen && text:byteAt(index: :parsePos, default: -1) == 125 }, {
			:parsePos: :parsePos + 1;
			return obj;
		});

		local Boolean is parsing: true;
		local Boolean is closed: false;
		while({ parsing && (:parsePos < :textLen) }, {
			:skipWhitespace(text: text);
			if({ text:byteAt(index: :parsePos, default: -1) != 34 }, {
				:syntaxFail(msg: 'Expected string key in object');
			});
			local String is key: :parseString(text: text);
			:skipWhitespace(text: text);
			if({ text:byteAt(index: :parsePos, default: -1) != 58 }, {
				:syntaxFail(msg: 'Expected \x27:\x27 after key in object');
			});
			:parsePos: :parsePos + 1;
			local Any is val: :parseValue(text: text);
			obj:set(key: key, value: val);
			:skipWhitespace(text: text);
			local Int is nextCh: text:byteAt(index: :parsePos, default: -1);
			if({ nextCh == 44 }, {
				:parsePos: :parsePos + 1;
			}, {
				if({ nextCh == 125 }, {
					:parsePos: :parsePos + 1;
					closed: true;
					parsing: false;
				}, {
					:syntaxFail(msg: 'Expected \x27,\x27 or \x27}\x27 in object');
				});
			});
		});
		if({ !closed }, {
			:syntaxFail(msg: 'Unclosed object, expected \x27}\x27');
		});
		return obj;
	}

	## Parses a JSON value at the current position.
	Function of Any is parseValue(String is text){
		:skipWhitespace(text: text);
		if({ :parsePos >= :textLen }, {
			:syntaxFail(msg: 'Unexpected end of input');
		});

		local Int is b: text:byteAt(index: :parsePos, default: -1);
		if({ b == 123 }, {
			return :parseObject(text: text);
		});
		if({ b == 91 }, {
			return :parseArray(text: text);
		});
		if({ b == 34 }, {
			return :parseString(text: text);
		});
		if({ b == 116 }, {
			if({ :parsePos + 4 <= :textLen && text:substring(start: :parsePos, end: :parsePos + 4) == 'true' }, {
				:parsePos: :parsePos + 4;
				return :bool(b: true);
			});
		});
		if({ b == 102 }, {
			if({ :parsePos + 5 <= :textLen && text:substring(start: :parsePos, end: :parsePos + 5) == 'false' }, {
				:parsePos: :parsePos + 5;
				return :bool(b: false);
			});
		});
		if({ b == 110 }, {
			if({ :parsePos + 4 <= :textLen && text:substring(start: :parsePos, end: :parsePos + 4) == 'null' }, {
				:parsePos: :parsePos + 4;
				return :nullValue();
			});
		});
		if({ b == 45 || (b >= 48 && b <= 57) }, {
			return :parseNumber(text: text);
		});

		:syntaxFail(msg: 'Unexpected character \x27' . text:substring(start: :parsePos, end: :parsePos + 1) . '\x27 at offset ' . (:parsePos as String));
		return :nullValue();
	}

	## Parses JSON text into Spec data structures, falling back to
	## [default] on any parse failure. Convenience sugar over the typed
	## result faces — callers that need the failure's kind and
	## description call `parseMapResult` / `parseArrayResult`.
	Function of Any is parse(String is text, Any is default: ''){
		local Any is out: default;
		out: try(
			body: local Function of Any(){
				return :parseText(text: text);
			},
			guard: local Function of Any(SpecError is e){
				return default;
			}
		);
		return out;
	}

	## Parses JSON text directly into a Map.
	Function of Map of String to Any is parseObjectText(String is text){
		local Any is res: :parse(text: text, default: :isEmptyMap());
		local String is t: Introspection:typeIdentity(obj: res);
		if({ t == 'Map' }, {
			return res;
		});
		return :isEmptyMap();
	}

	## Parses JSON text directly into an Array.
	Function of Array is parseArrayText(String is text){
		local Any is res: :parse(text: text, default: Array());
		local String is t: Introspection:typeIdentity(obj: res);
		if({ t == 'Array' }, {
			return res as Array;
		});
		return Array();
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
			local Int is b: str:byteAt(index: i, default: -1);
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
											out: out . "\\u00" . :hexDigit(d: b / 16) . :hexDigit(d: b % 16);
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
		if({ :isNull(value: value) }, {
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
			return '"' . :escapeString(str: :toStr(val: value)) . '"';
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
				out: out . :stringify(value: arr:get(index: i, default: ''));
				i: i + 1;
			});
			return out . ']';
		});
		if({ t == 'Map' }, {
			local Map of String to Any is m: value;
			local Array of String is keys: m:keys();
			local String is out: '{';
			local Int is len: keys:length();
			local Int is i: 0;
			while({ i < len }, {
				if({ i > 0 }, {
					out: out . ',';
				});
				local String is k: keys:get(index: i, default: '');
				out: out . '"' . :escapeString(str: k) . '":' . :stringify(value: m:get(key: k, default: ''));
				i: i + 1;
			});
			return out . '}';
		});
		if({ t == '' }, {
			return 'null';
		});
		return '"' . :escapeString(str: :toStr(val: value)) . '"';
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
		if({ :isNull(value: value) }, {
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
				out: out . :indentSpaces(level: level + 1, indentStep: indent) . :formatInner(value: arr:get(index: ai, default: ''), level: level + 1, indent: indent);
				if({ ai + 1 < aLen }, {
					out: out . ',';
				});
				out: out . "\n";
				ai: ai + 1;
			});
			out: out . :indentSpaces(level: level, indentStep: indent) . ']';
			return out;
		});
		if({ t == 'Map' }, {
			local Map of String to Any is m: value;
			local Array of String is keys: m:keys();
			local Int is kLen: keys:length();
			if({ kLen == 0 }, {
				return '{}';
			});
			local String is out: "{\n";
			local Int is ki: 0;
			while({ ki < kLen }, {
				local String is k: keys:get(index: ki, default: '');
				out: out . :indentSpaces(level: level + 1, indentStep: indent) . '"' . :escapeString(str: k) . '": ' . :formatInner(value: m:get(key: k, default: ''), level: level + 1, indent: indent);
				if({ ki + 1 < kLen }, {
					out: out . ',';
				});
				out: out . "\n";
				ki: ki + 1;
			});
			out: out . :indentSpaces(level: level, indentStep: indent) . '}';
			return out;
		});
		return :stringify(value: value);
	}

	## Formats a Spec value into pretty-printed JSON with indentation.
	Function of String is format(Any is value, Int is indent: 2){
		return :formatInner(value: value, level: 0, indent: indent);
	}
}
