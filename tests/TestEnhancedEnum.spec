#! SpecUnit tests for Enhanced Enum (Sum types with shared product members).
#! Verifies that Enums can declare shared fields and methods alongside variants,
#! that variant constructors inherit these shared members, that they can be read,
#! mutated, and called through base references and variant instances, and that
#! pattern matching with Conditional:match works seamlessly with shared members.

Class of SpecUnitTest is TestEnhancedEnum {

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	Function is testSharedFieldDefaults(){
		local Expr is num: Expr:Number(val: 42);
		local Expr is nilExpr: Expr:Nil;

		Assert:areEqualInt(10, num:line);
		Assert:areEqualString('main.spec', num:file);
		Assert:areEqualInt(10, nilExpr:line);
		Assert:areEqualString('main.spec', nilExpr:file);

		Assert:areEqualString('Number', num:name());
		Assert:areEqualString('Nil', nilExpr:name());
	}

	Function is testSharedFieldMutation(){
		local Expr is idExpr: Expr:Ident(name: 'x');
		Assert:areEqualInt(10, idExpr:line);

		idExpr:line: 45;
		idExpr:file: 'parser.spec';

		Assert:areEqualInt(45, idExpr:line);
		Assert:areEqualString('parser.spec', idExpr:file);
		Assert:areEqualString('Ident at parser.spec:45', idExpr:describe());
	}

	Function is testSharedMethodDispatch(){
		local Expr is num: Expr:Number(val: 100);
		local Expr is updated: num:withLine(newLine: 77);

		Assert:areEqualInt(77, num:line);
		Assert:areEqualInt(77, updated:line);
		Assert:areEqualString('Number at main.spec:77', num:describe());

		local SimpleState is r: SimpleState:Running;
		local SimpleState is s: SimpleState:Stopped;

		Assert:isTrue(r:isRunning());
		Assert:isFalse(s:isRunning());

		r:retryCount: 3;
		Assert:areEqualInt(3, r:retryCount);
		Assert:areEqualInt(0, s:retryCount);
	}

	Function is testPatternMatchingAndSharedFields(){
		local Expr is e1: Expr:Number(val: 5);
		e1:line: 20;

		local Expr is e2: Expr:Ident(name: 'myVar');
		e2:line: 30;

		local Int is val1: Conditional:match(on: e1, when: [
			Expr:Number: local Function of Int(Int is val){
				return val + e1:line;
			},
			Expr:Ident: local Function of Int(String is name){
				return e1:line;
			},
			Expr:Add: local Function of Int(Expr is left, Expr is right){
				return 0;
			},
			Expr:Nil: { 0 }
		]);
		Assert:areEqualInt(25, val1);

		local String is desc2: Conditional:match(on: e2, when: [
			Expr:Number: local Function of String(Int is val){
				return 'num';
			},
			Expr:Ident: local Function of String(String is name){
				return name . ':' . e2:line;
			},
			Expr:Add: local Function of String(Expr is left, Expr is right){
				return 'add';
			},
			Expr:Nil: { 'nil' }
		]);
		Assert:areEqualString('myVar:30', desc2);
	}

	Function is testRecursiveSumType(){
		local Expr is left: Expr:Number(val: 10);
		left:line: 1;

		local Expr is right: Expr:Number(val: 20);
		right:line: 2;

		local Expr is add: Expr:Add(left: left, right: right);
		add:line: 3;

		Assert:areEqualInt(1, left:line);
		Assert:areEqualInt(2, right:line);
		Assert:areEqualInt(3, add:line);

		local Int is total: self:evalExpr(expr: add);
		Assert:areEqualInt(30, total);
	}

	local Function of Int is evalExpr(Expr is expr){
		return Conditional:match(on: expr, when: [
			Expr:Number: local Function of Int(Int is val){
				return val;
			},
			Expr:Ident: local Function of Int(String is name){
				return 0;
			},
			Expr:Add: local Function of Int(Expr is left, Expr is right){
				return self:evalExpr(expr: left) + self:evalExpr(expr: right);
			},
			Expr:Nil: { 0 }
		]);
	}
}

Enum is Expr {
	Ident(String is name),
	Number(Int is val),
	Add(Expr is left, Expr is right),
	Nil,

	Int is line: 10;
	String is file: 'main.spec';

	Function of String is describe(){
		return self:name() . ' at ' . self:file . ':' . self:line;
	}

	Function of Expr is withLine(Int is newLine){
		self:line: newLine;
		return self;
	}
}

Enum is SimpleState {
	Starting,
	Running,
	Stopped,

	Int is retryCount: 0;

	Function of Boolean is isRunning(){
		return self:name() == 'Running';
	}
}
