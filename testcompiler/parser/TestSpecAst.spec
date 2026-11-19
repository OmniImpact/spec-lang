#! SpecUnit sweep (from spec_ast_test.spec): AST kind enums drive
#! match-dispatch, records carry their kind's fields, and the
#! cross-referencing node graph loads as a package.

Class of SpecUnitTest is TestSpecAst{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	# Records build and cross-reference: a binary expression over idents.
	Function is testExpressionRecordsCrossReference(){
		local Expression is lhs: Expression:Ident(name: 'a');
		local Expression is rhs: Expression:Ident(name: 'b');
		local Expression is bin: Expression:Binary(op: '+', left: lhs, right: rhs);
		local Boolean is ok: false;
		Conditional:match(on: bin, when: [
			Expression:Binary: local Function(String is op, Expression is l, Expression is r){
				Assert:areEqualString('+', op);
				Conditional:match(on: l, when: [
					Expression:Ident: local Function(String is lname){ Assert:areEqualString('a', lname); },
					else: {}
				]);
				Conditional:match(on: r, when: [
					Expression:Ident: local Function(String is rname){ Assert:areEqualString('b', rname); },
					else: {}
				]);
				ok: true;
			},
			else: {}
		]);
		Assert:isTrue(ok);
	}

	# Enum dispatch on the kind (the style contract's string-tag removal).
	Function is testMatchDispatchOnKind(){
		local Expression is bin: Expression:Binary(op: '+', left: Expression:Ident(name: 'a'), right: Expression:Ident(name: 'b'));
		local String is tag: '';
		Conditional:match(on: bin, when: [
			Expression:Binary: local Function(String is op, Expression is l, Expression is r){ tag: 'binary'; },
			Expression:Call: { tag: 'call'; },
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
					MemberKind:METHOD: { found: mem:name; },
					else: {}
				]);
			});
		});
		Assert:areEqualString('speak', found);
		Assert:areEqualInt(0, cls:baseClasses:length());
	}

	# Statements carry their variant's payload fields.
	Function is testStatementFields(){
		local Expression is bin: Expression:Binary(op: '+', left: Expression:Ident(name: 'a'), right: Expression:Ident(name: 'b'));
		local Statement is st: Statement:Return(returnExpr: bin, hasReturnExpr: true);
		st:setLine(line: 9);
		Assert:areEqualInt(9, st:line);
		Assert:areEqualString('Return', st:name());
		local Boolean is matched: false;
		match(on: st, when: [
			Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
				Assert:isTrue(hasReturnExpr);
				Assert:areEqualString('Binary', returnExpr:name());
				matched: true;
			},
			else: {}
		]);
		Assert:isTrue(matched);
	}
}
