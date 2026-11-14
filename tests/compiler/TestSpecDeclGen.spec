#! DeclarationGenerator port check: enum tables with of(), forward
#! declarations with C-mapped prototypes, structs without metadata.

Class of SpecUnitTest is TestSpecDeclGen{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'gen', DeclarationGenerator],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', ProgramNode]
	];

	Function of ProgramNode is parseSnippet(String is src){
		local Lexer is lx: Lexer:init(source: src);
		local Parser is p: Parser:init(tokens: lx:tokenize());
		return p:parseProgram();
	}

	Function of String is sampleSource(){
		return "Enum of String is Level {
	NONE: '',
	ERR: 'E'
}
Class is Widget{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	local Int is size: 0;
	local String is label;
	replace Function of Int is grow(Int is by){
		return self:size + by;
	}
}";
	}

	Function is testEnumAsClassModel(){
		local ProgramNode is prog: self:parseSnippet(src: self:sampleSource());
		local DeclarationGenerator is dg: DeclarationGenerator:init();
		local String is fwdC: dg:generateForwardDeclarations(classes: prog:classes);
		local String is structsC: dg:generateStructs(classes: prog:classes);
		Assert:isTrue(fwdC:contains(needle: 'Level_NONE__ensure(void);'));
		Assert:isTrue(structsC:contains(needle: 'String _backing;'));
	}

	Function is testForwardDeclarationsWithPrototypes(){
		local ProgramNode is prog: self:parseSnippet(src: self:sampleSource());
		local DeclarationGenerator is dg: DeclarationGenerator:init();
		local String is fwdC: dg:generateForwardDeclarations(classes: prog:classes);
		Assert:isTrue(fwdC:contains(needle: 'typedef struct Widget Widget;'));
		Assert:isTrue(fwdC:contains(needle: 'long long Widget_grow(Widget* self, long long by);'));
	}

	Function is testStructFieldsWithoutMetadataMembers(){
		local ProgramNode is prog: self:parseSnippet(src: self:sampleSource());
		local DeclarationGenerator is dg: DeclarationGenerator:init();
		local String is structsC: dg:generateStructs(classes: prog:classes);
		Assert:isTrue(structsC:contains(needle: 'struct Widget {'));
		Assert:isTrue(structsC:contains(needle: 'long long size;'));
		Assert:isFalse(structsC:contains(needle: 'namespace;'));
	}
}
