#! Part IV V2/V4: the value-yielding branch coverage matrix.
#! Every shape a yield can appear in, plus the use-after-yield ARC
#! regression (a yielded owned local must stay alive after the branch).

Class is ValueYieldTest{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', Output],
		['base', 'io', as Output()]
	];

	# Guard clause inside a value branch: the mid-body return leaves the
	# METHOD; the trailing expression is the yield.
	Function of Int is guardy(Int is n){
		Conditional:if(check: { n < 0 }, then: {
			return 0 - 1;
		});
		local Int is picked: Conditional:if(check: { n == 0 }, then: { 100 }, else: { n });
		return picked;
	}

	# A nested yield in a CHECK position: the inner branch call is the
	# outer check closure's trailing expression.
	Function of String is nestedCheck(Int is a, Int is b){
		local String is r: Conditional:if(check: { Conditional:if(check: { a > b }, then: { true }, else: { false }) }, then: { 'gt' }, else: { 'le' });
		return r;
	}

	replace Function is init(Map of String to String is args){
		Output:line('=== Value Yield Coverage ===');
		local Int is pass: 0;
		local Int is fail: 0;

		# 1. Use-after-yield: the yielded local must survive the branch.
		local String is name: 'long-name-value';
		local String is label: Conditional:if(check: { true }, then: { name }, else: { 'fallback' });
		Conditional:if(check: { label == 'long-name-value' && name:length() > 0 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] use-after-yield: label=' . label . ' nameLen=' . (name:length() as String));
		});

		# 2. Both branches yield; the else side taken.
		local String is picked: Conditional:if(check: { 3 > 9 }, then: { 'big' }, else: { 'small' });
		Conditional:if(check: { picked == 'small' }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] else-yield: ' . picked);
		});

		# 3. Guard clause inside a value method.
		Conditional:if(check: { self:guardy(-5) == 0 - 1 && self:guardy(0) == 100 && self:guardy(7) == 7 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] guard-in-value');
		});

		# 4. A yield feeding a binary operand.
		local Int is doubled: Conditional:if(check: { true }, then: { 21 }, else: { 0 }) * 2;
		Conditional:if(check: { doubled == 42 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] binary-operand yield: ' . (doubled as String));
		});

		# 5. A yield in return position (through a first-class closure).
		local Function of String is pick: { return Conditional:if(check: { true }, then: { 'ret' }, else: { 'no' }); };
		Conditional:if(check: { pick() == 'ret' }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] return-position yield');
		});

		# 6. A nested yield in a check position.
		Conditional:if(check: { self:nestedCheck(5, 2) == 'gt' && self:nestedCheck(2, 5) == 'le' }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] nested-check yield');
		});

		# 7. Bare if() yielding through the scoped provider.
		local Int is bare: if(check: { true }, then: { 11 }, else: { 22 });
		Conditional:if(check: { bare == 11 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] bare yield: ' . (bare as String));
		});

		# 8. An owned-local yield used on BOTH sides (two yields of one local).
		local String is shared: 'shared-state';
		local String is first: Conditional:if(check: { true }, then: { shared }, else: { 'x' });
		local String is second: Conditional:if(check: { false }, then: { shared }, else: { 'y' });
		Conditional:if(check: { first == 'shared-state' && second == 'y' && shared:length() > 0 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] double-yield of one local');
		});

		Conditional:if(check: { fail == 0 }, then: {
			Output:line('[PASS] value yield: ' . (pass as String) . ' checks');
		}, else: {
			Output:line('[FAIL] value yield: ' . (fail as String) . ' failures');
		});
	}
}
