#! Package base:compiler:ast
#! One class member: a method, field, or nested class definition.

Class is Member{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ClassInfo]
	];

	## Member category for enum dispatch.
	MemberKind is kind: MemberKind:FIELD;

	## One-based source line where the member was declared.
	Int is line: 0;

	## Source file where the member was declared (set by the loader;
	## preserved per-fragment when grouped classes merge).
	String is sourceFile: '';

	## Declared modifiers (e.g. replace, local, contained).
	Array of String is modifiers: [];

	## Return type for methods; value type for fields.
	Type is memberType;

	## Member identifier.
	String is name: '';

	## METHOD: formal parameter list.
	Array of Parameter is params: [];

	## METHOD: implementation statements.
	Array of Statement is body: [];

	## FIELD: initializer expression and its presence flag.
	Expression is initExpr;
	Boolean is hasInit: false;

	## CLASS: the nested class descriptor.
	ClassInfo is nestedClass;

	## Initializes a member descriptor.
	##
	## @param kind: Member category.
	replace Function is init(MemberKind is kind){
		self:kind: kind;
	}

	## Sets the one-based source line.
	##
	## @param line: Source line number.
	Function is setLine(Int is line){
		self:line: line;
	}

	## Sets the declaring source file.
	##
	## @param file: Source file path.
	Function is setSourceFile(String is file){
		self:sourceFile: file;
	}

	## Releases statement and expression nodes once method emission finishes.
	Function is clearBody(){
		self:body: [];
	}

	## True when the member carries the given modifier. Modifiers are
	## keywords ([Keyword:LOCAL], [Keyword:CONTAINED], [Keyword:REPLACE],
	## [Keyword:MERGE]).
	##
	## @param kw: The modifier keyword.
	## @return: true when present in [modifiers].
	Function of Boolean is hasModifier(Keyword is kw){
		return self:modifiers:indexOf(search: kw:value(), default: -1) >= 0;
	}
}
