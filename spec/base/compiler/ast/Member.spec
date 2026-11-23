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
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Member category for enum dispatch.
	MemberKind is kind: MemberKind:FIELD;

	## One-based source line where the member was declared.
	Int is line: 0;

	## Source file where the member was declared (set by the loader;
	## preserved per-fragment when grouped classes merge).
	String is sourceFile: '';

	## Declared modifiers (e.g. replace, local, contained).
	[String] is modifiers: [];

	## Return type for methods; value type for fields.
	Type is memberType: Type:EMPTY;

	## Member identifier.
	String is name: '';

	## METHOD: formal parameter list.
	[Parameter] is params: [];

	## METHOD: implementation statements.
	[Statement] is body: [];

	## FIELD: initializer expression and its presence flag.
	Expression is initExpr: Expression:Unknown;
	Boolean is hasInit: false;

	## CLASS: the nested class descriptor.
	ClassInfo is nestedClass: ClassInfo:EMPTY;

	## Initializes a member descriptor.
	##
	## @param kind: Member category.
	replace Function is init(MemberKind is kind){
		:kind: kind;
	}

	## Sets the one-based source line.
	##
	## @param line: Source line number.
	Function is setLine(Int is line){
		:line: line;
	}

	## Sets the declaring source file.
	##
	## @param file: Source file path.
	Function is setSourceFile(String is file){
		:sourceFile: file;
	}

	## Releases statement and expression nodes once method emission finishes.
	Function is clearBody(){
		:body: [];
	}

	## True when the member carries the given modifier. Modifiers are
	## keywords ([Keyword:LOCAL], [Keyword:CONTAINED], [Keyword:REPLACE],
	## [Keyword:MERGE]).
	##
	## @param kw: The modifier keyword.
	## @return: true when present in [modifiers].
	Function of Boolean is hasModifier(Keyword is kw){
		local String is target: kw:value();
		local Boolean is found: false;
		while([Int is i: 0], { !found && i < :modifiers:length() }, {
			if({ :modifiers:get(index: i) == target }, { found: true; });
			i++;
		});
		return found;
	}
}
