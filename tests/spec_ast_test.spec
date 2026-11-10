#! AST port check: kind enums drive when-dispatch, records carry their
#! kind's fields, and the cross-referencing node graph loads as a package.

Class is SpecAstTest{

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'io', Output],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'cases', as Cases()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Spec AST Test ===');
		local Int is failures: 0;

		# Records build and cross-reference: a binary expression over idents.
		local Expression is lhs: Expression:init(kind: ExpressionKind:IDENT);
		lhs:makeIdent(name: 'a');
		local Expression is rhs: Expression:init(kind: ExpressionKind:IDENT);
		rhs:makeIdent(name: 'b');
		local Expression is bin: Expression:init(kind: ExpressionKind:BINARY);
		bin:str: '+';
		bin:leftExpr: lhs;
		bin:rightExpr: rhs;
		Conditional:if(check: { bin:kind == ExpressionKind:BINARY && bin:leftExpr:str == 'a' && bin:rightExpr:str == 'b' }, then: {
			Output:line('[PASS] expression records cross-reference');
		}, else: {
			Output:line('[FAIL] expression records cross-reference');
			failures: failures + 1;
		});

		# Enum dispatch on the kind (the style contract's string-tag removal).
		local String is tag: '';
		Cases:match(on: bin:kind, when: [
			ExpressionKind:BINARY: { tag: 'binary'; },
			ExpressionKind:CALL: { tag: 'call'; },
			else: { tag: 'other'; }
		]);
		Conditional:if(check: { tag == 'binary' }, then: {
			Output:line('[PASS] match-dispatch on ExpressionKind');
		}, else: {
			Output:line('[FAIL] when-dispatch on ExpressionKind');
			failures: failures + 1;
		});

		# Types format canonically.
		local Type is elem: Type:init(name: 'String');
		local Type is arr: Type:init(name: 'Array');
		arr:params: [elem];
		Conditional:if(check: { arr:toString() == 'Array of String' && arr:isGeneric() && !elem:isGeneric() }, then: {
			Output:line('[PASS] canonical type formatting');
		}, else: {
			Output:line('[FAIL] canonical type formatting: ' . arr:toString());
			failures: failures + 1;
		});

		# Class -> member graph with the MemberKind dispatch.
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:name: 'speak';
		local ClassInfo is cls: ClassInfo:init(name: 'Widget', baseClass: '', members: [m]);
		local ProgramNode is prog: ProgramNode:init(classes: [cls]);
		local String is found: '';
		prog:classes:each(action: local Function(ClassInfo is c){
			c:members:each(action: local Function(Member is mem){
				Cases:match(on: mem:kind, when: [
					MemberKind:METHOD: { found: mem:name; }
				]);
			});
		});
		# (Implicit-Any parenting is the loader's appendImplicitAny job, not
		# the record's — a bare init carries no bases.)
		Conditional:if(check: { found == 'speak' && cls:baseClasses:length() == 0 }, then: {
			Output:line('[PASS] class graph record');
		}, else: {
			Output:line('[FAIL] class graph: ' . found);
			failures: failures + 1;
		});

		# Statements carry their kind's fields.
		local Statement is st: Statement:init(kind: StatementKind:RETURN);
		st:returnExpr: bin;
		st:hasReturnExpr: true;
		st:setLine(line: 9);
		Conditional:if(check: { st:kind == StatementKind:RETURN && st:hasReturnExpr && st:line == 9 && st:returnExpr:kind == ExpressionKind:BINARY }, then: {
			Output:line('[PASS] statement records carry their fields');
		}, else: {
			Output:line('[FAIL] statement records');
			failures: failures + 1;
		});

		Conditional:if(check: { failures == 0 }, then: {
			Output:line('[PASS] spec ast test complete');
		}, else: {
			Output:line('[FAIL] spec ast test: ' . (failures as String) . ' failures');
		});
	}
}
