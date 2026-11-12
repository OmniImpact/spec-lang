#! SpecUnit sweep (from stdlib_reflection_test.spec): the standard
#! library refactoring surface — SourceLocation & StackFrame, the meta
#! AST Type/Parameter/Member/ClassInfo records, and the meta AST
#! Expression/Statement kinds.

Class of SpecUnitTest is TestStdlibReflection{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
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

	## 1. SourceLocation & StackFrame: the frame carries its class and
	## method identity.
	Function is testStackFrameIdentity(){
		local SourceLocation is loc: SourceLocation:init(file: 'Player.spec', line: 42, col: 15);
		local StackFrame is frame: StackFrame:init(location: loc, className: 'Player', methodName: 'takeDamage');
		Assert:areEqualString('Player', frame:getClassName());
		Assert:areEqualString('takeDamage', frame:getMethodName());
	}

	## 2. Type reflection: genericity flags on simple and parameterized
	## types.
	Function is testTypeReflection(){
		local Type is intType: Type:init(name: 'Int');
		local Array of Type is arrParams: [];
		arrParams:add(item: Type:init(name: 'String'));
		local Type is arrType: Type:init(name: 'Array');
		arrType:params: arrParams;
		Assert:isTrue(arrType:isGeneric());
		Assert:isFalse(intType:isGeneric());
	}

	## 2b. The parameterized type renderings the old run printed.
	Function is testTypeRendering(){
		local Type is intType: Type:init(name: 'Int');
		local Array of Type is arrParams: [];
		arrParams:add(item: Type:init(name: 'String'));
		local Type is arrType: Type:init(name: 'Array');
		arrType:params: arrParams;
		local Array of Type is mapParams: [];
		mapParams:add(item: Type:init(name: 'String'));
		mapParams:add(item: Type:init(name: 'Int'));
		local Type is mapType: Type:init(name: 'Map');
		mapType:params: mapParams;
		Assert:areEqualString('Int', intType:toString());
		Assert:areEqualString('Array of String', arrType:toString());
		Assert:areEqualString('Map of String to Int', mapType:toString());
	}

	## 3. ClassInfo & Member reflection: the record fields hold what was
	## constructed into them.
	Function is testClassInfoAndMember(){
		local Type is intType: Type:init(name: 'Int');
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
		Assert:areEqualString('Healer', cls:name);
		Assert:areEqualString('Entity', cls:baseClass);
		Assert:areEqualInt(1, cls:members:length());
		Assert:areEqualString('heal', methodMem:name);
		Assert:areEqualInt(1, methodMem:params:length());
	}

	## 4. Meta AST Expression & Statement: the assign statement wires its
	## target and value, and the kinds read back.
	Function is testMetaAstKinds(){
		local Expression is numExpr: Expression:init(kind: ExpressionKind:NUMBER);
		numExpr:str: '100';
		local Expression is identExpr: Expression:init(kind: ExpressionKind:IDENT);
		identExpr:makeIdent(name: 'health');

		local Statement is assignStmt: Statement:init(kind: StatementKind:ASSIGN);
		assignStmt:assign(target: identExpr, value: numExpr);
		Assert:areEqualString('ASSIGN', assignStmt:kind:value());
		Assert:areEqualString('NUMBER', numExpr:kind:value());
	}
}
