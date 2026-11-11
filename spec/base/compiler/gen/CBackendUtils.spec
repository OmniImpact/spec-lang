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
		['base', 'sys', as Loops()],

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
		return Conditional:match(on: typeName, when: [
			'Int': { 'long long' },
			'Byte': { 'unsigned char' },
			'Float': { 'double' },
			'Boolean': { 'bool' },
			'String': { 'String' },
			['Void', 'void', '']: { 'void' },
			'Array': { 'SpecArray*' },
			'Map': { 'SpecMap*' },
			'Function': { 'SpecClosure*' },
			'InputHandler': { 'void*' },
			'LoopControl': { 'SpecLoopControl*' },
			['File', 'Process', 'Output', 'Input', 'Math', 'Loops']: { 'void*' },
			else: { self:cIdent(name: typeName) . '*' }
		]);
	}

	## Converts a lowerCamel name to snake_case for C floor binding
	## (bufGetByte -> buf_get_byte; the caller prepends spec_).
	##
	## @param name: lowerCamel name.
	## @return: snake_case form.
	Function of String is snakeCase(String is name){
		local String is res: '';
		local String is uppers: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
		local String is lowers: 'abcdefghijklmnopqrstuvwxyz';
		local Int is len: name:length();
		while(
			[Int is pos: 0],
			{ pos < len },
			{
				local String is ch: name:charAt(index: pos, default: '');
				pos++;
				local Int is u: uppers:indexOf(search: ch, default: -1);
				if({ u >= 0 }, {
					res: res . '_' . lowers:charAt(index: u, default: '');
				}, {
					res: res . ch;
				});
			}
		);
		return res;
	}

	## Sanitizes a Spec identifier against C reserved keywords.
	##
	## @param name: Spec identifier.
	## @return: C-compatible identifier.
	Function of String is cIdent(String is name){
		# the qualified class names
		# ('Outer:Helper') map the nesting separator to the C underscore.
		if({ name:contains(needle: ':') }, {
			return self:cIdent(name: name:replaceAll(search: ':', replacement: '_'));
		});
		return match(on: name, when: [
			'EOF': { '_EOF' },
			['default', 'case', 'switch', 'struct', 'union', 'enum', 'register',
			'static', 'extern', 'inline', 'const', 'volatile', 'auto', 'signed',
			'unsigned', 'short', 'long', 'sizeof', 'typedef', 'if', 'else',
			'for', 'while', 'do', 'return', 'goto', 'break', 'continue']: { '_' . name },
			else: { name }
		]);
	}

	## Escapes string content for a C string literal.
	##
	## @param s: Raw text.
	## @return: C-escaped text.
	Function of String is escapeString(String is s){
		local String is res: '';
		local Int is len: s:length();
		while(
			[Int is pos: 0],
			{ pos < len },
			{
				local String is ch: s:charAt(index: pos, default: '');
				pos++;
				match(on: ch, when: [
					"\n": { res: res . "\\n"; },
					"\t": { res: res . "\\t"; },
					"\r": { res: res . "\\r"; },
					'"': { res: res . "\\\""; },
					"\\": { res: res . "\\\\"; },
					else: {
						if({ ch == String:fromCharCode(code: 27) }, {
							res: res . "\\033";
						}, {
							res: res . ch;
						});
					}
				]);
			}
		);
		return res;
	}

	## Resolves the C return type of a method signature descriptor.
	##
	## @param t: Declared type descriptor.
	## @return: C return type string.
	Function of String is resolveReturnType(Type is t){
		if({ Primitive:of(t:name) == Primitive:FUNCTION }, {
			if({ t:params:length() > 0 }, {
				local Type is ret: t:params:get(index: 0);
				return self:cTypeFor(typeName: ret:name);
			});
			return 'void';
		});
		return self:cTypeFor(typeName: t:name);
	}
}
