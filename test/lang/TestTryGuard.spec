#! specunit: suite
#! Value-yield matrix for the try/guard construct:
#! 1. Success yields the body value; the guard never runs.
#! 2. An in-region raiseError yields the guard value with the error bound.
#! 3. An unwind from a CALLED function is caught (post-call check retarget).
#! 4. The guard may re-raise; a nested try catches it (propagation order).
#! 5. Type grounding: the construct's type flows to both regions.
#! 6. Defers pushed in the body region run at the FRAME's exit (Go-style),
#!    not at the catch — and the frame continues after the catch.

Enum is TryProbeKind{
	PROBE
}

Class of SpecUnitTest is TestTryGuard{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Defer()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array]
	];

	Function is testSuccessYieldsBodyValue(){
		local String is v: try(
			body: local Function of String(){ return 'direct'; },
			guard: local Function of String(SpecError is e){ return 'guard:' . e:description; }
		);
		Assert:areEqualString('direct', v);
	}

	Function is testInRegionRaiseYieldsGuardValue(){
		local String is v: try(
			body: local Function of String(){
				:raiseError(error: SpecError:init(kind: TryProbeKind:PROBE, description: 'boom'));
				return 'unreached';
			},
			guard: local Function of String(SpecError is e){ return 'caught:' . e:description; }
		);
		Assert:areEqualString('caught:boom', v);
	}

	local Function is doRaise(){
		:raiseError(error: SpecError:init(kind: TryProbeKind:PROBE, description: 'deep'));
	}

	Function is testCalledFunctionUnwindCaught(){
		local String is v: try(
			body: local Function of String(){
				:doRaise();
				return 'unreached';
			},
			guard: local Function of String(SpecError is e){ return 'deep:' . e:description; }
		);
		Assert:areEqualString('deep:deep', v);
	}

	Function is testGuardReraisePropagatesToOuterTry(){
		local String is outerCaught: '';
		local String is result: try(
			body: local Function of String(){
				return try(
					body: local Function of String(){
						:raiseError(error: SpecError:init(kind: TryProbeKind:PROBE, description: 'first'));
						return 'x';
					},
					guard: local Function of String(SpecError is e){
						:raiseError(error: SpecError:init(kind: TryProbeKind:PROBE, description: 'second'));
						return 'y';
					}
				);
			},
			guard: local Function of String(SpecError is e){
				outerCaught: e:description;
				return 'fallback';
			}
		);
		Assert:areEqualString('second', outerCaught);
		Assert:areEqualString('fallback', result);
	}

	Function is testTypeGroundingInt(){
		local Int is n: try(
			body: local Function of Int(){ return 7; },
			guard: local Function of Int(SpecError is e){ return 0; }
		);
		Assert:areEqualInt(7, n);
		local Int is m: try(
			body: local Function of Int(){
				:raiseError(error: SpecError:init(kind: TryProbeKind:PROBE, description: 'n'));
				return 1;
			},
			guard: local Function of Int(SpecError is e){ return 42; }
		);
		Assert:areEqualInt(42, m);
	}

	local Function of String is deferProbe(Array of String is lg){
		local String is v: try(
			body: local Function of String(){
				local Function is act: local Function(){ lg:add(item: 'cleanup'); };
				Defer:push(action: act);
				:raiseError(error: SpecError:init(kind: TryProbeKind:PROBE, description: 'd'));
				return 'unreached';
			},
			guard: local Function of String(SpecError is e){
				lg:add(item: 'guard');
				return 'g';
			}
		);
		lg:add(item: 'after-try');
		return v;
	}

	Function is testDeferInBodyRunsAtFrameExit(){
		local Array of String is log: Array();
		local String is v: :deferProbe(lg: log);
		Assert:areEqualString('g', v);
		Assert:areEqualString('guard', log:get(index: 0, default: ''));
		Assert:areEqualString('after-try', log:get(index: 1, default: ''));
		Assert:areEqualString('cleanup', log:get(index: 2, default: ''));
	}
}
