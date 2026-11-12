#! SpecUnit sweep (from while_loop_test.spec): the constructed Loops
#! surface — scoped loop variables with named arguments, positional
#! function-block shorthand, mixed scope (reading outer locals, mutating
#! outer collections and Maps), nested scoped loops, outer-state-only
#! loops, and Map mutations from the iterate closure.

Class of SpecUnitTest is TestWhileLoop{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', Output],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	# Case 1: Scoped loop variables with named arguments and auto-return
	Function is testScopedVarsNamedArgs(){
		local Int is sum1: 0;
		Loops(
			[Int is i: 0, Int is max: 10],
			evaluate: { i < max },
			iterate: {
				sum1: sum1 + i;
				i++;
			}
		);
		Assert:areEqualInt(45, sum1);
	}

	# Case 2: Positional arguments with function block shorthand
	Function is testPositionalShorthand(){
		local Int is prod2: 1;
		Loops(
			[Int is n: 1, Int is limit: 6],
			{ n < limit },
			{
				prod2: prod2 * n;
				n: n + 1;
			}
		);
		Assert:areEqualInt(120, prod2);
	}

	# Case 3: Mixed scope - reading and mutating outer collections and variables
	Function is testMixedScopeCollection(){
		local Array of Int is collected: [];
		local Int is outerMultiplier: 3;
		Loops(
			[Int is idx: 1, Int is total: 5],
			evaluate: { idx <= total },
			iterate: {
				collected:add(item: idx * outerMultiplier);
				idx: idx + 1;
			}
		);
		Assert:isTrue(collected:length() == 5 && collected:get(index: 0, default: 0) == 3 && collected:get(index: 4, default: 0) == 15);
	}

	# Case 4: Nested while loops with scoped state
	# row 0: 0+1+2+3 = 6, row 1: 10+11+12+13 = 46, row 2: 20+21+22+23 = 86
	Function is testNestedScopedLoops(){
		local Int is gridSum: 0;
		Loops(
			[Int is row: 0, Int is rowCount: 3],
			evaluate: { row < rowCount },
			iterate: {
				Loops(
					[Int is col: 0, Int is colCount: 4],
					evaluate: { col < colCount },
					iterate: {
						gridSum: gridSum + (row * 10 + col);
						col: col + 1;
					}
				);
				row: row + 1;
			}
		);
		Assert:areEqualInt(138, gridSum);
	}

	# Case 5: While loop without scoped variables (outer state only)
	Function is testOuterStateOnly(){
		local Int is countdown: 5;
		local Int is steps: 0;
		Loops(
			evaluate: { countdown > 0 },
			iterate: {
				countdown: countdown - 1;
				steps: steps + 1;
			}
		);
		Assert:isTrue(countdown == 0 && steps == 5);
	}

	# Case 6: Mixed scope Map mutations
	Function is testMapMutations(){
		local Map of String to String is counts: [:];
		Loops(
			[Int is k: 0, Int is kMax: 4],
			evaluate: { k < kMax },
			iterate: {
				local String is keyName: 'item_' . k;
				counts:set(key: keyName, value: '' . (k * 100));
				k: k + 1;
			}
		);
		Assert:isTrue(counts:length() == 4 && counts:getInt(key: 'item_0', default: -1) == 0 && counts:getInt(key: 'item_3', default: -1) == 300);
	}
}
