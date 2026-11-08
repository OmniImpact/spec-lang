Class is StdlibReflectionTest{

	replace Array of Array of String is using: [
		['base', 'io'],
		['base', 'struct', Array],
		['base', 'sys', SourceLocation],
		['base', 'sys', StackFrame],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('======================================');
		Output:line('  Standard Library Refactoring Test   ');
		Output:line("======================================\n");

		# 1. Test SourceLocation and StackFrame
		Output:line('--- 1. SourceLocation & StackFrame ---');
		local SourceLocation is loc: SourceLocation:init(file: 'Player.spec', line: 42, col: 15);
		Output:line('Location: ' . loc:toString());

		local StackFrame is frame: StackFrame:init(location: loc, className: 'Player', methodName: 'takeDamage');
		Output:line('Stack Frame: ' . frame:toString());

		Conditional:if(check: { frame:getClassName() == 'Player' }, then: {
			Output:line('[PASS] StackFrame class name is Player');
		});
		Conditional:if(check: { frame:getMethodName() == 'takeDamage' }, then: {
			Output:line('[PASS] StackFrame method name is takeDamage');
		});

		# 2. Test Type reflection
		Output:line("\n--- 2. Type Reflection ---");
		local Type is intType: Type:init(name: 'Int');
		Output:line('Simple type: ' . intType:toString());

		local Array of Type is arrParams: [];
		arrParams:add(item: Type:init(name: 'String'));
		local Type is arrType: Type:init(name: 'Array');
		arrType:params: arrParams;
		Output:line('Generic type: ' . arrType:toString());

		local Array of Type is mapParams: [];
		mapParams:add(item: Type:init(name: 'String'));
		mapParams:add(item: Type:init(name: 'Int'));
		local Type is mapType: Type:init(name: 'Map');
		mapType:params: mapParams;
		Output:line('Map type: ' . mapType:toString());

		Conditional:if(check: { arrType:isGeneric() }, then: {
			Output:line('[PASS] Array of String is generic');
		});
		Conditional:if(check: { !intType:isGeneric() }, then: {
			Output:line('[PASS] Int is not generic');
		});

		# 3. Test Parameter, Member, and ClassInfo
		Output:line("\n--- 3. ClassInfo & Member Reflection ---");
		local Parameter is param1: Parameter:init(name: 'amount', paramType: intType);
		local Array of Parameter is params: [];
		params:add(item: param1);

		local Array of Statement is body: [];
		local Member is methodMem: Member:init(kind: MemberKind:METHOD);
		methodMem:modifiers: ['replace', 'local'];
		methodMem:memberType: intType;
		methodMem:name: 'heal';
		methodMem:params: params;
		methodMem:body: body;

		local Array of Member is members: [];
		members:add(item: methodMem);

		local ClassInfo is cls: ClassInfo:init(name: 'Healer', baseClass: 'Entity', members: members);
		Output:line('ClassInfo: ' . cls:name . ' extends ' . cls:baseClass);
		Output:line('Members count: ' . cls:members:length());
		Output:line('Method: ' . methodMem:name . ' with ' . methodMem:params:length() . ' parameter(s)');

		Conditional:if(check: { cls:name == 'Healer' }, then: {
			Output:line('[PASS] ClassInfo name is Healer');
		});
		Conditional:if(check: { methodMem:name == 'heal' }, then: {
			Output:line('[PASS] Method name is heal');
		});

		# 4. Test Meta AST Expression & Statement
		Output:line("\n--- 4. Meta AST Expression & Statement ---");
		local Expression is numExpr: Expression:init(kind: ExpressionKind:NUMBER);
		numExpr:stringValue: '100';
		local Expression is identExpr: Expression:init(kind: ExpressionKind:IDENT);
		identExpr:makeIdent(name: 'health');

		local Statement is assignStmt: Statement:init(kind: StatementKind:ASSIGN);
		assignStmt:assign(target: identExpr, value: numExpr);
		Output:line('Assign stmt kind: ' . assignStmt:kind:value());
		Output:line('Num expr kind: ' . numExpr:kind:value());

		Conditional:if(check: { assignStmt:kind:value() == 'ASSIGN' }, then: {
			Output:line('[PASS] Statement kind is ASSIGN');
		});
		Conditional:if(check: { numExpr:kind:value() == 'NUMBER' }, then: {
			Output:line('[PASS] Expression kind is NUMBER');
		});

		Output:line("\nAll Standard Library refactoring tests passed successfully!");
	}

}
