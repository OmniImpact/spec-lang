#! SpecUnit sweep (from loops_test.spec): the Loops control-flow provider —
#! one as-import serves the loop constructs bare. The bare predicate
#! `while(evaluate:, iteration:)`, `repeat(count:, worker:)` with early
#! stop and full run, the do-while `until(evaluate:, iteration:)` with
#! its at-least-once guarantee, and nested loops whose closures capture.

Class of SpecUnitTest is TestLoops{

	replace Array of Array of String is using: [
		['base', 'iterator', LoopControl],
		['base', 'iterator', LoopCallback],
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

## LoopControl is a real ARC class: stop raises the flag, isStopped
	## reads it, and complete fires the assigned completion callback.
	Function is testLoopControlLifecycle(){
		local LoopControl is c: LoopControl();
		Assert:isFalse(c:isStopped());
		c:stop();
		Assert:isTrue(c:isStopped());

		local Int is fired: 0;
		c:onComplete: local Function(){
			fired: fired + 1;
		};
		c:complete();
		c:complete();
		Assert:areEqualInt(2, fired);

		## A fresh control with the default callback completes as a no-op.
		local LoopControl is fresh: LoopControl();
		fresh:complete();
		Assert:isFalse(fresh:isStopped());
	}

	## LoopCallback is a real Spec class: subclassable with virtual
	## dispatch through onComplete(control:).
	Function is testLoopCallbackLifecycle(){
		local LoopControl is ctrl: LoopControl();
		local LoopCallback is baseCb: LoopCallback();
		baseCb:onComplete(control: ctrl);
		Assert:isFalse(ctrl:isStopped());

		local TestCallbackSub is sub: TestCallbackSub();
		local LoopCallback is asBase: sub;
		asBase:onComplete(control: ctrl);
		Assert:areEqualInt(1, sub:calls);
		Assert:isTrue(ctrl:isStopped());
	}

	## Structurally inlined Loops:times with index parameter, early return
	## (acts as continue), and lexical hygiene against callee's `idx`.
	Function is testTimesInlinedAndHygiene(){
		local Int is idx: 100;
		local Int is sum: 0;
		times(count: 6, worker: local Function(Int is i){
			if({ i == 3 }, { return; });
			sum: sum + i;
		});
		# 0 + 1 + 2 + 4 + 5 = 12, and caller's `idx` is untouched.
		Assert:areEqualInt(12, sum);
		Assert:areEqualInt(100, idx);

		local Int is ticks: 0;
		times(count: 4, worker: { ticks++; });
		Assert:areEqualInt(4, ticks);
	}

	## Structurally inlined Loops:range, including nested ranges and empty range.
	Function is testRangeNestedAndEmpty(){
		local Int is sum: 0;
		range(start: 1, end: 4, worker: local Function(Int is r){
			range(start: 0, end: r, worker: local Function(Int is c){
				sum: sum + r * 10 + c;
			});
		});
		# r=1: 10; r=2: 20+21=41; r=3: 30+31+32=93 -> 144
		Assert:areEqualInt(144, sum);

		local Int is emptyRuns: 0;
		range(start: 5, end: 5, worker: local Function(Int is _i){ emptyRuns++; });
		Assert:areEqualInt(0, emptyRuns);
	}

	## Structurally inlined Loops:rangeStep with positive, negative, and zero step.
	Function is testRangeStep(){
		local Int is posSum: 0;
		rangeStep(start: 0, end: 10, step: 3, worker: local Function(Int is i){
			posSum: posSum + i;
		});
		# 0 + 3 + 6 + 9 = 18
		Assert:areEqualInt(18, posSum);

		local Int is negSum: 0;
		rangeStep(start: 10, end: 0, step: -4, worker: local Function(Int is i){
			negSum: negSum + i;
		});
		# 10 + 6 + 2 = 18
		Assert:areEqualInt(18, negSum);

		local Int is zeroRuns: 0;
		rangeStep(start: 0, end: 5, step: 0, worker: local Function(Int is _i){ zeroRuns++; });
		Assert:areEqualInt(0, zeroRuns);
	}

	## Structurally inlined Loops:forever (value-yielding Boolean worker).
	Function is testForever(){
		local Int is n: 0;
		forever(worker: {
			n++;
			return n < 5;
		});
		Assert:areEqualInt(5, n);

		local Int is m: 0;
		forever(worker: {
			m++;
			m < 3
		});
		Assert:areEqualInt(3, m);
	}

	## Structurally inlined Loops:each over [String].
	Function is testEachStringList(){
		local [String] is words: ['alpha', 'beta', 'gamma'];
		local String is joined: '';
		each(list: words, action: local Function(String is w){
			if({ joined != '' }, { joined: joined . '-'; });
			joined: joined . w;
		});
		Assert:areEqualString('alpha-beta-gamma', joined);
	}

	## Runtime fallback: passing a Function variable (non-literal) still works.
	Function is testRuntimeClosureFallback(){
		local Int is acc: 0;
		local Function is stepFn: local Function(Int is i){
			acc: acc + i;
		};
		Loops:times(count: 5, worker: stepFn);
		# 0 + 1 + 2 + 3 + 4 = 10
		Assert:areEqualInt(10, acc);
	}
}

Class of LoopCallback is TestCallbackSub{
	Int is calls: 0;

	replace Function is onComplete(LoopControl is control){
		:calls: :calls + 1;
		control:stop();
	}
}
