#! Package base:compiler:ast
#! One class member: a method, field, or nested class definition.

Class is Member{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'ast', Type],
		['spec', 'base', 'compiler', 'ast', MemberKind],
		['spec', 'base', 'compiler', 'ast', Parameter],
		['spec', 'base', 'compiler', 'ast', Statement],
		['spec', 'base', 'compiler', 'ast', Expression],
		['spec', 'base', 'compiler', 'ast', ClassInfo]
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

	## True when the member carries the given modifier.
	##
	## @param modifier: Modifier name (e.g. replace).
	## @return: true when present in [modifiers].
	Function of Boolean is hasModifier(String is modifier){
		return self:modifiers:indexOf(search: modifier, default: -1) >= 0;
	}
}
