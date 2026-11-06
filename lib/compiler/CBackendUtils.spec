#! Package compiler
#! C11 backend utilities: identifier sanitization, string escaping, type mapping, and builtin filtering.

## Utilities for generating C11 compatible code from Spec types and identifiers.
Class is CBackendUtils{

	replace Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Type
	];

	replace Function is init(){
	}

	## Maps a Spec type name to its corresponding C11 type signature.
	##
	## @param typeName: Spec type name.
	## @return: C11 type signature string.
	Function of String is cTypeFor(String is typeName){
	# Container checks match the builtin containers precisely (bare name or
	# generic suffix) so class names sharing a prefix (ArrayItemsLoop,
	# MapItemsLoop, ...) fall through to the class handling in the when below.
	if (typeName == 'List' || typeName:startsWith(prefix: 'List of') || typeName:startsWith(prefix: 'List:')) {
		if (typeName == 'List:Byte' || typeName == 'List of Byte') {
			return 'SpecByteBuffer*';
		}
		return 'SpecVec*';
	}
	if (typeName == 'Array' || typeName:startsWith(prefix: 'Array of') || typeName:startsWith(prefix: 'Array:')) {
		return 'SpecArray*';
	}
	if (typeName == 'Map' || typeName:startsWith(prefix: 'Map of') || typeName:startsWith(prefix: 'Map:')) {
		return 'SpecMap*';
	}
	if (typeName == 'Function' || typeName:startsWith(prefix: 'Function of') || typeName:startsWith(prefix: 'Function:')) {
		return 'SpecClosure*';
	}
		return when (typeName) {
			is 'Int', 'int': 'long long';
			is 'Byte', 'byte': 'unsigned char';
			is 'Float', 'float': 'double';
			is 'Boolean', 'bool': 'bool';
			is 'String', 'string': 'String';
			is 'void', 'Void', '': 'void';
			is 'Array': 'SpecArray*';
			is 'Map': 'SpecMap*';
			is 'Function': 'SpecClosure*';
			is 'InputHandler': 'void*';
			is 'LoopControl': 'SpecLoopControl*';
			is 'File', 'Process', 'Output', 'Input', 'Math', 'While': 'void*';
			else: typeName . '*';
		};
	}

	## Converts a lowerCamel method name to snake_case for C floor binding
	## (bufGetByte -> buf_get_byte; the caller prepends spec_).
	Function of String is snakeCase(String is name){
		local SnakeCaseLoop is loop: SnakeCaseLoop:init(src: name);
		While:run(loop: loop);
		return loop:res;
	}

	## Sanitizes a Spec identifier to avoid clashes with C reserved keywords.
	##
	## @param name: Identifier name.
	## @return: Sanitized C-compatible identifier name.
	Function of String is cIdent(String is name){
		return when (name) {
			is 'EOF': '_EOF';
			is 'default', 'case', 'switch', 'struct', 'union', 'enum', 'register',
				'static', 'extern', 'inline', 'const', 'volatile', 'auto', 'signed',
				'unsigned', 'short', 'long', 'sizeof', 'typedef': '_' . name;
			else: name;
		};
	}

	## Character walk for snakeCase: inserts '_' before each uppercase and
	## lowercases it.
	Class of Loop is SnakeCaseLoop{
		local String is src;
		local Int is pos: 0;
		local String is res: '';
		local String is uppers: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
		local String is lowers: 'abcdefghijklmnopqrstuvwxyz';

		replace Function is init(String is src){
			self:src: src;
			self:pos: 0;
			self:res: '';
		}

		replace Function of Boolean is evaluate(){
			return self:pos < self:src:length();
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:src:charAt(index: self:pos, default: '');
			self:pos: self:pos + 1;
			local Int is u: self:uppers:indexOf(search: ch, default: -1);
			if (u >= 0) {
				self:res: self:res . '_' . self:lowers:charAt(index: u, default: '');
			} else {
				self:res: self:res . ch;
			}
			return true;
		}
	}

	Class of Loop is EscapeLoop{
		local String is src;
		local Int is pos: 0;
		local String is res: '';

		replace Function is init(String is src){
			self:src: src;
			self:pos: 0;
			self:res: '';
		}

		replace Function of Boolean is evaluate(){
			return self:pos < self:src:length();
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:src:charAt(index: self:pos, default: '');
			self:pos: self:pos + 1;
			when (ch) {
				is "\n": { self:res: self:res . "\\n"; }
				is "\t": { self:res: self:res . "\\t"; }
				is "\r": { self:res: self:res . "\\r"; }
				is '"': { self:res: self:res . "\\\""; }
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
	Function of String is escapeString(String is s){
		local EscapeLoop is escLoop: EscapeLoop:init(src: s);
		While:run(loop: escLoop);
		return escLoop:res;
	}

	## Checks if a class name corresponds to an internal/builtin runtime type.
	##
	## @param name: ClassInfo identifier name.
	## @return: `true` if builtin runtime class, `false` otherwise.
	Function of Boolean is isBuiltinClass(String is name){
		return name == 'Array' || name == 'Map' || name == 'File' || name == 'LoopControl' ||
			name == 'Process' || name == 'Output' || name == 'Input' || name == 'Math' ||
			name == 'While' || name == 'Loop' || name == 'LoopCallback' || name == 'InputHandler' ||
			name == 'List' || name == 'String' || name == 'Buf';
	}

	## Resolves the C return type of a method signature descriptor.
	##
	## @param t: Declared [Type] descriptor.
	## @return: C return type string.
	local Function of String is resolveReturnType(Type is t){
		if (t:getName() == 'Function') {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return self:cTypeFor(typeName: ret:getName());
			}
			return 'void';
		}
		return self:cTypeFor(typeName: t:getName());
	}

}
