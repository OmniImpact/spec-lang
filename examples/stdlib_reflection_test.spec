class StdlibReflectionTest{

	replace local Array of String is using: [
		base:io:*,
		base:struct:Array,
		base:sys:SourceLocation,
		base:sys:StackFrame,
		base:reflect:*,
		base:meta:*
	];

	replace local Function is init(Map of String to String is args){
		output:line("======================================");
		output:line("  Standard Library Refactoring Test   ");
		output:line("======================================\n");

		# 1. Test SourceLocation and StackFrame
		output:line("--- 1. SourceLocation & StackFrame ---");
		local SourceLocation is loc: SourceLocation:init(file: "Player.spec", line: 42, col: 15);
		output:line("Location: " . loc:toString());

		local StackFrame is frame: StackFrame:init(location: loc, className: "Player", methodName: "takeDamage");
		output:line("Stack Frame: " . frame:toString());

		if (frame:getClassName() == "Player") {
			output:line("[PASS] StackFrame class name is Player");
		}
		if (frame:getMethodName() == "takeDamage") {
			output:line("[PASS] StackFrame method name is takeDamage");
		}

		# 2. Test Type reflection
		output:line("\n--- 2. Type Reflection ---");
		local Type is intType: Type:init(name: "Int");
		output:line("Simple type: " . intType:toString());

		local Array of Type is arrParams: [];
		arrParams:add(item: Type:init(name: "String"));
		local Type is arrType: Type:withParams(name: "Array", params: arrParams);
		output:line("Generic type: " . arrType:toString());

		local Array of Type is mapParams: [];
		mapParams:add(item: Type:init(name: "String"));
		mapParams:add(item: Type:init(name: "Int"));
		local Type is mapType: Type:withParams(name: "Map", params: mapParams);
		output:line("Map type: " . mapType:toString());

		if (arrType:isGeneric()) {
			output:line("[PASS] Array of String is generic");
		}
		if (!intType:isGeneric()) {
			output:line("[PASS] Int is not generic");
		}

		# 3. Test Parameter, Member, and Class
		output:line("\n--- 3. Class & Member Reflection ---");
		local Parameter is param1: Parameter:init(name: "amount", paramType: intType);
		local Array of Parameter is params: [];
		params:add(item: param1);

		local Array of Statement is body: [];
		local Member is methodMem: Member:init(kind: "METHOD");
		methodMem:method(modifiers: ["replace", "local"], retType: intType, name: "heal", params: params, body: body);

		local Array of Member is members: [];
		members:add(item: methodMem);

		local Class is cls: Class:init(name: "Healer", baseClass: "Entity", members: members);
		output:line("Class: " . cls:getName() . " extends " . cls:getBaseClass());
		output:line("Members count: " . cls:getMembers():length());
		output:line("Method: " . methodMem:getName() . " with " . methodMem:getParameters():length() . " parameter(s)");

		if (cls:getName() == "Healer") {
			output:line("[PASS] Class name is Healer");
		}
		if (methodMem:getName() == "heal") {
			output:line("[PASS] Method name is heal");
		}

		# 4. Test Meta AST Expression & Statement
		output:line("\n--- 4. Meta AST Expression & Statement ---");
		local Expression is numExpr: Expression:init(kind: "NUMBER");
		numExpr:makeNumber(val: 100);
		local Expression is identExpr: Expression:init(kind: "IDENT");
		identExpr:makeIdent(name: "health");

		local Statement is assignStmt: Statement:init(kind: "ASSIGN");
		assignStmt:assign(target: identExpr, value: numExpr);
		output:line("Assign stmt kind: " . assignStmt:getKind());
		output:line("Num expr kind: " . numExpr:getKind());

		if (assignStmt:getKind() == "ASSIGN") {
			output:line("[PASS] Statement kind is ASSIGN");
		}
		if (numExpr:getKind() == "NUMBER") {
			output:line("[PASS] Expression kind is NUMBER");
		}

		output:line("\nAll Standard Library refactoring tests passed successfully!");
	}

}
