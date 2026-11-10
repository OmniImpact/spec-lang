## Regression: class assembly. The `group:` partial mechanism is retired —
## multi-parent assembly is MI: `Class of A, B is Name`. The child sees both
## parents' members; the parents stay independently compilable classes.

Class is CalcArithmetic{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	Function of Int is add(Int is a, Int is b){
		return a + b;
	}
}

Class is CalcText{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];

	Function of String is shout(String is msg){
		return msg . '!';
	}
}

## The assembled class: both parents' members through normal MI.
Class of CalcArithmetic, CalcText is Calc{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
}

## Shared state lives IN the class (the field + the method that touches it).
Class is Accumulator{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];

	local Int is total: 0;

	replace Function is init(Int is start){
		self:total: start;
	}

	Function is bump(Int is by){
		self:total: self:total + by;
	}
}

Class is GroupingTest{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Output],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Regression: Class Assembly (MI) ===');
		local Int is pass: 0;
		local Int is fail: 0;

		# Case 1: the MI assembly exposes both parents' members.
		local Calc is calc: Calc:init();
		local Int is sum: calc:add(a: 2, b: 40);
		Conditional:if(check: { sum == 42 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] MI assembly: expected 42, got ' . sum);
		});

		# Case 2: the second parent's members are reachable on the child.
		local String is shouted: calc:shout(msg: 'grouped');
		Conditional:if(check: { shouted == 'grouped!' }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] MI parents: expected \'grouped!\', got ' . shouted);
		});

		# Case 3: shared state — the field and its method in one class.
		local Accumulator is acc: Accumulator:init(start: 100);
		acc:bump(by: 1);
		Conditional:if(check: { acc:total == 101 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] shared state: expected 101, got ' . acc:total);
		});

		Conditional:if(check: { fail == 0 }, then: {
			Output:line('[PASS] grouping: ' . (pass as String) . ' checks');
		}, else: {
			Output:line('[FAIL] grouping: ' . (fail as String) . ' failures');
		});
	}
}
