#! SpecUnit sweep (from value_yield_test.spec): the value-yielding branch
#! coverage matrix. Every shape a yield can appear in — use-after-yield,
#! the else side, a guard clause inside a value branch, a yield feeding a
#! binary operand, a yield in return position through a first-class
#! closure, a nested yield in a check position, the bare if() through the
#! scoped provider, and one local yielded on both sides — plus the
#! use-after-yield ARC regression (a yielded owned local must stay alive
#! after the branch).

Class of SpecUnitTest is TestValueYield{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Conditional()],
		['base', 'sys', Output],
		['base', 'sys', as Output()]
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

	# 1. Use-after-yield: the yielded local must survive the branch.
	Function is testUseAfterYield(){
		local String is name: 'long-name-value';
		local String is label: Conditional:if(check: { true }, then: { name }, else: { 'fallback' });
		Assert:areEqualString('long-name-value', label);
		Assert:isTrue(name:length() > 0);
	}

	# 2. Both branches yield; the else side taken.
	Function is testElseYield(){
		local String is picked: Conditional:if(check: { 3 > 9 }, then: { 'big' }, else: { 'small' });
		Assert:areEqualString('small', picked);
	}

	# 3. Guard clause inside a value method.
	Function is testGuardInValueMethod(){
		Assert:areEqualInt(0 - 1, self:guardy(-5));
		Assert:areEqualInt(100, self:guardy(0));
		Assert:areEqualInt(7, self:guardy(7));
	}

	# 4. A yield feeding a binary operand.
	Function is testBinaryOperandYield(){
		local Int is doubled: Conditional:if(check: { true }, then: { 21 }, else: { 0 }) * 2;
		Assert:areEqualInt(42, doubled);
	}

	# 5. A yield in return position (through a first-class closure).
	Function is testReturnPositionYield(){
		local Function of String is pick: { return Conditional:if(check: { true }, then: { 'ret' }, else: { 'no' }); };
		Assert:areEqualString('ret', pick());
	}

	# 6. A nested yield in a check position.
	Function is testNestedCheckYield(){
		Assert:areEqualString('gt', self:nestedCheck(5, 2));
		Assert:areEqualString('le', self:nestedCheck(2, 5));
	}

	# 7. Bare if() yielding through the scoped provider.
	Function is testBareYield(){
		local Int is bare: if(check: { true }, then: { 11 }, else: { 22 });
		Assert:areEqualInt(11, bare);
	}

	# 8. An owned-local yield used on BOTH sides (two yields of one local).
	Function is testDoubleYieldOfOneLocal(){
		local String is shared: 'shared-state';
		local String is first: Conditional:if(check: { true }, then: { shared }, else: { 'x' });
		local String is second: Conditional:if(check: { false }, then: { shared }, else: { 'y' });
		Assert:areEqualString('shared-state', first);
		Assert:areEqualString('y', second);
		Assert:isTrue(shared:length() > 0);
	}
}
