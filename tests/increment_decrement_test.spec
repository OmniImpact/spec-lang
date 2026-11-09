Class is IncrementDecrementTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'struct', Array],
		['base', 'iterator'],
		['base', 'io', as Output()],
		['base', 'iterator', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Int is count: 0;

	replace Function is init(Map of String to String is args){
		Output:line('=== Increment & Decrement Test ===');

		# Case 1: Postfix and prefix statements
		local Int is x: 10;
		x++;
		local Boolean is postIncStmt: x == 11;
		x--;
		local Boolean is postDecStmt: x == 10;
		++x;
		local Boolean is preIncStmt: x == 11;
		--x;
		local Boolean is preDecStmt: x == 10;

		Conditional:if(check: { postIncStmt && postDecStmt && preIncStmt && preDecStmt }, then: {
			Output:line('[PASS] Postfix and prefix statements modify operand in place');
		}, else: {
			Output:line('[FAIL] Postfix and prefix statements');
		});

		# Case 2: Expression semantics
		local Int is y: 5;
		local Int is valPostInc: y++;
		local Boolean is exprPostIncOk: valPostInc == 5 && y == 6;

		local Int is valPreInc: ++y;
		local Boolean is exprPreIncOk: valPreInc == 7 && y == 7;

		local Int is valPostDec: y--;
		local Boolean is exprPostDecOk: valPostDec == 7 && y == 6;

		local Int is valPreDec: --y;
		local Boolean is exprPreDecOk: valPreDec == 5 && y == 5;

		Conditional:if(check: { exprPostIncOk && exprPreIncOk && exprPostDecOk && exprPreDecOk }, then: {
			Output:line('[PASS] Postfix returns previous value; prefix returns updated value');
		}, else: {
			Output:line('[FAIL] Expression return values');
		});

		# Case 3: While loop iteration with increment
		local Int is sum: 0;
		Loops(
			[Int is i: 0],
			evaluate: { i < 5 },
			iterate: {
				sum: sum + i;
				i++;
			}
		);
		Conditional:if(check: { sum == 10 }, then: {
			Output:line('[PASS] While loop with iterate i++');
		}, else: {
			Output:line('[FAIL] While loop with i++, sum=' . sum);
		});

		# Case 4: While loop with decrement
		local Int is steps: 0;
		Loops(
			[Int is n: 5],
			evaluate: { n > 0 },
			iterate: {
				steps++;
				n--;
			}
		);
		Conditional:if(check: { steps == 5 }, then: {
			Output:line('[PASS] While loop with decrement n--');
		}, else: {
			Output:line('[FAIL] While loop with decrement, steps=' . steps);
		});

		# Case 5: Field access increment and decrement
		self:count: 42;
		self:count++;
		local Boolean is fieldIncOk: self:count == 43;
		self:count--;
		local Boolean is fieldDecOk: self:count == 42;
		Conditional:if(check: { fieldIncOk && fieldDecOk }, then: {
			Output:line('[PASS] Field increment and decrement');
		}, else: {
			Output:line('[FAIL] Field increment and decrement');
		});
	}
}
