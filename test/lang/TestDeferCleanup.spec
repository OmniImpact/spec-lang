#! specunit: suite
#! Cleanup-ordering tests for the Defer floor:
#! 1. A frame's registrations run newest-first on its normal exit.
#! 2. Barriers scope regions: nested defer-ful frames run only their own
#!    registrations at their own exits.
#! 3. On unwind, registered cleanups run BEFORE the frame's handler walk.
#! 4. Push ownership is Go-style: a registration belongs to the frame whose
#!    body performed the push (helper frames own and run their own).

Enum is DeferProbeKind{
	PROBE
}

Class of SpecUnitTest is TestDeferCleanup{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Defer()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array]
	];

	Array of String is log: [];

	## Consumes only the unwind-probe error; assert failures and any other
	## error pass through untouched.
	replace Function of Boolean is SpecErrorHandler(SpecError is error){
		if({ error:description == 'defer-unwind-probe' }, {
			:log:add(item: 'handler');
			return true;
		});
		return false;
	}

	Function is testNormalExitRunsNewestFirst(){
		:log: [];
		:inlinePushHelper(lg: :log);
		Assert:areEqualInt(2, :log:length());
		Assert:areEqualString('b', :log:get(index: 0, default: ''));
		Assert:areEqualString('a', :log:get(index: 1, default: ''));
	}

	## Pushes two registrations and returns; both belong to THIS frame, so
	## both run at its exit, newest-first.
	local Function is inlinePushHelper(Array of String is lg){
		local Function is aAct: local Function(){ lg:add(item: 'a'); };
		local Function is bAct: local Function(){ lg:add(item: 'b'); };
		Defer:push(action: aAct);
		Defer:push(action: bAct);
	}

	Function is testScopingAcrossNestedFrames(){
		:log: [];
		:nestedScopeHelper(lg: :log);
		Assert:areEqualInt(3, :log:length());
		Assert:areEqualString('inner', :log:get(index: 0, default: ''));
		Assert:areEqualString('mid', :log:get(index: 1, default: ''));
		Assert:areEqualString('outer', :log:get(index: 2, default: ''));
	}

	## Outer registers 'outer', calls inner (which registers 'inner').
	## 'inner' must run at the INNER frame's exit — observable because the
	## outer appends 'mid' directly after the inner call returns, before
	## its own exit runs 'outer'.
	local Function is nestedScopeHelper(Array of String is lg){
		local Function is oAct: local Function(){ lg:add(item: 'outer'); };
		Defer:push(action: oAct);
		:innerScopeHelper(lg: lg);
		lg:add(item: 'mid');
	}

	local Function is innerScopeHelper(Array of String is lg){
		local Function is iAct: local Function(){ lg:add(item: 'inner'); };
		Defer:push(action: iAct);
	}

	Function is testUnwindRunsCleanupBeforeHandler(){
		:log: [];
		:unwindHelper(lg: :log);
		Assert:areEqualInt(2, :log:length());
		Assert:areEqualString('cleanup', :log:get(index: 0, default: ''));
		Assert:areEqualString('handler', :log:get(index: 1, default: ''));
	}

	## Registers a cleanup, then raises: the frame's unwind block must run
	## the registration before the SpecErrorHandler walk records 'handler'.
	local Function is unwindHelper(Array of String is lg){
		local Function is cAct: local Function(){ lg:add(item: 'cleanup'); };
		Defer:push(action: cAct);
		:raiseError(error: SpecError:init(kind: DeferProbeKind:PROBE, description: 'defer-unwind-probe'));
	}

	Function is testHelperFrameOwnsItsPushes(){
		:log: [];
		:pushLog(lg: :log, tag: 'a');
		:pushLog(lg: :log, tag: 'b');
		Assert:areEqualInt(2, :log:length());
		Assert:areEqualString('a', :log:get(index: 0, default: ''));
		Assert:areEqualString('b', :log:get(index: 1, default: ''));
	}

	## The registration belongs to pushLog's frame (its body performs the
	## push), so it runs when pushLog exits — before the second call.
	local Function is pushLog(Array of String is lg, String is tag){
		local Function is act: local Function(){ lg:add(item: tag); };
		Defer:push(action: act);
	}
}
