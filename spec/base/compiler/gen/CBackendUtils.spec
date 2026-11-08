#! Package base:compiler:gen
#! C11 backend utilities: identifier sanitization, string escaping, and
#! type-name-to-C-type mapping.

Class is CBackendUtils{
	namespace: ['base', 'compiler', 'gen'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'lexer', Token],
		['base', 'iterator'],
		['base', 'iterator', as While()]
	];

	## Maps a Spec type name to its C11 type. Containers accept both
	## spellings (bare, `of`-form, colon-form); primitives map to their
	## machine representations; unknown names are user classes and map to
	## their struct pointers.
	##
	## @param typeName: Spec type name.
	## @return: C11 type string.
	Function of String is cTypeFor(String is typeName){
		Conditional:if(check: { typeName == 'List' || typeName:startsWith(prefix: 'List of ') || typeName:startsWith(prefix: 'List:') }, then: {
			Conditional:if(check: { typeName == 'List:Byte' || typeName == 'List of Byte' }, then: {
				return 'SpecByteBuffer*';
			});
			return 'SpecVec*';
		});
		Conditional:if(check: { typeName == 'Array' || typeName:startsWith(prefix: 'Array of ') || typeName:startsWith(prefix: 'Array:') }, then: {
			return 'SpecArray*';
		});
		Conditional:if(check: { typeName == 'Map' || typeName:startsWith(prefix: 'Map of ') || typeName:startsWith(prefix: 'Map:') }, then: {
			return 'SpecMap*';
		});
		Conditional:if(check: { typeName == 'Function' || typeName:startsWith(prefix: 'Function of ') || typeName:startsWith(prefix: 'Function:') }, then: {
			return 'SpecClosure*';
		});
		when (typeName) {
			is 'Int': { return 'long long'; }
			is 'Byte': { return 'unsigned char'; }
			is 'Float': { return 'double'; }
			is 'Boolean': { return 'bool'; }
			is 'String': { return 'String'; }
			is 'Void', 'void', '': { return 'void'; }
			is 'Array': { return 'SpecArray*'; }
			is 'Map': { return 'SpecMap*'; }
			is 'Function': { return 'SpecClosure*'; }
			is 'InputHandler': { return 'void*'; }
			is 'LoopControl': { return 'SpecLoopControl*'; }
			is 'File', 'Process', 'Output', 'Input', 'Math', 'While': { return 'void*'; }
			else: { return typeName . '*'; }
		}
	}

	## Converts a lowerCamel name to snake_case for C floor binding
	## (bufGetByte -> buf_get_byte; the caller prepends spec_).
	##
	## @param name: lowerCamel name.
	## @return: snake_case form.
	Function of String is snakeCase(String is name){
		local SnakeCaseLoop is loop: SnakeCaseLoop:init(src: name);
		While:run(loop: loop);
		return loop:res;
	}

	## Sanitizes a Spec identifier against C reserved keywords.
	##
	## @param name: Spec identifier.
	## @return: C-compatible identifier.
	Function of String is cIdent(String is name){
		return when (name) {
			is 'EOF': '_EOF';
			is 'default', 'case', 'switch', 'struct', 'union', 'enum', 'register',
				'static', 'extern', 'inline', 'const', 'volatile', 'auto', 'signed',
				'unsigned', 'short', 'long', 'sizeof', 'typedef', 'if', 'else',
				'for', 'while', 'do', 'return', 'goto', 'break', 'continue': '_' . name;
			else: name;
		};
	}

	## Escapes string content for a C string literal.
	##
	## @param s: Raw text.
	## @return: C-escaped text.
	Function of String is escapeString(String is s){
		local EscapeLoop is escLoop: EscapeLoop:init(src: s);
		While:run(loop: escLoop);
		return escLoop:res;
	}

	## Resolves the C return type of a method signature descriptor.
	##
	## @param t: Declared type descriptor.
	## @return: C return type string.
	Function of String is resolveReturnType(Type is t){
		Conditional:if(check: { Primitive:of(t:name) == Primitive:FUNCTION }, then: {
			Conditional:if(check: { t:params:length() > 0 }, then: {
				local Type is ret: t:params:get(index: 0);
				return self:cTypeFor(typeName: ret:name);
			});
			return 'void';
		});
		return self:cTypeFor(typeName: t:name);
	}

	## Character walk for snakeCase: inserts '_' before each uppercase and
	## lowercases it.
	Class of Loop is SnakeCaseLoop{

		replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
		];
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
			Conditional:if(check: { u >= 0 }, then: {
				self:res: self:res . '_' . self:lowers:charAt(index: u, default: '');
			}, else: {
				self:res: self:res . ch;
			});
			return true;
		}
	}

	## Character walk for escapeString.
	Class of Loop is EscapeLoop{

		replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
		];
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
					Conditional:if(check: { ch == String:fromCharCode(code: 27) }, then: {
						self:res: self:res . "\\033";
					}, else: {
						self:res: self:res . ch;
					});
				}
			}
			return true;
		}
	}
}
