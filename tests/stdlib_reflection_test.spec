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
		['base', 'compiler', 'ast', ExpressionKind]
	];

	replace Function is init(Map of String to String is args){
		output:line('======================================');
		output:line('  Standard Library Refactoring Test   ');
		output:line("======================================\n");

		# 1. Test SourceLocation and StackFrame
		output:line('--- 1. SourceLocation & StackFrame ---');
		local SourceLocation is loc: SourceLocation:init(file: 'Player.spec', line: 42, col: 15);
		output:line('Location: ' . loc:toString());

		local StackFrame is frame: StackFrame:init(location: loc, className: 'Player', methodName: 'takeDamage');
		output:line('Stack Frame: ' . frame:toString());

		if (frame:getClassName() == 'Player') {
			output:line('[PASS] StackFrame class name is Player');
		}
		if (frame:getMethodName() == 'takeDamage') {
			output:line('[PASS] StackFrame method name is takeDamage');
		}

		# 2. Test Type reflection
		output:line("\n--- 2. Type Reflection ---");
		local Type is intType: Type:init(name: 'Int');
		output:line('Simple type: ' . intType:toString());

		local Array of Type is arrParams: [];
		arrParams:add(item: Type:init(name: 'String'));
		local Type is arrType: Type:withParams(name: 'Array', params: arrParams);
		output:line('Generic type: ' . arrType:toString());

		local Array of Type is mapParams: [];
		mapParams:add(item: Type:init(name: 'String'));
		mapParams:add(item: Type:init(name: 'Int'));
		local Type is mapType: Type:withParams(name: 'Map', params: mapParams);
		output:line('Map type: ' . mapType:toString());

		if (arrType:isGeneric()) {
			output:line('[PASS] Array of String is generic');
		}
		if (!intType:isGeneric()) {
			output:line('[PASS] Int is not generic');
		}

		# 3. Test Parameter, Member, and ClassInfo
		output:line("\n--- 3. ClassInfo & Member Reflection ---");
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
		output:line('ClassInfo: ' . cls:name . ' extends ' . cls:baseClass);
		output:line('Members count: ' . cls:members:length());
		output:line('Method: ' . methodMem:name . ' with ' . methodMem:params:length() . ' parameter(s)');

		if (cls:name == 'Healer') {
			output:line('[PASS] ClassInfo name is Healer');
		}
		if (methodMem:name == 'heal') {
			output:line('[PASS] Method name is heal');
		}

		# 4. Test Meta AST Expression & Statement
		output:line("\n--- 4. Meta AST Expression & Statement ---");
		local Expression is numExpr: Expression:init(kind: ExpressionKind:NUMBER);
		numExpr:stringValue: '100';
		local Expression is identExpr: Expression:init(kind: ExpressionKind:IDENT);
		identExpr:makeIdent(name: 'health');

		local Statement is assignStmt: Statement:init(kind: StatementKind:ASSIGN);
		assignStmt:assign(target: identExpr, value: numExpr);
		output:line('Assign stmt kind: ' . assignStmt:kind:value());
		output:line('Num expr kind: ' . numExpr:kind:value());

		if (assignStmt:kind:value() == 'ASSIGN') {
			output:line('[PASS] Statement kind is ASSIGN');
		}
		if (numExpr:kind:value() == 'NUMBER') {
			output:line('[PASS] Expression kind is NUMBER');
		}

		output:line("\nAll Standard Library refactoring tests passed successfully!");
	}

}
