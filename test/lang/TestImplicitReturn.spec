#! specunit: suite

Class of SpecUnitTest is TestImplicitReturn{
	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', as Assert()],
		['base', 'sys', as Conditional()]
	];

	Function of Int is add(Int is a, Int is b){
		a + b;
	}

	Function of String is describe(Int is n){
		if({ n > 0 }, { 'positive' }, { 'non-positive' });
	}

	Function of Int is withEarlierReturn(Int is n){
		if({ n < 0 }, {
			return -1;
		});
		n * 2;
	}

	Function is voidTrailingExpr(){
		local Int is x: 1;
		x + 2;
	}

	Function is testMethodImplicitReturn(){
		Assert:areEqualInt(7, add(a: 3, b: 4));
		Assert:areEqualString('positive', describe(n: 5));
		Assert:areEqualString('non-positive', describe(n: 0));
		Assert:areEqualInt(-1, withEarlierReturn(n: -3));
		Assert:areEqualInt(10, withEarlierReturn(n: 5));
		voidTrailingExpr();
	}

	Function is testClosureImplicitReturn(){
		local Function of Int is dbl: local Function of Int(Int is x){
			x * 2;
		};
		local Function of String is wrap: local Function of String(String is s){
			"[{{s}}]";
		};
		Assert:areEqualInt(12, dbl(6));
		Assert:areEqualString('[hi]', wrap('hi'));
	}
}
