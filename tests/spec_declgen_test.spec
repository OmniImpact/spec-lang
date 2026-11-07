#! DeclarationGenerator port check: enum tables with of(), forward
#! declarations with C-mapped prototypes, structs without metadata.

Class is SpecDeclGenTest{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'gen', DeclarationGenerator],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'io', Output],
		['base', 'io', File]
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Spec DeclGen Test ===');
		local Int is failures: 0;

		local String is src: "Enum of String is Level {
	NONE: '',
	ERR: 'E'
}
Class is Widget{
	local Int is size: 0;
	local String is label;
	replace Function of Int is grow(Int is by){
		return self:size + by;
	}
}";
		local Lexer is lx: Lexer:init(source: src);
		local Parser is p: Parser:init(tokens: lx:tokenize());
		local ProgramNode is prog: p:parseProgram();
		local DeclarationGenerator is dg: DeclarationGenerator:init();
		local Map of String to String is enums: Map:init();
		enums:set(key: 'Level', value: 'true');
		dg:setEnumNames(names: enums);
		local String is enumsC: dg:generateEnums(classes: prog:classes);
		local String is fwdC: dg:generateForwardDeclarations(classes: prog:classes);
		local String is structsC: dg:generateStructs(classes: prog:classes);

		if (enumsC:contains(needle: 'Level_NONE = 0') && enumsC:contains(needle: 'Level_of(String v)') && enumsC:contains(needle: 'return Level_NONE;')) {
			output:line('[PASS] enum tables with of() and NONE default');
		} else {
			output:line('[FAIL] enum emission');
			failures: failures + 1;
		}

		if (fwdC:contains(needle: 'typedef struct Widget Widget;') && fwdC:contains(needle: 'long long Widget_grow(Widget* self, long long by);')) {
			output:line('[PASS] forward declarations with prototypes');
		} else {
			output:line('[FAIL] forward declarations');
			failures: failures + 1;
		}

		if (structsC:contains(needle: 'struct Widget {') && structsC:contains(needle: 'long long size;') && !structsC:contains(needle: 'namespace;')) {
			output:line('[PASS] struct fields without metadata members');
		} else {
			output:line('[FAIL] struct emission');
			failures: failures + 1;
		}

		if (failures == 0) {
			output:line('[PASS] spec declgen test complete');
		} else {
			output:line('[FAIL] spec declgen test: ' . (failures as String) . ' failures');
		}
	}
}
