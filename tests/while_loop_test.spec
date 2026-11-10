Class is WhileLoopTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'io', as Output()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== While Loop Test ===');

		# Case 1: Scoped loop variables with named arguments and auto-return
		local Int is sum1: 0;
		Loops(
			[Int is i: 0, Int is max: 10],
			evaluate: { i < max },
			iterate: {
				sum1: sum1 + i;
				i++;
			}
		);
		Conditional:if(check: { sum1 == 45 }, then: {
			Output:line('[PASS] Scoped variables with named arguments and auto-return predicate');
		}, else: {
			Output:line('[FAIL] Scoped variables with named arguments, sum1=' . sum1);
		});

		# Case 2: Positional arguments with function block shorthand
		local Int is prod2: 1;
		Loops(
			[Int is n: 1, Int is limit: 6],
			{ n < limit },
			{
				prod2: prod2 * n;
				n: n + 1;
			}
		);
		Conditional:if(check: { prod2 == 120 }, then: {
			Output:line('[PASS] Positional arguments with function block shorthand');
		}, else: {
			Output:line('[FAIL] Positional arguments, prod2=' . prod2);
		});

		# Case 3: Mixed scope - reading and mutating outer collections and variables
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
		local Boolean is collectedOk: collected:length() == 5 && collected:get(index: 0, default: 0) == 3 && collected:get(index: 4, default: 0) == 15;
		Conditional:if(check: { collectedOk }, then: {
			Output:line('[PASS] Mixed scope: reading outer variables and mutating outer collections');
		}, else: {
			Output:line('[FAIL] Mixed scope collection mutation');
		});

		# Case 4: Nested while loops with scoped state
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
		# row 0: 0+1+2+3 = 6
		# row 1: 10+11+12+13 = 46
		# row 2: 20+21+22+23 = 86
		# total = 138
		Conditional:if(check: { gridSum == 138 }, then: {
			Output:line('[PASS] Nested while loops with scoped state');
		}, else: {
			Output:line('[FAIL] Nested while loops, gridSum=' . gridSum);
		});

		# Case 5: While loop without scoped variables (outer state only)
		local Int is countdown: 5;
		local Int is steps: 0;
		Loops(
			evaluate: { countdown > 0 },
			iterate: {
				countdown: countdown - 1;
				steps: steps + 1;
			}
		);
		Conditional:if(check: { countdown == 0 && steps == 5 }, then: {
			Output:line('[PASS] While loop without scoped variables');
		}, else: {
			Output:line('[FAIL] While loop without scoped variables');
		});

		# Case 6: Mixed scope Map mutations
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
		local Boolean is mapOk: counts:length() == 4 && counts:getInt(key: 'item_0', default: -1) == 0 && counts:getInt(key: 'item_3', default: -1) == 300;
		Conditional:if(check: { mapOk }, then: {
			Output:line('[PASS] Mixed scope Map mutations');
		}, else: {
			Output:line('[FAIL] Mixed scope Map mutations');
		});
	}
}
