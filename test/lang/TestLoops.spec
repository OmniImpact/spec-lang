#! SpecUnit sweep (from loops_test.spec): the Loops control-flow provider —
#! one as-import serves the loop constructs bare. The bare predicate
#! `while(evaluate:, iteration:)`, `repeat(count:, worker:)` with early
#! stop and full run, the do-while `until(evaluate:, iteration:)` with
#! its at-least-once guarantee, and nested loops whose closures capture.

Class of SpecUnitTest is TestLoops{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];

	# The bare predicate loop: the closures' returns drive it
	# (evaluate true continues; iteration false stops).
	Function is testBareWhile(){
		local Int is total: 0;
		while(
			evaluate: local Function of Boolean(){ return total < 5; },
			iteration: local Function of Boolean(){
				total: total + 1;
				return true;
			}
		);
		Assert:areEqualInt(5, total);
	}

	# The counting loop: exactly N iterations, early stop on false.
	Function is testRepeatEarlyStop(){
		local Int is runs: 0;
		Loops:repeat(count: 10, worker: local Function of Boolean(){
			runs: runs + 1;
			return runs < 4;
		});
		Assert:areEqualInt(4, runs);
	}

	Function is testRepeatFull(){
		local Int is ticks: 0;
		Loops:repeat(count: 3, worker: local Function of Boolean(){
			ticks: ticks + 1;
			return true;
		});
		Assert:areEqualInt(3, ticks);
	}

	# The do-while: the body runs once even when the predicate starts
	# false, then repeats while it holds.
	Function is testUntil(){
		local Int is visits: 0;
		Loops:until(
			evaluate: local Function of Boolean(){ return visits >= 2; },
			iteration: local Function of Boolean(){
				visits: visits + 1;
				return true;
			}
		);
		Assert:areEqualInt(2, visits);
	}

	Function is testUntilAtLeastOnce(){
		local Int is once: 0;
		Loops:until(
			evaluate: local Function of Boolean(){ return true; },
			iteration: local Function of Boolean(){
				once: once + 1;
				return true;
			}
		);
		Assert:areEqualInt(1, once);
	}

	# The loop constructs nest, and their closures capture.
	Function is testNestedLoops(){
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
		Assert:areEqualInt(6, grid);
		Assert:areEqualInt(3, row);
	}
}
