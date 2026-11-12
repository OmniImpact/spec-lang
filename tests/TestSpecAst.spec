#! SpecUnit sweep (from spec_ast_test.spec): AST kind enums drive
#! match-dispatch, records carry their kind's fields, and the
#! cross-referencing node graph loads as a package.

Class of SpecUnitTest is TestSpecAst{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	# Records build and cross-reference: a binary expression over idents.
	Function is testExpressionRecordsCrossReference(){
		local Expression is lhs: Expression:init(kind: ExpressionKind:IDENT);
		lhs:makeIdent(name: 'a');
		local Expression is rhs: Expression:init(kind: ExpressionKind:IDENT);
		rhs:makeIdent(name: 'b');
		local Expression is bin: Expression:init(kind: ExpressionKind:BINARY);
		bin:str: '+';
		bin:leftExpr: lhs;
		bin:rightExpr: rhs;
		Assert:isTrue(bin:kind == ExpressionKind:BINARY);
		Assert:areEqualString('a', bin:leftExpr:str);
		Assert:areEqualString('b', bin:rightExpr:str);
	}

	# Enum dispatch on the kind (the style contract's string-tag removal).
	Function is testMatchDispatchOnKind(){
		local Expression is bin: Expression:init(kind: ExpressionKind:BINARY);
		local String is tag: '';
		Conditional:match(on: bin:kind, when: [
			ExpressionKind:BINARY: { tag: 'binary'; },
			ExpressionKind:CALL: { tag: 'call'; },
			else: { tag: 'other'; }
		]);
		Assert:areEqualString('binary', tag);
	}

	# Types format canonically.
	Function is testCanonicalTypeFormatting(){
		local Type is elem: Type:init(name: 'String');
		local Type is arr: Type:init(name: 'Array');
		arr:params: [elem];
		Assert:areEqualString('Array of String', arr:toString());
		Assert:isTrue(arr:isGeneric());
		Assert:isFalse(elem:isGeneric());
	}

	# Class -> member graph with the MemberKind dispatch.
	# (Implicit-Any parenting is the loader's appendImplicitAny job, not
	# the record's — a bare init carries no bases.)
	Function is testClassMemberGraph(){
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:name: 'speak';
		local ClassInfo is cls: ClassInfo:init(name: 'Widget', baseClass: '', members: [m]);
		local ProgramNode is prog: ProgramNode:init(classes: [cls]);
		local String is found: '';
		prog:classes:each(action: local Function(ClassInfo is c){
			c:members:each(action: local Function(Member is mem){
				Conditional:match(on: mem:kind, when: [
					MemberKind:METHOD: { found: mem:name; }
				]);
			});
		});
		Assert:areEqualString('speak', found);
		Assert:areEqualInt(0, cls:baseClasses:length());
	}

	# Statements carry their kind's fields.
	Function is testStatementFields(){
		local Expression is bin: Expression:init(kind: ExpressionKind:BINARY);
		local Statement is st: Statement:init(kind: StatementKind:RETURN);
		st:returnExpr: bin;
		st:hasReturnExpr: true;
		st:setLine(line: 9);
		Assert:isTrue(st:kind == StatementKind:RETURN);
		Assert:isTrue(st:hasReturnExpr);
		Assert:areEqualInt(9, st:line);
		Assert:isTrue(st:returnExpr:kind == ExpressionKind:BINARY);
	}
}
