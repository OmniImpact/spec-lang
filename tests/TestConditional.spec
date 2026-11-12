#! SpecUnit sweep (from conditional_test.spec): Conditional (Part II) —
#! every conditional shape: 2-arg, 3-arg, 4-arg finally, guard clauses,
#! nesting, bare calls, value-yielding branches, and the scoped region.

Class of SpecUnitTest is TestConditional{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Conditional()]
	];

	## A guard clause: the branch returns from the method.
	Function of String is guard(Int is v){
		Conditional:if(check: { v < 0; }, then: {
			return 'negative';
		});
		return 'non-negative';
	}

	Function is testTwoArgPrimitive(){
		local Int is hits: 0;
		Conditional:if(check: { 1 > 0; }, then: {
			hits: hits + 1;
		});
		Conditional:if(check: { 1 > 2; }, then: {
			hits: hits + 10;
		});
		Assert:areEqualInt(1, hits);
	}

	Function is testThreeArgComposed(){
		local String is which: '';
		Conditional:if(check: { 5 > 3; }, then: {
			which: 'then';
		}, else: {
			which: 'else';
		});
		Conditional:if(check: { 1 > 3; }, then: {
			which: which . '!';
		}, else: {
			which: which . '2';
		});
		Assert:areEqualString('then2', which);
	}

	Function is testFinally(){
		local String is order: '';
		Conditional:if(check: { true; }, then: {
			order: 't';
		}, else: {
			order: 'e';
		}, finally: {
			order: order . 'f';
		});
		Assert:areEqualString('tf', order);
	}

	Function is testGuardClause(){
		local String is g1: guard(5);
		local String is g2: guard(-1);
		Assert:areEqualString('non-negative', g1);
		Assert:areEqualString('negative', g2);
	}

	Function is testNesting(){
		local String is nest: '';
		Conditional:if(check: { 1 < 2; }, then: {
			Conditional:if(check: { 2 < 3; }, then: {
				nest: 'deep';
			});
		});
		Assert:areEqualString('deep', nest);
	}

	Function is testBareCalls(){
		local Int is bareHits: 0;
		if(check: { true; }, then: {
			bareHits: bareHits + 1;
		});
		Assert:areEqualInt(1, bareHits);
	}

	Function is testValueYield(){
		local String is picked: Conditional:if(check: { 3 > 2 }, then: { 'big' }, else: { 'small' });
		local String is picked2: Conditional:if(check: { 3 > 9 }, then: { picked . '!' }, else: { 'tiny' });
		Assert:areEqualString('big', picked);
		Assert:areEqualString('tiny', picked2);
	}

	Function is testScopedRegion(){
		local Int is scopedHits: 0;
		as: Conditional:if(check: { 2 > 1; });
			scopedHits: scopedHits + 1;
		Assert:areEqualInt(1, scopedHits);
	}
}
