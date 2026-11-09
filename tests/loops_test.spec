#! II.4: the Loops control-flow provider — one as-import
#! serves the loop constructs bare. `while(evaluate:, iteration:)` is
#! the native-inlined predicate loop; `repeat(count:, worker:)` runs a
#! body exactly N times; `until(evaluate:, iteration:)` is the do-while
#! (the body always runs once). `Loops:run(loop:, control:)` drives the
#! Loop-class protocol (the compiler's own loops use it).

Class is LoopsTest{
	replace Array of Array of String is using: [
		['base', 'iterator', as Loops()],
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local Int is pass: 0;
		local Int is fail: 0;

		# The bare predicate loop: the closures' returns drive it
		# (evaluate true continues; iteration false stops).
		local Int is total: 0;
		while(
			evaluate: local Function of Boolean(){ return total < 5; },
			iteration: local Function of Boolean(){
				total: total + 1;
				return true;
			}
		);
		Conditional:if(check: { total == 5 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] bare while: ' . (total as String));
		});

		# The counting loop: exactly N iterations, early stop on false.
		local Int is runs: 0;
		Loops:repeat(count: 10, worker: local Function of Boolean(){
			runs: runs + 1;
			return runs < 4;
		});
		Conditional:if(check: { runs == 4 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] repeat early stop: ' . (runs as String));
		});

		local Int is ticks: 0;
		Loops:repeat(count: 3, worker: local Function of Boolean(){
			ticks: ticks + 1;
			return true;
		});
		Conditional:if(check: { ticks == 3 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] repeat full: ' . (ticks as String));
		});

		# The do-while: the body runs once even when the predicate starts
		# false, then repeats while it holds.
		local Int is visits: 0;
		Loops:until(
			evaluate: local Function of Boolean(){ return visits >= 2; },
			iteration: local Function of Boolean(){
				visits: visits + 1;
				return true;
			}
		);
		Conditional:if(check: { visits == 2 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] until: ' . (visits as String));
		});

		local Int is once: 0;
		Loops:until(
			evaluate: local Function of Boolean(){ return true; },
			iteration: local Function of Boolean(){
				once: once + 1;
				return true;
			}
		);
		Conditional:if(check: { once == 1 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] at-least-once: ' . (once as String));
		});

		# The loop constructs nest, and their closures capture.
		local Int is grid: 0;
		local Int is row: 0;
		while(
			evaluate: local Function of Boolean(){ return row < 3; },
			iteration: local Function of Boolean(){
				local Int is col: 0;
				Loops:repeat(count: 2, worker: local Function of Boolean(){
					col: col + 1;
					grid: grid + 1;
					return true;
				});
				row: row + 1;
				return true;
			}
		);
		Conditional:if(check: { grid == 6 && row == 3 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] nested: ' . (grid as String) . 'x' . (row as String));
		});

		Conditional:if(check: { fail == 0 }, then: {
			Output:line('[PASS] loops: ' . (pass as String) . ' checks');
		}, else: {
			Output:line('[FAIL] loops: ' . (fail as String) . ' failures');
		});
	}
}
