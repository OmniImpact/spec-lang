#! SpecUnit sweep (from increment_decrement_test.spec): increment and
#! decrement — postfix/prefix statements, expression return values,
#! while-loop iteration through Loops with ++/--, and field-access
#! increment and decrement.

Class of SpecUnitTest is TestIncrementDecrement{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'iterator'],
		['base', 'sys', as Loops()]
	];

	local Int is count: 0;

	## Case 1: postfix and prefix statements modify the operand in place.
	Function is testPostfixPrefixStatements(){
		local Int is x: 10;
		x++;
		Assert:areEqualInt(11, x);
		x--;
		Assert:areEqualInt(10, x);
		++x;
		Assert:areEqualInt(11, x);
		--x;
		Assert:areEqualInt(10, x);
	}

	## Case 2: postfix returns the previous value; prefix returns the
	## updated value.
	Function is testExpressionSemantics(){
		local Int is y: 5;
		local Int is valPostInc: y++;
		Assert:areEqualInt(5, valPostInc);
		Assert:areEqualInt(6, y);

		local Int is valPreInc: ++y;
		Assert:areEqualInt(7, valPreInc);
		Assert:areEqualInt(7, y);

		local Int is valPostDec: y--;
		Assert:areEqualInt(7, valPostDec);
		Assert:areEqualInt(6, y);

		local Int is valPreDec: --y;
		Assert:areEqualInt(5, valPreDec);
		Assert:areEqualInt(5, y);
	}

	## Case 3: while-loop iteration with increment.
	Function is testWhileLoopWithIncrement(){
		local Int is sum: 0;
		Loops(
			[Int is i: 0],
			evaluate: { i < 5 },
			iterate: {
				sum: sum + i;
				i++;
			}
		);
		Assert:areEqualInt(10, sum);
	}

	## Case 4: while loop with decrement.
	Function is testWhileLoopWithDecrement(){
		local Int is steps: 0;
		Loops(
			[Int is n: 5],
			evaluate: { n > 0 },
			iterate: {
				steps++;
				n--;
			}
		);
		Assert:areEqualInt(5, steps);
	}

	## Case 5: field access increment and decrement.
	Function is testFieldIncrementDecrement(){
		self:count: 42;
		self:count++;
		Assert:areEqualInt(43, self:count);
		self:count--;
		Assert:areEqualInt(42, self:count);
	}
}
