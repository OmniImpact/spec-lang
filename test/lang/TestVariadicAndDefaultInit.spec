#! specunit: suite

Class of SpecUnitTest is TestVariadicAndDefaultInit{
	merge Array of Array of String is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sys', as Introspection()]
	];

	Function of Int is sumNums(Array of Int is *nums){
		local Int is total: 0;
		nums:each(action: local Function(Int is n){
			total: total + n;
		});
		total;
	}

	Function of String is joinWith(String is sep, Array of String is *parts){
		parts:join(separator: sep);
	}

	Function of Int is sumScores(Int is bonus: 0, Map of String to Int is *scores){
		local Int is total: bonus;
		scores:keys():each(action: local Function(String is k){
			total: total + scores:get(key: k, default: 0);
		});
		total;
	}

	Function is testPositionalVarargs(){
		Assert:areEqualInt(0, sumNums());
		Assert:areEqualInt(5, sumNums(5));
		Assert:areEqualInt(15, sumNums(1, 2, 3, 4, 5));
		Assert:areEqualString('', joinWith('-'));
		Assert:areEqualString('a-b-c', joinWith('-', 'a', 'b', 'c'));
	}

	Function is testNamedVarargs(){
		Assert:areEqualInt(0, sumScores());
		Assert:areEqualInt(10, sumScores(bonus: 10));
		Assert:areEqualInt(35, sumScores(bonus: 5, alice: 10, bob: 20));
	}

	Function is testIntrospectionFieldAccess(){
		local VarBox is b: VarBox(title: 'hello', count: 7);
		Assert:isTrue(Introspection:hasField(obj: b, name: 'title'));
		Assert:isTrue(Introspection:hasField(obj: b, name: 'count'));
		Assert:isFalse(Introspection:hasField(obj: b, name: 'missing'));
		Assert:areEqualString('String', Introspection:fieldType(obj: b, name: 'title'));
		Assert:areEqualString('Int', Introspection:fieldType(obj: b, name: 'count'));

		Introspection:setField(obj: b, name: 'title', value: 'updated');
		Assert:areEqualString('updated', b:title);
	}

	Function is testDefaultClassInitAssignsMatchingFields(){
		local VarBox is b: VarBox(title: 'spec', count: 42, ignored: 'nope', count2: 99);
		Assert:areEqualString('spec', b:title);
		Assert:areEqualInt(42, b:count);
		Assert:isTrue(b:active);

		# Override defaulted field too
		local VarBox is b2: VarBox(title: 'off', count: 1, active: false);
		Assert:areEqualString('off', b2:title);
		Assert:areEqualInt(1, b2:count);
		Assert:isFalse(b2:active);

		# Blocked default init
		local BlockedBox is bb: BlockedBox();
		Assert:areEqualInt(99, bb:code);
	}
}

Class is VarBox{
	String is title;
	Int is count;
	Boolean is active: true;
}

Class is BlockedBox{
	Int is code: 99;

	replace Function is init(){
	}
}
