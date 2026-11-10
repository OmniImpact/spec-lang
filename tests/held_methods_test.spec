#! Held functions (PLAN-ENUM Stage 1): receiver-free class-scoped
#! functions dispatched through the class-name prefix. No vtable, no
#! self; bodies see the class's held fields (through the class name)
#! and construct instances under the declaring class's import rules.
#! An instance receiver never reaches a held function.

Class is HeldMath{
	namespace: ['test'];

	held Int is scale: 3;

	held Function of Int is triple(Int is n){
		return n * HeldMath:scale;
	}

	held Function of String is describe(Int is n){
		# A held function calling a sibling held function.
		return 'n=' . (HeldMath:triple(n: n) as String);
	}

	held Function of HeldCounter is freshCounter(){
		# Construction inside a held function: the declaring class's
		# import rules gate it (same-file grant here).
		return HeldCounter:init();
	}

	held Function of Int is withDefault(Int is n : 5){
		return n + 1;
	}
}

Class is HeldCounter{
	namespace: ['test'];

	local Int is value: 0;

	Function is bump(){
		self:value: self:value + 1;
	}

	Function of Int is get(){
		return self:value;
	}
}

Class is HeldMathUser{
	namespace: ['test'];

	Function of Boolean is crossClassCall(){
		# A public held function called through the class-name prefix
		# from another class's instance method.
		return HeldMath:triple(n: 14) == 42;
	}

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];
}

Class is HeldMethodsTest{
	namespace: ['test'];

	replace Function is init(Map of String to String is args){
		local Int is failures: 0;

		Conditional:if(check: { HeldMath:triple(n: 7) == 21 }, then: {
		}, else: {
			Output:line('[FAIL] held function dispatch: ' . (HeldMath:triple(n: 7) as String));
			failures: failures + 1;
		});

		# The held function read the class-held field through the class
		# name (scale=3 -> 7*3=21 was checked above); here the sibling
		# call chains two held functions together.
		Conditional:if(check: { HeldMath:describe(n: 2) == 'n=6' }, then: {
		}, else: {
			Output:line('[FAIL] held function sibling call: ' . HeldMath:describe(n: 2));
			failures: failures + 1;
		});

		# Construction inside a held function.
		local HeldCounter is c: HeldMath:freshCounter();
		c:bump();
		c:bump();
		Conditional:if(check: { c:get() == 2 }, then: {
		}, else: {
			Output:line('[FAIL] held function constructing instances');
			failures: failures + 1;
		});

		# Parameter defaults work in the held form.
		Conditional:if(check: { HeldMath:withDefault() == 6 && HeldMath:withDefault(n: 1) == 2 }, then: {
		}, else: {
			Output:line('[FAIL] held function parameter defaults');
			failures: failures + 1;
		});

		# Cross-class call from instance code.
		local HeldMathUser is u: HeldMathUser:init();
		Conditional:if(check: { u:crossClassCall() }, then: {
		}, else: {
			Output:line('[FAIL] cross-class held function call');
			failures: failures + 1;
		});

		# The strict resolution rule: an instance receiver never
		# reaches a held function — instance methods on the same class
		# keep calling through the class name.
		Conditional:if(check: { HeldMath:triple(n: 1) == 3 }, then: {
		}, else: {
			Output:line('[FAIL] held function repeat call');
			failures: failures + 1;
		});

		Conditional:if(check: { failures == 0 }, then: {
			Output:line('[PASS] held methods test complete');
		}, else: {
			Output:line('[FAIL] held methods test: ' . (failures as String) . ' failures');
		});
	}

	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];
}
