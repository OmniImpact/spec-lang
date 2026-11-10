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
		['base', 'io', File],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Spec DeclGen Test ===');
		local Int is failures: 0;

		local String is src: "Enum of String is Level {
	NONE: '',
	ERR: 'E'
}
Class is Widget{

	replace Array of Array of String is using: [
		['base', 'io', as Output()]
	];
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
		local String is fwdC: dg:generateForwardDeclarations(classes: prog:classes);
		local String is structsC: dg:generateStructs(classes: prog:classes);

		# PLAN-ENUM Stage 4: Level desugars to the class model — the held
		# accessors and the backing field carry it (the C enum tables
		# retired with the legacy emission in Stage 6).
		Conditional:if(check: { fwdC:contains(needle: 'Level_NONE__ensure(void);') && structsC:contains(needle: 'String _backing;') }, then: {
			Output:line('[PASS] enum as class model (held accessors, backing field)');
		}, else: {
			Output:line('[FAIL] enum emission');
			failures: failures + 1;
		});

		Conditional:if(check: { fwdC:contains(needle: 'typedef struct Widget Widget;') && fwdC:contains(needle: 'long long Widget_grow(Widget* self, long long by);') }, then: {
			Output:line('[PASS] forward declarations with prototypes');
		}, else: {
			Output:line('[FAIL] forward declarations');
			failures: failures + 1;
		});

		Conditional:if(check: { structsC:contains(needle: 'struct Widget {') && structsC:contains(needle: 'long long size;') && !structsC:contains(needle: 'namespace;') }, then: {
			Output:line('[PASS] struct fields without metadata members');
		}, else: {
			Output:line('[FAIL] struct emission');
			failures: failures + 1;
		});

		Conditional:if(check: { failures == 0 }, then: {
			Output:line('[PASS] spec declgen test complete');
		}, else: {
			Output:line('[FAIL] spec declgen test: ' . (failures as String) . ' failures');
		});
	}
}
