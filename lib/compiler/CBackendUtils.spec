#! Package compiler
#! C11 backend utilities: identifier sanitization, string escaping, type mapping, and builtin filtering.

## Utilities for generating C11 compatible code from Spec types and identifiers.
Class is CBackendUtils{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Type
	];

	replace local Function is init(){
	}

	## Maps a Spec type name to its corresponding C11 type signature.
	##
	## @param typeName: Spec type name.
	## @return: C11 type signature string.
	local Function of String is cTypeFor(String is typeName){
		if (typeName:startsWith(prefix: "Array")) {
			return "SpecArray*";
		}
		if (typeName:startsWith(prefix: "Map")) {
			return "SpecMap*";
		}
		if (typeName:startsWith(prefix: "Function")) {
			return "void*";
		}
		return when (typeName) {
			is "Int", "int": "long long";
			is "Float", "float": "double";
			is "Boolean", "bool": "bool";
			is "String", "string": "const char*";
			is "void", "Void", "": "void";
			is "Array": "SpecArray*";
			is "Map": "SpecMap*";
			is "Function": "void*";
			is "InputHandler": "void*";
			is "LoopControl": "SpecLoopControl*";
			is "File", "Process", "Output", "Input", "Math", "While": "void*";
			else: typeName . "*";
		};
	}

	## Sanitizes a Spec identifier to avoid clashes with C reserved keywords.
	##
	## @param name: Identifier name.
	## @return: Sanitized C-compatible identifier name.
	local Function of String is cIdent(String is name){
		return when (name) {
			is "EOF": "_EOF";
			is "default", "case", "switch", "struct", "union", "enum", "register",
				"static", "extern", "inline", "const", "volatile", "auto", "signed",
				"unsigned", "short", "long", "sizeof", "typedef": "_" . name;
			else: name;
		};
	}

	Class is EscapeLoop extends Loop{
		local String is src;
		local Int is pos: 0;
		local String is res: "";

		replace local Function is init(String is src){
			self:src: src;
			self:pos: 0;
			self:res: "";
		}

		replace local Function of Boolean is evaluate(){
			return self:pos < self:src:length();
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:src:charAt(index: self:pos, default: "");
			self:pos: self:pos + 1;
			when (ch) {
				is "\n": { self:res: self:res . "\\n"; }
				is "\t": { self:res: self:res . "\\t"; }
				is "\r": { self:res: self:res . "\\r"; }
				is "\"": { self:res: self:res . "\\\""; }
				is "\\": { self:res: self:res . "\\\\"; }
				else: {
					if (ch == String:fromCharCode(code: 27)) {
						self:res: self:res . "\\033";
					} else {
						self:res: self:res . ch;
					}
				}
			}
			return true;
		}
	}

	## Escapes special characters within string literals for C source output.
	##
	## @param s: Raw string text.
	## @return: C-escaped string.
	local Function of String is escapeString(String is s){
		local EscapeLoop is escLoop: EscapeLoop:init(src: s);
		While:run(loop: escLoop);
		return escLoop:res;
	}

	## Checks if a class name corresponds to an internal/builtin runtime type.
	##
	## @param name: ClassInfo identifier name.
	## @return: `true` if builtin runtime class, `false` otherwise.
	local Function of Boolean is isBuiltinClass(String is name){
		return name == "Array" || name == "Map" || name == "File" || name == "LoopControl" ||
			name == "Process" || name == "Output" || name == "Input" || name == "Math" ||
			name == "While" || name == "Loop" || name == "LoopCallback" || name == "InputHandler";
	}

	## Resolves the C return type of a method signature descriptor.
	##
	## @param t: Declared [Type] descriptor.
	## @return: C return type string.
	local Function of String is resolveReturnType(Type is t){
		if (t:getName() == "Function") {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return self:cTypeFor(typeName: ret:getName());
			}
			return "void";
		}
		return self:cTypeFor(typeName: t:getName());
	}

}
